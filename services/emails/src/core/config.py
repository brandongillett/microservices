from pydantic_settings import BaseSettings


class settings(BaseSettings):
    SERVICE_NAME: str = "emails"

    # SMTP settings
    SMTP_TLS: bool = True
    SMTP_SSL: bool = False
    SMTP_PORT: int = 587
    SMTP_HOST: str | None = None
    SMTP_USER: str | None = None
    SMTP_PASSWORD: str | None = None
    EMAILS_FROM_EMAIL: str | None = None


settings = settings()  # type: ignore
