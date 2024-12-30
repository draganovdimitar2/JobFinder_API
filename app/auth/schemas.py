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
