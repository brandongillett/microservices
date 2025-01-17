from fastapi import APIRouter

from src.api.v1.routes import utils

api_router = APIRouter()

api_router.include_router(utils.router, prefix="/utils", tags=["utils"])
