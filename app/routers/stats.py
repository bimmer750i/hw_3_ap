from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.database import get_db
from app.models import models, schemas
from app.models.models import Link

router = APIRouter()


@router.get("/{short_code}/stats", response_model=schemas.LinkStats)
async def get_link_stats(short_code: str, db: AsyncSession = Depends(get_db)):
    result = await db.execute(
        select(models.Link).where(Link.short_code == short_code)
    )
    link = result.scalar_one_or_none()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")

    return {
        "hits": link.hits,
        "created_at": link.created_at,
        "last_used": link.last_used,
    }