from datetime import datetime, timedelta
from typing import Annotated, Any
from uuid import uuid4

from fastapi import APIRouter, Depends, HTTPException, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from libs.auth_lib.api.events import CREATE_USER_ROUTE, FORGOT_PASSWORD_SEND_ROUTE
from libs.auth_lib.core.security import (
    is_email_valid,
    is_password_complex,
    is_username_valid,
    verify_password,
)
from libs.auth_lib.schemas import (
    CreateUserEvent,
    ForgotPasswordSendEvent,
    TokenData,
)
from libs.auth_lib.utils import (
    gen_password_reset_token,
    invalidate_password_reset_token,
    verify_password_reset_token,
)
from libs.users_lib.api.events import PASSWORD_UPDATED_ROUTE, UPDATE_PASSWORD_ROUTE
from libs.users_lib.crud import (
    get_user,
    get_user_by_email,
    get_user_by_username,
    update_user_password,
)
from libs.users_lib.schemas import (
    UpdateUserPasswordEvent,
    UserPasswordUpdatedEvent,
    UserPublic,
)
from libs.utils_lib.api.deps import async_session_dep, client_ip_dep
from libs.utils_lib.api.events import handle_publish_event
from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.core.limiter import Limiter
from libs.utils_lib.crud import create_outbox_event
from libs.utils_lib.schemas import Message
from src.api.config import api_settings
from src.api.deps import consumed_refresh_token, get_valid_user
from src.core.security import gen_token
from src.crud import (
    authenticate_user,
    create_refresh_token,
    create_user,
    delete_max_tokens,
    get_refresh_tokens,
)
from src.schemas import RefreshTokenCreate, ResetPassword, Token, UserCreate

router = APIRouter()


@router.post(
    "/register",
    response_model=UserPublic,
    dependencies=[Depends(Limiter("5/minute,25/hour,50/day"))],
)
async def register(session: async_session_dep, user: UserCreate) -> Any:
    """
    Register a new user.

    Args:
        request (Request): The request object.
        session (AsyncSession): The database session.
        user (UserCreate): The user data.

    Returns:
        UserPublic: The user data.
    """
    # Check if email, username, and password meet the required complexity
    username_complexity = is_username_valid(user.username)
    if username_complexity:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=username_complexity
        )
    email_valid = is_email_valid(user.email)
    if email_valid:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=email_valid
        )
    password_complexity = is_password_complex(user.password)
    if password_complexity:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=password_complexity
        )

    # Check if username and email are unique
    if await get_user_by_username(session, username=user.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username is already taken"
        )
    if await get_user_by_email(session, email=user.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email is already taken"
        )

    # Convert username and email to lowercase
    user.username = user.username.lower()
    user.email = user.email.lower()

    # Create the user
    new_user = await create_user(session, user_create=user, commit=False)

    # Create event for user creation
    event_users_create_user_id = uuid4()
    event_users_create_user_schema = CreateUserEvent(
        event_id=event_users_create_user_id, user=new_user
    )

    event_users_create_user = await create_outbox_event(
        session=session,
        event_id=event_users_create_user_id,
        event_type=CREATE_USER_ROUTE.subject_for("users"),
        data=event_users_create_user_schema.model_dump(mode="json"),
        commit=False,
    )

    # Create create user email event
    event_emails_create_user_id = uuid4()
    event_emails_create_user_schema = CreateUserEvent(
        event_id=event_emails_create_user_id, user=new_user
    )

    event_emails_create_user = await create_outbox_event(
        session=session,
        event_id=event_emails_create_user_id,
        event_type=CREATE_USER_ROUTE.subject_for("emails"),
        data=event_emails_create_user_schema.model_dump(mode="json"),
        commit=False,
    )

    # Commit and refresh the user
    await session.commit()
    await session.refresh(new_user)
    await session.refresh(event_users_create_user)
    await session.refresh(event_emails_create_user)

    # Publish the events
    await handle_publish_event(
        session=session,
        event=event_users_create_user,
        event_schema=event_users_create_user_schema,
    )
    await handle_publish_event(
        session=session,
        event=event_emails_create_user,
        event_schema=event_emails_create_user_schema,
    )

    # Return the user data
    return new_user


