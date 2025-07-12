from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel


class UserSchema(BaseModel):
    first_name: str
    last_name: str
    createdAt: Optional[datetime] = None
    updatedAt: Optional[datetime] = None

    class Config:
        orm_mode = True
        arbitrary_types_allowed = True


class ListUserResponse(BaseModel):
    status: str
    results: int
    users: List[UserSchema]