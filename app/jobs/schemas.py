from pydantic import BaseModel
from typing import Optional
import uuid


class JobCreateModel(BaseModel):
    title: str
    description: Optional[str] = ''
    type: str
    category: str


class JobResponseModelWithAuthorName(BaseModel):
    _id: uuid.UUID
    title: str
    description: str
    type: str
    likes: int
    category: str
    isActive: bool
    authorName: str  # This will hold the author's username
    isLiked: bool


class JobUpdateModel(BaseModel):
    title: str
    description: Optional[str] = ""
    category: str
    type: str
