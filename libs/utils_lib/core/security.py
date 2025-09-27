from fastapi import HTTPException, Request, status
from itsdangerous import URLSafeTimedSerializer
from pydantic_settings import BaseSettings

from libs.utils_lib.core.config import settings as utils_lib_settings


# Security Settings
class security_settings(BaseSettings):
    # Rate limit settings
    def get_enable_rate_limit(self) -> bool:
        return utils_lib_settings.ENVIRONMENT != "local"

    # rate limiting disabled in local environment
    ENABLE_RATE_LIMIT = property(get_enable_rate_limit)


security_settings = security_settings()  # type: ignore


# Get IP address from request headers
def get_client_ip(request: Request) -> str:
    """
    Get the client's IP address from the request.

    Args:
        request (Request): The request object

    Returns:
        str: The client's IP address
    """
    if utils_lib_settings.CLIENT_IP_HEADER:
        custom_ip = request.headers.get(utils_lib_settings.CLIENT_IP_HEADER)
        if custom_ip:
            return custom_ip.strip()

    x_forwarded_for = request.headers.get("x-forwarded-for")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()

    return request.client.host if request.client else "0.0.0.0"


# URL safe token generation and verification
def gen_url_token(data: dict, salt: str) -> str:
    """
    Generate a URL-safe token with the provided data and salt.

    Args:
        data (dict): The data to encode in the token
        salt (str): The salt to use for encoding

    Returns:
        str: The URL-safe token.
    """
    serializer = URLSafeTimedSerializer(
        secret_key=utils_lib_settings.SECRET_KEY, salt=salt
    )

    return serializer.dumps(data)


def verify_url_token(token: str, salt: str, expiration: int) -> dict:
    """
    Verify a URL-safe token and extract the data.

    Args:
        token (str): The token to verify
        salt (str): The salt to use for verification
        expiration (int): The maximum age of the token in minutes

    Returns:
        dict: The data extracted from the token. If the token is invalid or expired, an HTTPException is raised.
    """
    serializer = URLSafeTimedSerializer(
        secret_key=utils_lib_settings.SECRET_KEY, salt=salt
    )

    try:
        data = serializer.loads(token, max_age=expiration * 60)
        return data
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )
