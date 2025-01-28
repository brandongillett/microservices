import pytest


@pytest.mark.anyio
async def test_pass() -> None:
    assert True
