from pydantic_settings import BaseSettings


class settings(BaseSettings):
    SERVICE_NAME: str = "users"


settings = settings()  # type: ignore
