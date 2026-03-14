import urllib.parse
from fastapi.logger import logger
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from dateutil import tz
from app.database import get_db
from app import models, crud, cache, utils
from app.models import schemas
from app.auth import get_current_user, check_admin
from app.models.models import User
from app.models.models import Link
router = APIRouter()

@router.post("/shorten", response_model=schemas.LinkResponse)
def create_short_link(
    link: schemas.LinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user, use_cache=False)  # Опциональная аутентификация
):
    """
    Создает короткую ссылку. Доступно всем пользователям.
    Если пользователь авторизован, ссылка будет привязана к его аккаунту.
    """
    # Генерируем короткий код, если он не указан
    short_code = link.short_code or utils.generate_short_code()
    
    # Проверяем, существует ли уже ссылка с таким кодом
    if crud.get_link(db, short_code):
        raise HTTPException(status_code=400, detail="Alias already exists")

    # Создаем новую ссылку
    db_link = Link(
        short_code=short_code,
        original_url=link.original_url,
        expires_at=link.expires_at,
        created_at=datetime.utcnow(),
        user_id=current_user.id if current_user else None  # Привязка к пользователю, если авторизован
    )

    try:
        db.add(db_link)
        db.commit()
        db.refresh(db_link)
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    # Кэширование
    if db_link.expires_at:
        ttl = (db_link.expires_at - datetime.utcnow()).total_seconds()
        cache.cache_url(short_code, db_link.original_url, ttl=int(ttl))
    else:
        cache.cache_url(short_code, db_link.original_url)
    
    return db_link

@router.put("/{short_code}", response_model=schemas.LinkResponse)
def update_link(
    short_code: str,
    link: schemas.LinkCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Обязательная аутентификация
):
    """
    Изменяет короткую ссылку. Только для владельцев ссылок.
    """
    try:
        db_link = crud.get_link(db, short_code)
        if not db_link:
            raise HTTPException(status_code=404, detail="Link not found")

        # Проверка прав (только для авторизованных пользователей)
        if not current_user or db_link.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="You don't have permission to update this link"
            )

        # Обновление данных
        updates = {
            "original_url": link.original_url,
            "expires_at": link.expires_at
        }

        if link.short_code and link.short_code != short_code:
            if crud.get_link(db, link.short_code):
                raise HTTPException(status_code=400, detail="New alias already exists")
            updates["short_code"] = link.short_code

        old_short_code = short_code
        for key, value in updates.items():
            setattr(db_link, key, value)
        
        db.commit()
        db.refresh(db_link)
        
        if "short_code" in updates:
            cache.delete_cached_url(old_short_code)
            cache.cache_url(db_link.short_code, db_link.original_url)
        
        return db_link
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/{short_code}/redirect")
def redirect_to_original(
    short_code: str, 
    db: Session = Depends(get_db)
):
    """
    Перенаправляет на оригинальный URL. Доступно всем.
    """
    # Проверка кэша
    cached_url = cache.get_cached_url(short_code)
    if cached_url:
        link = crud.get_link(db, short_code)
        if link:
            link.hits += 1
            link.last_used = datetime.utcnow()
            try:
                db.commit()
            except SQLAlchemyError as error:
                db.rollback()
                logger.error(f"Database error: {error}")
        return {"url": cached_url}

    # Поиск в БД
    link = crud.get_link(db, short_code)
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    # Проверка срока действия
    moscow_tz = tz.gettz("Europe/Moscow")
    current_time = datetime.now(moscow_tz)
    
    if link.expires_at:
        expires_at = link.expires_at.astimezone(moscow_tz) if link.expires_at.tzinfo else link.expires_at.replace(tzinfo=moscow_tz)
        if expires_at < current_time:
            cache.delete_cached_url(short_code)
            raise HTTPException(status_code=410, detail="Link expired")

    # Обновление статистики
    link.hits += 1
    link.last_used = current_time
    try:
        db.commit()
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

    # Обновление кэша
    if link.expires_at:
        ttl = (expires_at - current_time).total_seconds()
        cache.cache_url(short_code, link.original_url, ttl=int(ttl))
    else:
        cache.cache_url(short_code, link.original_url)

    return {"url": link.original_url}

@router.get("/search")
def search_links(
    original_url: str = Query(..., description="URL для поиска"),
    db: Session = Depends(get_db)
):
    """
    Поиск ссылок по оригинальному URL. Доступно всем.
    """
    decoded_url = urllib.parse.unquote(original_url).strip()
    if not decoded_url.startswith(('http://', 'https://')):
        decoded_url = f"https://{decoded_url}"
    
    links = crud.get_links_by_url(db, decoded_url)
    if not links:
        raise HTTPException(status_code=404, detail="Ссылки не найдены")
    
    return links

@router.delete("/{short_code}")
def delete_link(
    short_code: str,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Только для авторизованных
):
    """
    Удаляет ссылку. Только для владельцев.
    """
    try:
        db_link = crud.get_link(db, short_code)
        if not db_link:
            raise HTTPException(status_code=404, detail="Link not found")

        if not current_user or db_link.user_id != current_user.id:
            raise HTTPException(
                status_code=403,
                detail="Нет прав для удаления"
            )

        crud.delete_link(db, short_code)
        cache.delete_cached_url(short_code)
        return {"message": "Ссылка удалена"}
    except SQLAlchemyError as e:
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {str(e)}")

@router.delete("/", summary="Удалить все ссылки")
def delete_all_links(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)  # Только для админов
):
    """
    Удаляет все ссылки. Только для администраторов.
    """
    check_admin(current_user)
    try:
        db.query(Link).delete()
        db.commit()
        return {"message": "Все ссылки удалены"}
    except SQLAlchemyError as e:
        db.rollback()
        raise HTTPException(status_code=500, detail=f"Ошибка базы данных: {str(e)}")