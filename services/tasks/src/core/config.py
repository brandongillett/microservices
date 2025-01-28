from pydantic_settings import BaseSettings


class settings(BaseSettings):
    SERVICE_NAME: str = "tasks"


settings = settings()  # type: ignore
