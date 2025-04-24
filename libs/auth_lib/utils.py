from uuid import UUID

from fastapi import HTTPException, status

from libs.auth_lib.api.deps import RoleChecker
from libs.auth_lib.core.security import security_settings as auth_lib_security_settings
from libs.users_lib.models import UserRole
from libs.utils_lib.core.security import gen_url_token, verify_url_token

# Roles/Permissions
ROLES = {role.value for role in UserRole}

GEN_ACCESS: list[UserRole] = [UserRole.user, UserRole.admin, UserRole.root]
MGMT_ACCESS: list[UserRole] = [UserRole.admin, UserRole.root]
ROOT_ACCESS: list[UserRole] = [UserRole.root]

GEN_ROLE_CHECKER = RoleChecker(allowed_roles={role.value for role in GEN_ACCESS})
MGMT_ROLE_CHECKER = RoleChecker(allowed_roles={role.value for role in MGMT_ACCESS})
ROOT_ROLE_CHECKER = RoleChecker(allowed_roles={role.value for role in ROOT_ACCESS})


## Token generation and verification functions
def gen_email_verification_token(user_id: UUID) -> str:
    """
    Generate an email verification token with the provided data.

    Args:
        user_id (UUID): The user ID to encode in the token.

    Returns:
        str: The email verification token.
    """
    data = {"user_id": str(user_id)}
    return gen_url_token(data, "email_verification")


def verify_email_verification_token(token: str) -> UUID:
    """
    Verify an email verification token and extract the data.

    Args:
        token (str): The token to verify

    Returns:
        user_id (UUID): The user ID extracted from the token.
    """
    token_data = verify_url_token(
        token=token,
        salt="email_verification",
        expiration=auth_lib_security_settings.EMAIL_VERIFICATION_EXPIRES_MINUTES,
    )

    user_id = UUID(token_data.get("user_id"))

    if not user_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid token"
        )

    return user_id
