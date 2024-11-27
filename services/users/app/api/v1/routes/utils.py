from fastapi import APIRouter

router = APIRouter()


@router.get("/health")
async def health_check() -> bool:
    """
    Health check endpoint.

    Returns:
        bool: True
    """
    return True


@router.get("/version")
async def version() -> str:
    """
    Get the API version.

    Returns:
        str: The API version.
    """
    return "v1"
