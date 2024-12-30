import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncEngine, async_sessionmaker, create_async_engine
from sqlmodel.ext.asyncio.session import AsyncSession

# from sqlmodel import SQLModel
from libs.utils_lib.core.config import settings as utils_lib_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class DatabaseSessionManager:
    def __init__(
        self,
        database_url: str,
        pool_size: int = 150,
        max_overflow: int = 100,
        pool_timeout: int = 30,
    ):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.engine: AsyncEngine | None = None
        self.session_maker: async_sessionmaker[AsyncSession] | None = None

    async def create_database(self) -> None:
        database_url_without_db = f"mysql+aiomysql://{utils_lib_settings.MYSQL_USER}:{utils_lib_settings.MYSQL_PASSWORD}@{utils_lib_settings.MYSQL_SERVER}:{utils_lib_settings.MYSQL_PORT}"

        # Create the engine for MySQL connection (no database specified here)
        temp_engine = create_async_engine(
            database_url_without_db,
            echo=(utils_lib_settings.ENVIRONMENT == "local"),
        )

        # Connect to the MySQL server and check for the existence of the database
        async with temp_engine.connect() as connection:
            try:
                # Check if the database exists by querying `information_schema.schemata`
                result = await connection.execute(
                    text(
                        "SELECT SCHEMA_NAME FROM information_schema.schemata WHERE SCHEMA_NAME = :db_name"
                    ),
                    {"db_name": utils_lib_settings.MYSQL_DATABASE},
                )

                if not result.fetchone():
                    # Database does not exist, create it
                    logger.info(
                        f"Database '{utils_lib_settings.MYSQL_DATABASE}' does not exist. Creating it..."
                    )
                    await connection.execute(
                        text(f"CREATE DATABASE `{utils_lib_settings.MYSQL_DATABASE}`")
                    )
                    await connection.commit()
                    logger.info(
                        f"Database '{utils_lib_settings.MYSQL_DATABASE}' created successfully."
                    )
            except OperationalError as e:
                logger.error(f"Error checking database existence: {e}")
                raise e

        # Close the connection
        await temp_engine.dispose()

    async def init_db(self) -> None:
        """
        Initializes the database connection.
        """
        self.engine = create_async_engine(
            self.database_url,
            pool_pre_ping=True,
            echo=(utils_lib_settings.ENVIRONMENT == "local"),
            pool_size=self.pool_size,
            max_overflow=self.max_overflow,
            pool_timeout=self.pool_timeout,
        )

        self.session_maker = async_sessionmaker(
            bind=self.engine,
            expire_on_commit=False,
            autocommit=False,
            autoflush=False,
            class_=AsyncSession,
        )

        # Create tables with SQLModel metadata (uncomment if not using Alembic also comment out alembic upgrade head in backend/scripts/prestart.sh)
        # async with self.engine.begin() as conn:
        #     await conn.run_sync(SQLModel.metadata.create_all)

        logger.info("Database initialized successfully.")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        if not self.session_maker:
            raise RuntimeError("Session maker is not initialized")

        async with self.session_maker() as session:
            yield session

    async def close(self) -> None:
        """
        Closes the database connection.
        """
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed.")


session_manager = DatabaseSessionManager(database_url=utils_lib_settings.DATABASE_URL)
