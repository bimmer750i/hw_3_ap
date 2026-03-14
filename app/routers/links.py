from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from dateutil import tz
from app.database import get_db
from app import models, crud, cache, utils
from app.models import schemas
from app.auth import get_current_user, check_admin
from app.models.models import User
from app.models.models import Link
import urllib.parse
import logging

logger = logging.getLogger(__name__)
router = APIRouter()


@router.post("/shorten", response_model=schemas.LinkResponse)
async def create_short_link(
        link: schemas.LinkCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user, use_cache=False)
):
    """
    Создает короткую ссылку. Доступно всем пользователям.
    Если пользователь авторизован, ссылка будет привязана к его аккаунту.
    """
    short_code = link.short_code or utils.generate_short_code()

    if await crud.get_link(db, short_code):
        raise HTTPException(status_code=400, detail="Alias already exists")

    db_link = Link(
        short_code=short_code,
        original_url=link.original_url,
        expires_at=link.expires_at,
        created_at=datetime.utcnow(),
        user_id=current_user.id if current_user else None
    )

    try:
        db.add(db_link)
        await db.commit()
        await db.refresh(db_link)
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if db_link.expires_at:
        ttl = (db_link.expires_at - datetime.utcnow()).total_seconds()
        cache.cache_url(short_code, db_link.original_url, ttl=int(ttl))
    else:
        cache.cache_url(short_code, db_link.original_url)

    return db_link


@router.put("/{short_code}", response_model=schemas.LinkResponse)
async def update_link(
        short_code: str,
        link: schemas.LinkCreate,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Изменяет короткую ссылку. Только для владельцев ссылок.
    """
    try:
        db_link = await crud.get_link(db, short_code)
        if not db_link:
            raise HTTPException(status_code=404, detail="Link not found")

        if not current_user or db_link.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to update this link"
            )

        updates = {
            "original_url": link.original_url,
            "expires_at": link.expires_at
        }

        if link.short_code and link.short_code != short_code:
            if await crud.get_link(db, link.short_code):
                raise HTTPException(status_code=400, detail="New alias already exists")
            updates["short_code"] = link.short_code

        old_short_code = short_code
        for key, value in updates.items():
            setattr(db_link, key, value)

        await db.commit()
        await db.refresh(db_link)

        if "short_code" in updates:
            cache.delete_cached_url(old_short_code)
            cache.cache_url(db_link.short_code, db_link.original_url)

        return db_link
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")


@router.get("/{short_code}/redirect")
async def redirect_to_original(
        short_code: str,
        db: AsyncSession = Depends(get_db)
):
    """
    Перенаправляет на оригинальный URL. Доступно всем.
    """
    cached_url = cache.get_cached_url(short_code)
    if cached_url:
        link = await crud.get_link(db, short_code)
        if link:
            link.hits += 1
            link.last_used = datetime.utcnow()
            try:
                await db.commit()
            except SQLAlchemyError as error:
                await db.rollback()
                logger.error(f"Database error: {error}")
        return {"url": cached_url}

    link = await crud.get_link(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    moscow_tz = tz.gettz("Europe/Moscow")
    current_time = datetime.now(moscow_tz)

    if link.expires_at:
        expires_at = link.expires_at.astimezone(moscow_tz) if link.expires_at.tzinfo else link.expires_at.replace(
            tzinfo=moscow_tz)
        if expires_at < current_time:
            cache.delete_cached_url(short_code)
            raise HTTPException(status_code=410, detail="Link expired")

    link.hits += 1
    link.last_used = current_time
    try:
        await db.commit()
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    if link.expires_at:
        ttl = (expires_at - current_time).total_seconds()
        cache.cache_url(short_code, link.original_url, ttl=int(ttl))
    else:
        cache.cache_url(short_code, link.original_url)

    return {"url": link.original_url}


@router.get("/search")
async def search_links(
        original_url: str = Query(..., description="URL для поиска"),
        db: AsyncSession = Depends(get_db)
):
    """
    Поиск ссылок по оригинальному URL. Доступно всем.
    """
    decoded_url = urllib.parse.unquote(original_url).strip()
    if not decoded_url.startswith(('http://', 'https://')):
        decoded_url = f"https://{decoded_url}"

    links = await crud.get_links_by_url(db, decoded_url)
    if not links:
        raise HTTPException(status_code=404, detail="Ссылки не найдены")

    return links


@router.delete("/{short_code}")
async def delete_link(
        short_code: str,
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Удаляет ссылку. Только для владельцев.
    """
    try:
        db_link = await crud.get_link(db, short_code)
        if not db_link:
            raise HTTPException(status_code=404, detail="Link not found")

        if not current_user or db_link.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Нет прав для удаления"
            )

        await crud.delete_link(db, short_code)
        cache.delete_cached_url(short_code)
        return {"message": "Ссылка удалена"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {str(e)}")


@router.delete("/", summary="Удалить все ссылки")
async def delete_all_links(
        db: AsyncSession = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """
    Удаляет все ссылки. Только для администраторов.
    """
    check_admin(current_user)
    try:
        await db.execute(Link.__table__.delete())
        await db.commit()
        return {"message": "Все ссылки удалены"}
    except SQLAlchemyError as e:
        await db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {str(e)}")