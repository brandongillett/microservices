from faststream.rabbit.fastapi import RabbitRouter

from src.broker import publishers

rabbit_router = RabbitRouter()

rabbit_router.include_router(publishers.rabbit_router)
