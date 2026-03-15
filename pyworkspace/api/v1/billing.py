"""Resource usage and billing endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException

from pyworkspace.auth.middleware import CurrentUser

router = APIRouter(tags=["billing"])


@router.get("/workspaces/{workspace_id}/usage")
async def get_workspace_usage(workspace_id: str, user: CurrentUser) -> dict:
    """Get CPU/memory/disk/network usage for a workspace."""
    return {
        "workspace_id": workspace_id,
        "cpu_core_hours": 0.0,
        "memory_gib_hours": 0.0,
        "disk_gib_hours": 0.0,
        "network_egress_gb": 0.0,
    }


@router.get("/orgs/{org_id}/usage")
async def get_org_usage(org_id: str, user: CurrentUser) -> dict:
    """Get aggregated usage for an organization."""
    if not user.can_access_org(org_id):
        raise HTTPException(status_code=403, detail="Access denied")
    return {
        "org_id": org_id,
        "total_cpu_core_hours": 0.0,
        "total_memory_gib_hours": 0.0,
        "total_disk_gib_hours": 0.0,
        "total_network_egress_gb": 0.0,
        "active_workspaces": 0,
    }


@router.get("/workspaces/{workspace_id}/cost")
async def get_workspace_cost(workspace_id: str, user: CurrentUser) -> dict:
    """Get cost estimate / actual for a workspace."""
    return {
        "workspace_id": workspace_id,
        "estimated_cost_usd": 0.0,
        "actual_cost_usd": 0.0,
        "period": "current_month",
    }
