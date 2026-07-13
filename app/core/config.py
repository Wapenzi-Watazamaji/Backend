from pydantic_settings import BaseSettings
from typing import Optional


class Settings(BaseSettings):
    PROJECT_NAME: str 
    DATABASE_URL: str 
    DB_USERNAME: str
    DB_PASSWORD: str 
    SECRET_KEY: str
    REDIS_URL: str
    REDIS_PASSWORD: str

    # Africa's Talking SMS Configuration
    AT_USERNAME: str = "sandbox"
    AT_API_KEY: str = ""
    AT_SENDER_ID: str = ""

    # Firebase Admin SDK Configuration
    FIREBASE_CREDENTIALS_PATH: Optional[str] = None

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()