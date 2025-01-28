from pydantic_settings import BaseSettings

from libs.utils_lib.core.config import settings as utils_lib_settings


class api_settings(BaseSettings):
    TOKEN_URL: str = f"http://auth.{utils_lib_settings.DOMAIN}/auth/login"


api_settings = api_settings()  # type: ignore
