import os
from datetime import timedelta, datetime, timezone
from typing import Annotated

from fastapi.security import HTTPBearer, OAuth2PasswordRequestForm, APIKeyQuery, APIKeyHeader
from fastapi import Depends, HTTPException, status, APIRouter, Security
from sqlalchemy.orm import Session

from app.auth.schemas import Token
from app.database import get_db
from app.users.models import User
from app.api_keys.models import api_key_crud

from jose import jwt, JWTError, ExpiredSignatureError
from passlib.context import CryptContext


router = APIRouter()

bcrypt_context = CryptContext(schemes=['bcrypt'], deprecated='auto')
oauth2_bearer = HTTPBearer()


api_key_query = APIKeyQuery(
    name="api-key", scheme_name="API key query", auto_error=False
)
api_key_header = APIKeyHeader(
    name="x-api-key", scheme_name="API key header", auto_error=False
)


def authenticate_user(usernane:str, password: str, db: Session):
    user = db.query(User).filter(User.username == usernane).first()
    if not user:
        return False
    if not bcrypt_context.verify(password, user.password):
        return False
    return user


def create_access_token(uid: str, expires_delta: timedelta):
    encode = {'uid': uid}
    expires = datetime.now(timezone.utc) + expires_delta
    encode.update({'exp': expires})
    return jwt.encode(encode, os.getenv('SECRET_KEY'), algorithm='HS256')


def get_current_user(token: Annotated[str, Depends(oauth2_bearer)]):
    try:
        payload = jwt.decode(token.credentials, os.getenv('SECRET_KEY'), algorithms='HS256')
        username: str = payload.get('username')
        if username is None:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                                detail='Could not validate user.')
        return {'username': username}
    except ExpiredSignatureError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail="Token is expired")
    except JWTError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail='Could not validate user.')


@router.post("/token", response_model=Token)
async def login_access_token(requests:OAuth2PasswordRequestForm= Depends(), db: Session=Depends(get_db)):
    user = authenticate_user(usernane=requests.username, password=requests.password, db=db)
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED,
                            detail= "Could not validate user")
    token = create_access_token(user.uid, timedelta(minutes=20))
    return {'access_token': token, 'token_type': 'bearer'}