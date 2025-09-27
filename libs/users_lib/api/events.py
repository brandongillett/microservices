from libs.utils_lib.core.faststream import nats
from libs.utils_lib.schemas import EventRoute
from src.core.config import settings

UPDATE_USERNAME_ROUTE = EventRoute(
    service=settings.SERVICE_NAME,
    name="update.username",
    stream_name=nats.stream,
)

UPDATE_PASSWORD_ROUTE = EventRoute(
    service=settings.SERVICE_NAME,
    name="update.password",
    stream_name=nats.stream,
)

PASSWORD_UPDATED_ROUTE = EventRoute(
    service=settings.SERVICE_NAME,
    name="password.updated",
    stream_name=nats.stream,
)

UPDATE_ROLE_ROUTE = EventRoute(
    service=settings.SERVICE_NAME,
    name="update.role",
    stream_name=nats.stream,
)
