from datetime import datetime
from uuid import UUID, uuid4

import jwt
from pydantic_settings import BaseSettings

from libs.auth_lib.core.security import security_settings as auth_lib_security_settings
from libs.auth_lib.schemas import TokenData
from libs.utils_lib.core.config import settings


# Security Settings
class SecuritySettings(BaseSettings):
    pass


security_settings = SecuritySettings()


# JWT token generation
def gen_token(data: TokenData, expire: datetime) -> tuple[str, UUID]:
    """
    Generate a JWT token with the provided data and expiration time.

    Args:
        data (TokenData): The data to encode in the token
        expire (datetime): The expiration time of the token

    Returns:
        tuple[str, UUID]: The encoded JWT token and its JTI (unique identifier)
    """
    jti = uuid4()

    to_encode = data.model_dump(mode="json")

    to_encode["exp"] = expire
    to_encode["jti"] = str(jti)

    encoded_JWT = jwt.encode(
        to_encode, settings.SECRET_KEY, algorithm=auth_lib_security_settings.ALGORITHM
    )
    return encoded_JWT, jti
