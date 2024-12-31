import logging

from faststream.rabbit import RabbitBroker
from faststream.rabbit.fastapi import RabbitRouter

from libs.utils_lib.core.config import settings as utils_lib_settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class RabbitMQ:
    def __init__(self, url: str):
        self.url = url
        self.broker: RabbitBroker = RabbitBroker(url)
        self.router: RabbitRouter = RabbitRouter(
            url,
            schema_url=None,
            setup_state=False,
        )

    async def start(self) -> None:
        try:
            await self.broker.start()
            logger.info("Successfully established RabbitMQ connection.")
        except Exception as e:
            logger.error(f"Error connecting to RabbitMQ: {e}")
            raise

    async def close(self) -> None:
        await self.broker.close()
        logger.info("RabbitMQ broker closed.")


rabbitmq = RabbitMQ(utils_lib_settings.RABBITMQ_URL)
