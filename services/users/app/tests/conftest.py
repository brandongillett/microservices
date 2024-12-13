from collections.abc import AsyncGenerator

import pytest
from sqlmodel import delete, not_
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.models import Users
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.tests.conftest import anyio_backend, auth_client, client

__all__ = ["anyio_backend", "client", "auth_client"]


@pytest.fixture(scope="session", autouse=True)
async def db() -> AsyncGenerator[AsyncSession, None]:
    await session_manager.init_db()
    if not session_manager.session_maker:
        raise Exception("Session manager not initialized")
    async with session_manager.session_maker() as session:
        yield session

        statement = delete(Users).where(not_(Users.username == "root"))
        await session.execute(statement)
        await session.commit()