@router.post(
    "/login",
    response_model=Token,
    dependencies=[Depends(Limiter("10/minute,50/hour,200/day"))],
)
async def login(
    response: Response,
    ip_address: client_ip_dep,
    session: async_session_dep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Login a user and return an access token.

    Args:
        response (Response): The response object.
        request (Request): The request object.
        ip_address (str): The client IP address.
        session (AsyncSession): The database session.
        form_data (OAuth2PasswordRequestForm): The form data.

    Returns:
        Token: The access token.
    """
    # Try to authenticate the user with the provided credentials
    user = await authenticate_user(
        session=session, username_email=form_data.username, password=form_data.password
    )
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )

    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="User inactive"
        )

    if utils_lib_settings.REQUIRE_USER_VERIFICATION and not user.verified:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not verified",
        )

    current_time = datetime.utcnow()

    # Generate access token
    access_token_expires = current_time + timedelta(
        minutes=api_settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token_data = TokenData(
        user_id=user.id, role=user.role.value, verified=user.verified, type="access"
    )
    access_token, _ = gen_token(
        data=access_token_data,
        expire=access_token_expires,
    )

    # Generate refresh token and store JTI in database
    refresh_token_expires = current_time + timedelta(
        days=api_settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    refresh_token_data = TokenData(
        user_id=user.id, role=user.role.value, verified=user.verified, type="refresh"
    )
    refresh_token, refresh_jti = gen_token(
        data=refresh_token_data,
        expire=refresh_token_expires,
    )
    refresh_token_create = RefreshTokenCreate(
        user_id=user.id,
        jti=refresh_jti,
        created_at=current_time,
        expires_at=refresh_token_expires,
        last_used_at=current_time,
        ip_address=ip_address,
    )
    await create_refresh_token(
        session=session, refresh_token_create=refresh_token_create
    )

    # Check if user has more than the maximum number of refresh tokens
    current_refresh_tokens = await get_refresh_tokens(session=session, user_id=user.id)
    if len(current_refresh_tokens) > api_settings.MAX_REFRESH_TOKENS:
        await delete_max_tokens(session=session, user_id=user.id)

    # Set refresh token in cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=api_settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/logout",
    response_model=Message,
    dependencies=[Depends(Limiter("20/minute,100/hour"))],
)
async def logout(
    session: async_session_dep, consumed_refresh_token: consumed_refresh_token
) -> Message:
    """
    Logout current user.

    Args:
        session (AsyncSession): The database session.
        consumed_refresh_token (RefreshToken): The consumed refresh token.

    Returns:
        dict: The logout message.
    """
    user = await get_user(session, user_id=consumed_refresh_token.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    return Message(message=f"Logged out of {user.username}")


@router.post(
    "/token/refresh",
    response_model=Token,
    dependencies=[Depends(Limiter("10/minute,60/hour"))],
)
async def refresh_access_token(
    response: Response,
    ip_address: client_ip_dep,
    session: async_session_dep,
    consumed_refresh_token: consumed_refresh_token,
) -> Token:
    """
    Refresh the access and refresh token.

    Args:
        response (Response): The response object.
        ip_address (str): The client IP address.
        session (AsyncSession): The database session.
        consumed_refresh_token (RefreshToken): The consumed refresh token.

    Returns:
        Token: The access token.
    """
    user = await get_valid_user(session=session, user_id=consumed_refresh_token.user_id)

    current_time = datetime.utcnow()

    # Create a new access token
    access_token_expires = current_time + timedelta(
        minutes=api_settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token_data = TokenData(
        user_id=user.id, role=user.role.value, verified=user.verified, type="access"
    )
    access_token, _ = gen_token(
        data=access_token_data,
        expire=access_token_expires,
    )

    # Create a new refresh token and store JTI in database
    refresh_token_expires = current_time + timedelta(
        days=api_settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    refresh_token_data = TokenData(
        user_id=user.id, role=user.role.value, verified=user.verified, type="refresh"
    )
    refresh_token, refresh_jti = gen_token(
        data=refresh_token_data,
        expire=refresh_token_expires,
    )
    refresh_token_create = RefreshTokenCreate(
        user_id=user.id,
        jti=refresh_jti,
        created_at=consumed_refresh_token.created_at,
        expires_at=refresh_token_expires,
        last_used_at=current_time,
        ip_address=ip_address,
    )
    await create_refresh_token(
        session=session, refresh_token_create=refresh_token_create
    )

    # Set refresh token in cookie
    response.set_cookie(
        key="refresh_token",
        value=refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=api_settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return Token(access_token=access_token, token_type="bearer")


@router.post(
    "/password/forgot",
    response_model=Message,
    dependencies=[Depends(Limiter("5/minute,15/hour,25/day"))],
)
async def send_forgot_password(
    session: async_session_dep, username_email: str
) -> Message:
    """
    Send a password reset email.

    Args:
        session (AsyncSession): The database session.

    Returns:
        Message: The response message.
    """

    # Check if the username or email exists
    if "@" in username_email:
        user = await get_valid_user(session=session, email=username_email)
    else:
        user = await get_valid_user(session=session, username=username_email)

    # Generate password reset token
    reset_token = await gen_password_reset_token(user.id)

    # Create forgot password event
    event_emails_send_forgot_password_id = uuid4()
    event_emails_send_forgot_password_schema = ForgotPasswordSendEvent(
        event_id=event_emails_send_forgot_password_id,
        user_id=user.id,
        token=reset_token,
    )

    event_emails_send_forgot_password = await create_outbox_event(
        session=session,
        event_id=event_emails_send_forgot_password_id,
        event_type=FORGOT_PASSWORD_SEND_ROUTE.subject_for("emails"),
        data=event_emails_send_forgot_password_schema.model_dump(mode="json"),
        commit=False,
    )

    await session.commit()
    await session.refresh(event_emails_send_forgot_password)

    # Publish the event
    await handle_publish_event(
        session=session,
        event=event_emails_send_forgot_password,
        event_schema=event_emails_send_forgot_password_schema,
    )

    return Message(message=f"Password reset email sent to {user.email}")


@router.post(
    "/password/reset",
    response_model=Message,
    dependencies=[Depends(Limiter("5/minute,15/hour,25/day"))],
)
async def reset_password(session: async_session_dep, body: ResetPassword) -> Message:
    """
    Reset user password.

    Args:
        session (AsyncSession): The database session.
        token (str): The password reset token.
        body (ResetPassword): Body containing the new password.

    Returns:
        Message: The response message.
    """
    # Verify the password reset token
    user_id, token_id = await verify_password_reset_token(body.token)

    user = await get_valid_user(session=session, user_id=user_id)

    # Check if the current password is same as the new password
    if await verify_password(body.new_password, user.password):
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="New password cannot be same as the current password",
        )

    # Check password complexity
    password_complexity = is_password_complex(body.new_password)
    if password_complexity:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=password_complexity
        )

    # Update the user password
    user = await update_user_password(
        session=session,
        user_id=user.id,
        new_password=body.new_password,
        commit=False,
    )

    # Users password updated event
    event_users_update_password_id = uuid4()
    event_users_update_password_schema = UpdateUserPasswordEvent(
        event_id=event_users_update_password_id,
        user_id=user.id,
        new_password=user.password,
    )

    event_users_update_password = await create_outbox_event(
        session=session,
        event_id=event_users_update_password_id,
        event_type=UPDATE_PASSWORD_ROUTE.subject_for("users"),
        data=event_users_update_password_schema.model_dump(mode="json"),
        commit=False,
    )

    # Emails password updated event
    event_emails_password_updated_id = uuid4()
    event_emails_password_updated_schema = UserPasswordUpdatedEvent(
        event_id=event_emails_password_updated_id, user=user
    )

    event_emails_password_updated = await create_outbox_event(
        session=session,
        event_id=event_emails_password_updated_id,
        event_type=PASSWORD_UPDATED_ROUTE.subject_for("emails"),
        data=event_emails_password_updated_schema.model_dump(mode="json"),
        commit=False,
    )

    await invalidate_password_reset_token(token_id)

    await session.commit()
    await session.refresh(user)
    await session.refresh(event_users_update_password)
    await session.refresh(event_emails_password_updated)

    # Publish events
    await handle_publish_event(
        session=session,
        event=event_users_update_password,
        event_schema=event_users_update_password_schema,
    )

    await handle_publish_event(
        session=session,
        event=event_emails_password_updated,
        event_schema=event_emails_password_updated_schema,
    )

    return Message(message="Password has been reset successfully")
