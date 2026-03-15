"""Snapshot and restore endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

from pyworkspace.core.lifecycle import LifecycleManager

router = APIRouter(prefix="/workspaces/{workspace_id}/snapshots", tags=["snapshots"])

_snapshots: dict[str, list[dict]] = {}


class CreateSnapshotRequest(BaseModel):
    name: str = "manual"


@router.get("")
async def list_snapshots(workspace_id: str) -> list[dict]:
    """List all snapshots for a workspace."""
    return _snapshots.get(workspace_id, [])


@router.post("", status_code=201)
async def create_snapshot(workspace_id: str, req: CreateSnapshotRequest) -> dict:
    """Create a named snapshot."""
    from pyworkspace.api.v1.workspaces import _workspaces

    workspace = _workspaces.get(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    lifecycle = LifecycleManager()
    snapshot = await lifecycle.snapshot(workspace, req.name)

    _snapshots.setdefault(workspace_id, []).append(snapshot)
    return snapshot


@router.post("/{snapshot_id}/restore")
async def restore_snapshot(workspace_id: str, snapshot_id: str) -> dict:
    """Restore a workspace from a snapshot."""
    snapshots = _snapshots.get(workspace_id, [])
    snapshot = next((s for s in snapshots if s.get("id") == snapshot_id), None)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return {
        "workspace_id": workspace_id,
        "snapshot_id": snapshot_id,
        "status": "restoring",
    }


@router.get("/{snapshot_id}/download")
async def download_snapshot(workspace_id: str, snapshot_id: str) -> dict:
    """Get download URL for a snapshot."""
    snapshots = _snapshots.get(workspace_id, [])
    snapshot = next((s for s in snapshots if s.get("id") == snapshot_id), None)
    if not snapshot:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return {
        "workspace_id": workspace_id,
        "snapshot_id": snapshot_id,
        "download_url": f"/snapshots/{workspace_id}/{snapshot_id}/data",
        "size_bytes": snapshot.get("size_bytes", 0),
    }
