from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

    OPEN_AI_KEY: str
    MCP_URL: str = "http://localhost:6274/sse"
    PORT: int = 8002  # Default port if not specified in .env
    
    # MCP connection settings
    MCP_RETRY_ATTEMPTS: int = 3
    MCP_RETRY_DELAY: int = 2  # seconds
    MCP_TIMEOUT: int = 30  # seconds


settings = Settings()
