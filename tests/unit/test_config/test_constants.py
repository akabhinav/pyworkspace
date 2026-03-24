from pyworkspace.config.constants import (
    BLOCKED_SHELL_PATTERNS,
    TIER_LIMITS,
    WORKSPACE_STATUS_RUNNING,
    WORKSPACE_STATUSES,
)


class TestConstants:
    def test_workspace_statuses(self):
        assert "running" in WORKSPACE_STATUSES
        assert "provisioning" in WORKSPACE_STATUSES
        assert "paused" in WORKSPACE_STATUSES
        assert "destroyed" in WORKSPACE_STATUSES
        assert "error" in WORKSPACE_STATUSES

    def test_workspace_status_running(self):
        assert WORKSPACE_STATUS_RUNNING == "running"

    def test_tier_limits_dev(self):
        assert TIER_LIMITS["dev"]["max_workspaces"] == 2
        assert TIER_LIMITS["dev"]["max_services"] == 5

    def test_tier_limits_standard(self):
        assert TIER_LIMITS["standard"]["max_workspaces"] == 5
        assert TIER_LIMITS["standard"]["max_services"] == 15

    def test_tier_limits_enterprise(self):
        assert TIER_LIMITS["enterprise"]["max_workspaces"] == 999

    def test_blocked_shell_patterns(self):
        assert "rm -rf /" in BLOCKED_SHELL_PATTERNS
        assert "mkfs" in BLOCKED_SHELL_PATTERNS
        assert len(BLOCKED_SHELL_PATTERNS) > 0
