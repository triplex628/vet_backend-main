from pydantic import BaseModel
from typing import Optional


class UserBase(BaseModel):
    email: str


class User(UserBase):
    id: int
    is_active: bool
    is_purchased: bool
    is_subscribed: bool
    is_admin: bool = False
    is_approved: bool = False


class UserCreate(UserBase):
    password: str
    approve_code: int
    is_purchased: bool = False
    is_subscribed: bool = False


class UserAuth(BaseModel):
    email: str
    password: str


class UserApproveCode(BaseModel):
    code: int


class UserEmail(BaseModel):
    email: str


class UserConfirmResetPassword(BaseModel):
    email: str
    code: int
    new_password: str
