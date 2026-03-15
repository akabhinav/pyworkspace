"""Repository for Workspace CRUD operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pyworkspace.db.models import Workspace


class WorkspaceRepository:
    """Async repository for workspaces."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, workspace: Workspace) -> Workspace:
        self._session.add(workspace)
        await self._session.flush()
        return workspace

    async def get_by_id(self, workspace_id: str) -> Optional[Workspace]:
        return await self._session.get(Workspace, workspace_id)

    async def get_by_name(self, name: str) -> Optional[Workspace]:
        stmt = select(Workspace).where(Workspace.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_by_org(
        self, org_id: str, *, offset: int = 0, limit: int = 50
    ) -> Sequence[Workspace]:
        stmt = (
            select(Workspace)
            .where(Workspace.org_id == org_id)
            .order_by(Workspace.created_at.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_by_status(self, status: str) -> Sequence[Workspace]:
        stmt = (
            select(Workspace)
            .where(Workspace.status == status)
            .order_by(Workspace.created_at.desc())
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update_status(
        self,
        workspace_id: str,
        status: str,
        *,
        error_message: Optional[str] = None,
    ) -> Optional[Workspace]:
        workspace = await self.get_by_id(workspace_id)
        if workspace is None:
            return None
        workspace.status = status
        workspace.error_message = error_message
        if status == "paused":
            workspace.paused_at = datetime.now(timezone.utc)
        elif status == "running":
            workspace.paused_at = None
            workspace.last_active_at = datetime.now(timezone.utc)
        await self._session.flush()
        return workspace

    async def update(
        self, workspace_id: str, **fields: object
    ) -> Optional[Workspace]:
        workspace = await self.get_by_id(workspace_id)
        if workspace is None:
            return None
        for key, value in fields.items():
            if hasattr(workspace, key):
                setattr(workspace, key, value)
        await self._session.flush()
        return workspace

    async def delete(self, workspace_id: str) -> bool:
        workspace = await self.get_by_id(workspace_id)
        if workspace is None:
            return False
        await self._session.delete(workspace)
        await self._session.flush()
        return True
