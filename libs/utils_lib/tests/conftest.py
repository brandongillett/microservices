from collections.abc import AsyncGenerator

import pytest
from httpx import ASGITransport, AsyncClient

from libs.utils_lib.core.config import settings as utils_lib_settings
from src.main import app


@pytest.fixture(scope="session")
def anyio_backend() -> str:
    return "asyncio"


@pytest.fixture(scope="session")
async def client() -> AsyncGenerator[AsyncClient, None]:
    url = "http://localhost:8000"
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url=url,
        headers={"X-Bypass-RateLimit": "true"},
    ) as ac:
        yield ac


@pytest.fixture(scope="session")
async def auth_client() -> AsyncGenerator[AsyncClient, None]:
    auth_url = (
        "http://auth:8000"
        if utils_lib_settings.ENVIRONMENT == "local"
        else f"https://api.{utils_lib_settings.DOMAIN}/auth"
    )
    async with AsyncClient(
        base_url=auth_url, headers={"X-Bypass-RateLimit": "true"}
    ) as ac:
        yield ac
