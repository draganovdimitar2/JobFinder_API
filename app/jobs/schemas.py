from pydantic import BaseModel
from typing import Optional
import uuid


class JobCreateModel(BaseModel):
    title: str
    description: Optional[str]
    type: str
    category: str


class JobResponseModelWithAuthorName(BaseModel):
    uid: uuid.UUID
    title: str
    description: str
    type: str
    likes: int
    category: str
    is_active: bool
    authorName: str  # This will hold the author's username
    isLiked: bool


class JobUpdateModel(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    category: Optional[str] = None
    type: Optional[str] = None
