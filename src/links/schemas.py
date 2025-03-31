from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional
import uuid

UUID_ID = uuid.UUID

class LinkBase(BaseModel):
    original_url: str
    custom_alias: Optional[str] = Field(None, min_length=3, max_length=32)
    expires_at: Optional[datetime] = None

class LinkCreate(LinkBase):
    pass

class LinkResponse(LinkBase):
    short_code: str
    created_at: datetime
    clicks: int
    last_clicked_at: Optional[datetime]
    user_id: Optional[UUID_ID]

    class Config:
        from_attributes = True

class LinkStats(BaseModel):
    original_url: str
    created_at: datetime
    clicks: int
    last_clicked_at: Optional[datetime]
    expires_at: Optional[datetime]

class LinkSearchResponse(LinkResponse):
    pass  