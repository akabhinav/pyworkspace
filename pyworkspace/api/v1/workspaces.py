"""Workspace CRUD and lifecycle endpoints."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Literal

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel, Field
from sqlalchemy.ext.asyncio import AsyncSession

from pyworkspace.auth.middleware import CurrentUser
from pyworkspace.core.destroyer import WorkspaceDestroyer
from pyworkspace.core.lifecycle import LifecycleManager
from pyworkspace.core.provisioner import WorkspaceProvisioner
from pyworkspace.core.specs import AgentSpec, ResourceSpec, ServiceSpec, WorkspaceSpec
from pyworkspace.db.models import Workspace
from pyworkspace.db.repositories.workspace_repo import WorkspaceRepository
from pyworkspace.db.session import get_db

router = APIRouter(prefix="/workspaces", tags=["workspaces"])


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


# ── Helpers ─────────────────────────────────────────────────────────


def _workspace_to_dict(ws: Workspace) -> dict:
    """Convert a Workspace ORM object to a dict for provisioner compat."""
    return {
        "id": ws.id,
        "name": ws.name,
        "owner_id": ws.owner_id,
        "org_id": ws.org_id,
        "tier": ws.tier,
        "status": ws.status,
        "spec": ws.spec or {},
        "k8s_namespace": ws.k8s_namespace,
        "dns_zone": ws.dns_zone,
        "created_at": ws.created_at,
        "updated_at": ws.updated_at,
        "tags": ws.tags or {},
        "error_message": ws.error_message,
    }


# ── Endpoints ────────────────────────────────────────────────────────


@router.post("", response_model=WorkspaceResponse, status_code=201)
async def create_workspace(
    req: CreateWorkspaceRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a workspace from spec or template."""
    if not user.can_access_org(req.org_id):
        raise HTTPException(status_code=403, detail="Cannot create workspace in this org")

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
    workspace_dict = await provisioner.provision(spec)

    # Persist to DB
    repo = WorkspaceRepository(db)
    ws = Workspace(
        name=workspace_dict["name"],
        owner_id=workspace_dict["owner_id"],
        org_id=workspace_dict["org_id"],
        tier=workspace_dict["tier"],
        spec=workspace_dict.get("spec"),
        k8s_namespace=workspace_dict.get("k8s_namespace"),
        dns_zone=workspace_dict.get("dns_zone"),
        tags=workspace_dict.get("tags"),
    )
    ws.status = workspace_dict["status"]
    created = await repo.create(ws)

    result = _workspace_to_dict(created)
    result["id"] = created.id
    return result


@router.get("", response_model=list[WorkspaceResponse])
async def list_workspaces(
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    org_id: str | None = Query(None),
    status: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list:
    """List workspaces with optional filters."""
    repo = WorkspaceRepository(db)
    target_org = org_id or user.org_id

    if not user.can_access_org(target_org):
        raise HTTPException(status_code=403, detail="Cannot access this org's workspaces")

    if status:
        workspaces = await repo.list_by_status(status)
        # Filter by org
        workspaces = [w for w in workspaces if w.org_id == target_org]
    else:
        workspaces = await repo.list_by_org(target_org, offset=offset, limit=limit)

    return list(workspaces)


@router.get("/{workspace_id}", response_model=WorkspaceResponse)
async def get_workspace(
    workspace_id: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """Get workspace details."""
    repo = WorkspaceRepository(db)
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not user.can_access_org(workspace.org_id):
        raise HTTPException(status_code=403, detail="Access denied")
    return workspace


@router.patch("/{workspace_id}", response_model=WorkspaceResponse)
async def update_workspace(
    workspace_id: str,
    req: UpdateWorkspaceRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> Workspace:
    """Update workspace metadata."""
    repo = WorkspaceRepository(db)
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not user.can_access_org(workspace.org_id):
        raise HTTPException(status_code=403, detail="Access denied")

    updates = {}
    if req.tags is not None:
        updates["tags"] = req.tags
    if req.description is not None:
        spec = workspace.spec or {}
        spec["description"] = req.description
        updates["spec"] = spec
    if req.ttl_hours is not None:
        spec = workspace.spec or {}
        spec["ttl_hours"] = req.ttl_hours
        updates["spec"] = spec

    if updates:
        workspace = await repo.update(workspace_id, **updates)

    return workspace


@router.delete("/{workspace_id}", status_code=202)
async def delete_workspace(
    workspace_id: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Destroy a workspace (async)."""
    repo = WorkspaceRepository(db)
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not user.can_access_org(workspace.org_id):
        raise HTTPException(status_code=403, detail="Access denied")

    destroyer = WorkspaceDestroyer()
    await destroyer.destroy(_workspace_to_dict(workspace))

    await repo.update_status(workspace_id, "destroyed")
    return {"status": "destroying", "workspace_id": workspace_id}


@router.get("/{workspace_id}/status")
async def get_workspace_status(
    workspace_id: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get real-time provisioning status."""
    repo = WorkspaceRepository(db)
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {
        "workspace_id": workspace_id,
        "status": workspace.status,
        "error_message": workspace.error_message,
    }


# ── Lifecycle endpoints ──────────────────────────────────────────────


@router.post("/{workspace_id}/pause", status_code=202)
async def pause_workspace(
    workspace_id: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Pause a running workspace."""
    repo = WorkspaceRepository(db)
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not user.can_access_org(workspace.org_id):
        raise HTTPException(status_code=403, detail="Access denied")

    lifecycle = LifecycleManager()
    await lifecycle.pause(_workspace_to_dict(workspace))

    await repo.update_status(workspace_id, "paused")
    return {"status": "paused", "workspace_id": workspace_id}


@router.post("/{workspace_id}/resume", status_code=202)
async def resume_workspace(
    workspace_id: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Resume a paused workspace."""
    repo = WorkspaceRepository(db)
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not user.can_access_org(workspace.org_id):
        raise HTTPException(status_code=403, detail="Access denied")

    lifecycle = LifecycleManager()
    await lifecycle.resume(_workspace_to_dict(workspace))

    await repo.update_status(workspace_id, "running")
    return {"status": "running", "workspace_id": workspace_id}


@router.post("/{workspace_id}/restart", status_code=202)
async def restart_workspace(
    workspace_id: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Restart all services in a workspace."""
    repo = WorkspaceRepository(db)
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    return {"status": "restarting", "workspace_id": workspace_id}


@router.post("/{workspace_id}/clone", status_code=201)
async def clone_workspace(
    workspace_id: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    new_name: str = Query(...),
) -> dict:
    """Clone a workspace."""
    repo = WorkspaceRepository(db)
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")
    if not user.can_access_org(workspace.org_id):
        raise HTTPException(status_code=403, detail="Access denied")

    lifecycle = LifecycleManager()
    new_spec = await lifecycle.clone(
        _workspace_to_dict(workspace), new_name, workspace.owner_id
    )
    return {"status": "cloning", "source_id": workspace_id, "new_spec": new_spec}
