"""Platform-wide constants. No env vars here — just fixed values."""

from __future__ import annotations

# Workspace status values
WORKSPACE_STATUS_PROVISIONING = "provisioning"
WORKSPACE_STATUS_RUNNING = "running"
WORKSPACE_STATUS_PAUSED = "paused"
WORKSPACE_STATUS_RESUMING = "resuming"
WORKSPACE_STATUS_DESTROYING = "destroying"
WORKSPACE_STATUS_ERROR = "error"
WORKSPACE_STATUS_DESTROYED = "destroyed"

WORKSPACE_STATUSES = {
    WORKSPACE_STATUS_PROVISIONING,
    WORKSPACE_STATUS_RUNNING,
    WORKSPACE_STATUS_PAUSED,
    WORKSPACE_STATUS_RESUMING,
    WORKSPACE_STATUS_DESTROYING,
    WORKSPACE_STATUS_ERROR,
    WORKSPACE_STATUS_DESTROYED,
}

# Service status values
SERVICE_STATUS_STARTING = "starting"
SERVICE_STATUS_HEALTHY = "healthy"
SERVICE_STATUS_UNHEALTHY = "unhealthy"
SERVICE_STATUS_STOPPED = "stopped"

# Provisioning states
PROVISION_STATE_REQUESTED = "requested"
PROVISION_STATE_CREATING_NAMESPACE = "creating_namespace"
PROVISION_STATE_GENERATING_SECRETS = "generating_secrets"
PROVISION_STATE_RESOLVING_SERVICES = "resolving_services"
PROVISION_STATE_PROVISIONING_SERVICES = "provisioning_services"
PROVISION_STATE_WAITING_HEALTHY = "waiting_healthy"
PROVISION_STATE_STARTING_AGENT = "starting_agent"
PROVISION_STATE_RUNNING = "running"
PROVISION_STATE_ERROR = "error"

# Tier resource limits
TIER_LIMITS: dict[str, dict[str, int | str]] = {
    "dev": {
        "cpu": 2,
        "memory_gi": 4,
        "disk_gi": 20,
        "max_services": 5,
        "max_workspaces": 2,
    },
    "standard": {
        "cpu": 8,
        "memory_gi": 16,
        "disk_gi": 100,
        "max_services": 15,
        "max_workspaces": 5,
    },
    "enterprise": {
        "cpu": 32,
        "memory_gi": 64,
        "disk_gi": 500,
        "max_services": 999,
        "max_workspaces": 999,
    },
}

# Health check defaults
HEALTH_CHECK_INTERVAL_SECONDS = 10
HEALTH_CHECK_TIMEOUT_SECONDS = 5
SERVICE_START_TIMEOUT_SECONDS = 300

# Rate limiting
RATE_LIMIT_WORKSPACE_OPS = 100  # per minute
RATE_LIMIT_PROVISIONING = 10  # per minute

# Audit log actions
AUDIT_ACTION_CREATED = "created"
AUDIT_ACTION_PAUSED = "paused"
AUDIT_ACTION_RESUMED = "resumed"
AUDIT_ACTION_DESTROYED = "destroyed"
AUDIT_ACTION_AGENT_EXECUTED = "agent_executed"
AUDIT_ACTION_SERVICE_ADDED = "service_added"
AUDIT_ACTION_SNAPSHOT_TAKEN = "snapshot_taken"

# Snapshot types
SNAPSHOT_TYPE_AUTO = "auto"
SNAPSHOT_TYPE_MANUAL = "manual"

# Agent blocked shell commands (security)
BLOCKED_SHELL_PATTERNS = [
    "rm -rf /",
    "chmod 777 /",
    "wget|curl.*|.*bash",
    ":(){ :|:& };:",  # fork bomb
    "mkfs",
    "dd if=",
    "mount",
    "insmod",
    "modprobe",
]
