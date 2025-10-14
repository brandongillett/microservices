from pydantic import computed_field
from pydantic_settings import BaseSettings

from libs.utils_lib.core.config import settings as utils_lib_settings


class APISettings(BaseSettings):
    @computed_field  # type: ignore[prop-decorator]
    @property
    def TOKEN_URL(self) -> str:
        scheme = "http" if utils_lib_settings.ENVIRONMENT == "local" else "https"
        return f"{scheme}://api.{utils_lib_settings.DOMAIN}/auth/login"


api_settings = APISettings()
