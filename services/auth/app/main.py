from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware
from pydantic_settings import BaseSettings

from app.api.v1.main import api_router as v1_router
from app.core.config import settings
from app.core.database import session_manager
from app.core.redis import redis_client
from app.core.security import rate_limit_exceeded_handler, rate_limiter

class app_settings(BaseSettings):
    TITLE: str = f"{settings.PROJECT_NAME} [Auth]"
    DESCRIPTION: str = """
    A REST API service for user authentication.

    This REST API:
    - Allows users to register and login.
    - Generates access tokens and refresh tokens.
    - Allows users to refresh their access tokens.
    - Allows users to logout.
    - Allows users to view and revoke their refresh tokens.
    """

app_settings = app_settings()  # type: ignore

@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    _ = app  # Unused variable
    # Initialize database and Redis connections on startup
    await session_manager.init_db()
    await redis_client.connect()
    yield
    # Close database and Redis connections on shutdown
    await session_manager.close()
    await redis_client.close()


app = FastAPI(
    version="latest",
    title=app_settings.TITLE,
    description=app_settings.DESCRIPTION,
    docs_url=settings.DOCS_URL,
    lifespan=lifespan,
)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.all_cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter settings
app.state.limiter = rate_limiter
app.add_exception_handler(RateLimitExceeded, rate_limit_exceeded_handler)


# Mount versions to the main app
app_v1 = FastAPI(
    version="v1", 
    title=app_settings.TITLE, 
    description=app_settings.DESCRIPTION, 
    docs_url=settings.DOCS_URL
)

app_v1.include_router(v1_router)

app.mount("/v1", app_v1)

# Include latest version in the main app (Update this when adding new versions)
app.include_router(v1_router)
