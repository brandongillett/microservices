import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.tests.utils.utils import (
    create_and_login_user_auth_client as create_and_login_user,
)
from libs.utils_lib.tests.utils.utils import random_lower_string, test_password


# User Details
@pytest.mark.anyio
async def test_my_details(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers, new_user = await create_and_login_user(db, auth_client)

    user_response = await client.get("/users/me", headers=headers)
    user_details = user_response.json()

    assert user_response.status_code == 200
    assert user_details["username"] == new_user.username
    assert user_details["email"] == new_user.email


@pytest.mark.anyio
async def test_my_details_incorrect(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers, _ = await create_and_login_user(db, auth_client)

    headers["Authorization"] += "wrong"
    user_response = await client.get("/users/me", headers=headers)

    assert user_response.status_code == 401


@pytest.mark.anyio
async def test_my_details_no_token(client: AsyncClient) -> None:
    user_response = await client.get("/users/me")
    assert user_response.status_code == 401


# Update Username
@pytest.mark.anyio
async def test_update_username(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers, _ = await create_and_login_user(db, auth_client)

    update_data = {"new_username": random_lower_string()}
    update_response = await client.patch(
        "/users/me/username",
        headers=headers,
        json=update_data,
    )

    user_response = await client.get("/users/me", headers=headers)
    user_details = user_response.json()

    assert update_response.status_code == 200
    assert user_response.status_code == 200
    assert user_details["username"] == update_data["new_username"]


@pytest.mark.anyio
async def test_update_username_same_username(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers, new_user = await create_and_login_user(db, auth_client)

    update_data = {"new_username": new_user.username}
    update_response = await client.patch(
        "/users/me/username",
        headers=headers,
        json=update_data,
    )

    assert update_response.status_code == 400


@pytest.mark.anyio
async def test_update_username_invalid_username(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers, _ = await create_and_login_user(db, auth_client)

    update_data = {"new_username": "A"}
    update_response = await client.patch(
        "/users/me/username",
        headers=headers,
        json=update_data,
    )

    assert update_response.status_code == 422


@pytest.mark.anyio
async def test_update_username_no_token(client: AsyncClient) -> None:
    update_data = {"new_username": random_lower_string()}
    update_response = await client.patch("/users/me/username", json=update_data)

    assert update_response.status_code == 401


# Update Password
@pytest.mark.anyio
async def test_update_password(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers, new_user = await create_and_login_user(db, auth_client)

    update_data = {
        "current_password": test_password,
        "new_password": "NewPassword@1",
    }
    update_response = await client.patch(
        "/users/me/password",
        headers=headers,
        json=update_data,
    )

    login_response = await auth_client.post(
        "/auth/login",
        data={"username": new_user.username, "password": "NewPassword@1"},
    )

    assert update_response.status_code == 200
    assert login_response.status_code == 200


@pytest.mark.anyio
async def test_update_password_incorrect_password(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers, _ = await create_and_login_user(db, auth_client)

    update_data = {
        "current_password": "WrongPassword@1",
        "new_password": "NewPassword@1",
    }
    update_response = await client.patch(
        "/users/me/password",
        headers=headers,
        json=update_data,
    )

    assert update_response.status_code == 400


@pytest.mark.anyio
async def test_update_password_same_password(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers, new_user = await create_and_login_user(db, auth_client)

    update_data = {"current_password": test_password, "new_password": test_password}
    update_response = await client.patch(
        "/users/me/password",
        headers=headers,
        json=update_data,
    )

    assert update_response.status_code == 400


@pytest.mark.anyio
async def test_update_password_invalid_password(
    db: AsyncSession, client: AsyncClient, auth_client: AsyncClient
) -> None:
    headers, _ = await create_and_login_user(db, auth_client)

    update_data = {"current_password": test_password, "new_password": "A"}
    update_response = await client.patch(
        "/users/me/password",
        headers=headers,
        json=update_data,
    )

    assert update_response.status_code == 422


@pytest.mark.anyio
async def test_update_password_no_token(client: AsyncClient) -> None:
    update_data = {"current_password": test_password, "new_password": "NewPassword@1"}
    update_response = await client.patch("/users/me/password", json=update_data)

    assert update_response.status_code == 401
