from datetime import datetime
from sqlalchemy.orm import Session
from app.models.models import Link
from sqlalchemy import func 

def create_link(db: Session, link: Link):
    db.add(link)
    db.commit()
    db.refresh(link)
    return link

def get_link(db: Session, short_code: str):
    return db.query(Link).filter(Link.short_code == short_code).first()

def get_links_by_url(db: Session, url: str):
    """
    Ищет ссылки по original_url (без учёта регистра и пробелов).
    """
    # Удаляем пробелы и приводим к нижнему регистру
    cleaned_url = url.strip().lower()
    return db.query(Link).filter(func.lower(func.trim(Link.original_url)) == cleaned_url).all()

def delete_link(db: Session, short_code: str):
    link = db.query(Link).filter(Link.short_code == short_code).first()
    if link:
        db.delete(link)
        db.commit()
        return True
    return False

def delete_expired_links(db: Session):
    current_time = datetime.utcnow()
    expired_links = db.query(Link).filter(Link.expires_at < current_time).all()
    for link in expired_links:
        db.delete(link)
    db.commit()
    return len(expired_links)