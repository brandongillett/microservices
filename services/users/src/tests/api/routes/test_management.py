from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.tests.utils.utils import (
    create_and_login_user_helper,
    login_root_user_helper,
)


# User Details
@pytest.mark.anyio
async def test_get_roles(client: AsyncClient, auth_client: AsyncClient) -> None:
    headers = await login_root_user_helper(auth_client)

    response = await client.get("/management/roles", headers=headers)

    assert response.status_code == 200


@pytest.mark.anyio
async def test_get_roles_unauthorized(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers, _ = await create_and_login_user_helper(db, auth_client)

    response = await client.get("/management/roles", headers=headers)

    assert response.status_code == 403


@pytest.mark.anyio
async def test_update_role(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers = await login_root_user_helper(auth_client)

    _, new_user = await create_and_login_user_helper(db, auth_client)

    update_data = {"user_id": new_user.id, "role": "admin"}
    response = await client.patch("/management/role", headers=headers, json=update_data)

    assert response.status_code == 200


@pytest.mark.anyio
async def test_update_role_invalid_role(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers = await login_root_user_helper(auth_client)

    _, new_user = await create_and_login_user_helper(db, auth_client)

    update_data = {"user_id": new_user.id, "role": "invalid"}
    response = await client.patch("/management/role", headers=headers, json=update_data)

    assert response.status_code == 400


@pytest.mark.anyio
async def test_update_role_invalid_user(
    client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers = await login_root_user_helper(auth_client)

    update_data = {"user_id": str(uuid4()), "role": "admin"}
    response = await client.patch("/management/role", headers=headers, json=update_data)

    assert response.status_code == 404
