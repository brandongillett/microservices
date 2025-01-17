import asyncio

from libs.utils_lib.backend_pre_start import (
    logger,
    test_db_connection,
    test_rabbitmq_connection,
    test_redis_connection,
)
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.rabbitmq import rabbitmq
from libs.utils_lib.core.redis import redis_client


async def main() -> None:
    """
    Main function to run the initialization process.
    """
    try:
        logger.info("Initializing services...")
        await session_manager.create_database()
        await test_db_connection(session_manager)
        await test_redis_connection(redis_client)
        await test_rabbitmq_connection(rabbitmq)
        logger.info("Services finished initializing...")
    except Exception as e:
        logger.critical(f"Service initialization failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
