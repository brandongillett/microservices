import emails  # type: ignore
from celery import Celery  # type: ignore

from libs.utils_lib.core.config import settings as utils_lib_settings
from src.core.config import settings

c_app = Celery(
    "tasks",
    broker=utils_lib_settings.REDIS_URL,
    backend=utils_lib_settings.REDIS_URL,
    broker_connection_retry_on_startup=True,
)


@c_app.task  # type: ignore
def send_email(email_to: str, subject: str, html: str) -> str:
    """
    Sends an email.

    Args:
        email (str): The email to send the message to.
        subject (str): The subject of the email.
        html (str): The HTML content of the email.
    """
    message = emails.Message(
        subject=subject,
        html=html,
        mail_from=(utils_lib_settings.PROJECT_NAME, settings.EMAILS_FROM_EMAIL),
    )
    smtp_options = {"host": settings.SMTP_HOST, "port": settings.SMTP_PORT}
    if settings.SMTP_TLS:
        smtp_options["tls"] = True
    elif settings.SMTP_SSL:
        smtp_options["ssl"] = True
    if settings.SMTP_USER:
        smtp_options["user"] = settings.SMTP_USER
    if settings.SMTP_PASSWORD:
        smtp_options["password"] = settings.SMTP_PASSWORD

    try:
        response = message.send(to=email_to, smtp=smtp_options)
        if response.status_code != 250:
            return f"Failed to send email, response: {response.status_text}"
        return "Email sent successfully"
    except Exception as e:
        return str(e)
