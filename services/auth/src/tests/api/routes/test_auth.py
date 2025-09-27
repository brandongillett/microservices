from datetime import datetime, timedelta
from uuid import uuid4

import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.schemas import TokenData
from libs.auth_lib.utils import gen_password_reset_token
from libs.utils_lib.tests.utils.utils import (
    random_email,
    random_lower_string,
    test_password,
)
from src.api.config import api_settings
from src.core.security import gen_token
from src.crud import create_user
from src.schemas import UserCreate


@pytest.mark.anyio
async def test_login(db: AsyncSession, client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()
    user_data = UserCreate(username=username, email=email, password=test_password)
    new_user = await create_user(session=db, user_create=user_data)

    new_user.verified = True
    await db.commit()

    login_data_username = {"username": username, "password": test_password}
    login_data_email = {"username": email, "password": test_password}

    response_username = await client.post("/login", data=login_data_username)
    response_email = await client.post("/login", data=login_data_email)

    tokens_username = response_username.json()
    tokens_email = response_email.json()
    response_username.cookies.get("refresh_token")

    assert response_username.status_code == 200
    assert "access_token" in tokens_username
    assert tokens_username["access_token"]

    assert response_email.status_code == 200
    assert "access_token" in tokens_email
    assert tokens_email["access_token"]


@pytest.mark.anyio
async def test_login_not_verified(db: AsyncSession, client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()
    user_data = UserCreate(username=username, email=email, password=test_password)
    await create_user(session=db, user_create=user_data)

    login_data_username = {"username": username, "password": test_password}
    login_data_email = {"username": email, "password": test_password}

    response_username = await client.post("/login", data=login_data_username)
    response_email = await client.post("/login", data=login_data_email)

    assert response_username.status_code == 401
    assert response_email.status_code == 401


@pytest.mark.anyio
async def test_login_incorrect(db: AsyncSession, client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()
    user_data = UserCreate(username=username, email=email, password=test_password)
    await create_user(session=db, user_create=user_data)

    login_data_username = {"username": username, "password": "WrongPassword@1"}
    login_data_email = {"username": email, "password": "WrongPassword@1"}

    response_username = await client.post("/login", data=login_data_username)
    response_email = await client.post("/login", data=login_data_email)

    assert response_username.status_code == 401
    assert response_email.status_code == 401


@pytest.mark.anyio
async def test_login_disabled(db: AsyncSession, client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()
    user_data = UserCreate(username=username, email=email, password=test_password)
    user = await create_user(session=db, user_create=user_data)

    user.disabled = True
    db.add(user)
    await db.commit()

    login_data_username = {"username": username, "password": test_password}
    login_data_email = {"username": email, "password": test_password}

    response_username = await client.post("/login", data=login_data_username)
    response_email = await client.post("/login", data=login_data_email)

    assert response_username.status_code == 401
    assert response_email.status_code == 401


@pytest.mark.anyio
async def test_register(client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()
    data = {"username": username, "email": email, "password": test_password}

    response = await client.post("/register", json=data)
    user = response.json()

    assert response.status_code == 200
    assert user["username"] == username
    assert user["email"] == email
    assert user["id"]


@pytest.mark.anyio
async def test_register_username_exists(client: AsyncClient) -> None:
    username = random_lower_string()
    data = {"username": username, "email": random_email(), "password": test_password}
    data2 = {"username": username, "email": random_email(), "password": test_password}

    response1 = await client.post("/register", json=data)
    response2 = await client.post("/register", json=data2)

    assert response1.status_code == 200
    assert response2.status_code == 409


@pytest.mark.anyio
async def test_register_email_exists(client: AsyncClient) -> None:
    email = random_email()
    data1 = {
        "username": random_lower_string(),
        "email": email,
        "password": test_password,
    }
    data2 = {
        "username": random_lower_string(),
        "email": email,
        "password": test_password,
    }

    response1 = await client.post("/register", json=data1)
    response2 = await client.post("/register", json=data2)

    assert response1.status_code == 200
    assert response2.status_code == 409


@pytest.mark.anyio
async def test_register_username_invalid(client: AsyncClient) -> None:
    short_username = {
        "username": "a",
        "email": random_email(),
        "password": test_password,
    }
    long_username = {
        "username": "a" * 23,
        "email": random_email(),
        "password": test_password,
    }
    space_username = {
        "username": "aaa aa",
        "email": random_email(),
        "password": test_password,
    }
    trailing_special = {
        "username": "aaaa.",
        "email": random_email(),
        "password": test_password,
    }
    leading_special = {
        "username": ".aaaa",
        "email": random_email(),
        "password": test_password,
    }
    consecutive_special = {
        "username": "aa..aa",
        "email": random_email(),
        "password": test_password,
    }

    short_username_response = await client.post("/register", json=short_username)
    long_username_response = await client.post("/register", json=long_username)
    space_username_response = await client.post("/register", json=space_username)
    trailing_special_response = await client.post("/register", json=trailing_special)
    leading_special_response = await client.post("/register", json=leading_special)
    consecutive_special_response = await client.post(
        "/register", json=consecutive_special
    )

    assert short_username_response.status_code == 422
    assert long_username_response.status_code == 422
    assert space_username_response.status_code == 422
    assert trailing_special_response.status_code == 422
    assert leading_special_response.status_code == 422
    assert consecutive_special_response.status_code == 422


@pytest.mark.anyio
async def test_register_password_invalid(client: AsyncClient) -> None:
    short_password = {
        "username": random_lower_string(),
        "email": random_email(),
        "password": "a",
    }
    long_password = {
        "username": random_lower_string(),
        "email": random_email(),
        "password": "a" * 41,
    }
    spacePassword = {
        "username": random_lower_string(),
        "email": random_email(),
        "password": "aaaa aaaa",
    }
    no_letter_password = {
        "username": random_lower_string(),
        "email": random_email(),
        "password": "1234567&",
    }
    no_digit_password = {
        "username": random_lower_string(),
        "email": random_email(),
        "password": "Abcdefg&",
    }
    no_special_password = {
        "username": random_lower_string(),
        "email": random_email(),
        "password": "Abcdefg1",
    }

    short_password_response = await client.post("/register", json=short_password)
    long_password_response = await client.post("/register", json=long_password)
    space_password_response = await client.post("/register", json=spacePassword)
    no_letter_password_response = await client.post(
        "/register", json=no_letter_password
    )
    no_digit_password_response = await client.post("/register", json=no_digit_password)
    no_special_password_response = await client.post(
        "/register", json=no_special_password
    )

    assert short_password_response.status_code == 422
    assert long_password_response.status_code == 422
    assert space_password_response.status_code == 422
    assert no_letter_password_response.status_code == 422
    assert no_digit_password_response.status_code == 422
    assert no_special_password_response.status_code == 422


@pytest.mark.anyio
async def test_logout(db: AsyncSession, client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()
    user_data = UserCreate(username=username, email=email, password=test_password)
    new_user = await create_user(session=db, user_create=user_data)

    new_user.verified = True
    await db.commit()

    login_response = await client.post(
        "/login",
        data={"username": username, "password": test_password},
    )
    refresh_token = login_response.cookies.get("refresh_token")
    if refresh_token:
        client.cookies.set("refresh_token", refresh_token)

    response_logout = await client.post("/logout")

    assert response_logout.status_code == 200

    # check if refresh token cannot be used (not in db)
    refresh_access_token = await client.post("/token/refresh")
    assert refresh_access_token.status_code == 401


@pytest.mark.anyio
async def test_logout_no_token(client: AsyncClient) -> None:
    client.cookies.set("refresh_token", "")
    response_logout = await client.post("/logout")

    assert response_logout.status_code == 401


@pytest.mark.anyio
async def test_logout_invalid_token(client: AsyncClient) -> None:
    client.cookies.set("refresh_token", "invalid_token")
    response_logout1 = await client.post("/logout")
    token_data = TokenData(
        user_id=uuid4(),
        role="user",
        verified=True,
        type="refresh",
    )
    random_token, _ = gen_token(
        data=token_data,
        expire=datetime.utcnow()
        + timedelta(days=api_settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    client.cookies.set("refresh_token", random_token)
    response_logout2 = await client.post("/logout")

    assert response_logout1.status_code == 401
    assert response_logout2.status_code == 401


@pytest.mark.anyio
async def test_refresh_token(db: AsyncSession, client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()
    user_data = UserCreate(username=username, email=email, password=test_password)
    new_user = await create_user(session=db, user_create=user_data)

    new_user.verified = True
    await db.commit()

    login_response = await client.post(
        "/login",
        data={"username": username, "password": test_password},
    )
    refresh_token = login_response.cookies.get("refresh_token")
    if refresh_token:
        client.cookies.set("refresh_token", refresh_token)

    response_refresh = await client.post("/token/refresh")

    assert response_refresh.status_code == 200
    assert response_refresh.json()["access_token"]


@pytest.mark.anyio
async def test_refresh_token_no_token(client: AsyncClient) -> None:
    client.cookies.set("refresh_token", "")
    response_refresh = await client.post("/token/refresh")

    assert response_refresh.status_code == 401


@pytest.mark.anyio
async def test_refresh_token_invalid_token(client: AsyncClient) -> None:
    client.cookies.set("refresh_token", "invalid_token")
    response_refresh1 = await client.post("/token/refresh")
    token_data = TokenData(
        user_id=uuid4(),
        role="user",
        verified=True,
        type="refresh",
    )
    random_token, _ = gen_token(
        data=token_data,
        expire=datetime.utcnow()
        + timedelta(days=api_settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    client.cookies.set("refresh_token", random_token)
    response_refresh2 = await client.post("/token/refresh")

    assert response_refresh1.status_code == 401
    assert response_refresh2.status_code == 401


@pytest.mark.anyio
async def test_refresh_token_not_in_db(db: AsyncSession, client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()
    user_data = UserCreate(username=username, email=email, password=test_password)
    user = await create_user(session=db, user_create=user_data)

    token_data = TokenData(
        user_id=user.id,
        role=user.role,
        verified=user.verified,
        type="refresh",
    )
    refresh_token, _ = gen_token(
        data=token_data,
        expire=datetime.utcnow()
        + timedelta(days=api_settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )

    client.cookies.set("refresh_token", refresh_token)

    response_refresh = await client.post("/token/refresh")

    assert response_refresh.status_code == 401


@pytest.mark.anyio
async def test_forgot_password(db: AsyncSession, client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()
    user_data = UserCreate(username=username, email=email, password=test_password)
    user = await create_user(session=db, user_create=user_data)

    user.verified = True
    await db.commit()

    email_response_forgot = await client.post(
        f"/password/forgot?username_email={user.email}"
    )
    username_response_forgot = await client.post(
        f"/password/forgot?username_email={user.username}"
    )

    assert email_response_forgot.status_code == 200
    assert username_response_forgot.status_code == 200


@pytest.mark.anyio
async def test_reset_password(db: AsyncSession, client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()
    user_data = UserCreate(username=username, email=email, password=test_password)
    user = await create_user(session=db, user_create=user_data)

    user.verified = True
    await db.commit()

    token = await gen_password_reset_token(user_id=user.id)
    body = {
        "token": token,
        "new_password": "NewPassword@1",
    }
    response_reset = await client.post("/password/reset", json=body)

    assert response_reset.status_code == 200


@pytest.mark.anyio
async def test_reset_password_same_password(
    db: AsyncSession, client: AsyncClient
) -> None:
    username = random_lower_string()
    email = random_email()
    user_data = UserCreate(username=username, email=email, password=test_password)
    user = await create_user(session=db, user_create=user_data)

    user.verified = True
    await db.commit()

    token = await gen_password_reset_token(user_id=user.id)
    body = {
        "token": token,
        "new_password": test_password,
    }
    response_reset = await client.post("/password/reset", json=body)

    assert response_reset.status_code == 422


@pytest.mark.anyio
async def test_reset_password_invalid_password(
    db: AsyncSession, client: AsyncClient
) -> None:
    username = random_lower_string()
    email = random_email()
    user_data = UserCreate(username=username, email=email, password=test_password)
    user = await create_user(session=db, user_create=user_data)

    user.verified = True
    await db.commit()

    token = await gen_password_reset_token(user_id=user.id)
    body = {
        "token": token,
        "new_password": "short",
    }
    response_reset = await client.post("/password/reset", json=body)

    assert response_reset.status_code == 422


@pytest.mark.anyio
async def test_reset_password_invalid_token(
    db: AsyncSession, client: AsyncClient
) -> None:
    username = random_lower_string()
    email = random_email()
    user_data = UserCreate(username=username, email=email, password=test_password)
    user = await create_user(session=db, user_create=user_data)

    user.verified = True
    await db.commit()

    token = "invalid_token"
    body = {
        "token": token,
        "new_password": "NewPassword@1",
    }
    response_reset = await client.post("/password/reset", json=body)

    assert response_reset.status_code == 401


@pytest.mark.anyio
async def test_reset_password_duplicate_token(
    db: AsyncSession, client: AsyncClient
) -> None:
    username = random_lower_string()
    email = random_email()
    user_data = UserCreate(username=username, email=email, password=test_password)
    user = await create_user(session=db, user_create=user_data)

    user.verified = True
    await db.commit()

    token = await gen_password_reset_token(user_id=user.id)
    body = {
        "token": token,
        "new_password": "NewPassword@1",
    }
    response_reset1 = await client.post("/password/reset", json=body)
    body["new_password"] = "NewPassword@2"
    response_reset2 = await client.post("/password/reset", json=body)

    assert response_reset1.status_code == 200
    assert response_reset2.status_code == 400
