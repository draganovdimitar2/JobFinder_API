from pydantic import BaseModel, Field
from typing import Optional, List
import uuid


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


class UserPasswordChangeModel(BaseModel):
    oldPassword: str
    newPassword: str
