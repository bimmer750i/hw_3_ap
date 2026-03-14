import secrets
import string
import random
from passlib.context import CryptContext
from jose import jwt
from .config import settings

# Настройка для хеширования паролей
pwd_context = CryptContext(schemes=["argon2"], deprecated="auto")

# Генерация короткого кода
def generate_short_code(length: int = 6) -> str:
    chars = string.ascii_letters + string.digits
    return ''.join(random.choice(chars) for _ in range(length))

# Хеширование пароля
def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

# Проверка пароля
def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

# Генерация API токена
def generate_api_token() -> str:
    return secrets.token_urlsafe(32)  # Генерация случайного токена

# Декодирование JWT токена
def decode_access_token(token: str):
    try:
        payload = jwt.decode(
            token,
            settings.secret_key,
            algorithms=[settings.algorithm]
        )
        return payload
    except jwt.JWTError:
        return None