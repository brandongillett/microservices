from uuid import UUID, uuid4

from faststream.rabbit.fastapi import RabbitRouter

from libs.users_lib.models import Users
from libs.users_lib.schemas import (
    CreateUserEvent,
    UpdateUserPasswordEvent,
    UpdateUserRoleEvent,
    UpdateUserUsernameEvent,
)
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.core.rabbitmq import rabbitmq
from libs.utils_lib.events import event_exists, logger, mark_event_processed, retry_task

rabbit_router = RabbitRouter()


# Subscriber events
async def _process_create_user_event(
    session: async_session_dep, event: CreateUserEvent
) -> None:
    """
    Logic to create a user.

    Args:
        session: The database session.
        event: The event containing the user details to be created.
    """
    dbObj = Users.model_validate(event.user)
    session.add(dbObj)
    await session.commit()
    await session.refresh(dbObj)

    await mark_event_processed(event.event_id)


@rabbit_router.subscriber("create_user")
async def create_user_event(session: async_session_dep, event: CreateUserEvent) -> None:
    """
    Subscribes to an event to create a user.

    Args:
        session: The database session.
        user (User): The user to create.
    """
    if await event_exists(event.event_id):
        logger.info(f"Event {event.event_id} already processed.")
        return

    try:
        # Retry the task if it fails
        await retry_task(
            lambda: _process_create_user_event(session, event), retries=5, delay=2
        )
    except Exception as e:
        logger.error(f"Failed to process event {event.event_id}: {str(e)}")
        # Event to revert the user creation for auth service (will be implemented in the future)


# Publisher events
async def update_user_username_event(user_id: UUID, new_username: str) -> None:
    """
    Publishes an event to update a user's username.

    Args:
        user_id (UUID): The user's ID.
        new_username (str): The new username.
    """
    event_id = uuid4()
    event = UpdateUserUsernameEvent(
        event_id=event_id, user_id=user_id, new_username=new_username
    )
    await rabbitmq.broker.publish(event, queue="update_user_username")


async def update_user_password_event(user_id: UUID, new_password: str) -> None:
    """
    Publishes a event to update a user's password.

    Args:
        user_id (UUID): The user's ID.
        new_password (str): The new password.
    """
    event_id = uuid4()
    event = UpdateUserPasswordEvent(
        event_id=event_id, user_id=user_id, new_password=new_password
    )
    await rabbitmq.broker.publish(event, queue="update_user_password")


async def update_user_role_event(user_id: UUID, new_role: str) -> None:
    """
    Publishes an event to update a user's role.

    Args:
        user_id (UUID): The user's ID.
        new_role (str): The new role.
    """
    event_id = uuid4()
    event = UpdateUserRoleEvent(event_id=event_id, user_id=user_id, new_role=new_role)
    await rabbitmq.broker.publish(event, queue="update_user_role")
