from collections.abc import AsyncGenerator

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.faststream import nats
from libs.utils_lib.core.redis import redis_client
from libs.utils_lib.tests.conftest import anyio_backend, auth_client, client

__all__ = ["anyio_backend", "client", "auth_client"]


@pytest.fixture(autouse=True)
async def lifespan() -> AsyncGenerator[None, None]:
    await redis_client.connect()
    await nats.start()
    yield
    await redis_client.close()
    await nats.close()


@pytest.fixture(scope="session", autouse=True)
async def db() -> AsyncGenerator[AsyncSession, None]:
    await session_manager.init_db()
    async with session_manager.get_session() as session:
        yield session

    await nats.start()
    await nats.broker.publish("", subject="cleanup_database")
    await nats.close()
