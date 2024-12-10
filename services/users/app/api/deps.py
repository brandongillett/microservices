from fastapi.security import OAuth2PasswordBearer

from libs.utils_lib.core.config import settings

# Required to return access token for authentication
oauth2 = OAuth2PasswordBearer(tokenUrl=f"http://auth.{settings.DOMAIN}/auth/login")
