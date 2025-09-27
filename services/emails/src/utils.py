import asyncio
import json
import logging
import time
from pathlib import Path
from typing import Any
from uuid import UUID

import httpx
from jinja2 import Environment, FileSystemLoader, select_autoescape
from pydantic_settings import BaseSettings

from libs.auth_lib.core.security import security_settings as auth_lib_security_settings
from libs.auth_lib.utils import gen_email_verification_token
from libs.utils_lib.core.config import settings as utils_lib_settings
from src.core.config import settings
from src.tasks import send_email

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class utils_settings(BaseSettings):
    # Cache settings
    CACHE_TTL_SECONDS: int = 0 if utils_lib_settings.ENVIRONMENT == "local" else 600


utils_settings = utils_settings()  # type: ignore

_cached_tokens: dict[str, Any] | None = None
_cache_timestamp: float | None = None
_cache_lock = asyncio.Lock()


# Email Generation Functions
async def load_tokens() -> None:
    """
    Loads and caches design tokens.
    """
    global _cached_tokens, _cache_timestamp

    async with _cache_lock:
        # Check if tokens are already cached and not expired (double-checked locking)
        now = time.time()
        cache_expired = (
            _cache_timestamp is None
            or (now - _cache_timestamp) > utils_settings.CACHE_TTL_SECONDS
        )
        if _cached_tokens is not None and not cache_expired:
            return

        token_files = ["color.json", "typography.json"]

        tokens: dict[str, Any] = {}

        async with httpx.AsyncClient(timeout=5.0) as client:
            for filename in token_files:
                url = f"{settings.TOKENS_URL}/{filename}"
                try:
                    response = await client.get(url)
                    response.raise_for_status()
                    data = response.json()
                    key = filename.removesuffix(".json")
                    tokens[key] = data
                except (httpx.HTTPError, json.JSONDecodeError) as e:
                    raise RuntimeError(f"Failed to load token from {url}: {e}")

        _cached_tokens = tokens
        _cache_timestamp = time.time()


async def get_base_context() -> dict[str, Any]:
    """
    Returns the base context for email templates.

    Returns:
        dict[str, Any]: A dictionary containing the base context.
    """
    global _cached_tokens, _cache_timestamp

    # Check if tokens are cached and not expired
    now = time.time()
    cache_expired = (
        _cache_timestamp is None
        or (now - _cache_timestamp) > utils_settings.CACHE_TTL_SECONDS
    )

    if _cached_tokens is None or cache_expired:
        logger.info("Loading design tokens...")
        await load_tokens()

    return {
        "project_name": utils_lib_settings.PROJECT_NAME,
        "project_url": utils_lib_settings.FRONTEND_HOST,
        "assets_url": settings.ASSETS_URL,
        "tokens": _cached_tokens,
    }


async def render_email_template(*, template_name: str, context: dict[str, Any]) -> str:
    """
    Renders an email template with the given context.
    Args:
        template_name: The name of the template file (without extension).
        context: A dictionary containing the context for rendering the template.

    Returns:
        str: The rendered HTML content of the email template.
    """
    base_path = Path.cwd() / "src" / "email-templates"

    base_context = await get_base_context()

    merged_context = {**base_context, **context}

    env = Environment(
        loader=FileSystemLoader(str(base_path)),
        autoescape=select_autoescape(["html", "xml"]),
        enable_async=True,
    )

    template = env.get_template(f"{template_name}.html")
    return await template.render_async(merged_context)


# Generate links
def get_verification_link(user_id: UUID) -> str:
    """
    Generates a verification link for the user.

    Args:
        user_id: The ID of the user.

    Returns:
        str: The verification link.
    """
    scheme = "http" if utils_lib_settings.ENVIRONMENT == "local" else "https"

    verification_base_url = (
        f"{scheme}://api.{utils_lib_settings.DOMAIN}/auth/verification/email/"
    )
    verification_token = gen_email_verification_token(user_id)
    return f"{verification_base_url}{verification_token}"


def get_password_reset_link(token: str) -> str:
    """
    Generates a password reset link for the user.

    Args:
        user_id: The ID of the user.

    Returns:
        str: The password reset link.
    """
    return f"{utils_lib_settings.FRONTEND_HOST}/reset-password?token={token}"


# Email Sending Functions
async def send_verification(user_id: UUID, username: str, email: str) -> None:
    """
    Sends a verification email to the user.

    Args:
        user_id: The ID of the user.
        username: The username of the user.
        verification_token: The verification token for the user.
    """
    subject = "Verify Your Email Address"

    context = {
        "subject": subject,
        "username": username,
        "verification_link": get_verification_link(user_id),
        "token_expiration": auth_lib_security_settings.EMAIL_VERIFICATION_EXPIRES_MINUTES,
    }
    html = await render_email_template(
        template_name="verification",
        context=context,
    )

    await send_email.kiq(
        email_to=email,
        subject=subject,
        html=html,
    )


async def send_password_updated(username: str, email: str) -> None:
    """
    Sends a password updated notification email to the user.

    Args:
        username: The username of the user.
        email: The email address of the user.
    """
    subject = "Your Password Has Changed"

    context = {
        "username": username,
        "password_reset_link": utils_lib_settings.FRONTEND_HOST,
    }
    html = await render_email_template(
        template_name="password_updated",
        context=context,
    )

    await send_email.kiq(
        email_to=email,
        subject=subject,
        html=html,
    )


async def send_forgot_password(token: str, username: str, email: str) -> None:
    """
    Sends a forgot password email to the user.

    Args:
        user_id: The ID of the user.
        username: The username of the user.
        email: The email address of the user.
    """
    subject = "Reset Your Password"

    context = {
        "username": username,
        "reset_link": get_password_reset_link(token),
        "token_expiration": auth_lib_security_settings.PASSWORD_RESET_EXPIRES_MINUTES,
    }
    html = await render_email_template(
        template_name="forgot_password",
        context=context,
    )

    await send_email.kiq(
        email_to=email,
        subject=subject,
        html=html,
    )
