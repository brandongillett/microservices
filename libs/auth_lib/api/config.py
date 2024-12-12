from pydantic_settings import BaseSettings


class api_settings(BaseSettings):
    roles: list[str] = ["admin", "user"]


api_settings = api_settings()  # type: ignore
