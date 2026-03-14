from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import models, schemas
from app.models.models import Link

router = APIRouter()

@router.get("/{short_code}/stats", response_model=schemas.LinkStats)
def get_link_stats(short_code: str, db: Session = Depends(get_db)):
    link = db.query(models.Link).filter(Link.short_code == short_code).first()
    if not link:
        raise HTTPException(status_code=404, detail="Link not found")
    
    return {
        "hits": link.hits,
        "created_at": link.created_at,
        "last_used": link.last_used,
    }