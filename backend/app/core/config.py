from functools import lru_cache
from pathlib import Path

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    app_name: str = "嘭咔智能电子物料仓库管理系统"
    environment: str = "development"
    database_url: str = "sqlite:///./pengka.db"
    session_hours: int = 8
    cookie_secure: bool = False
    attachment_dir: Path = Path("../storage/attachments")
    max_upload_mb: int = 20
    login_max_attempts: int = 5
    login_lock_minutes: int = 15
    business_timezone: str = "Asia/Shanghai"
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
