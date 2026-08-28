"""应用配置。"""
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    SECRET_KEY: str = "prod-secret-key-change-123456789"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    REDIS_URL: str = "redis://127.0.0.1:6379/0"
    # 头像存储目录
    UPLOAD_DIR: str = "./uploads"

settings = Settings()