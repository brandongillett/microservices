import logging
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from sqlalchemy import text
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
        pool_size: int = 10,
        max_overflow: int = 5,
        pool_timeout: int = 30,
    ):
        self.database_url = database_url
        self.pool_size = pool_size
        self.max_overflow = max_overflow
        self.pool_timeout = pool_timeout
        self.engine: AsyncEngine | None = None
        self.session_maker: async_sessionmaker[AsyncSession] | None = None
        self.read_engine: AsyncEngine | None = None
        self.read_session_maker: async_sessionmaker[AsyncSession] | None = None

    async def create_database(self) -> None:
        """
        Creates the database if it does not exist.
        """
        # Connect to the default 'postgres' database to create the target database
        db_url = (
            f"{utils_lib_settings.POSTGRES_CONNECTION_SCHEME}+asyncpg://{utils_lib_settings.POSTGRES_USER}:{utils_lib_settings.POSTGRES_PASSWORD}"
            f"@{utils_lib_settings.POSTGRES_SERVER}:{utils_lib_settings.POSTGRES_PORT}/postgres"
        )

        engine = create_async_engine(db_url, isolation_level="AUTOCOMMIT")

        async with engine.connect() as connection:
            check_db_sql = text("SELECT 1 FROM pg_database WHERE datname = :db_name")
            result = await connection.execute(
                check_db_sql, {"db_name": utils_lib_settings.POSTGRES_DB}
            )
            exists = result.scalar() is not None
            if exists:
                logger.info(
                    f"Database '{utils_lib_settings.POSTGRES_DB}' already exists."
                )
            else:
                create_db_sql = text(
                    f'CREATE DATABASE "{utils_lib_settings.POSTGRES_DB}"'
                )
                await connection.execute(create_db_sql)
                logger.info(
                    f"Database '{utils_lib_settings.POSTGRES_DB}' created successfully."
                )

        await engine.dispose()

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

        if utils_lib_settings.READ_DATABASE_URL:
            self.read_engine = create_async_engine(
                str(utils_lib_settings.READ_DATABASE_URL),
                pool_pre_ping=True,
                echo=(utils_lib_settings.ENVIRONMENT == "local"),
                pool_size=self.pool_size,
                max_overflow=self.max_overflow,
                pool_timeout=self.pool_timeout,
            )

            self.read_session_maker = async_sessionmaker(
                bind=self.read_engine,
                expire_on_commit=False,
                autocommit=False,
                autoflush=False,
                class_=AsyncSession,
            )

            logger.info("Read database detected and initialized successfully.")

    @asynccontextmanager
    async def get_session(
        self, read_only: bool = False
    ) -> AsyncGenerator[AsyncSession, None]:
        """
        Gets the database session.

        Args:
            read_only (bool): Whether to use the read-only session (if configured).
        Yields:
            AsyncSession: The database session.
        """
        if read_only and self.read_session_maker:
            async with self.read_session_maker() as session:
                yield session
        elif self.session_maker:
            async with self.session_maker() as session:
                yield session
        else:
            raise Exception("Session maker not initialized")

    async def close(self) -> None:
        """
        Closes the database connection.
        """
        if self.engine:
            await self.engine.dispose()
            logger.info("Database connection closed.")


session_manager = DatabaseSessionManager(
    database_url=str(utils_lib_settings.DATABASE_URL)
)
