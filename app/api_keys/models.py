import hashlib
import threading
import uuid
from typing import List
from datetime import datetime, UTC, timedelta

from sqlalchemy import (Column, Integer, String, ForeignKey, Boolean,
                        TIMESTAMP,
                        JSON, desc)
from sqlalchemy.sql import func
from sqlalchemy.orm import Session


from app.database import Base, SessionLocal
from app.config import settings


class APIKey(Base):
    __tablename__ = "api_keys"
    api_key = Column(String, primary_key=True, index=True)
    name = Column(String)
    user_uid = Column(String, ForeignKey("users.uid"))
    is_active = Column(Boolean, default=True)
    never_expire = Column(Boolean, default=False)
    expiration_time = Column(TIMESTAMP(timezone=True), nullable=True, server_default=func.now())
    last_query_date = Column(TIMESTAMP(timezone=True), nullable=True, server_default=func.now())
    total_queries = Column(Integer, default=0)
    iam_roles = Column(JSON, default={})
    config = Column(JSON, default={})

    @classmethod
    def hash_api_key(self, api_key):
        return hashlib.sha256(api_key.encode("utf-8")).hexdigest()

    @classmethod
    def create_key(
            self,
            db: Session,
            name: str,
            user_uid: str,
            never_expire: bool,
            iam_roles: list[str],
            config: dict,
    ) -> str:
        api_key = str(uuid.uuid4())
        db_api_key = APIKey(
            api_key=self.hash_api_key(api_key),
            name=name,
            user_uid=user_uid,
            never_expire=never_expire,
            expiration_time=datetime.now(UTC)
            + timedelta(hours=settings.default_apikey_ttl_hour),
            last_query_date=datetime.now(UTC),
            iam_roles=iam_roles,
            config=config,
        )
        db.add(db_api_key)
        db.commit()
        db.refresh(db_api_key)
        return api_key

    @classmethod
    def _update_usage(cls, api_key: str) -> None:
        db: Session = SessionLocal()
        try:
            row = db.query(cls).filter(cls.api_key == cls.hash_api_key(api_key)).first()
            if row:
                row.total_queries += 1
                row.last_query_date = datetime.now(UTC)
                db.commit()
        except Exception:
            db.rollback()
            raise
        finally:
            db.close()

    @classmethod
    def get_usage_status(cls, db: Session, user_uid: str) -> List["APIKey"]:
        """
        Lấy danh sách API keys của user, sắp xếp theo latest_query_date (mới nhất trước).
        """
        return (
            db.query(cls)
            .filter(cls.user_uid == user_uid)
            .order_by(desc(cls.last_query_date))
            .all()
        )

    @classmethod
    def check_key(cls, db: Session, api_key: str) -> dict | None:
        """
        Checks if an API key is valid (ORM style with Session)
        """
        row = (
            db.query(cls)
            .filter(
                (cls.api_key == cls.hash_api_key(api_key)) &
                (cls.never_expire | (cls.expiration_time > datetime.now(UTC)))
            )
            .first()
        )
        if not row:
            return None

        # convert ORM object -> dict
        response = {
            "user_uid": row.user_uid,
            "is_active": row.is_active,
            "iam_roles": row.iam_roles,
            "config": row.config,
            "last_query_date": row.last_query_date,
        }

        if not response["is_active"]:
            return None

        # cập nhật usage async
        threading.Thread(target=cls._update_usage, args=(api_key,)).start()

        return response


api_key_crud = APIKey()