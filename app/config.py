from pydantic_settings import BaseSettings
from dotenv import load_dotenv


load_dotenv()


class Settings(BaseSettings):
    POSTGRES_HOSTNAME: str
    POSTGRES_USER: str = "postgres"
    POSTGRES_PASSWORD: str = "123"
    POSTGRES_DB: str = "system-crud"
    DATABASE_PORT: int = 5432

    class Config:
        env_file = ".env"


settings = Settings()