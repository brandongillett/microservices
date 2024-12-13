from contextlib import asynccontextmanager
from typing import Any

from fastapi import FastAPI

from libs.auth_lib.core.redis import redis_tokens_client
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.redis import redis_client


@asynccontextmanager
async def lifespan(app: FastAPI) -> Any:
    _ = app  # Unused variable
    # Initialize database and Redis connections on startup
    await session_manager.init_db()
    await redis_client.connect()
    await redis_tokens_client.connect()
    yield
    # Close database and Redis connections on shutdown
    await session_manager.close()
    await redis_client.close()
    await redis_tokens_client.close()
