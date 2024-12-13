from fastapi import APIRouter

from app.api.v1.routes import management, users, utils

api_router = APIRouter()

api_router.include_router(users.router, prefix="/users", tags=["users"])
api_router.include_router(management.router, prefix="/management", tags=["management"])
api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
