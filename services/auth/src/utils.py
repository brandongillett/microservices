from libs.auth_lib.api.events import CREATE_ROOT_USER_ROUTE
from libs.utils_lib.core.config import settings as utils_lib_settings
from libs.utils_lib.core.database import session_manager
from libs.utils_lib.core.faststream import nats
from src.crud import create_root_user


async def init_root_user() -> None:
    """
    Initialize the root user if the ROOT_USER_PASSWORD is set in the configuration.
    """
    if utils_lib_settings.ROOT_USER_PASSWORD:
        async with session_manager.get_session() as session:
            root_user = await create_root_user(
                session, utils_lib_settings.ROOT_USER_PASSWORD
            )
        await nats.broker.publish(
            root_user, subject=CREATE_ROOT_USER_ROUTE.subject_for("users")
        )
        await nats.broker.publish(
            root_user, subject=CREATE_ROOT_USER_ROUTE.subject_for("emails")
        )
