"""Tests for RBAC middleware."""

import pytest

from pyworkspace.auth.middleware import AuthUser, ROLE_HIERARCHY


class TestAuthUser:
    def test_admin_has_all_roles(self):
        user = AuthUser(user_id="u1", org_id="org1", role="admin")
        assert user.has_role("viewer")
        assert user.has_role("member")
        assert user.has_role("org_admin")
        assert user.has_role("admin")

    def test_member_cannot_be_admin(self):
        user = AuthUser(user_id="u1", org_id="org1", role="member")
        assert user.has_role("viewer")
        assert user.has_role("member")
        assert not user.has_role("org_admin")
        assert not user.has_role("admin")

    def test_viewer_is_lowest(self):
        user = AuthUser(user_id="u1", org_id="org1", role="viewer")
        assert user.has_role("viewer")
        assert not user.has_role("member")

    def test_can_access_own_org(self):
        user = AuthUser(user_id="u1", org_id="org1", role="member")
        assert user.can_access_org("org1")
        assert not user.can_access_org("org2")

    def test_admin_can_access_any_org(self):
        user = AuthUser(user_id="u1", org_id="org1", role="admin")
        assert user.can_access_org("org1")
        assert user.can_access_org("org2")
        assert user.can_access_org("any-org")


class TestRoleHierarchy:
    def test_hierarchy_order(self):
        assert ROLE_HIERARCHY["viewer"] < ROLE_HIERARCHY["member"]
        assert ROLE_HIERARCHY["member"] < ROLE_HIERARCHY["org_admin"]
        assert ROLE_HIERARCHY["org_admin"] < ROLE_HIERARCHY["admin"]
