from datetime import datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm

from libs.auth_lib.core.security import (
    is_password_complex,
    is_username_complex,
)
from libs.auth_lib.schemas import TokenData
from libs.users_lib.crud import get_user, get_user_by_email, get_user_by_username
from libs.users_lib.schemas import UserPublic
from libs.utils_lib.api.deps import async_session_dep, client_ip_dep
from libs.utils_lib.core.security import rate_limiter
from libs.utils_lib.schemas import Message
from src.api.config import api_settings
from src.api.deps import consumed_refresh_token
from src.api.events import create_user_event
from src.core.security import (
    gen_token,
    get_login_attempts,
    increment_login_attempts,
    reset_login_attempts,
    security_settings,
)
from src.crud import (
    authenticate_user,
    create_refresh_token,
    create_user,
    delete_max_tokens,
    get_refresh_tokens,
)
from src.schemas import RefreshTokenCreate, Token, UserCreate

router = APIRouter()


@router.post("/register", response_model=UserPublic)
@rate_limiter.limit("10/minute; 30/hour")
async def register(
    request: Request, session: async_session_dep, user: UserCreate
) -> Any:
    """
    Register a new user.

    Args:
        request (Request): The request object.
        session (AsyncSession): The database session.
        user (UserCreate): The user data.

    Returns:
        UserPublic: The user data.
    """
    _ = request  # Unused variable (mandatory for rate limiter)

    # Check if username and password meet the required complexity
    username_complexity = is_username_complex(user.username)
    if username_complexity:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=username_complexity
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

    try:
        # Create the user
        new_user = await create_user(session, user_create=user, commit=False)

        # Publish the user to the broker
        await create_user_event(session=session, user=new_user)
    except Exception:
        # Rollback the transaction if the event fails
        await session.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user {new_user.username}",
        )

    await session.commit()
    await session.refresh(new_user)

    # Return the user data
    return new_user


@router.post("/login", response_model=Token)
@rate_limiter.limit("1/second; 10/minute")
async def login(
    response: Response,
    request: Request,
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
    _ = request  # Unused variable (mandatory for rate limiter)

    # Check if user has exceeded the maximum number of failed login attempts
    if (
        await get_login_attempts(form_data.username)
        >= security_settings.MAX_FAILED_LOGIN_ATTEMPTS
    ):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Too many failed login attempts (Please try again later)",
        )

    # Try to authenticate the user with the provided credentials
    user = await authenticate_user(
        session=session, username_email=form_data.username, password=form_data.password
    )
    if not user:
        # Increment the number of failed login attempts
        current_attempts = await increment_login_attempts(form_data.username)
        remaining_attempts = (
            security_settings.MAX_FAILED_LOGIN_ATTEMPTS - current_attempts
        )
        invalid_message = (
            f"Invalid login attempt ({remaining_attempts} attempts left)"
            if current_attempts > 1
            else "Invalid login attempt"
        )

        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=invalid_message,
            headers={"WWW-Authenticate": "Bearer"},
        )
    if user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    # Reset the number of failed login attempts
    await reset_login_attempts(form_data.username)

    current_time = datetime.utcnow()

    # Generate access token
    access_token_expires = current_time + timedelta(
        minutes=api_settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token_data = TokenData(user_id=user.id, role=user.role, type="access")
    access_token, _ = gen_token(
        data=access_token_data,
        expire=access_token_expires,
    )

    # Generate refresh token and store JTI in database
    refresh_token_expires = current_time + timedelta(
        days=api_settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    refresh_token_data = TokenData(user_id=user.id, role=user.role, type="refresh")
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


@router.post("/logout", response_model=Message)
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


@router.post("/token/refresh", response_model=Token)
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
    user = await get_user(session, user_id=consumed_refresh_token.user_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )
    current_time = datetime.utcnow()

    # Create a new access token
    access_token_expires = current_time + timedelta(
        minutes=api_settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token_data = TokenData(user_id=user.id, role=user.role, type="access")
    access_token, _ = gen_token(
        data=access_token_data,
        expire=access_token_expires,
    )

    # Create a new refresh token and store JTI in database
    refresh_token_expires = current_time + timedelta(
        days=api_settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    refresh_token_data = TokenData(user_id=user.id, role=user.role, type="refresh")
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
