from fastapi import APIRouter

from pysandbox.config import settings

router = APIRouter()


@router.get("/plugin/manifest")
async def get_manifest():
    return {
        "kind": "PyWorkspacePlugin",
        "name": "pysandbox",
        "version": "1.0.0",
        "display_name": "PySandbox",
        "description": "Isolated code execution with gVisor/Firecracker",
        "team": "sandbox-team",
        "categories": ["runtime", "security"],
        "base_url": f"http://localhost:{settings.port}",
        "api_version": "v1",
        "auth_type": "api_key",
        "service": {
            "image": "yourorg/pysandbox:1.0.0",
            "port": settings.port,
            "health_check": {
                "endpoint": "/healthz",
                "interval_seconds": 15,
                "timeout_seconds": 5,
            },
            "resources": {"cpu": "1.0", "memory": "2Gi", "disk": "10Gi"},
            "env": {
                "SANDBOX_RUNTIME": "gvisor",
                "SANDBOX_MAX_EXECUTION_TIME": "300",
            },
        },
        "tools": [
            {
                "name": "sandbox_create",
                "description": "Create a new isolated sandbox environment",
                "endpoint": "/v1/sandbox/create",
                "method": "POST",
                "timeout_seconds": 30,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "language": {"type": "string"},
                        "timeout_seconds": {"type": "integer"},
                        "memory_mb": {"type": "integer"},
                    },
                },
            },
            {
                "name": "sandbox_execute",
                "description": "Execute code in an existing sandbox",
                "endpoint": "/v1/sandbox/execute",
                "method": "POST",
                "timeout_seconds": 120,
                "input_schema": {
                    "type": "object",
                    "properties": {
                        "sandbox_id": {"type": "string"},
                        "code": {"type": "string"},
                        "stdin": {"type": "string"},
                    },
                    "required": ["sandbox_id", "code"],
                },
            },
            {
                "name": "sandbox_destroy",
                "description": "Destroy a sandbox and cleanup resources",
                "endpoint": "/v1/sandbox/destroy",
                "method": "POST",
                "timeout_seconds": 10,
                "input_schema": {
                    "type": "object",
                    "properties": {"sandbox_id": {"type": "string"}},
                    "required": ["sandbox_id"],
                },
            },
        ],
        "events": {
            "publishes": [
                "sandbox.created",
                "sandbox.completed",
                "sandbox.failed",
                "sandbox.timeout",
            ],
            "subscribes": ["workspace.created", "workspace.destroyed"],
            "callback_url": f"http://localhost:{settings.port}/webhooks/events",
        },
        "depends_on": [],
        "config": {},
    }
