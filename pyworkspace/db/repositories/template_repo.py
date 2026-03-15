"""Repository for WorkspaceTemplate CRUD operations."""

from __future__ import annotations

from typing import Optional, Sequence

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from pyworkspace.db.models import WorkspaceTemplate


class TemplateRepository:
    """Async repository for workspace templates."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    async def create(self, template: WorkspaceTemplate) -> WorkspaceTemplate:
        self._session.add(template)
        await self._session.flush()
        return template

    async def get_by_id(self, template_id: str) -> Optional[WorkspaceTemplate]:
        return await self._session.get(WorkspaceTemplate, template_id)

    async def get_by_name(self, name: str) -> Optional[WorkspaceTemplate]:
        stmt = select(WorkspaceTemplate).where(WorkspaceTemplate.name == name)
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none()

    async def list_all(
        self, *, offset: int = 0, limit: int = 100
    ) -> Sequence[WorkspaceTemplate]:
        stmt = (
            select(WorkspaceTemplate)
            .order_by(WorkspaceTemplate.usage_count.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def list_by_category(
        self, category: str, *, offset: int = 0, limit: int = 100
    ) -> Sequence[WorkspaceTemplate]:
        stmt = (
            select(WorkspaceTemplate)
            .where(WorkspaceTemplate.category == category)
            .order_by(WorkspaceTemplate.usage_count.desc())
            .offset(offset)
            .limit(limit)
        )
        result = await self._session.execute(stmt)
        return result.scalars().all()

    async def increment_usage(self, template_id: str) -> Optional[WorkspaceTemplate]:
        template = await self.get_by_id(template_id)
        if template is None:
            return None
        template.usage_count += 1
        await self._session.flush()
        return template

    async def delete(self, template_id: str) -> bool:
        template = await self.get_by_id(template_id)
        if template is None:
            return False
        await self._session.delete(template)
        await self._session.flush()
        return True
