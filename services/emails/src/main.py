from contextlib import asynccontextmanager
from typing import Any

import anyio
from fastapi import FastAPI
from prometheus_client import start_http_server
from pydantic_settings import BaseSettings
from starlette.middleware.cors import CORSMiddleware

from libs.utils_lib.api import events as utils_lib_events
from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.faststream import nats
from libs.utils_lib.core.limiter import Limiter
from libs.utils_lib.core.prometheus import PrometheusMiddleware
from libs.utils_lib.core.redis import redis_client
from libs.utils_lib.core.security import (
    security_settings as utils_lib_security_settings,
)
from libs.utils_lib.main import generate_openapi
from libs.utils_lib.tasks import schedule_jobs
from src.api import events
from src.api.v1.main import api_router as v1_router
from src.core.config import settings
from src.tasks import tasks_settings


class AppSettings(BaseSettings):
    THREAD_POOL_SIZE: int = 40
    TITLE: str = f"{utils_lib_settings.PROJECT_NAME} [{settings.SERVICE_NAME}]"
    ROOT_PATH: str = f"/{settings.SERVICE_NAME}"
    DESCRIPTION: str = """
    A REST API service for email notifications.

    This REST API:
    - Sends email notifications to users.
    """
    swagger_ui_parameters: dict[str, Any] = {
        "displayRequestDuration": True,
    }


app_settings = AppSettings()


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    _ = app  # Unused variable
    # Generate OpenAPI documentation
    generate_openapi(app)
    # Set thread pool size
    thread_pool_limiter = anyio.to_thread.current_default_thread_limiter()
    thread_pool_limiter.total_tokens = app_settings.THREAD_POOL_SIZE
    # Start Prometheus metrics server on port 9000 (separate from FastAPI app)
    prometheus_server, prometheus_thread = start_http_server(9000)
    # Initialize database, Redis, NATS, and Rate Limiter connections on startup
    await session_manager.init_db()
    await redis_client.connect()
    await nats.start()
    Limiter.init(
        redis_client=redis_client,
        enable_limiter=utils_lib_security_settings.ENABLE_RATE_LIMIT,
    )
    # Schedule jobs
    await schedule_jobs(jobs=tasks_settings.JOBS)
    yield
    # Shutdown Prometheus metrics server
    prometheus_server.shutdown()
    prometheus_thread.join()
    # Close database, Redis, and NATS connections on shutdown
    await session_manager.close()
    await redis_client.close()
    await nats.close()


app = FastAPI(
    version="latest",
    title=app_settings.TITLE,
    description=app_settings.DESCRIPTION,
    docs_url=utils_lib_settings.DOCS_URL
    if utils_lib_settings.ENVIRONMENT in ["local", "staging"]
    else None,
    lifespan=lifespan,
    swagger_ui_parameters=app_settings.swagger_ui_parameters,
    root_path=app_settings.ROOT_PATH,
)

# Include nats router
nats.router.include_router(events.nats_router)
nats.router.include_router(utils_lib_events.nats_router)  # acknowledgements
app.include_router(nats.router)

# Set all CORS enabled origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=utils_lib_settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Add Prometheus middleware
app.add_middleware(
    PrometheusMiddleware,
    root_path=app_settings.ROOT_PATH,
)

# Mount versions to the main app
app_v1 = FastAPI(
    version="v1",
    title=app_settings.TITLE,
    description=app_settings.DESCRIPTION,
    docs_url=utils_lib_settings.DOCS_URL
    if utils_lib_settings.ENVIRONMENT in ["local", "staging"]
    else None,
)

app_v1.include_router(v1_router)

app.mount("/v1", app_v1)

# Include latest version in the main app (Update this when adding new versions)
app.include_router(v1_router)
