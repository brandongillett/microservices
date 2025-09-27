from libs.utils_lib.core.faststream import nats
from libs.utils_lib.schemas import EventRoute
from src.core.config import settings

VERIFY_USER_ROUTE = EventRoute(
    service=settings.SERVICE_NAME,
    name="verify.user",
    stream_name=nats.stream,
)

VERIFICATION_SEND_ROUTE = EventRoute(
    service=settings.SERVICE_NAME,
    name="verification.send",
    stream_name=nats.stream,
)

CREATE_USER_ROUTE = EventRoute(
    service=settings.SERVICE_NAME,
    name="create.user",
    stream_name=nats.stream,
)

CREATE_ROOT_USER_ROUTE = EventRoute(
    service=settings.SERVICE_NAME,
    name="create.root_user",
    stream_name=nats.stream,
)

FORGOT_PASSWORD_SEND_ROUTE = EventRoute(
    service=settings.SERVICE_NAME,
    name="password.forgot.send",
    stream_name=nats.stream,
)
