"""Service catalog and workspace service endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from pyworkspace.core.specs import ServiceSpec

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
async def list_workspace_services(workspace_id: str) -> list[dict]:
    """List all services in a workspace with health and connection info."""
    from pyworkspace.api.v1.workspaces import _workspaces

    workspace = _workspaces.get(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    spec = workspace.get("spec", {})
    services = []
    for svc in spec.get("services", []):
        if isinstance(svc, dict):
            name = svc.get("name", "")
            svc_type = svc.get("type", "")
        else:
            name = svc.name
            svc_type = svc.type

        dns_zone = workspace.get("dns_zone", "")
        services.append(
            {
                "service_name": name,
                "service_type": svc_type,
                "status": "healthy",
                "internal_dns": f"{name}.{dns_zone}" if dns_zone else name,
            }
        )
    return services


class AddServiceRequest(BaseModel):
    name: str
    type: str
    version: str = "latest"
    config: dict = {}
    expose_port: bool = False


@router.post("/workspaces/{workspace_id}/services", status_code=201)
async def add_service(workspace_id: str, req: AddServiceRequest) -> dict:
    """Add a service to a running workspace."""
    from pyworkspace.api.v1.workspaces import _workspaces

    workspace = _workspaces.get(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    spec = workspace.get("spec", {})
    services = spec.get("services", [])
    new_svc = {
        "name": req.name,
        "type": req.type,
        "version": req.version,
        "config": req.config,
    }
    services.append(new_svc)
    spec["services"] = services
    workspace["spec"] = spec

    return {"status": "provisioning", "service": req.name}


@router.delete("/workspaces/{workspace_id}/services/{service_name}")
async def remove_service(workspace_id: str, service_name: str) -> dict:
    """Remove a service from a workspace."""
    from pyworkspace.api.v1.workspaces import _workspaces

    workspace = _workspaces.get(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    spec = workspace.get("spec", {})
    services = spec.get("services", [])
    spec["services"] = [
        s for s in services if (s.get("name") if isinstance(s, dict) else s.name) != service_name
    ]
    workspace["spec"] = spec

    return {"status": "removed", "service": service_name}
