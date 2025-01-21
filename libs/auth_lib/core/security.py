import re
from uuid import UUID

import jwt
from fastapi import HTTPException, status
from itsdangerous import URLSafeTimedSerializer
from passlib.context import CryptContext
from pydantic_settings import BaseSettings

from libs.utils_lib.core.config import settings as utils_libs_settings


# Security Settings
class security_settings(BaseSettings):
    # Roles
    roles: list[str] = ["user", "admin", "root"]

    # Hashing algorithm (for tokens)
    ALGORITHM: str = "HS256"
    # Username and password constraints
    USERNAME_MIN_LENGTH: int = 3
    USERNAME_MAX_LENGTH: int = 22
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_MAX_LENGTH: int = 40
    EMAIL_MIN_LENGTH: int = 3
    EMAIL_MAX_LENGTH: int = 255

    # Email verification token expiration time
    EMAIL_VERIFICATION_EXPIRES_MINUTES: int = 30


security_settings = security_settings()  # type: ignore


# JTI token extraction
def get_token_jti(token: str) -> UUID | None:
    """
    Extract the JTI (unique identifier) from a JWT token.

    Args:
        token (str): The JWT token to extract the JTI from

    Returns:
        UUID | None: The JTI of the token, or None if the token is invalid.
    """
    try:
        payload = jwt.decode(
            token,
            utils_libs_settings.SECRET_KEY,
            algorithms=[security_settings.ALGORITHM],
        )
        jti = payload.get("jti")
        return UUID(jti)
    except jwt.PyJWTError:
        return None


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
        secret_key=utils_libs_settings.SECRET_KEY, salt=salt
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
        secret_key=utils_libs_settings.SECRET_KEY, salt=salt
    )

    try:
        data = serializer.loads(token, max_age=expiration * 60)
        return data
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )


# Password hashing
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a hashed password.

    Args:
        plain_password (str): The plain text password to verify
        hashed_password (str): The hashed password to verify against

    Returns:
        bool: True if the passwords match, False otherwise.
    """
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    """
    Get the hash of a password.

    Args:
        password (str): The password to hash

    Returns:
        str: The hashed password.
    """
    return pwd_context.hash(password)


# Username and password validation
def is_email_valid(email: str) -> str | None:
    """
    Check if an email address is valid.

    Args:
        email (str): The email address to validate

    Returns:
        str | None: An error message if the email is invalid, None otherwise.
    """
    if not (
        security_settings.EMAIL_MIN_LENGTH
        <= len(email)
        <= security_settings.EMAIL_MAX_LENGTH
    ):
        return f"Email must be between {security_settings.EMAIL_MIN_LENGTH} and {security_settings.EMAIL_MAX_LENGTH} characters long"

    if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
        return "Invalid email address"

    return None


def is_username_complex(username: str) -> str | None:
    """
    Check if a username meets the required complexity.

    Username rules:
    - Must be between USERNAME_MIN_LENGTH and USERNAME_MAX_LENGTH characters long
    - Must not contain spaces
    - Must not start or end with underscores (_) or periods (.)
    - Must not contain consecutive underscores (_) or periods (.)
    - Must contain only alphanumeric characters, underscores, and periods

    Args:
        username (str): The username to validate

    Returns:
        str | None: An error message if the username is invalid, None otherwise.
    """

    # Check if username is between 5 and 22 characters long
    if not (
        security_settings.USERNAME_MIN_LENGTH
        <= len(username)
        <= security_settings.USERNAME_MAX_LENGTH
    ):
        return f"Username must be between {security_settings.USERNAME_MIN_LENGTH} and {security_settings.USERNAME_MAX_LENGTH} characters long"
    if username[0] in "_." or username[-1] in "_.":
        return "Username must not start or end with underscores (_) or periods (.)"

    # Check if username contains only alphanumeric characters, underscores, and periods, and no consecutive underscores or periods
    last_char = ""
    for char in username:
        if char.isspace():
            return "Username must not contain spaces"
        if not char.isalnum() and char not in "_.":
            return "Username contains an invalid character"
        if char == last_char and char in "_.":
            return (
                "Username must not contain consecutive underscores (_) or periods (.)"
            )
        last_char = char

    return None


def is_password_complex(password: str) -> str | None:
    """
    Check if a password meets the required complexity.

    Password rules:
    - Must be between PASSWORD_MIN_LENGTH and PASSWORD_MAX_LENGTH characters long
    - Must not contain spaces
    - Must contain at least one letter
    - Must contain at least one digit
    - Must contain at least one uppercase letter
    - Must contain at least one lowercase letter
    - Must contain at least one special character (!@#$%^&*()-_=+[]{}|;:,.<>?/)

    Args:
        password (str): The password to validate

    Returns:
       str | None: An error message if the password is invalid, None otherwise.
    """

    special_chars = set("!@#$%^&*()-_=+[]{}|;:,.<>?/")

    if not (
        security_settings.PASSWORD_MIN_LENGTH
        <= len(password)
        <= security_settings.PASSWORD_MAX_LENGTH
    ):
        return f"Password must be between {security_settings.PASSWORD_MIN_LENGTH} and {security_settings.PASSWORD_MAX_LENGTH} characters long"

    has_alpha = has_digit = has_upper = has_lower = has_special = False

    for char in password:
        if not char.isalnum() and char not in special_chars:
            return "Password contains an invalid character"
        if char.isspace():
            return "Password must not contain spaces"
        if char.isalpha():
            has_alpha = True
        if char.isdigit():
            has_digit = True
        if char.isupper():
            has_upper = True
        if char.islower():
            has_lower = True
        if char in special_chars:
            has_special = True

    if not has_alpha:
        return "Password must contain at least one letter"
    if not has_digit:
        return "Password must contain at least one digit"
    if not has_upper:
        return "Password must contain at least one uppercase letter"
    if not has_lower:
        return "Password must contain at least one lowercase letter"
    if not has_special:
        return "Password must contain at least one special character"

    return None
