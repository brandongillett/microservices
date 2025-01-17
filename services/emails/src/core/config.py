from pydantic_settings import BaseSettings


class settings(BaseSettings):
    SERVICE_NAME: str = "emails"


settings = settings()  # type: ignore
