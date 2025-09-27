import secrets
import warnings
from typing import Literal

from pydantic import PostgresDsn, computed_field, model_validator
from pydantic_core import MultiHostUrl
from pydantic_settings import BaseSettings
from typing_extensions import Self


class settings(BaseSettings):
    DOMAIN: str = "localhost"
    PROJECT_NAME: str
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    FRONTEND_HOST: str = "http://localhost:5173"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ROOT_USER_PASSWORD: str | None = None

    # Header to get the client IP address (This will be tried first if set)
    CLIENT_IP_HEADER: str = "CF-Connecting-IP"

    # Auth settings
    REQUIRE_USER_VERIFICATION: bool = True

    # Postgres settings
    POSTGRES_CONNECTION_SCHEME: str = "postgressql"
    POSTGRES_SERVER: str
    POSTGRES_READ_SERVER: str | None = None
    POSTGRES_DB: str
    POSTGRES_PORT: int = 5432
    POSTGRES_USER: str
    POSTGRES_PASSWORD: str

    # Redis settings
    REDIS_URL: str

    # NATS settings
    NATS_URL: str

    @computed_field  # type: ignore[prop-decorator]
    @property
    def DATABASE_URL(self) -> PostgresDsn:
        return MultiHostUrl.build(
            scheme=f"{self.POSTGRES_CONNECTION_SCHEME}+asyncpg",
            username=self.POSTGRES_USER,
            password=self.POSTGRES_PASSWORD,
            host=self.POSTGRES_SERVER,
            port=self.POSTGRES_PORT,
            path=self.POSTGRES_DB,
        )

    @computed_field  # type: ignore[prop-decorator]
    @property
    def READ_DATABASE_URL(self) -> PostgresDsn | None:
        if self.POSTGRES_READ_SERVER:
            return MultiHostUrl.build(
                scheme=f"{self.POSTGRES_CONNECTION_SCHEME}+asyncpg",
                username=self.POSTGRES_USER,
                password=self.POSTGRES_PASSWORD,
                host=self.POSTGRES_READ_SERVER,
                port=self.POSTGRES_PORT,
                path=self.POSTGRES_DB,
            )
        return None

    def get_cors_origins(self) -> list[str]:
        """
        Returns a list of allowed CORS origins based on the environment.
        Returns:
            list[str]: A list of allowed CORS origins.
        """
        # Fix this to allow api.{DOMAIN} to avoid CORS issues
        return [self.FRONTEND_HOST]

    CORS_ORIGINS = property(get_cors_origins)

    def get_docs_url(self) -> str | None:
        """
        Returns the URL for the API documentation. (Only available in local and staging environments.)

        Returns:
            str | None: The URL for the API documentation.
        """
        if self.ENVIRONMENT == "local" or self.ENVIRONMENT == "staging":
            return "/docs"
        else:
            return None

    # docs url if environment is local
    DOCS_URL = property(get_docs_url)

    def _check_default_secret(self, var_name: str, value: str | None) -> None:
        if value == "changethis":
            message = (
                f'The value of {var_name} is "changethis", '
                "for security, please change it, at least for deployments."
            )
            if self.ENVIRONMENT == "local":
                warnings.warn(message, stacklevel=1)
            else:
                raise ValueError(message)

    @model_validator(mode="after")
    def _enforce_non_default_secrets(self) -> Self:
        self._check_default_secret("SECRET_KEY", self.SECRET_KEY)
        self._check_default_secret("POSTGRES_PASSWORD", self.POSTGRES_PASSWORD)
        self._check_default_secret("ROOT_USER_PASSWORD", self.ROOT_USER_PASSWORD)

        return self


settings = settings()  # type: ignore
