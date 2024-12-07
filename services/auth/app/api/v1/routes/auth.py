from datetime import datetime, timedelta
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from fastapi.security import OAuth2PasswordRequestForm
from shared_lib.schemas import UserPublic

from app.api.config import api_settings
from app.api.v1.deps import async_session_dep, credential_exception, get_user_from_token
from app.core.security import (
    blacklist_access_token,
    gen_token,
    get_client_ip,
    get_login_attempts,
    get_token_jti,
    increment_login_attempts,
    is_password_complex,
    is_username_complex,
    rate_limiter,
    reset_login_attempts,
    security_settings,
)
from app.crud import (
    authenticate_refresh_token,
    authenticate_user,
    create_refresh_token,
    create_user,
    delete_max_tokens,
    delete_refresh_token,
    get_refresh_tokens,
    get_user_by_email,
    get_user_by_username,
)
from app.schemas import RefreshTokenCreate, Token, UserCreate

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

    # Create the user
    return await create_user(session, user_create=user)


@router.post("/login", response_model=Token)
@rate_limiter.limit("1/second; 10/minute")
async def login(
    response: Response,
    request: Request,
    session: async_session_dep,
    form_data: Annotated[OAuth2PasswordRequestForm, Depends()],
) -> Token:
    """
    Login a user and return an access token.

    Args:
        response (Response): The response object.
        request (Request): The request object.
        session (AsyncSession): The database session.
        form_data (OAuth2PasswordRequestForm): The form data.

    Returns:
        Token: The access token.
    """
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
    elif user.disabled:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user"
        )

    # Reset the number of failed login attempts
    await reset_login_attempts(form_data.username)

    current_time = datetime.utcnow()
    ip_address = get_client_ip(request)

    # Generate access token
    access_token_expires = current_time + timedelta(
        minutes=api_settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token, access_jti = gen_token(
        data={"sub": str(user.id)}, expire=access_token_expires
    )

    # Generate refresh token and store JTI in database
    refresh_token_expires = current_time + timedelta(
        days=api_settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    refresh_token, refresh_jti = gen_token(
        data={"sub": str(user.id)}, expire=refresh_token_expires
    )
    refresh_token_create = RefreshTokenCreate(
        user_id=user.id,
        refresh_jti=refresh_jti,
        access_jti=access_jti,
        created=current_time,
        expires=refresh_token_expires,
        last_used=current_time,
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


@router.post("/logout")
async def logout(
    response: Response, request: Request, session: async_session_dep
) -> dict[str, str]:
    """
    Logout current user.

    Args:
        response (Response): The response object.
        request (Request): The request object.
        session (AsyncSession): The database session.

    Returns:
        dict: The logout message.
    """
    # Check if user has a refresh token
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise credential_exception

    # Get the user from the refresh token
    user = await get_user_from_token(session=session, token=refresh_token)
    if not user:
        raise credential_exception

    # Get the JTI from the refresh token
    refresh_jti = get_token_jti(refresh_token)
    if not refresh_jti:
        raise credential_exception

    # Verify token and delete token from cookie and database
    authenticate_token = await authenticate_refresh_token(
        session=session, user_id=user.id, refresh_jti=refresh_jti
    )
    if authenticate_token:
        last_used = authenticate_token.last_used
        current_time = datetime.utcnow()

        # Delete the refresh token from the database
        await delete_refresh_token(
            session=session, user_id=user.id, refresh_token_id=authenticate_token.id
        )

        # Add Access JTI to redis blacklist if access token has not expired
        if (current_time - last_used) < timedelta(
            minutes=api_settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ):
            expiration_time = timedelta(
                minutes=api_settings.ACCESS_TOKEN_EXPIRE_MINUTES
            ) - (current_time - last_used)
            await blacklist_access_token(authenticate_token.access_jti, expiration_time)

    response.delete_cookie(key="refresh_token")

    return {"detail": f"Logged out of {user.username}"}


@router.post("/refresh-token")
async def refresh_access_token(
    response: Response, request: Request, session: async_session_dep
) -> Token:
    """
    Refresh the access and refresh token.

    Args:
        response (Response): The response object.
        request (Request): The request object.
        session (AsyncSession): The database session.

    Returns:
        Token: The access token.
    """
    # Get the refresh token
    refresh_token = request.cookies.get("refresh_token")
    if not refresh_token:
        raise credential_exception

    # Get the user from the refresh token
    user = await get_user_from_token(session=session, token=refresh_token)
    if not user:
        raise credential_exception

    # Get the JTI from the refresh token
    refresh_jti = get_token_jti(refresh_token)
    if not refresh_jti:
        raise credential_exception

    # Verify token and delete token from database
    prev_refresh_token = await authenticate_refresh_token(
        session=session, user_id=user.id, refresh_jti=refresh_jti
    )
    if not prev_refresh_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Session no longer exists"
        )

    current_time = datetime.utcnow()
    prev_last_used = prev_refresh_token.last_used
    ip_address = get_client_ip(request)

    # Delete the previous refresh token from the database
    await delete_refresh_token(
        session=session, user_id=user.id, refresh_token_id=prev_refresh_token.id
    )

    # Add Access JTI to redis blacklist if access token has not expired
    if (current_time - prev_last_used) < timedelta(
        minutes=api_settings.ACCESS_TOKEN_EXPIRE_MINUTES
    ):
        expiration_time = timedelta(
            minutes=api_settings.ACCESS_TOKEN_EXPIRE_MINUTES
        ) - (current_time - prev_last_used)
        await blacklist_access_token(prev_refresh_token.access_jti, expiration_time)

    # Create a new access token
    access_token_expires = current_time + timedelta(
        minutes=api_settings.ACCESS_TOKEN_EXPIRE_MINUTES
    )
    access_token, access_jti = gen_token(
        data={"sub": str(user.id)}, expire=access_token_expires
    )

    # Create a new refresh token and store JTI in database
    new_refresh_token_expires = current_time + timedelta(
        days=api_settings.REFRESH_TOKEN_EXPIRE_DAYS
    )
    new_refresh_token, new_refresh_jti = gen_token(
        data={"sub": str(user.id)}, expire=new_refresh_token_expires
    )
    refresh_token_create = RefreshTokenCreate(
        user_id=user.id,
        refresh_jti=new_refresh_jti,
        access_jti=access_jti,
        created=prev_refresh_token.created,
        expires=new_refresh_token_expires,
        last_used=current_time,
        ip_address=ip_address,
    )
    await create_refresh_token(
        session=session, refresh_token_create=refresh_token_create
    )

    # Set refresh token in cookie
    response.set_cookie(
        key="refresh_token",
        value=new_refresh_token,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=api_settings.REFRESH_TOKEN_EXPIRE_DAYS * 24 * 60 * 60,
    )

    return Token(access_token=access_token, token_type="bearer")
