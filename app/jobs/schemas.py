from pydantic import BaseModel
from typing import Optional, List
import uuid


class JobCreateModel(BaseModel):
    title: str
    description: Optional[str]
    type: str
    category: str


class JobResponseModel(BaseModel):
    uid: uuid.UUID
    title: str
    description: Optional[str]
    type: str
    likes: int
    category: str
    author_uid: uuid.UUID  # Include the foreign key in the response
    is_active: bool
    applicants: List[uuid.UUID] = []
    likedBy: List[uuid.UUID] = []

class JobUpdateModel(BaseModel):
    title: str
    description: str
    category: str
    type: str
