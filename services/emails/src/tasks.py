from celery import Celery  # type: ignore

from libs.utils_lib.core.config import settings as utils_lib_settings

c_app = Celery(
    "tasks", broker=utils_lib_settings.REDIS_URL, backend=utils_lib_settings.REDIS_URL
)


@c_app.task  # type: ignore
def send_email(email: str, subject: str, message: str) -> str:
    """
    Sends an email.

    Args:
        email (str): The email to send the message to.
        subject (str): The subject of the email.
        message (str): The message to send.
    """
    return f"Sending email to {email} with subject {subject} and message {message}."
