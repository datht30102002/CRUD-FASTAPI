from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from dotenv import load_dotenv

from app.auth import auth as auth_routers
from app.users import models, routers as user_routers
from app.api_keys import routers as api_key_routers
from app.database import engine
from app.config import rate_limiter
from slowapi.errors import RateLimitExceeded
from slowapi import  _rate_limit_exceeded_handler


models.Base.metadata.create_all(bind=engine)


load_dotenv()


origins = {
    "http://localhost:8000"
}


def get_application() -> FastAPI:
    application = FastAPI()
    application.add_middleware(
        CORSMiddleware,
        allow_origins=['*'],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    application.state.limiter = rate_limiter
    application.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
    application.include_router(user_routers.router, tags=['Users'], prefix='/api/users')
    application.include_router(auth_routers.router, tags=['Auth'], prefix='/api/auth')
    application.include_router(api_key_routers.router, tags=['Api-key'], prefix='/api/api-key')
    return application


app = get_application()
