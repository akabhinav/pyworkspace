"""Hard limits enforcement per org/user tier."""

from __future__ import annotations

from pyworkspace.config.constants import TIER_LIMITS


class QuotaEnforcer:
    """Enforces resource quotas per tier."""

    @staticmethod
    def check_workspace_limit(tier: str, current_count: int) -> bool:
        """Check if org can create another workspace."""
        limits = TIER_LIMITS.get(tier, TIER_LIMITS["dev"])
        return current_count < int(limits["max_workspaces"])

    @staticmethod
    def check_service_limit(tier: str, current_count: int) -> bool:
        """Check if workspace can add another service."""
        limits = TIER_LIMITS.get(tier, TIER_LIMITS["dev"])
        return current_count < int(limits["max_services"])

    @staticmethod
    def get_tier_limits(tier: str) -> dict:
        """Get resource limits for a tier."""
        return dict(TIER_LIMITS.get(tier, TIER_LIMITS["dev"]))
