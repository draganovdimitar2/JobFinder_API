from pydantic import BaseModel
from typing import Optional


class JobCreateModel(BaseModel):
    title: str
    description: Optional[str] = ''
    type: str
    category: str


class JobUpdateModel(BaseModel):
    title: str
    description: Optional[str] = ""
    category: str
    type: str
