from fastapi import APIRouter

from pysandbox.sandbox_manager import sandbox_manager

router = APIRouter()


@router.post("/webhooks/events")
async def handle_event(event: dict):
    event_type = event.get("event_type")

    if event_type == "workspace.created":
        workspace_id = event.get("workspace_id", "unknown")
        # Pre-warm a sandbox for the new workspace
        sandbox_manager.create_sandbox(
            language="python",
            timeout=300,
            memory=512,
            workspace_id=workspace_id,
        )
    elif event_type == "workspace.destroyed":
        workspace_id = event.get("workspace_id", "unknown")
        # Clean up sandboxes for the workspace
        sandbox_manager.destroy_sandboxes_for_workspace(workspace_id)

    return {"status": "received", "event_type": event_type}
