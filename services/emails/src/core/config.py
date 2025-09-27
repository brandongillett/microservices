from pydantic_settings import BaseSettings

from libs.utils_lib.core.config import settings as utils_lib_settings


class settings(BaseSettings):
    SERVICE_NAME: str = "emails"

    # SMTP settings
    SMTP_TLS: bool = True
    SMTP_PORT: int = 587
    SMTP_HOST: str
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    # Email settings
    EMAILS_FROM_EMAIL: str
    EMAILS_FROM_NAME: str | None = None

    # Assets URL
    ASSETS_URL: str = f"{utils_lib_settings.FRONTEND_HOST}/assets"

    # Tokens URL (for retrieving design tokens)
    def get_tokens_url(self) -> str | None:
        """
        Returns the URL for the tokens.

        Returns:
            str | None: The URL for the tokens.
        """
        # Tokens are rendered in the container so internal URLs are used in dev
        return (
            "http://frontend/assets/tokens"
            if utils_lib_settings.ENVIRONMENT == "local"
            else f"{self.ASSETS_URL}/tokens"
        )

    # assets url
    TOKENS_URL = property(get_tokens_url)


settings = settings()  # type: ignore
