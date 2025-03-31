from pydantic import BaseModel
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
import os
load_dotenv()
class Settings(BaseSettings):
    DATABASE_URL: str = os.getenv("DATABASE_URL")
    REDIS_URL: str = os.getenv("REDIS_URL")
    SECRET_KEY: str = os.getenv("SECRET_KEY")
    ACCESS_TOKEN_EXPIRE: int = int(os.getenv("ACCESS_TOKEN_EXPIRE"))
    UNUSED_LINKS_TTL_DAYS: int = int(os.getenv("UNUSED_LINKS_TTL_DAYS"))

settings = Settings()