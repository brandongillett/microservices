from fastapi import APIRouter

from src.api.v1.routes import auth, tokens, utils, verification

api_router = APIRouter()

api_router.include_router(auth.router, tags=["auth"])
api_router.include_router(tokens.router, prefix="/tokens", tags=["tokens"])
api_router.include_router(
    verification.router, prefix="/verification", tags=["verification"]
)
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
