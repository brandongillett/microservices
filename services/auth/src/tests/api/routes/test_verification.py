import pytest
from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.utils import gen_email_verification_token
from libs.utils_lib.tests.utils.utils import create_and_login_user_helper


@pytest.mark.anyio
async def test_verify_email(db: AsyncSession, client: AsyncClient) -> None:
    _, new_user = await create_and_login_user_helper(db, client)

    token = gen_email_verification_token(new_user.id)

    response = await client.get(f"/verification/email/{token}")

    assert response.status_code == 200
