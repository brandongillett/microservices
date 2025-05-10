from pydantic_settings import BaseSettings

from libs.utils_lib.core.config import settings as utils_lib_settings


class api_settings(BaseSettings):
    def get_token_url(self) -> str:
        if utils_lib_settings.ENVIRONMENT == "local":
            return "http://auth.localhost/auth/login"
        else:
            return f"https://auth.{utils_lib_settings.DOMAIN}/auth/login"

    TOKEN_URL = property(get_token_url)


api_settings = api_settings()  # type: ignore
