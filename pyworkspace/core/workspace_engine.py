"""Central workspace state machine — governs all status transitions."""

from __future__ import annotations

import structlog

from pyworkspace.config.constants import (
    WORKSPACE_STATUS_DESTROYING,
    WORKSPACE_STATUS_ERROR,
    WORKSPACE_STATUS_PAUSED,
    WORKSPACE_STATUS_PROVISIONING,
    WORKSPACE_STATUS_RESUMING,
    WORKSPACE_STATUS_RUNNING,
)

logger = structlog.get_logger()

# Valid state transitions
_TRANSITIONS: dict[str, set[str]] = {
    WORKSPACE_STATUS_PROVISIONING: {WORKSPACE_STATUS_RUNNING, WORKSPACE_STATUS_ERROR},
    WORKSPACE_STATUS_RUNNING: {
        WORKSPACE_STATUS_PAUSED,
        WORKSPACE_STATUS_DESTROYING,
        WORKSPACE_STATUS_ERROR,
    },
    WORKSPACE_STATUS_PAUSED: {
        WORKSPACE_STATUS_RESUMING,
        WORKSPACE_STATUS_DESTROYING,
        WORKSPACE_STATUS_ERROR,
    },
    WORKSPACE_STATUS_RESUMING: {WORKSPACE_STATUS_RUNNING, WORKSPACE_STATUS_ERROR},
    WORKSPACE_STATUS_DESTROYING: {WORKSPACE_STATUS_ERROR},
    WORKSPACE_STATUS_ERROR: {
        WORKSPACE_STATUS_PROVISIONING,
        WORKSPACE_STATUS_DESTROYING,
    },
}


class InvalidTransitionError(Exception):
    """Raised when a workspace status transition is not allowed."""


def validate_transition(current: str, target: str) -> None:
    """Raise if the transition is not allowed."""
    allowed = _TRANSITIONS.get(current, set())
    if target not in allowed:
        raise InvalidTransitionError(
            f"Cannot transition from '{current}' to '{target}'. "
            f"Allowed: {allowed}"
        )


class WorkspaceStateMachine:
    """Tracks workspace status and enforces valid transitions."""

    def __init__(self, workspace_id: str, current_status: str) -> None:
        self.workspace_id = workspace_id
        self.status = current_status

    def transition(self, target: str) -> str:
        validate_transition(self.status, target)
        previous = self.status
        self.status = target
        logger.info(
            "workspace_state_transition",
            workspace_id=self.workspace_id,
            from_status=previous,
            to_status=target,
        )
        return self.status

    def can_transition(self, target: str) -> bool:
        return target in _TRANSITIONS.get(self.status, set())
