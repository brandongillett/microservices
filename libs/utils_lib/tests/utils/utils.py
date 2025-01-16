import random
import string
import time

from httpx import AsyncClient
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.utils_lib.core.database import session_manager
from libs.utils_lib.crud import get_outbox_event
from libs.utils_lib.models import EventStatus
from libs.users_lib.models import Users
from libs.utils_lib.core.config import settings as utils_lib_settings

test_password = "Password@2"


def random_lower_string() -> str:
    return "".join(random.choices(string.ascii_lowercase, k=20))


def random_email() -> str:
    return f"{random_lower_string()}@{random_lower_string()}.com"


async def create_and_login_user_helper(
    db: AsyncSession, client: AsyncClient
) -> tuple[dict[str, str], Users]:
    """Helper function to create a user and login."""
    username = random_lower_string()
    email = random_email()

    create_response = await client.post(
        "/auth/register",
        json={"username": username, "email": email, "password": test_password},
    )
    new_user = Users(**create_response.json())

    await db.commit()

    login_response = await client.post(
        "/auth/login",
        data={"username": username, "password": test_password},
    )
    login_json = login_response.json()
    token = login_json["access_token"]

    headers = {"Authorization": f"Bearer {token}"}
    return headers, new_user


async def login_root_user_helper(auth_client: AsyncClient) -> dict[str, str]:
    """
    Login the root user.

    Args:
        auth_client (AsyncClient): The auth client.

    Returns:
        str: The access token.
    """
    login_response = await auth_client.post(
        "/auth/login",
        data={"username": "root", "password": utils_lib_settings.ROOT_USER_PASSWORD},
    )
    login_json = login_response.json()
    token = login_json["access_token"]

    return {"Authorization": f"Bearer {token}"}


async def event_processed_helper(event_id, timeout=1, poll_interval=0.1):
    """
    Polls the outbox event to check if it has been processed.

    Args:
        event_id (int): The event ID.
        timeout (int, optional): The timeout in seconds. Defaults to 1.
        poll_interval (float, optional): The poll interval in seconds. Defaults to 0.1.

    Returns:
        bool: True if the event has been processed, False otherwise.
    """

    start_time = time.time()
    
    while time.time() - start_time < timeout:
        time.sleep(poll_interval)

        async with session_manager.get_session() as new_session:
            outbox_event = await get_outbox_event(session=new_session, event_id=event_id)
        
        if outbox_event.status == EventStatus.processed:
            return True

    return False