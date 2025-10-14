from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SERVICE_NAME: str = "users"


settings = Settings()
