from pydantic import BaseModel


class ApplicationRequestModel(BaseModel):
    coverLetter: str


class ApplicationUpdateModel(BaseModel):
    status: str
