from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    # Настройки аутентификации
    secret_key: str  
    algorithm: str = "HS256"  
    access_token_expire_minutes: int = 30  
    
    # Настройки базы данных
    database_url: str  
    
    # Настройки Redis
    redis_url: str
    
    # Настройки администратора
    admin_username: str  
    admin_password: str  
    admin_email: str 

    class Config:
        env_file = ".env"  # Указываем файл .env для загрузки переменных окружения

# Создаем экземпляр настроек
settings = Settings()