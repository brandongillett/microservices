import asyncio

from libs.auth_lib.core.redis import redis_tokens_client
from libs.utils_lib.backend_pre_start import (
    logger,
    test_db_connection,
    test_redis_connection,
)
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.redis import redis_client


async def main() -> None:
    """
    Main function to run the initialization process.
    """
    try:
        logger.info("Initializing services...")
        await test_db_connection(session_manager)
        await test_redis_connection(redis_client)
        await test_redis_connection(redis_tokens_client)
        logger.info("Services finished initializing...")
    except Exception as e:
        logger.critical(f"Service initialization failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
