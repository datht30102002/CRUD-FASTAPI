from dataclasses import dataclass
from pydantic import BaseModel


class Token(BaseModel):
    access_token: str
    token_type: str


@dataclass
class KCInfo:
    is_enabled: bool
    roles: list[str]


@dataclass
class Authinfo:
    user_uid: str
    roles: list[str]


class CheckKey(BaseModel):
    user_id: str
    user_login: str
    iam_roles: list | None
    config: dict | None