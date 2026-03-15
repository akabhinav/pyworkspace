"""Tests for workspace TTL management."""

from datetime import datetime, timedelta, timezone

import pytest

from pyworkspace.core.ttl_manager import TTLManager, cleanup_expired_workspaces


class TestTTLManager:
    def test_no_ttl_never_expires(self):
        ttl = TTLManager()
        ws = {"spec": {"ttl_hours": None}, "created_at": datetime(2020, 1, 1, tzinfo=timezone.utc)}
        assert not ttl.is_expired(ws)

    def test_unexpired_workspace(self):
        ttl = TTLManager()
        ws = {
            "spec": {"ttl_hours": 24},
            "created_at": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        assert not ttl.is_expired(ws)

    def test_expired_workspace(self):
        ttl = TTLManager()
        ws = {
            "spec": {"ttl_hours": 1},
            "created_at": datetime.now(timezone.utc) - timedelta(hours=2),
        }
        assert ttl.is_expired(ws)

    def test_time_remaining_positive(self):
        ttl = TTLManager()
        ws = {
            "spec": {"ttl_hours": 24},
            "created_at": datetime.now(timezone.utc) - timedelta(hours=1),
        }
        remaining = ttl.time_remaining(ws)
        assert remaining is not None
        assert remaining > timedelta(hours=22)

    def test_time_remaining_zero_when_expired(self):
        ttl = TTLManager()
        ws = {
            "spec": {"ttl_hours": 1},
            "created_at": datetime.now(timezone.utc) - timedelta(hours=5),
        }
        remaining = ttl.time_remaining(ws)
        assert remaining == timedelta(0)

    def test_time_remaining_none_without_ttl(self):
        ttl = TTLManager()
        ws = {"spec": {}, "created_at": datetime.now(timezone.utc)}
        assert ttl.time_remaining(ws) is None

    def test_string_created_at(self):
        ttl = TTLManager()
        past = (datetime.now(timezone.utc) - timedelta(hours=5)).isoformat()
        ws = {"spec": {"ttl_hours": 1}, "created_at": past}
        assert ttl.is_expired(ws)

    def test_grace_period(self):
        ttl = TTLManager(grace_period_minutes=60)
        # Expired 30 min ago — still in 60min grace
        ws = {
            "spec": {"ttl_hours": 1},
            "created_at": datetime.now(timezone.utc) - timedelta(minutes=90),
        }
        assert ttl.is_expired(ws)
        assert ttl.is_in_grace_period(ws)

    def test_past_grace_period(self):
        ttl = TTLManager(grace_period_minutes=30)
        # Expired 2 hours ago — past 30min grace
        ws = {
            "spec": {"ttl_hours": 1},
            "created_at": datetime.now(timezone.utc) - timedelta(hours=3),
        }
        assert ttl.is_expired(ws)
        assert not ttl.is_in_grace_period(ws)


class TestCleanupExpiredWorkspaces:
    @pytest.mark.asyncio
    async def test_no_running_workspaces(self):
        result = await cleanup_expired_workspaces([])
        assert result == {"paused": [], "destroyed": []}

    @pytest.mark.asyncio
    async def test_skips_non_running(self):
        ws = [
            {
                "id": "ws1",
                "status": "provisioning",
                "spec": {"ttl_hours": 1},
                "created_at": datetime.now(timezone.utc) - timedelta(hours=5),
            }
        ]
        result = await cleanup_expired_workspaces(ws)
        assert result == {"paused": [], "destroyed": []}

    @pytest.mark.asyncio
    async def test_skips_unexpired(self):
        ws = [
            {
                "id": "ws1",
                "status": "running",
                "spec": {"ttl_hours": 24},
                "created_at": datetime.now(timezone.utc) - timedelta(hours=1),
            }
        ]
        result = await cleanup_expired_workspaces(ws)
        assert result == {"paused": [], "destroyed": []}

    @pytest.mark.asyncio
    async def test_destroys_past_grace(self):
        ws = [
            {
                "id": "ws1",
                "status": "running",
                "spec": {"ttl_hours": 1},
                "created_at": datetime.now(timezone.utc) - timedelta(hours=5),
            }
        ]
        result = await cleanup_expired_workspaces(ws)
        assert "ws1" in result["destroyed"]
