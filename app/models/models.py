from sqlalchemy import Column, String, DateTime, Integer, ForeignKey, Boolean
from sqlalchemy.orm import relationship
from app.database import Base
from datetime import datetime

class User(Base):
    __tablename__ = "users"
    
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, index=True)
    email = Column(String(100), unique=True, index=True)
    hashed_password = Column(String(200))
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    role = Column(String(50), default="user")
    
    links = relationship("Link", back_populates="owner")

class Link(Base):
    __tablename__ = "links"
    
    short_code = Column(String(50), primary_key=True)
    original_url = Column(String(500), nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow)
    expires_at = Column(DateTime(timezone=True), nullable=True)
    hits = Column(Integer, default=0)
    last_used = Column(DateTime(timezone=True), nullable=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    
    owner = relationship("User", back_populates="links")