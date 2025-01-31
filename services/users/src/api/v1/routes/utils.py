from fastapi import APIRouter, Request

from libs.utils_lib.core.security import rate_limiter

router = APIRouter()


@router.get("/health")
@rate_limiter.limit("10/minute")
async def health_check(request: Request) -> bool:
    """
    Health check endpoint.

    Returns:
        bool: True
    """
    _ = request  # Unused variable (mandatory for rate limiter)

    return True


@router.get("/version")
@rate_limiter.limit("10/minute")
async def version(request: Request) -> str:
    """
    Get the API version.

    Returns:
        str: The API version.
    """
    _ = request  # Unused variable (mandatory for rate limiter)

    return "v1"
