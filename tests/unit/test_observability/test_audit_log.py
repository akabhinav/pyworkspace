import pytest

from pyworkspace.observability import audit_log


class TestAuditLog:
    def setup_method(self):
        audit_log._audit_logs.clear()

    @pytest.mark.asyncio
    async def test_log_action(self):
        entry = await audit_log.log_action(
            workspace_id="ws-1",
            actor_id="user-1",
            action="created",
        )
        assert entry["workspace_id"] == "ws-1"
        assert entry["actor_id"] == "user-1"
        assert entry["action"] == "created"
        assert "id" in entry
        assert "timestamp" in entry

    @pytest.mark.asyncio
    async def test_log_action_with_metadata(self):
        entry = await audit_log.log_action(
            workspace_id="ws-1",
            actor_id="user-1",
            action="service_added",
            metadata={"service": "postgres"},
            ip_address="10.0.0.1",
        )
        assert entry["metadata"]["service"] == "postgres"
        assert entry["ip_address"] == "10.0.0.1"

    @pytest.mark.asyncio
    async def test_get_audit_logs(self):
        await audit_log.log_action("ws-1", "user-1", "created")
        await audit_log.log_action("ws-2", "user-2", "paused")

        logs = await audit_log.get_audit_logs()
        assert len(logs) == 2

    @pytest.mark.asyncio
    async def test_get_audit_logs_filtered(self):
        await audit_log.log_action("ws-1", "user-1", "created")
        await audit_log.log_action("ws-2", "user-2", "paused")

        logs = await audit_log.get_audit_logs(workspace_id="ws-1")
        assert len(logs) == 1
        assert logs[0]["workspace_id"] == "ws-1"

    @pytest.mark.asyncio
    async def test_get_audit_logs_limit(self):
        for i in range(10):
            await audit_log.log_action(f"ws-{i}", "user-1", "action")

        logs = await audit_log.get_audit_logs(limit=3)
        assert len(logs) == 3
