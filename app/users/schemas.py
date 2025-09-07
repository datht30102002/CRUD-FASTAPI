from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class UserSchema(BaseModel):
    id: int
    uid: str
    first_name: str
    last_name: str
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class UserCrateSchema(BaseModel):
    username: str
    password: str


class ListUserResponse(BaseModel):
    status: str
    results: int
    users: List[UserSchema]


class UserUpdateSchema(BaseModel):
    first_name: str
    last_name: str
