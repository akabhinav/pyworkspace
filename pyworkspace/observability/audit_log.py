"""Audit logging for all workspace actions."""

from __future__ import annotations

import uuid
from datetime import datetime, timezone

import structlog

logger = structlog.get_logger()

# In-memory audit store; production uses DB
_audit_logs: list[dict] = []


async def log_action(
    workspace_id: str,
    actor_id: str,
    action: str,
    metadata: dict | None = None,
    ip_address: str | None = None,
) -> dict:
    """Record an auditable action."""
    entry = {
        "id": str(uuid.uuid4()),
        "workspace_id": workspace_id,
        "actor_id": actor_id,
        "action": action,
        "metadata": metadata or {},
        "ip_address": ip_address,
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }
    _audit_logs.append(entry)

    logger.info(
        "audit_log",
        workspace_id=workspace_id,
        actor_id=actor_id,
        action=action,
    )
    return entry


async def get_audit_logs(
    workspace_id: str | None = None,
    limit: int = 100,
) -> list[dict]:
    """Retrieve audit logs, optionally filtered by workspace."""
    logs = _audit_logs
    if workspace_id:
        logs = [l for l in logs if l["workspace_id"] == workspace_id]
    return logs[-limit:]
