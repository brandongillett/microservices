import asyncio

from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.faststream import nats
from libs.utils_lib.core.redis import redis_client
from libs.utils_lib.prestart import (
    db_create_database,
    logger,
    nats_create_stream,
    test_db_connection,
    test_nats_connection,
    test_redis_connection,
)


async def main() -> None:
    """
    Main function to run the initialization process.
    """
    try:
        logger.info("Initializing services...")
        await db_create_database(session_manager)
        await test_db_connection(session_manager)
        await test_redis_connection(redis_client)
        await test_nats_connection(nats)
        await nats_create_stream(nats)
        logger.info("Services finished initializing...")
    except Exception as e:
        logger.critical(f"Service initialization failed: {e}")


if __name__ == "__main__":
    asyncio.run(main())
