from faststream.nats.fastapi import NatsRouter
from sqlmodel import delete, not_
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.users_lib.api.events import (
    UPDATE_PASSWORD_ROUTE,
    UPDATE_ROLE_ROUTE,
    UPDATE_USERNAME_ROUTE,
)
from libs.users_lib.crud import get_user, update_user_role, update_user_username
from libs.users_lib.models import Users
from libs.users_lib.schemas import (
    UpdateUserPasswordEvent,
    UpdateUserRoleEvent,
    UpdateUserUsernameEvent,
)
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.api.events import (
    handle_subscriber_event,
    logger,
)
from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.models import EventInbox, EventOutbox
from src.core.config import settings
from src.models import RefreshTokens

nats_router = NatsRouter()


# Exchanges
@nats_router.subscriber(
    subject="cleanup_database", queue=f"cleanup_database_{settings.SERVICE_NAME}"
)
async def cleanup_database_event(session: async_session_dep) -> None:
    """
    Subscribes to an event to clean up the database.

    Args:
        session: The database session.
    """
    if utils_lib_settings.ENVIRONMENT in ["local", "staging"]:
        statement = delete(RefreshTokens)
        await session.execute(statement)
        statement = delete(Users).where(not_(Users.username == "root"))
        await session.execute(statement)
        statement = delete(EventOutbox)
        await session.execute(statement)
        statement = delete(EventInbox)
        await session.execute(statement)
        await session.commit()
    else:
        logger.error("Cannot clean up database in this environment.")
        return


# Subscriber events
@nats_router.subscriber(
    subject=UPDATE_USERNAME_ROUTE.subject,
    stream=UPDATE_USERNAME_ROUTE.stream,
    pull_sub=UPDATE_USERNAME_ROUTE.pull_sub,
    durable=UPDATE_USERNAME_ROUTE.durable,
)
async def update_username_event(
    session: async_session_dep, data: UpdateUserUsernameEvent
) -> None:
    """
    Subscribes to an event to update a user's username.

    Args:
        session: The database session.
        data: The event containing the user details to be updated.
    """

    # Callable function to process the event
    async def process_update_username(
        session: AsyncSession, data: UpdateUserUsernameEvent
    ) -> None:
        """
        Processes the logic for updating a user's username.

        Args:
            session: The database session.
            data: The event containing the user details to be updated.

        Returns:
            None
        """
        await update_user_username(session, data.user_id, data.new_username)

    await handle_subscriber_event(
        session=session,
        event_id=data.event_id,
        event_type=UPDATE_USERNAME_ROUTE.subject,
        process_fn=process_update_username,
        data=data,
    )


@nats_router.subscriber(
    subject=UPDATE_PASSWORD_ROUTE.subject,
    stream=UPDATE_PASSWORD_ROUTE.stream,
    pull_sub=UPDATE_PASSWORD_ROUTE.pull_sub,
    durable=UPDATE_PASSWORD_ROUTE.durable,
)
async def update_password_event(
    session: async_session_dep, data: UpdateUserPasswordEvent
) -> None:
    """
    Subscribes to an event to update a user's password.

    Args:
        session: The database session.
        data: The event containing the user details to be updated
    """

    async def process_update_password(
        session: AsyncSession, data: UpdateUserPasswordEvent
    ) -> None:
        """
        Processes the logic for updating a user's password.

        Args:
            session: The database session.
            data: The event containing the user details to be updated.

        Returns:
            None
        """
        user = await get_user(session, data.user_id)

        if not user:
            raise ValueError(f"User {data.user_id} not found.")

        user.password = data.new_password
        session.add(user)
        await session.commit()
        await session.refresh(user)

    await handle_subscriber_event(
        session=session,
        event_id=data.event_id,
        event_type=UPDATE_PASSWORD_ROUTE.subject,
        process_fn=process_update_password,
        data=data,
    )


@nats_router.subscriber(
    subject=UPDATE_ROLE_ROUTE.subject,
    stream=UPDATE_ROLE_ROUTE.stream,
    pull_sub=UPDATE_ROLE_ROUTE.pull_sub,
    durable=UPDATE_ROLE_ROUTE.durable,
)
async def update_role_event(
    session: async_session_dep, data: UpdateUserRoleEvent
) -> None:
    """
    Subscribes to an event to update a user's role.

    Args:
        session: The database session.
        data: The event containing the user details to be updated
    """

    async def process_user_role(
        session: AsyncSession, data: UpdateUserRoleEvent
    ) -> None:
        """
        Processes the logic for updating a user's role.

        Args:
            session: The database session.
            data: The event containing the user details to be updated.

        Returns:
            None
        """
        await update_user_role(session, data.user_id, data.new_role)

    await handle_subscriber_event(
        session=session,
        event_id=data.event_id,
        event_type=UPDATE_ROLE_ROUTE.subject,
        process_fn=process_user_role,
        data=data,
    )
