import logging

from faststream.nats import NatsBroker
from faststream.nats.fastapi import NatsRouter
from nats.aio.client import Client as NATS
from nats.js.api import StreamConfig
from nats.js.errors import NotFoundError

from libs.utils_lib.core.config import settings as utils_lib_settings
from src.core.config import settings

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class NatsClient:
    def __init__(self, url: str):
        self.url = url
        self.broker: NatsBroker = NatsBroker(url)
        self.router: NatsRouter = NatsRouter(
            url,
            schema_url=None,
            setup_state=False,
        )
        self.stream = f"{settings.SERVICE_NAME}_stream"
        # Standard stream configuration (Manually update to scale)
        self.stream_config = StreamConfig(
            name=self.stream,
            subjects=[f"{settings.SERVICE_NAME}.>"],
            retention="limits",
            max_msgs=-1,
            max_bytes=-1,
            max_age=86400 * 3,  # 3 days
            storage="file",
            discard="old",
            num_replicas=1,
        )

    async def create_stream(self) -> None:
        """
        Create the JetStream stream if it doesn't already exist.
        """
        nc = NATS()
        await nc.connect(servers=[self.url])
        js = nc.jetstream()

        try:
            await js.stream_info(self.stream)
            logger.info(f"JetStream stream '{self.stream}' already exists.")
        except NotFoundError:
            logger.warning(
                f"JetStream stream '{self.stream}' not found. Creating it..."
            )
            await js.add_stream(self.stream_config)
            logger.info(f"JetStream stream '{self.stream}' created successfully.")

        await nc.close()

    async def start(self) -> None:
        """
        Starts the NATS broker connection.
        """
        try:
            await self.broker.start()
            logger.info("Successfully established NATS connection.")
        except Exception as e:
            logger.error(f"Error connecting to NATS: {e}")
            raise

    async def close(self) -> None:
        """
        Closes the NATS broker connection.
        """
        await self.broker.close()
        logger.info("NATS broker closed.")


nats = NatsClient(utils_lib_settings.NATS_URL)
