from pydantic_settings import BaseSettings

from src.core.config import settings


class APISettings(BaseSettings):
    MAX_REFRESH_TOKENS: int = 10
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 60

    TOKEN_URL: str = f"/{settings.SERVICE_NAME}/login"


api_settings = APISettings()
