import secrets
import warnings
from typing import Literal

from pydantic import model_validator
from pydantic_settings import BaseSettings
from typing_extensions import Self


class settings(BaseSettings):
    DOMAIN: str = "localhost"
    PROJECT_NAME: str
    ENVIRONMENT: Literal["local", "staging", "production"] = "local"
    FRONTEND_HOST: str = "http://localhost:5173"
    SECRET_KEY: str = secrets.token_urlsafe(32)
    ROOT_USER_PASSWORD: str

    # MySQL settings
    MYSQL_SERVER: str
    MYSQL_DATABASE: str
    MYSQL_PORT: int = 3306
    MYSQL_USER: str
    MYSQL_PASSWORD: str

    # Redis settings
    REDIS_URL: str
    REDIS_TOKENS_URL: str

    # RabbitMQ settings
    RABBITMQ_SERVER: str
    RABBITMQ_PORT: int = 5672
    RABBITMQ_USER: str
    RABBITMQ_PASSWORD: str

    def get_cors_origins(self) -> list[str]:
        if self.ENVIRONMENT == "local":
            return ["*"]
        else:
            return [self.FRONTEND_HOST]

    CORS_ORIGINS = property(get_cors_origins)

    def get_rabbitmq_url(self) -> str:
        """
        Returns the RabbitMQ URL.

        Returns:
            str: The RabbitMQ URL.
        """
        return f"amqp://{self.RABBITMQ_USER}:{self.RABBITMQ_PASSWORD}@{self.RABBITMQ_SERVER}:{self.RABBITMQ_PORT}"

    RABBITMQ_URL = property(get_rabbitmq_url)

    def get_database_url(self) -> str:
        """
        Returns the database URL.

        Returns:
            str: The database URL.
        """
        return f"mysql+aiomysql://{self.MYSQL_USER}:{self.MYSQL_PASSWORD}@{self.MYSQL_SERVER}:{self.MYSQL_PORT}/{self.MYSQL_DATABASE}"

    DATABASE_URL = property(get_database_url)

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
        self._check_default_secret("MYSQL_PASSWORD", self.MYSQL_PASSWORD)
        self._check_default_secret("ROOT_USER_PASSWORD", self.ROOT_USER_PASSWORD)
        self._check_default_secret("RABBITMQ_PASSWORD", self.RABBITMQ_PASSWORD)

        return self


settings = settings()  # type: ignore
