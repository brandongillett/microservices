from collections.abc import AsyncGenerator

import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.rabbitmq import rabbitmq
from libs.utils_lib.tests.conftest import anyio_backend, client

__all__ = ["anyio_backend", "client"]


@pytest.fixture(autouse=True)
async def lifespan() -> AsyncGenerator[None, None]:
    await rabbitmq.start()
    yield
    await rabbitmq.close()


@pytest.fixture(scope="session", autouse=True)
async def db() -> AsyncGenerator[AsyncSession, None]:
    await session_manager.init_db()
    async with session_manager.get_session() as session:
        yield session

    await rabbitmq.start()
    await rabbitmq.broker.publish(exchange="cleanup_database")
    await rabbitmq.close()
