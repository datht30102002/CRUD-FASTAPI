from pydantic_settings import BaseSettings
from pydantic import  field_validator

from dotenv import load_dotenv

from slowapi import Limiter
from slowapi.util import get_remote_address


load_dotenv()


class Settings(BaseSettings):
    POSTGRES_HOSTNAME: str
    POSTGRES_USER: str = ""
    POSTGRES_PASSWORD: str = ""
    POSTGRES_DB: str = ""
    DATABASE_PORT: int
    SECRET_KEY: str = ""
    root_path: str = ""
    default_apikey_ttl_hour: int = 15 * 24  # in hours
    cors_origins_regex: str = ".*"
    cors_allow_methods: str = "*"
    rate_limit: str = "20/minute"
    show_technical_endpoints: bool = False
    use_authlib_oauth: bool = True

    @field_validator("cors_allow_methods")
    def parse_cors_allow_methods(cls, v):
        """Parse CORS allowed methods."""
        return [method.strip().upper() for method in v.split(",")]

    @field_validator("root_path")
    def parse_root_path(cls, v):
        """Parse root path"""
        return v.rstrip("/")

    class Config:
        env_file = ".env"


settings = Settings()


rate_limiter = Limiter(key_func=get_remote_address)