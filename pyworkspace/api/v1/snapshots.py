"""Snapshot and restore endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from pyworkspace.auth.middleware import CurrentUser
from pyworkspace.core.lifecycle import LifecycleManager
from pyworkspace.db.models import Workspace, WorkspaceSnapshot
from pyworkspace.db.repositories.workspace_repo import WorkspaceRepository
from pyworkspace.db.session import get_db

router = APIRouter(prefix="/workspaces/{workspace_id}/snapshots", tags=["snapshots"])


class CreateSnapshotRequest(BaseModel):
    name: str = "manual"


def _snapshot_to_dict(snap: WorkspaceSnapshot) -> dict:
    return {
        "id": snap.id,
        "workspace_id": snap.workspace_id,
        "name": snap.name,
        "type": snap.type,
        "minio_path": snap.minio_path,
        "services_included": snap.services_included,
        "size_bytes": snap.size_bytes,
        "status": snap.status,
        "created_at": snap.created_at.isoformat() if snap.created_at else None,
    }


@router.get("")
async def list_snapshots(
    workspace_id: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> list[dict]:
    """List all snapshots for a workspace."""
    from sqlalchemy import select

    stmt = (
        select(WorkspaceSnapshot)
        .where(WorkspaceSnapshot.workspace_id == workspace_id)
        .order_by(WorkspaceSnapshot.created_at.desc())
    )
    result = await db.execute(stmt)
    snapshots = result.scalars().all()
    return [_snapshot_to_dict(s) for s in snapshots]


@router.post("", status_code=201)
async def create_snapshot(
    workspace_id: str,
    req: CreateSnapshotRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a named snapshot."""
    repo = WorkspaceRepository(db)
    workspace = await repo.get_by_id(workspace_id)
    if not workspace:
        raise HTTPException(status_code=404, detail="Workspace not found")

    lifecycle = LifecycleManager()
    from pyworkspace.api.v1.workspaces import _workspace_to_dict

    snapshot_data = await lifecycle.snapshot(_workspace_to_dict(workspace), req.name)

    snap = WorkspaceSnapshot(
        workspace_id=workspace_id,
        name=snapshot_data["name"],
        type=snapshot_data["type"],
        minio_path=snapshot_data["minio_path"],
        services_included=snapshot_data.get("services_included"),
        size_bytes=snapshot_data.get("size_bytes", 0),
    )
    snap.status = "ready"
    db.add(snap)
    await db.flush()

    return _snapshot_to_dict(snap)


@router.post("/{snapshot_id}/restore")
async def restore_snapshot(
    workspace_id: str,
    snapshot_id: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Restore a workspace from a snapshot."""
    snapshot = await db.get(WorkspaceSnapshot, snapshot_id)
    if not snapshot or snapshot.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return {
        "workspace_id": workspace_id,
        "snapshot_id": snapshot_id,
        "status": "restoring",
    }


@router.get("/{snapshot_id}/download")
async def download_snapshot(
    workspace_id: str,
    snapshot_id: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get download URL for a snapshot."""
    snapshot = await db.get(WorkspaceSnapshot, snapshot_id)
    if not snapshot or snapshot.workspace_id != workspace_id:
        raise HTTPException(status_code=404, detail="Snapshot not found")

    return {
        "workspace_id": workspace_id,
        "snapshot_id": snapshot_id,
        "download_url": f"/snapshots/{workspace_id}/{snapshot_id}/data",
        "size_bytes": snapshot.size_bytes,
    }
