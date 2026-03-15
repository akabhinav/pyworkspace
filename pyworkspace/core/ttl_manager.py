"""Workspace TTL enforcement — pauses or destroys expired workspaces."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import structlog

logger = structlog.get_logger()


class TTLManager:
    """Checks workspace TTL and handles expired workspaces."""

    def __init__(self, grace_period_minutes: int = 30) -> None:
        self.grace_period = timedelta(minutes=grace_period_minutes)

    def is_expired(self, workspace: dict) -> bool:
        """Check if a workspace has exceeded its TTL."""
        ttl_hours = self._get_ttl(workspace)
        if ttl_hours is None:
            return False  # No TTL = never expires

        created_at = workspace.get("created_at")
        if created_at is None:
            return False

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        expiry = created_at + timedelta(hours=ttl_hours)
        return datetime.now(timezone.utc) > expiry

    def time_remaining(self, workspace: dict) -> timedelta | None:
        """Return time remaining before TTL expiry, or None if no TTL."""
        ttl_hours = self._get_ttl(workspace)
        if ttl_hours is None:
            return None

        created_at = workspace.get("created_at")
        if created_at is None:
            return None

        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        expiry = created_at + timedelta(hours=ttl_hours)
        remaining = expiry - datetime.now(timezone.utc)
        return max(remaining, timedelta(0))

    def is_in_grace_period(self, workspace: dict) -> bool:
        """Check if workspace is expired but still within grace period."""
        remaining = self.time_remaining(workspace)
        if remaining is None:
            return False
        return remaining == timedelta(0) and self._within_grace(workspace)

    def _within_grace(self, workspace: dict) -> bool:
        ttl_hours = self._get_ttl(workspace)
        if ttl_hours is None:
            return False

        created_at = workspace.get("created_at")
        if isinstance(created_at, str):
            created_at = datetime.fromisoformat(created_at)
        if created_at and created_at.tzinfo is None:
            created_at = created_at.replace(tzinfo=timezone.utc)

        expiry = created_at + timedelta(hours=ttl_hours)
        grace_end = expiry + self.grace_period
        return datetime.now(timezone.utc) <= grace_end

    @staticmethod
    def _get_ttl(workspace: dict) -> int | None:
        spec = workspace.get("spec", {})
        if isinstance(spec, dict):
            return spec.get("ttl_hours")
        return getattr(spec, "ttl_hours", None)


async def cleanup_expired_workspaces(
    workspaces: list[dict],
    lifecycle_manager=None,
    destroyer=None,
) -> dict:
    """
    Process expired workspaces:
    - In grace period → pause
    - Past grace period → destroy

    Returns summary of actions taken.
    """
    ttl = TTLManager()
    paused = []
    destroyed = []

    for ws in workspaces:
        if ws.get("status") not in ("running", "paused"):
            continue

        if not ttl.is_expired(ws):
            continue

        ws_id = ws.get("id", "unknown")

        if ttl.is_in_grace_period(ws) and ws.get("status") == "running":
            # Grace period: pause the workspace
            if lifecycle_manager:
                await lifecycle_manager.pause(ws)
            paused.append(ws_id)
            logger.info("ttl_workspace_paused", workspace_id=ws_id)

        elif not ttl.is_in_grace_period(ws):
            # Past grace: destroy
            if destroyer:
                await destroyer.destroy(ws)
            destroyed.append(ws_id)
            logger.info("ttl_workspace_destroyed", workspace_id=ws_id)

    return {"paused": paused, "destroyed": destroyed}
