from faststream.rabbit.fastapi import RabbitRouter

from src.broker import subscribers

rabbit_router = RabbitRouter()

rabbit_router.include_router(subscribers.rabbit_router)
