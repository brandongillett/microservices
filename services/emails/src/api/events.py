from faststream.nats.fastapi import NatsRouter
from sqlmodel import delete, not_
from sqlmodel.ext.asyncio.session import AsyncSession

from libs.auth_lib.api.events import (
    CREATE_ROOT_USER_ROUTE,
    CREATE_USER_ROUTE,
    FORGOT_PASSWORD_SEND_ROUTE,
    VERIFICATION_SEND_ROUTE,
    VERIFY_USER_ROUTE,
)
from libs.auth_lib.schemas import (
    CreateUserEvent,
    ForgotPasswordSendEvent,
    VerificationSendEvent,
    VerifyUserEvent,
)
from libs.users_lib.api.events import PASSWORD_UPDATED_ROUTE, UPDATE_USERNAME_ROUTE
from libs.users_lib.models import Users
from libs.users_lib.schemas import UpdateUserUsernameEvent, UserPasswordUpdatedEvent
from libs.utils_lib.api.deps import async_session_dep
from libs.utils_lib.api.events import (
    handle_subscriber_event,
    logger,
)
from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.models import EventInbox, EventOutbox
from src.core.config import settings
from src.crud import (
    get_user,
    get_user_by_username,
    update_user_username,
    verify_user_email,
)
from src.models import UserEmails
from src.utils import send_forgot_password, send_password_updated, send_verification

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
        statement = delete(UserEmails).where(not_(UserEmails.username == "root"))
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
    Subscribes to an event to create a root user.

    Args:
        session: The database session.
        user (User): The user to create.
    """
    user_exists = await get_user_by_username(session, user.username)

    if not user_exists:
        dbObj = UserEmails.model_validate(user)
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
        data: The event containing the user details to be created.
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
        dbObj = UserEmails.model_validate(data.user)
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
    try:
        await send_verification(
            user_id=data.user.id,
            username=data.user.username,
            email=data.user.email,
        )
    except Exception as e:
        logger.error(f"Failed to send verification email: {e}")


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
    subject=PASSWORD_UPDATED_ROUTE.subject,
    stream=PASSWORD_UPDATED_ROUTE.stream,
    pull_sub=PASSWORD_UPDATED_ROUTE.pull_sub,
    durable=PASSWORD_UPDATED_ROUTE.durable,
)
async def password_updated_send_event(
    session: async_session_dep, data: UserPasswordUpdatedEvent
) -> None:
    """
    Subscribes to an event to notify that a user's password has been updated.

    Args:
        session: The database session.
        data: The event containing the user details whose password was updated.
    """

    async def process_password_updated_send_event(
        session: async_session_dep,
        data: UserPasswordUpdatedEvent,
    ) -> None:
        """
        Processes the logic for notifying that a user's password has been updated.

        Args:
            session: The database session.
            data: The event containing the user details whose password was updated.

        Returns:
            None
        """
        _ = session  # Unused session

        user_data = UserEmails.model_validate(data.user)
        await send_password_updated(
            username=user_data.username,
            email=user_data.email,
        )

    await handle_subscriber_event(
        session=session,
        event_id=data.event_id,
        event_type=PASSWORD_UPDATED_ROUTE.subject,
        process_fn=process_password_updated_send_event,
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
        data: The event containing the user details to be verified.
    """

    async def process_verify_user_event(
        session: AsyncSession, data: VerifyUserEvent
    ) -> None:
        """
        Processes the logic for verifying a user's email.

        Args:
            session: The database session.
            data: The event containing the user details to be verified.

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


@nats_router.subscriber(
    subject=VERIFICATION_SEND_ROUTE.subject,
    stream=VERIFICATION_SEND_ROUTE.stream,
    pull_sub=VERIFICATION_SEND_ROUTE.pull_sub,
    durable=VERIFICATION_SEND_ROUTE.durable,
)
async def verification_send_event(
    session: async_session_dep, data: VerificationSendEvent
) -> None:
    """
    Subscribes to an event to send a verification email.

    Args:
        data: The user to send the verification email to.
    """

    async def process_verification_send_event(
        session: AsyncSession, data: VerificationSendEvent
    ) -> None:
        """
        Processes the logic for sending a verification email.

        Args:
            session: The database session.
            data: The event containing the user details to send the verification email to.

        Returns:
            None
        """
        user_data = UserEmails.model_validate(data.user)

        user = await get_user(
            session=session,
            user_id=user_data.id,
        )

        if not user or user.verified:
            logger.warning(
                f"User {user_data.id} does not exist or is already verified. Skipping verification email."
            )
            return

        await send_verification(
            user_id=user.id,
            username=user.username,
            email=user.email,
        )

    await handle_subscriber_event(
        session=session,
        event_id=data.event_id,
        event_type=VERIFICATION_SEND_ROUTE.subject,
        process_fn=process_verification_send_event,
        data=data,
    )


@nats_router.subscriber(
    subject=FORGOT_PASSWORD_SEND_ROUTE.subject,
    stream=FORGOT_PASSWORD_SEND_ROUTE.stream,
    pull_sub=FORGOT_PASSWORD_SEND_ROUTE.pull_sub,
    durable=FORGOT_PASSWORD_SEND_ROUTE.durable,
)
async def forgot_password_send_event(
    session: async_session_dep, data: ForgotPasswordSendEvent
) -> None:
    """
    Subscribes to an event to send a forgot password email.

    Args:
        session: The database session.
        data: The event containing the user details to send the forgot password email to.
    """

    async def process_forgot_password_send_event(
        session: AsyncSession, data: ForgotPasswordSendEvent
    ) -> None:
        """
        Processes the logic for sending a forgot password email.

        Args:
            session: The database session.
            data: The event containing the user details to send the forgot password email to.

        Returns:
            None
        """
        user = await get_user(session, user_id=data.user_id)

        if not user:
            logger.warning(
                f"User {data.user_id} does not exist. Skipping forgot password email."
            )
            return

        await send_forgot_password(
            token=data.token,
            username=user.username,
            email=user.email,
        )

    await handle_subscriber_event(
        session=session,
        event_id=data.event_id,
        event_type=FORGOT_PASSWORD_SEND_ROUTE.subject,
        process_fn=process_forgot_password_send_event,
        data=data,
    )
