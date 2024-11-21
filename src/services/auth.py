from datetime import datetime, timedelta
from typing import Optional

from jose import jwt
from sqlalchemy.orm import Session

from src import models
from src.utils import password
from src.config import get_settings
from src import repositories
from src import schemas
from src import services
import uuid


def authenticate_user(db: Session, email: str, plain_password: str) -> Optional[str]:
    user = repositories.get_user_with_password_by_email(db, email)
    if user is None or not password.verify_password(plain_password, user.password):
        return None
    return user.email


def create_access_token(db: Session, data: dict, expires_delta: Optional[timedelta] = None) -> str:
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.utcnow() + expires_delta
    else:
        expire = datetime.utcnow() + timedelta(hours=get_settings().access_token_expire_hours)
    str_uuid = uuid.uuid4().__str__()
    to_encode.update({"exp": expire, "access_uuid": str_uuid})
    encoded_jwt = jwt.encode(to_encode, get_settings().secret_key, algorithm=get_settings().access_token_alg)
    user: models.User = services.user.get_user_by_email(db, data.get('sub'))
    repositories.set_uuid_token(db, user.id, str_uuid)
    return encoded_jwt
