from sqlalchemy import Column, String, Integer, Boolean, TIMESTAMP
from sqlalchemy.orm import declarative_base
from sqlalchemy.sql import func
from fastapi_users_db_sqlalchemy.generics import GUID
import datetime

Base = declarative_base()

class Link(Base):
    __tablename__ = "links"
    short_code = Column(String, primary_key=True, index=True)
    original_url = Column(String, index=True)
    user_id = Column(GUID, nullable=True)
    created_at = Column(TIMESTAMP(timezone=True), server_default=func.now())
    expires_at = Column(TIMESTAMP(timezone=True), default=func.now() + datetime.timedelta(days=1), nullable=True)
    clicks = Column(Integer, default=0)
    last_clicked_at = Column(TIMESTAMP(timezone=True), nullable=True)
    custom_alias = Column(String, unique=True, nullable=True)
    is_active = Column(Boolean, default=True)