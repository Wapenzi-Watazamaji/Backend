from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str
    DATABASE_URL: str
    SECRET_KEY: str
    DB_USERNAME: str
    DB_PASSWORD: str
    REDIS_URL: str
    REDIS_PASSWORD: str

    class Config:
        env_file = ".env"


settings = Settings()
