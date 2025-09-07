import os


from typing import Annotated
from datetime import  datetime


from fastapi import Request, Query, APIRouter, Depends, HTTPException, Security, status, Header
from fastapi.security import HTTPBearer, APIKeyHeader, APIKeyQuery

from sqlalchemy.orm import Session


from pydantic import BaseModel, Json


from jose import jwt


from app.config import settings, rate_limiter
from app.api_keys.models import api_key_crud
from app.auth.schemas import Authinfo, CheckKey
from app.database import get_db


oauth2_bearer = HTTPBearer()


router = APIRouter()


api_key_query = APIKeyQuery(
    name="api-key", scheme_name="API key query", auto_error=False
)
api_key_header = APIKeyHeader(
    name="x-api-key", scheme_name="API key header", auto_error=False
)


@router.post("/new")
async def get_new_api_key(
    auth_info: Annotated[Authinfo, Depends(oauth2_bearer)],
    request: Request,
    name: Annotated[
        str,
        Query(
            description="set API key name",
        ),
    ],
    config: Annotated[
        Json,
        Query(
            description="Free JSON object that can be used to configure services",
        ),
    ] = None,
    never_expires: Annotated[
        bool,
        Query(
            description="if set, the created API key will never be considered expired",
        ),
    ] = False,
    db: Session = Depends(get_db)
) -> str:
    auth_header = request.headers.get('authorization')
    token = auth_header[len("Bearer "):] if auth_header.startswith("Bearer ") else auth_header
    payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms='HS256')
    """
    Returns:
        api_key: a newly generated API key
    """
    return api_key_crud.create_key(
        db= db,
        name = name,
        user_uid = payload.get("uid"),
        never_expire = never_expires,
        iam_roles =['admin'],
        config= config or {},
    )


@router.delete("/revoke")
async def revoke_api_key(
    auth_info: Annotated[Authinfo, Depends(oauth2_bearer)],
    api_key: Annotated[
        str, Query(..., alias="api-key", description="the api_key to revoke")
    ],
) -> None:
    """
    Revoke an API key associated with my account.
    """
    return api_key_crud.revoke_key(auth_info.user_id, api_key)


@router.patch("/renew")
async def renew_api_key(
    auth_info: Annotated[Authinfo, Depends(oauth2_bearer)],
    api_key: Annotated[
        str, Query(..., alias="api-key", description="the API key to renew")
    ],
    expiration_date: Annotated[
        str | None,
        Query(
            alias="expiration-date",
            description="the new expiration date in ISO format",
        ),
    ] = None,
) -> str | None:
    """
    Renew an API key associated with my account, reactivate it if it was revoked.
    """
    return api_key_crud.renew_key(auth_info.user_id, api_key, expiration_date)


class UsageLog(BaseModel):
    api_key: str | None = None
    name: str
    user_uid: str
    never_expire: bool
    expiration_time: datetime
    last_query_date: datetime | None
    total_queries: int
    iam_roles: list[str] | None
    config: dict | None


@router.get(
    "/list",
    response_model=list[UsageLog],
    response_model_exclude_none=True,
)
def get_api_key_usage_logs(
    request: Request,
    auth_info: Annotated[Authinfo, Depends(oauth2_bearer)],
    db: Session = Depends(get_db)
) -> list[UsageLog]:
    auth_header = request.headers.get('authorization')
    token = auth_header[len("Bearer "):] if auth_header.startswith("Bearer ") else auth_header
    payload = jwt.decode(token, os.getenv('SECRET_KEY'), algorithms='HS256')
    """
    Returns usage information for all API keys
    """
    # TODO Add some sort of filtering on older keys/unused keys?
    return [
        UsageLog(
            api_key=row.api_key,
            name=row.name,
            user_uid=row.user_uid,
            never_expire=row.never_expire,
            expiration_time=row.expiration_time,
            last_query_date=row.last_query_date,
            total_queries=row.total_queries,
            iam_roles=row.iam_roles,
            config=row.config,
        )
        for row in api_key_crud.get_usage_status(db,payload.get("uid"))
    ]


async def api_key_security(
    query_param: Annotated[str, Security(api_key_query)],
    header_param: Annotated[str, Security(api_key_header)],
    db: Session = Depends(get_db)
):
    if not query_param and not header_param:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="An API key must be passed as query or header",
        )

    key_info = api_key_crud.check_key(db, query_param or header_param)

    if key_info:
        return key_info
    else:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Wrong, revoked, or expired API key."
        )



def custom_rate_limiter(func):
    """Customize the rate_limiter depending on our configuration."""
    # If the env variable is not defined, don't use a rate limiter
    if not settings.rate_limit:
        return func
    # Else return the check_api_key function decorated with
    # the rate_limiter configured with our setting
    return rate_limiter.limit(settings.rate_limit)(func)


@router.get(
    "/check_key",
    response_model=CheckKey,
    include_in_schema=settings.show_technical_endpoints,
)
@custom_rate_limiter
async def check_api_key(
    request: Request,
    query_param: Annotated[str, Security(api_key_query)],
    header_param: Annotated[str, Security(api_key_header)],
):
    """
    Check an API KEY validity in the database.
    \f
    Todo:
        * Synchronize database with keycloak.
    """
    return await api_key_security(query_param, header_param)