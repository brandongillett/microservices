from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI
from pydantic_settings import BaseSettings
from slowapi.errors import RateLimitExceeded
from starlette.middleware.cors import CORSMiddleware

from libs.utils_lib.api import events as utils_lib_events
from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.rabbitmq import rabbitmq
from libs.utils_lib.core.redis import redis_client
from libs.utils_lib.core.security import rate_limit_exceeded_handler, rate_limiter
from src.api import events
from src.api.v1.main import api_router as v1_router
from src.core.config import settings


class app_settings(BaseSettings):
    TITLE: str = f"{utils_lib_settings.PROJECT_NAME} [{settings.SERVICE_NAME}]"
    DESCRIPTION: str = """
    A REST API service for email notifications.

    This REST API:
    - Sends email notifications to users.
    """
    swagger_ui_parameters: dict[str, Any] = {
        "displayRequestDuration": True,
    }


app_settings = app_settings()  # type: ignore


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    _ = app  # Unused variable
    # Initialize database, Redis, and RabbitMQ connections on startup
    await session_manager.init_db()
    await redis_client.connect()
    await rabbitmq.start()
    yield
    # Close database, Redis, and RabbitMQ connections on shutdown
    await session_manager.close()
    await redis_client.close()
    await rabbitmq.close()


app = FastAPI(
    version="latest",
    title=app_settings.TITLE,
    description=app_settings.DESCRIPTION,
    docs_url=utils_lib_settings.DOCS_URL,
    lifespan=lifespan,
    swagger_ui_parameters=app_settings.swagger_ui_parameters,
)

# Include rabbitmq router
rabbitmq.router.include_router(events.rabbit_router)
rabbitmq.router.include_router(utils_lib_events.rabbit_router)  # acknowledgements
app.include_router(rabbitmq.router)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=utils_lib_settings.CORS_ORIGINS,
    allow_origin_regex=rf"https://.*\.{utils_lib_settings.DOMAIN}",
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
    docs_url=utils_lib_settings.DOCS_URL,
)

app_v1.include_router(v1_router)

app.mount("/v1", app_v1)

# Include latest version in the main app (Update this when adding new versions)
app.include_router(v1_router)
