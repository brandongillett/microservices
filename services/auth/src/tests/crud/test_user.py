import pytest
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.core.security import verify_password
from libs.auth_lib.crud import verify_user_email
from libs.utils_lib.tests.utils.utils import (
    random_email,
    random_lower_string,
    test_password,
)
from src.crud import (
    authenticate_user,
    create_user,
)
from src.schemas import UserCreate


@pytest.mark.anyio
async def test_create_user(db: AsyncSession) -> None:
    username = random_lower_string()
    email = random_email()

    create = UserCreate(username=username, email=email, password=test_password)
    new_user = await create_user(session=db, user_create=create)

    assert new_user
    assert new_user.email == email
    assert new_user.username == username
    assert await verify_password(test_password, new_user.password)
    assert new_user.id


@pytest.mark.anyio
async def test_authenticate_user(db: AsyncSession) -> None:
    username = random_lower_string()
    email = random_email()

    create = UserCreate(username=username, email=email, password=test_password)
    new_user = await create_user(session=db, user_create=create)

    authenticatedUserUsername = await authenticate_user(
        session=db, username_email=username, password=test_password
    )
    authenticatedUserEmail = await authenticate_user(
        session=db, username_email=email, password=test_password
    )

    assert authenticatedUserUsername
    assert authenticatedUserEmail
    assert new_user == authenticatedUserUsername
    assert new_user == authenticatedUserEmail


@pytest.mark.anyio
async def test_not_authenticate_user(db: AsyncSession) -> None:
    username = random_lower_string()
    email = random_email()

    authenticatedUserUsername = await authenticate_user(
        session=db, username_email=username, password=test_password
    )
    authenticatedUserEmail = await authenticate_user(
        session=db, username_email=email, password=test_password
    )

    assert authenticatedUserUsername is None
    assert authenticatedUserEmail is None


@pytest.mark.anyio
async def test_verify_user_email(db: AsyncSession) -> None:
    username = random_lower_string()
    email = random_email()

    create = UserCreate(username=username, email=email, password=test_password)
    new_user = await create_user(session=db, user_create=create)

    verified_user = await verify_user_email(session=db, user_id=new_user.id)

    assert verified_user
    assert verified_user.verified
