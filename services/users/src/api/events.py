from uuid import UUID, uuid4

from faststream.rabbit.fastapi import RabbitRouter
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.users_lib.crud import get_user_by_username
from libs.users_lib.models import Users
from libs.users_lib.schemas import (
    CreateUserEvent,
    UpdateUserPasswordEvent,
    UpdateUserRoleEvent,
    UpdateUserUsernameEvent,
)
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.api.events import (
    handle_publish_event,
    handle_subscriber_event,
    logger,
)

rabbit_router = RabbitRouter()


# Subscriber events
@rabbit_router.subscriber("create_root_user", retry=10)
async def create_root_user_event(session: async_session_dep, user: Users) -> None:
    """
    Subscribes to an event to create a user.

    Args:
        session: The database session.
        user (User): The user to create.
    """
    user_exists = await get_user_by_username(session, user.username)

    if not user_exists:
        dbObj = Users.model_validate(user)
        session.add(dbObj)
        await session.commit()
        await session.refresh(dbObj)
        logger.info("Root user created.")


@rabbit_router.subscriber("create_user", retry=10)
async def create_user_event(session: async_session_dep, data: CreateUserEvent) -> None:
    """
    Subscribes to an event to create a user.

    Args:
        session: The database session.
        user (User): The user to create.
    """

    async def process_create_user(session: AsyncSession, data: CreateUserEvent) -> None:
        """
        Processes the logic for creating a user.

        Args:
            session: The database session.
            data: The event containing the user details to be created.

        Returns:
            None
        """
        dbObj = Users.model_validate(data.user)
        session.add(dbObj)
        await session.commit()
        await session.refresh(dbObj)

    await handle_subscriber_event(
        session=session,
        event_id=data.event_id,
        event_type="create_user",
        process_fn=process_create_user,
        data=data,
    )


# Publisher events
async def update_user_username_event(
    session: AsyncSession, user_id: UUID, new_username: str
) -> None:
    """
    Publishes an event to update a user's username.

    Args:
        user_id (UUID): The user's ID.
        new_username (str): The new username.
    """
    event_schema = UpdateUserUsernameEvent(
        event_id=uuid4(), user_id=user_id, new_username=new_username
    )
    await handle_publish_event(
        session=session, event_type="update_user_username", event_schema=event_schema
    )


async def update_user_password_event(
    session: AsyncSession, user_id: UUID, new_password: str
) -> None:
    """
    Publishes a event to update a user's password.

    Args:
        user_id (UUID): The user's ID.
        new_password (str): The new password.
    """
    event_schema = UpdateUserPasswordEvent(
        event_id=uuid4(), user_id=user_id, new_password=new_password
    )
    await handle_publish_event(
        session=session, event_type="update_user_password", event_schema=event_schema
    )


async def update_user_role_event(
    session: AsyncSession, user_id: UUID, new_role: str
) -> None:
    """
    Publishes an event to update a user's role.

    Args:
        user_id (UUID): The user's ID.
        new_role (str): The new role.
    """
    event_schema = UpdateUserRoleEvent(
        event_id=uuid4(), user_id=user_id, new_role=new_role
    )
    await handle_publish_event(
        session=session, event_type="update_user_role", event_schema=event_schema
    )
