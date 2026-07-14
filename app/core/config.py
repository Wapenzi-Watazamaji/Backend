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

    # Azure OpenAI Configuration (AI Chat Companion)
    AZURE_OPENAI_ENDPOINT: str = ""
    AZURE_OPENAI_API_KEY: str = ""
    AZURE_OPENAI_CHAT_DEPLOYMENT: str = ""
    AZURE_OPENAI_API_VERSION: str = "2024-10-21"

    # Chat rate-limiting
    CHAT_RATE_LIMIT_PER_MINUTE: int = 20

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()