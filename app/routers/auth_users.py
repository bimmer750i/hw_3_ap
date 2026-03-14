from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from datetime import timedelta
from app.database import get_db
from app import models, utils
from app.models import schemas
from app.auth import create_access_token
from app.config import settings
from app.models.models import User

router = APIRouter(tags=["auth_users"])


@router.post("/register", response_model=schemas.UserResponse)
async def register(user: schemas.UserCreate, db: AsyncSession = Depends(get_db)):
    """
    Регистрирует нового пользователя.
    """
    result = await db.execute(
        select(User).where(
            or_(User.email == user.email, User.username == user.username)
        )
    )
    existing_user = result.scalar_one_or_none()

    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="User with this email or username already exists"
        )

    hashed_password = utils.get_password_hash(user.password)

    db_user = User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        role="user"
    )

    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)

    return db_user


@router.post("/login", response_model=schemas.Token)
async def login(
        username: str,
        password: str,
        db: AsyncSession = Depends(get_db)
):
    """
    Аутентифицирует пользователя и возвращает JWT токен.
    """
    user = await authenticate_user(db, username, password)

    access_token_expires = timedelta(minutes=settings.access_token_expire_minutes)
    access_token = create_access_token(
        data={"sub": user.username},
        expires_delta=access_token_expires
    )

    return {
        "access_token": access_token,
        "token_type": "bearer"
    }


async def authenticate_user(db: AsyncSession, username: str, password: str) -> User:
    """
    Аутентифицирует пользователя по username и password.
    """
    result = await db.execute(
        select(User).where(User.username == username)
    )
    user = result.scalar_one_or_none()

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )

    if not utils.verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect password"
        )

    return user