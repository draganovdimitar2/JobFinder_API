from pydantic import BaseModel
from typing import Optional


class UserCreateModel(BaseModel):  # registration Model
    username: str
    password: str
    email: str
    firstName: Optional[str] = ""
    lastName: Optional[str] = ""
    role: Optional[str] = 'USER'  # Default role if not provided


class UserLoginModel(BaseModel):
    username: str
    password: str


class UserUpdateRequestModel(BaseModel):
    username: Optional[str] = ''
    email: Optional[str] = ''
    firstName: Optional[str] = ''
    lastName: Optional[str] = ''
    avatar_url: Optional[str] = None


class UserPasswordChangeModel(BaseModel):
    oldPassword: str
    newPassword: str
