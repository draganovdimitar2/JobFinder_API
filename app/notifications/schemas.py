from pydantic import BaseModel
import uuid


class NotificationResponseModel(BaseModel):
    sender_id: uuid
    message: str
