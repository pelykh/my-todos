from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env")

    database_url: str = "sqlite:///./todos.db"
    jwt_secret: str
    jwt_expire_days: int = 90


@lru_cache
def get_settings() -> Settings:
    return Settings()
