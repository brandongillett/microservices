import pytest
from httpx import AsyncClient

from libs.auth_lib.utils import gen_email_verification_token
from libs.users_lib.models import Users
from libs.utils_lib.tests.utils.utils import (
    random_email,
    random_lower_string,
    test_password,
)


@pytest.mark.anyio
async def test_verify_email(client: AsyncClient) -> None:
    username = random_lower_string()
    email = random_email()

    create_response = await client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": test_password},
    )
    new_user = Users(**create_response.json())

    token = gen_email_verification_token(new_user.id)

    response = await client.get(f"/verification/email/{token}")

    assert response.status_code == 200
