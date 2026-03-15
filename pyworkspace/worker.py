"""Celery worker for long-running provisioning tasks."""

from __future__ import annotations

import asyncio

from celery import Celery

from pyworkspace.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "pyworkspace",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
    beat_schedule={
        "record-resource-usage": {
            "task": "pyworkspace.worker.record_all_usage",
            "schedule": 60.0,  # Every 60 seconds
        },
        "cleanup-expired-workspaces": {
            "task": "pyworkspace.worker.cleanup_expired_workspaces_task",
            "schedule": 300.0,  # Every 5 minutes
        },
    },
)


def _run_async(coro):
    """Run async function in sync Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@celery_app.task(bind=True, max_retries=3)
def provision_workspace_task(self, workspace_id: str, spec_dict: dict):
    """Celery task: provision a workspace asynchronously."""
    from pyworkspace.core.provisioner import WorkspaceProvisioner
    from pyworkspace.core.specs import WorkspaceSpec

    async def _provision():
        spec = WorkspaceSpec(**spec_dict)
        provisioner = WorkspaceProvisioner()
        workspace = await provisioner.provision(spec)
        return await provisioner.execute_provisioning(workspace, spec)

    try:
        return _run_async(_provision())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@celery_app.task(bind=True, max_retries=2)
def destroy_workspace_task(self, workspace_id: str, workspace_dict: dict):
    """Celery task: destroy a workspace asynchronously."""
    from pyworkspace.core.destroyer import WorkspaceDestroyer

    async def _destroy():
        destroyer = WorkspaceDestroyer()
        return await destroyer.destroy(workspace_dict)

    try:
        return _run_async(_destroy())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@celery_app.task
def record_all_usage():
    """Celery beat task: record resource usage for all running workspaces."""
    from pyworkspace.billing.metering import ResourceMeter

    async def _record():
        meter = ResourceMeter()
        # In production: query DB for all running workspaces
        # For now, this is a no-op placeholder
        pass

    _run_async(_record())


@celery_app.task
def cleanup_expired_workspaces_task():
    """Celery beat task: pause/destroy workspaces that have exceeded their TTL."""
    from pyworkspace.core.ttl_manager import cleanup_expired_workspaces
    from pyworkspace.core.lifecycle import LifecycleManager
    from pyworkspace.core.destroyer import WorkspaceDestroyer

    async def _cleanup():
        from pyworkspace.db.session import get_db_session

        async with get_db_session() as session:
            from sqlalchemy import select
            from pyworkspace.db.models import Workspace

            stmt = select(Workspace).where(
                Workspace.status.in_(["running", "paused"])
            )
            result = await session.execute(stmt)
            workspaces = result.scalars().all()

            ws_dicts = []
            for ws in workspaces:
                ws_dicts.append({
                    "id": ws.id,
                    "name": ws.name,
                    "status": ws.status,
                    "spec": ws.spec or {},
                    "k8s_namespace": ws.k8s_namespace,
                    "dns_zone": ws.dns_zone,
                    "created_at": ws.created_at,
                    "owner_id": ws.owner_id,
                })

            lifecycle = LifecycleManager()
            destroyer = WorkspaceDestroyer()
            summary = await cleanup_expired_workspaces(
                ws_dicts, lifecycle_manager=lifecycle, destroyer=destroyer
            )

            # Update statuses in DB
            from pyworkspace.db.repositories.workspace_repo import WorkspaceRepository
            repo = WorkspaceRepository(session)
            for ws_id in summary.get("paused", []):
                await repo.update_status(ws_id, "paused")
            for ws_id in summary.get("destroyed", []):
                await repo.update_status(ws_id, "destroyed")

            return summary

    return _run_async(_cleanup())


@celery_app.task
def snapshot_workspace_task(workspace_id: str, workspace_dict: dict, name: str):
    """Celery task: take a workspace snapshot."""
    from pyworkspace.core.lifecycle import LifecycleManager

    async def _snapshot():
        lifecycle = LifecycleManager()
        return await lifecycle.snapshot(workspace_dict, name)

    return _run_async(_snapshot())
