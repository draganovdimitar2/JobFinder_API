from pydantic import BaseModel
from typing import Optional


class UserCreateModel(BaseModel):  # registration Model
    username: str
    password: str
    email: str
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    role: Optional[str] = 'user'  # Default role if not provided


class UserLoginModel(BaseModel):
    email: str
    password: str
