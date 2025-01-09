from pydantic_settings import BaseSettings


class settings(BaseSettings):
    SERVICE_NAME: str = "auth"


settings = settings()  # type: ignore
