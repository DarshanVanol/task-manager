from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    DATABASE_URL: str
    APP_NAME: str
    PORT:int
    DJANGO_SECRET_KEY: str
    JWT_ALGORITHM: str


settings = Settings()
