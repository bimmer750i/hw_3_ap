from pydantic_settings import BaseSettings, SettingsConfigDict

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

    model_config = SettingsConfigDict(
            env_file=".env",  # Указываем файл .env
            env_file_encoding="utf-8",  # Явно указываем кодировку
            extra="ignore"  # Игнорировать лишние поля
        )

# Создаем экземпляр настроек
settings = Settings()