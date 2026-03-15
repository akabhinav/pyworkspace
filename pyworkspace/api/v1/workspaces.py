"""Workspace CRUD and lifecycle endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from pyworkspace.core.provisioner import WorkspaceProvisioner
from pyworkspace.core.lifecycle import LifecycleManager
from pyworkspace.core.destroyer import WorkspaceDestroyer
from pyworkspace.core.specs import AgentSpec, ResourceSpec, ServiceSpec, WorkspaceSpec

router = APIRouter(prefix="/workspaces", tags=["workspaces"])

# In-memory store for demo; production uses DB repos
_workspaces: dict[str, dict] = {}


# ── Request/Response models ──────────────────────────────────────────


class CreateWorkspaceRequest(BaseModel):
    name: str
    template: str | None = None
    description: str = ""
    owner_id: str
    org_id: str
    tier: Literal["dev", "standard", "enterprise"] = "standard"
    services: list[ServiceSpec] = Field(default_factory=list)
    agent: AgentSpec = Field(default_factory=AgentSpec)
    resources: ResourceSpec = Field(
        default_factory=lambda: ResourceSpec(cpu="4", memory="8Gi", disk="50Gi")
    )
    egress_allowed: bool = True
    expose_services: list[str] = Field(default_factory=list)
    ttl_hours: int | None = 24
    auto_snapshot: bool = True
    tags: dict[str, str] = Field(default_factory=dict)


class WorkspaceResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: str
    name: str
    owner_id: str = ""
    org_id: str = ""
    tier: str = "standard"
    status: str = "provisioning"
    k8s_namespace: str | None = None
    dns_zone: str | None = None
    created_at: datetime | str | None = None
    error_message: str | None = None


class UpdateWorkspaceRequest(BaseModel):
    description: str | None = None
    tags: dict[str, str] | None = None
    ttl_hours: int | None = None


# ── Endpoints ────────────────────────────────────────────────────────


@router.post("", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(req: CreateWorkspaceRequest) -> dict:
    """Create a workspace from spec or template."""
    spec = WorkspaceSpec(
        name=req.name,
        template=req.template,
        description=req.description,
        owner_id=req.owner_id,
        org_id=req.org_id,
        tier=req.tier,
        services=req.services,
        agent=req.agent,
        resources=req.resources,
        egress_allowed=req.egress_allowed,
        expose_services=req.expose_services,
        ttl_hours=req.ttl_hours,
        auto_snapshot=req.auto_snapshot,
        tags=req.tags,
    )

    provisioner = WorkspaceProvisioner()
    workspace = await provisioner.provision(spec)
    _workspaces[workspace["id"]] = workspace
    return workspace


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    org_id: str | None = Query(None),
    status: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[dict]:
    """List workspaces with optional filters."""
    results = list(_workspaces.values())
    if org_id:
        results = [w for w in results if w.get("org_id") == org_id]
    if status:
        results = [w for w in results if w.get("status") == status]
    return results[offset : offset + limit]


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(workspace_id: str) -> dict:
    """Get workspace details."""
    workspace = _workspaces.get(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(workspace_id: str, req: UpdateWorkspaceRequest) -> dict:
    """Update workspace metadata."""
    workspace = _workspaces.get(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    if req.description is not None:
        workspace.setdefault("spec", {})["description"] = req.description
    if req.tags is not None:
        workspace["tags"] = req.tags
    if req.ttl_hours is not None:
        workspace.setdefault("spec", {})["ttl_hours"] = req.ttl_hours
    workspace["updated_at"] = datetime.now(timezone.utc).isoformat()
    return workspace


@router.delete("/{workspace_id}", status_code=202)
async def delete_workspace(workspace_id: str) -> dict:
    """Destroy a workspace (async)."""
    workspace = _workspaces.get(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    destroyer = WorkspaceDestroyer()
    await destroyer.destroy(workspace)
    _workspaces.pop(workspace_id, None)
    return {"status": "destroying", "workspace_id": workspace_id}


@router.get("/{workspace_id}/status")
async def get_workspace_status(workspace_id: str) -> dict:
    """Get real-time provisioning status."""
    workspace = _workspaces.get(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {
        "workspace_id": workspace_id,
        "status": workspace.get("status"),
        "error_message": workspace.get("error_message"),
    }


# ── Lifecycle endpoints ──────────────────────────────────────────────


@router.post("/{workspace_id}/pause", status_code=202)
async def pause_workspace(workspace_id: str) -> dict:
    """Pause a running workspace."""
    workspace = _workspaces.get(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    lifecycle = LifecycleManager()
    updated = await lifecycle.pause(workspace)
    _workspaces[workspace_id] = updated
    return {"status": "paused", "workspace_id": workspace_id}


@router.post("/{workspace_id}/resume", status_code=202)
async def resume_workspace(workspace_id: str) -> dict:
    """Resume a paused workspace."""
    workspace = _workspaces.get(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    lifecycle = LifecycleManager()
    updated = await lifecycle.resume(workspace)
    _workspaces[workspace_id] = updated
    return {"status": "running", "workspace_id": workspace_id}


@router.post("/{workspace_id}/restart", status_code=202)
async def restart_workspace(workspace_id: str) -> dict:
    """Restart all services in a workspace."""
    workspace = _workspaces.get(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"status": "restarting", "workspace_id": workspace_id}


@router.post("/{workspace_id}/clone", status_code=201)
async def clone_workspace(workspace_id: str, new_name: str = Query(...)) -> dict:
    """Clone a workspace."""
    workspace = _workspaces.get(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    lifecycle = LifecycleManager()
    new_spec = await lifecycle.clone(workspace, new_name, workspace.get("owner_id", ""))
    return {"status": "cloning", "source_id": workspace_id, "new_spec": new_spec}
