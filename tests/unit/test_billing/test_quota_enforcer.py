from pyworkspace.billing.quota_enforcer import QuotaEnforcer


class TestQuotaEnforcer:
    def test_workspace_limit_dev_within(self):
        assert QuotaEnforcer.check_workspace_limit("dev", 1) is True

    def test_workspace_limit_dev_at_limit(self):
        assert QuotaEnforcer.check_workspace_limit("dev", 2) is False

    def test_workspace_limit_enterprise(self):
        assert QuotaEnforcer.check_workspace_limit("enterprise", 100) is True

    def test_service_limit_dev_within(self):
        assert QuotaEnforcer.check_service_limit("dev", 3) is True

    def test_service_limit_dev_at_limit(self):
        assert QuotaEnforcer.check_service_limit("dev", 5) is False

    def test_service_limit_standard(self):
        assert QuotaEnforcer.check_service_limit("standard", 14) is True
        assert QuotaEnforcer.check_service_limit("standard", 15) is False

    def test_get_tier_limits_dev(self):
        limits = QuotaEnforcer.get_tier_limits("dev")
        assert limits["max_workspaces"] == 2
        assert limits["max_services"] == 5

    def test_get_tier_limits_unknown_falls_back_to_dev(self):
        limits = QuotaEnforcer.get_tier_limits("unknown_tier")
        assert limits["max_workspaces"] == 2
