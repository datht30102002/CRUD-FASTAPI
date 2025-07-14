from pydantic_settings import BaseSettings
from dotenv import load_dotenv


load_dotenv()


class Settings(BaseSettings):
    POSTGRES_HOSTNAME: str
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "postgres"
    POSTGRES_DB: str = "fastapi-app"
    DATABASE_PORT: int = 5432

    class Config:
        env_file = ".env"


settings = Settings()