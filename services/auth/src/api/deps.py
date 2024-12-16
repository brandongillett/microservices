from fastapi.security import OAuth2PasswordBearer

# Required to return access token for authentication
oauth2 = OAuth2PasswordBearer(tokenUrl="auth/login")
