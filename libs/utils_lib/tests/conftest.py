from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from libs.utils_lib.core.config import settings
from src.main import app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://localhost:8000",
    ) as ac:
        yield ac


@pytest.fixture(scope="session")
async def auth_client() -> AsyncGenerator[AsyncClient, None]:
    auth_url = "http://auth-service:8000"
    if settings.ENVIRONMENT != "local":
        auth_url = f"http://auth.{settings.DOMAIN}"

    async with AsyncClient(
        base_url=auth_url,
    ) as ac:
        yield ac
