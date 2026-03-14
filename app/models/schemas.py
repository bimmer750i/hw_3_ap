from pydantic import BaseModel, Field, EmailStr
from datetime import datetime
from typing import Optional

# Схемы для пользователей
class UserBase(BaseModel):
    username: str = Field(..., example="john")
    email: EmailStr = Field(..., example="john@example.com")

class UserCreate(UserBase):
    password: str = Field(..., example="123")

class UserResponse(UserBase):
    id: int
    is_active: bool
    created_at: datetime
    role: str = Field(..., example="user")

    class Config:
        from_attributes = True

# Схемы для токенов
class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel):
    username: Optional[str] = None

# Схемы для ссылок
class LinkCreate(BaseModel):
    original_url: str
    short_code: Optional[str] = None
    expires_at: Optional[datetime] = None

class LinkResponse(LinkCreate):
    short_code: str
    created_at: datetime
    hits: int
    last_used: Optional[datetime]
    user_id: Optional[int]

    class Config:
        from_attributes = True

class LinkStats(BaseModel):
    hits: int
    created_at: datetime
    last_used: Optional[datetime]