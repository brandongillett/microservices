from fastapi import APIRouter

from src.api.v1.routes import auth, tokens, utils

api_router = APIRouter()

api_router.include_router(auth.router, prefix="/auth", tags=["auth"])
api_router.include_router(tokens.router, prefix="/tokens", tags=["tokens"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
