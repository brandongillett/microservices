from fastapi import APIRouter
from fastapi.params import Depends

from libs.utils_lib.core.limiter import Limiter

router = APIRouter()


@router.get("/health", dependencies=[Depends(Limiter("30/minute"))])
async def health_check() -> bool:
    """
    Health check endpoint.

    Returns:
        bool: True
    """
    return True


@router.get("/version", dependencies=[Depends(Limiter("30/minute"))])
async def version() -> str:
    """
    Get the API version.

    Returns:
        str: The API version.
    """
    return "v1"
