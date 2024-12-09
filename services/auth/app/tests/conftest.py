from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient
from sqlmodel import delete
from sqlmodel.ext.asyncio.session import AsyncSession

from app.main import app
from libs.auth_lib.models import RefreshTokens, Users
from libs.utils_lib.core.config import settings
from libs.utils_lib.core.database import session_manager


@pytest.fixture(scope="session", autouse=True)
async def db() -> AsyncGenerator[AsyncSession, None]:
    await session_manager.init_db()
    if not session_manager.session_maker:
        raise Exception("Session manager not initialized")
    async with session_manager.session_maker() as session:
        yield session

        statement = delete(RefreshTokens)
        await session.execute(statement)
        statement = delete(Users)
        await session.execute(statement)
        await session.commit()


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=f"{settings.LOCAL_BASE_URL}",
    ) as ac:
        yield ac
