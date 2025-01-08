from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.tests.utils.utils import (
    create_and_login_user_helper,
    login_root_user_helper,
)


# Users
@pytest.mark.anyio
async def test_get_user_data(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers = await login_root_user_helper(auth_client)

    _, new_user = await create_and_login_user_helper(db, auth_client)

    response_email = await client.get(
        f"/management/users?email={new_user.email}", headers=headers
    )

    response_username = await client.get(
        f"/management/users?username={new_user.username}", headers=headers
    )

    assert response_email.status_code == 200
    assert response_username.status_code == 200


@pytest.mark.anyio
async def test_get_user_data_unauthorized(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers, _ = await create_and_login_user_helper(db, auth_client)

    response = await client.get("/management/users", headers=headers)

    assert response.status_code == 403


@pytest.mark.anyio
async def test_get_user_data_invalid(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers = await login_root_user_helper(auth_client)

    _, new_user = await create_and_login_user_helper(db, auth_client)

    response_both = await client.get(
        f"/management/users?email={new_user.email}&username={new_user.username}",
        headers=headers,
    )
    response_none = await client.get("/management/users", headers=headers)

    assert response_both.status_code == 400
    assert response_none.status_code == 400


@pytest.mark.anyio
async def test_get_user_data_not_found(
    client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers = await login_root_user_helper(auth_client)

    response_email = await client.get(
        "/management/users?email=test_email@test.com", headers=headers
    )
    response_username = await client.get(
        "/management/users?username=test_username", headers=headers
    )

    assert response_email.status_code == 404
    assert response_username.status_code == 404


# Roles
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

    update_data = {"new_role": "admin"}
    response = await client.patch(
        f"/management/users/{new_user.id}/role", headers=headers, json=update_data
    )

    assert response.status_code == 200


@pytest.mark.anyio
async def test_update_role_unauthorized(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers, _ = await create_and_login_user_helper(db, auth_client)

    _, new_user = await create_and_login_user_helper(db, auth_client)

    update_data = {"new_role": "admin"}
    response = await client.patch(
        f"/management/users/{new_user.id}/role", headers=headers, json=update_data
    )

    assert response.status_code == 403


@pytest.mark.anyio
async def test_update_role_invalid_role(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers = await login_root_user_helper(auth_client)

    _, new_user = await create_and_login_user_helper(db, auth_client)

    update_data = {"new_role": "invalid"}
    response = await client.patch(
        f"/management/users/{new_user.id}/role", headers=headers, json=update_data
    )

    assert response.status_code == 400


@pytest.mark.anyio
async def test_update_role_invalid_user(
    client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers = await login_root_user_helper(auth_client)

    update_data = {"new_role": "admin"}
    response = await client.patch(
        f"/management/users/{str(uuid4())}/role", headers=headers, json=update_data
    )

    assert response.status_code == 404
