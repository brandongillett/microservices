# from sqlmodel import SQLModel
from app.core.config import settings
from libs.utils_lib.core.database import DatabaseSessionManager

# Initialize the DatabaseSessionManager
session_manager = DatabaseSessionManager(database_url=settings.DATABASE_URL)
