from pydantic_settings import BaseSettings


class api_settings(BaseSettings):
    MAX_REFRESH_TOKENS: int = 10
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 15
    REFRESH_TOKEN_EXPIRE_DAYS: int = 60


api_settings = api_settings()  # type: ignore
