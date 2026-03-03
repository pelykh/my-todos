from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "sqlite:///./todos.db"
    jwt_secret: str = "change-me-in-production"
    jwt_expire_days: int = 30

    class Config:
        env_file = ".env"


def get_settings() -> Settings:
    return Settings()
