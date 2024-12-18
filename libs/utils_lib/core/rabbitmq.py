from faststream.rabbit import RabbitBroker

from libs.utils_lib.core.config import settings as utils_lib_settings

rabbit_broker = RabbitBroker(utils_lib_settings.RABBITMQ_URL)