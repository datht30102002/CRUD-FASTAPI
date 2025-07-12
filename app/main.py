from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.users import models, routers
from app.database import engine
from dotenv import load_dotenv


models.Base.metadata.create_all(bind=engine)


load_dotenv()


app = FastAPI()


origins = {
    "http://localhost:8000"
}


app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(routers.router, tags=['Users'], prefix='/api/users')
