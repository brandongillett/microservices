from faststream.nats.fastapi import NatsRouter
from sqlmodel import delete, not_
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.api.events import (
    CREATE_ROOT_USER_ROUTE,
    CREATE_USER_ROUTE,
    VERIFY_USER_ROUTE,
)
from libs.auth_lib.crud import verify_user_email
from libs.auth_lib.schemas import CreateUserEvent, VerifyUserEvent
from libs.users_lib.api.events import UPDATE_PASSWORD_ROUTE
from libs.users_lib.crud import get_user, get_user_by_username
from libs.users_lib.models import Users
from libs.users_lib.schemas import UpdateUserPasswordEvent
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.api.events import (
    handle_subscriber_event,
    logger,
)
from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.models import EventInbox, EventOutbox
from src.core.config import settings

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
    subject=CREATE_ROOT_USER_ROUTE.subject,
    stream=CREATE_ROOT_USER_ROUTE.stream,
    pull_sub=CREATE_ROOT_USER_ROUTE.pull_sub,
    durable=CREATE_ROOT_USER_ROUTE.durable,
)
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


@nats_router.subscriber(
    subject=CREATE_USER_ROUTE.subject,
    stream=CREATE_USER_ROUTE.stream,
    pull_sub=CREATE_USER_ROUTE.pull_sub,
    durable=CREATE_USER_ROUTE.durable,
)
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
        event_type=CREATE_USER_ROUTE.subject,
        process_fn=process_create_user,
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
    subject=VERIFY_USER_ROUTE.subject,
    stream=VERIFY_USER_ROUTE.stream,
    pull_sub=VERIFY_USER_ROUTE.pull_sub,
    durable=VERIFY_USER_ROUTE.durable,
)
async def verify_user_event(session: async_session_dep, data: VerifyUserEvent) -> None:
    """
    Subscribes to an event to to verify a user's email.

    Args:
        session: The database session.
        user (User): The user to create.
    """

    async def process_verify_user_event(
        session: AsyncSession, data: VerifyUserEvent
    ) -> None:
        """
        Processes the logic for verifying a user's email.

        Args:
            session: The database session.
            data: The event containing the user details to be created.

        Returns:
            None
        """
        await verify_user_email(session, data.user_id)

    await handle_subscriber_event(
        session=session,
        event_id=data.event_id,
        event_type=VERIFY_USER_ROUTE.subject,
        process_fn=process_verify_user_event,
        data=data,
    )
