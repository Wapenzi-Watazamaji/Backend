from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    PROJECT_NAME: str = "binticare"
    DATABASE_URL: str = "sqlite:///./app.db"
    SECRET_KEY: str = "changeme-in-production"

    class Config:
        env_file = ".env"


settings = Settings()
