"""Tests for JWT token creation and verification."""

import time

import pytest

from pyworkspace.auth.jwt_handler import create_token, verify_token


SECRET = "test-secret-key"


class TestCreateToken:
    def test_creates_valid_token(self):
        token = create_token({"sub": "user-1", "role": "admin"}, SECRET)
        assert isinstance(token, str)
        parts = token.split(".")
        assert len(parts) == 3

    def test_token_contains_claims(self):
        token = create_token(
            {"sub": "user-1", "org_id": "org-1", "role": "member"}, SECRET
        )
        payload = verify_token(token, SECRET)
        assert payload["sub"] == "user-1"
        assert payload["org_id"] == "org-1"
        assert payload["role"] == "member"
        assert "iat" in payload
        assert "exp" in payload

    def test_custom_expiry(self):
        token = create_token({"sub": "u"}, SECRET, expires_in=60)
        payload = verify_token(token, SECRET)
        assert payload["exp"] - payload["iat"] == 60


class TestVerifyToken:
    def test_valid_token(self):
        token = create_token({"sub": "user-1"}, SECRET)
        payload = verify_token(token, SECRET)
        assert payload["sub"] == "user-1"

    def test_invalid_secret_raises(self):
        token = create_token({"sub": "user-1"}, SECRET)
        with pytest.raises(ValueError, match="signature"):
            verify_token(token, "wrong-secret")

    def test_expired_token_raises(self):
        token = create_token({"sub": "user-1"}, SECRET, expires_in=-1)
        with pytest.raises(ValueError, match="expired"):
            verify_token(token, SECRET)

    def test_malformed_token_raises(self):
        with pytest.raises(ValueError, match="Invalid token format"):
            verify_token("not.a.valid.token.format", SECRET)

    def test_tampered_payload_raises(self):
        token = create_token({"sub": "user-1"}, SECRET)
        parts = token.split(".")
        # Tamper with payload
        import base64, json
        payload = json.loads(base64.urlsafe_b64decode(parts[1] + "=="))
        payload["role"] = "admin"
        tampered = base64.urlsafe_b64encode(json.dumps(payload).encode()).rstrip(b"=").decode()
        tampered_token = f"{parts[0]}.{tampered}.{parts[2]}"
        with pytest.raises(ValueError, match="signature"):
            verify_token(tampered_token, SECRET)
