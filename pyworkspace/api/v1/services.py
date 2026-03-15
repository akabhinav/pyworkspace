"""Service catalog and workspace service endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from pyworkspace.auth.middleware import CurrentUser
from pyworkspace.db.repositories.service_repo import ServiceRepository
from pyworkspace.db.repositories.workspace_repo import WorkspaceRepository
from pyworkspace.db.session import get_db

router = APIRouter(tags=["services"])


# ── Catalog endpoints ────────────────────────────────────────────────


@router.get("/catalog", tags=["catalog"])
async def list_catalog() -> list[dict]:
    """List all available services in the catalog."""
    from pyworkspace.catalog import list_services

    return list_services()


@router.get("/catalog/{service_type}", tags=["catalog"])
async def get_catalog_service(service_type: str) -> dict:
    """Get service details, versions, and config options."""
    from pyworkspace.catalog import get_service_definition

    try:
        defn = get_service_definition(service_type)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Service '{service_type}' not found")

    return {
        "type": defn.service_type,
        "display_name": defn.display_name,
        "description": defn.description,
        "default_version": defn.default_version,
        "supported_versions": defn.supported_versions,
        "default_port": defn.default_port,
        "categories": defn.categories,
        "agent_tools": defn.get_agent_tools(),
        "default_resources": {
            "cpu": defn.default_resources.cpu,
            "memory": defn.default_resources.memory,
            "disk": defn.default_resources.disk,
        },
    }


@router.get("/catalog/{service_type}/schema", tags=["catalog"])
async def get_catalog_schema(service_type: str) -> dict:
    """JSON Schema for service config validation."""
    from pyworkspace.catalog import get_service_definition

    try:
        defn = get_service_definition(service_type)
    except Exception:
        raise HTTPException(status_code=404, detail=f"Service '{service_type}' not found")

    return {
        "type": defn.service_type,
        "config_schema": {
            "type": "object",
            "properties": {},
            "additionalProperties": True,
        },
    }


# ── Workspace service management ────────────────────────────────────


@router.get("/workspaces/{workspace_id}/services")
async def list_workspace_services(
    workspace_id: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all services in a workspace with health and connection info."""
    repo = WorkspaceRepository(db)
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    svc_repo = ServiceRepository(db)
    services = await svc_repo.list_by_workspace(workspace_id)
    if services:
        return [
            {
                "service_name": s.service_name,
                "service_type": s.service_type,
                "status": s.status,
                "internal_dns": s.internal_dns or s.service_name,
            }
            for s in services
        ]

    # Fallback: derive from spec
    spec = workspace.spec or {}
    result = []
    for svc in spec.get("services", []):
        if isinstance(svc, dict):
            name = svc.get("name", "")
            svc_type = svc.get("type", "")
        else:
            name = svc.name
            svc_type = svc.type
        dns_zone = workspace.dns_zone or ""
        result.append(
            {
                "service_name": name,
                "service_type": svc_type,
                "status": "healthy",
                "internal_dns": f"{name}.{dns_zone}" if dns_zone else name,
            }
        )
    return result


class AddServiceRequest(BaseModel):
    name: str
    type: str
    version: str = "latest"
    config: dict = {}
    expose_port: bool = False


@router.post("/workspaces/{workspace_id}/services", status_code=201)
async def add_service(
    workspace_id: str,
    req: AddServiceRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Add a service to a running workspace."""
    repo = WorkspaceRepository(db)
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    spec = workspace.spec or {}
    services = spec.get("services", [])
    new_svc = {
        "name": req.name,
        "type": req.type,
        "version": req.version,
        "config": req.config,
    }
    services.append(new_svc)
    spec["services"] = services
    await repo.update(workspace_id, spec=spec)

    return {"status": "provisioning", "service": req.name}


@router.delete("/workspaces/{workspace_id}/services/{service_name}")
async def remove_service(
    workspace_id: str,
    service_name: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Remove a service from a workspace."""
    repo = WorkspaceRepository(db)
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    spec = workspace.spec or {}
    services = spec.get("services", [])
    spec["services"] = [
        s
        for s in services
        if (s.get("name") if isinstance(s, dict) else s.name) != service_name
    ]
    await repo.update(workspace_id, spec=spec)

    return {"status": "removed", "service": service_name}
