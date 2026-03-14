from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, delete, func
from app.models.models import Link


async def create_link(db: AsyncSession, link: Link):
    db.add(link)
    await db.commit()
    await db.refresh(link)
    return link


async def get_link(db: AsyncSession, short_code: str):
    query = select(Link).where(Link.short_code == short_code)
    result = await db.execute(query)
    return result.scalar_one_or_none()


async def get_links_by_url(db: AsyncSession, url: str):
    """
    Ищет ссылки по original_url (без учёта регистра и пробелов).
    """
    # Удаляем пробелы и приводим к нижнему регистру
    cleaned_url = url.strip().lower()

    # Используем func.lower и func.trim для поиска без учёта регистра и пробелов
    query = select(Link).where(
        func.lower(func.trim(Link.original_url)) == cleaned_url
    )
    result = await db.execute(query)
    return result.scalars().all()


async def delete_link(db: AsyncSession, short_code: str):
    # Сначала находим ссылку
    query = select(Link).where(Link.short_code == short_code)
    result = await db.execute(query)
    link = result.scalar_one_or_none()

    if link:
        await db.delete(link)
        await db.commit()
        return True
    return False


async def delete_expired_links(db: AsyncSession):
    current_time = datetime.utcnow()

    # Находим все просроченные ссылки
    query = select(Link).where(Link.expires_at < current_time)
    result = await db.execute(query)
    expired_links = result.scalars().all()

    # Удаляем каждую
    for link in expired_links:
        await db.delete(link)

    await db.commit()
    return len(expired_links)


# Дополнительные полезные функции

async def update_link_hits(db: AsyncSession, short_code: str):
    """Увеличивает счетчик переходов по ссылке и обновляет last_used"""
    query = select(Link).where(Link.short_code == short_code)
    result = await db.execute(query)
    link = result.scalar_one_or_none()

    if link:
        link.hits += 1
        link.last_used = datetime.utcnow()
        await db.commit()
        await db.refresh(link)
        return link
    return None


async def get_link_stats(db: AsyncSession, short_code: str):
    """Получает статистику по ссылке"""
    query = select(Link).where(Link.short_code == short_code)
    result = await db.execute(query)
    link = result.scalar_one_or_none()

    if link:
        return {
            "hits": link.hits,
            "created_at": link.created_at,
            "last_used": link.last_used,
            "expires_at": link.expires_at
        }
    return None


async def get_user_links(db: AsyncSession, user_id: int):
    """Получает все ссылки пользователя"""
    query = select(Link).where(Link.user_id == user_id)
    result = await db.execute(query)
    return result.scalars().all()


async def update_link(
        db: AsyncSession,
        short_code: str,
        new_original_url: str = None,
        new_expires_at: datetime = None
):
    """Обновляет ссылку"""
    query = select(Link).where(Link.short_code == short_code)
    result = await db.execute(query)
    link = result.scalar_one_or_none()

    if link:
        if new_original_url:
            link.original_url = new_original_url
        if new_expires_at:
            link.expires_at = new_expires_at

        await db.commit()
        await db.refresh(link)
        return link
    return None


async def link_exists(db: AsyncSession, short_code: str):
    """Проверяет, существует ли ссылка с таким short_code"""
    query = select(Link).where(Link.short_code == short_code)
    result = await db.execute(query)
    return result.scalar_one_or_none() is not None