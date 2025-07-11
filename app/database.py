from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import settings

POSTGRES_URL = (
    f"postgresql://{settings.POSTGRES_USER}:{settings.POSTGRES_PASSWORD}@{settings.POSTGRES_HOSTNAME}"
    f":{settings.DATABASE_PORT}/{settings.POSTGRES_DB}"
)
print(POSTGRES_URL)
# Create the engine
engine = create_engine(
    POSTGRES_URL,
    echo=True
)

print("Connecting to:", POSTGRES_URL)

# Create the session
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Create declarative base
Base = declarative_base()

# Dependency to get DB session
def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
