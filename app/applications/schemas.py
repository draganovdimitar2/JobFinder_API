from pydantic import BaseModel
from typing import Optional
import uuid


class ApplicationRequestModel(BaseModel):
    coverLetter: str
