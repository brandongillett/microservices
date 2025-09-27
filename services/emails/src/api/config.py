from pydantic_settings import BaseSettings

from libs.utils_lib.core.config import settings as utils_lib_settings


class api_settings(BaseSettings):
    def get_token_url(self) -> str:
        scheme = "http" if utils_lib_settings.ENVIRONMENT == "local" else "https"
        return f"{scheme}://api.{utils_lib_settings.DOMAIN}/auth/login"

    TOKEN_URL = property(get_token_url)


api_settings = api_settings()  # type: ignore
