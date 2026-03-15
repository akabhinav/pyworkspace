"""Tests for workspace lifecycle manager."""
import pytest
from pyworkspace.core.lifecycle import LifecycleManager

class TestLifecycleManager:
    @pytest.mark.asyncio
    async def test_pause_workspace(self):
        workspace = {
            "id": "test-123",
            "status": "running",
            "k8s_namespace": "pyws-test",
            "spec": {"auto_snapshot": False, "services": []},
        }
        lifecycle = LifecycleManager()
        result = await lifecycle.pause(workspace)
        assert result["status"] == "paused"
        assert result["paused_at"] is not None

    @pytest.mark.asyncio
    async def test_resume_workspace(self):
        workspace = {
            "id": "test-123",
            "status": "paused",
            "k8s_namespace": "pyws-test",
            "spec": {"services": []},
        }
        lifecycle = LifecycleManager()
        result = await lifecycle.resume(workspace)
        assert result["status"] == "running"
        assert result["paused_at"] is None

    @pytest.mark.asyncio
    async def test_snapshot(self):
        workspace = {
            "id": "test-123",
            "status": "running",
            "spec": {"services": [{"name": "postgres", "type": "postgres"}]},
        }
        lifecycle = LifecycleManager()
        snapshot = await lifecycle.snapshot(workspace, "test-snap")
        assert snapshot["name"] == "test-snap"
        assert snapshot["status"] == "ready"
        assert snapshot["workspace_id"] == "test-123"

    @pytest.mark.asyncio
    async def test_clone(self):
        workspace = {
            "id": "source-123",
            "name": "source",
            "status": "running",
            "spec": {
                "services": [{"name": "postgres", "type": "postgres", "version": "16", "config": {}}],
                "org_id": "org-1",
                "tier": "standard",
            },
        }
        lifecycle = LifecycleManager()
        result = await lifecycle.clone(workspace, "cloned", "new-owner")
        assert result["name"] == "cloned"
