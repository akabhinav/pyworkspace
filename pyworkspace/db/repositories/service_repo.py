"""Repository for WorkspaceService CRUD operations."""

from __future__ import annotations

from datetime import datetime, timezone
from typing import Optional, Sequence

from sqlalchemy import delete as sa_delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from pyworkspace.db.models import WorkspaceService


class ServiceRepository:
    """Async repository for workspace services."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, service: WorkspaceService) -> WorkspaceService:
        self._session.add(service)
        await self._session.flush()
        return service

    async def get_by_id(self, service_id: str) -> Optional[WorkspaceService]:
        return await self._session.get(WorkspaceService, service_id)

    async def list_by_workspace(
        self, workspace_id: str
    ) -> Sequence[WorkspaceService]:
        stmt = (
            select(WorkspaceService)
            .where(WorkspaceService.workspace_id == workspace_id)
            .order_by(WorkspaceService.service_name)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def update_status(
        self, service_id: str, status: str
    ) -> Optional[WorkspaceService]:
        service = await self.get_by_id(service_id)
        if service is None:
            return None
        service.status = status
        if status == "running" and service.started_at is None:
            service.started_at = datetime.now(timezone.utc)
        await self._session.flush()
        return service

    async def update_health(self, service_id: str) -> Optional[WorkspaceService]:
        service = await self.get_by_id(service_id)
        if service is None:
            return None
        service.health_last_checked = datetime.now(timezone.utc)
        await self._session.flush()
        return service

    async def delete(self, service_id: str) -> bool:
        service = await self.get_by_id(service_id)
        if service is None:
            return False
        await self._session.delete(service)
        await self._session.flush()
        return True

    async def delete_by_workspace(self, workspace_id: str) -> int:
        stmt = sa_delete(WorkspaceService).where(
            WorkspaceService.workspace_id == workspace_id
        )
        result = await self._session.execute(stmt)
        return result.rowcount  # type: ignore[return-value]
