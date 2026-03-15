"""JWT authentication middleware and RBAC dependencies for FastAPI."""

from __future__ import annotations

from typing import Annotated

import structlog
from fastapi import Depends, HTTPException, Request, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pyworkspace.auth.jwt_handler import verify_token
from pyworkspace.config.settings import get_settings

logger = structlog.get_logger()

_bearer_scheme = HTTPBearer(auto_error=False)

# Role hierarchy: admin > org_admin > member > viewer
ROLE_HIERARCHY: dict[str, int] = {
    "viewer": 0,
    "member": 1,
    "org_admin": 2,
    "admin": 3,
}


class AuthUser:
    """Authenticated user extracted from JWT claims."""

    __slots__ = ("user_id", "org_id", "role", "email")

    def __init__(self, user_id: str, org_id: str, role: str, email: str = "") -> None:
        self.user_id = user_id
        self.org_id = org_id
        self.role = role
        self.email = email

    def has_role(self, minimum_role: str) -> bool:
        return ROLE_HIERARCHY.get(self.role, 0) >= ROLE_HIERARCHY.get(minimum_role, 0)

    def can_access_org(self, org_id: str) -> bool:
        return self.role == "admin" or self.org_id == org_id


async def get_current_user(
    request: Request,
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer_scheme),
) -> AuthUser:
    """Extract and validate the current user from the Authorization header.

    In dev mode, if no token is provided, returns a default dev user.
    """
    settings = get_settings()

    # Dev mode: allow unauthenticated access with a default user
    if settings.PYWORKSPACE_ENV == "dev" and credentials is None:
        return AuthUser(
            user_id="dev-user",
            org_id="dev-org",
            role="admin",
            email="dev@pyworkspace.local",
        )

    if credentials is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        payload = verify_token(
            credentials.credentials,
            settings.PYWORKSPACE_MASTER_KEY.get_secret_value(),
        )
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"},
        )

    return AuthUser(
        user_id=payload.get("sub", ""),
        org_id=payload.get("org_id", ""),
        role=payload.get("role", "member"),
        email=payload.get("email", ""),
    )


# Convenient type alias for dependency injection
CurrentUser = Annotated[AuthUser, Depends(get_current_user)]


def require_role(minimum_role: str):
    """Dependency factory that enforces a minimum role."""

    async def _check(user: CurrentUser) -> AuthUser:
        if not user.has_role(minimum_role):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Requires role '{minimum_role}' or higher",
            )
        return user

    return _check
