"""Agent session and command execution endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

router = APIRouter(prefix="/workspaces/{workspace_id}/agent", tags=["agent"])


class AgentExecuteRequest(BaseModel):
    prompt: str
    stream: bool = True


@router.post("/execute")
async def execute_agent_prompt(workspace_id: str, req: AgentExecuteRequest) -> dict:
    """Send a prompt to the PyOz agent. Returns execution result."""
    from pyworkspace.api.v1.workspaces import _workspaces

    workspace = _workspaces.get(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if workspace.get("status") != "running" and workspace.get("status") != "provisioning":
        raise HTTPException(status_code=409, detail="Workspace not running")

    return {
        "workspace_id": workspace_id,
        "prompt": req.prompt,
        "status": "executing",
        "message": "Agent task submitted",
    }


@router.get("/status")
async def get_agent_status(workspace_id: str) -> dict:
    """Get agent health and current task."""
    from pyworkspace.api.v1.workspaces import _workspaces

    workspace = _workspaces.get(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    return {
        "workspace_id": workspace_id,
        "agent_status": "idle",
        "current_task": None,
    }


@router.get("/history")
async def get_agent_history(workspace_id: str) -> list[dict]:
    """Get agent execution history."""
    return []


@router.post("/stop")
async def stop_agent(workspace_id: str) -> dict:
    """Stop current agent task."""
    return {"workspace_id": workspace_id, "status": "stopped"}


@router.post("/restart")
async def restart_agent(workspace_id: str) -> dict:
    """Restart agent pod."""
    return {"workspace_id": workspace_id, "status": "restarting"}
