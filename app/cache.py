import redis
from app.config import settings

try:
    redis_client = redis.Redis.from_url(settings.redis_url)
    redis_client.ping()  # Проверка соединения
except redis.RedisError as e:
    print(f"Redis connection error: {e}")
    redis_client = None  # В случае ошибки инициализируем как None

def get_cached_url(short_code: str) -> str | None:
    """Получение URL из кэша"""
    if not redis_client:
        return None
        
    try:
        cached_url = redis_client.get(f"url:{short_code}")
        return cached_url.decode() if cached_url else None
    except redis.RedisError:
        return None

def cache_url(short_code: str, url: str, ttl: int = 3600) -> None:
    """Сохранение URL в кэш"""
    if not redis_client:
        return
        
    try:
        redis_client.setex(f"url:{short_code}", ttl, url)
    except redis.RedisError as e:
        print(f"Cache write error: {e}")

def delete_cached_url(short_code: str) -> None:
    """Удаление URL из кэша"""
    if not redis_client:
        return
        
    try:
        redis_client.delete(f"url:{short_code}")
    except redis.RedisError as e:
        print(f"Cache delete error: {e}")