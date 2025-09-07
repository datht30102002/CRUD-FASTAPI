import uuid

from app.database import Base
from sqlalchemy import TIMESTAMP, Column, String, Integer
from sqlalchemy.sql import func


class User(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    username = Column(String, unique=True, nullable=False)
    password = Column(String(60), nullable=False)
    uid = Column(String, unique=True, nullable=False, default=uuid.uuid4)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    createdAt = Column(TIMESTAMP(timezone=True), nullable=True, server_default=func.now())
    updatedAt = Column(TIMESTAMP(timezone=True), nullable=True, server_default=func.now())
