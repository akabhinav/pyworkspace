import pytest

from pyworkspace.auth.middleware import AuthUser, ROLE_HIERARCHY


class TestAuthUserMiddleware:
    def test_has_role_admin(self):
        user = AuthUser(user_id="u1", org_id="org1", role="admin")
        assert user.has_role("admin") is True
        assert user.has_role("member") is True
        assert user.has_role("viewer") is True

    def test_has_role_member(self):
        user = AuthUser(user_id="u1", org_id="org1", role="member")
        assert user.has_role("admin") is False
        assert user.has_role("member") is True
        assert user.has_role("viewer") is True

    def test_has_role_viewer(self):
        user = AuthUser(user_id="u1", org_id="org1", role="viewer")
        assert user.has_role("admin") is False
        assert user.has_role("member") is False
        assert user.has_role("viewer") is True

    def test_can_access_own_org(self):
        user = AuthUser(user_id="u1", org_id="org1", role="member")
        assert user.can_access_org("org1") is True
        assert user.can_access_org("org2") is False

    def test_admin_can_access_any_org(self):
        user = AuthUser(user_id="u1", org_id="org1", role="admin")
        assert user.can_access_org("org1") is True
        assert user.can_access_org("org2") is True

    def test_email_field(self):
        user = AuthUser(user_id="u1", org_id="org1", role="member", email="test@test.com")
        assert user.email == "test@test.com"


class TestRoleHierarchy:
    def test_hierarchy_values(self):
        assert ROLE_HIERARCHY["viewer"] < ROLE_HIERARCHY["member"]
        assert ROLE_HIERARCHY["member"] < ROLE_HIERARCHY["org_admin"]
        assert ROLE_HIERARCHY["org_admin"] < ROLE_HIERARCHY["admin"]
