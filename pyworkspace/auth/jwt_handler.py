"""JWT token creation and verification."""

from __future__ import annotations

import time
from typing import Any

import structlog
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import ec

logger = structlog.get_logger()

# Use HMAC-SHA256 via PyJWT-compatible manual implementation
# to avoid adding another dependency.  We use the stdlib + cryptography.
import hashlib
import hmac
import base64
import json


def _b64url_encode(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode()


def _b64url_decode(s: str) -> bytes:
    padding = 4 - len(s) % 4
    return base64.urlsafe_b64decode(s + "=" * padding)


_HEADER = _b64url_encode(json.dumps({"alg": "HS256", "typ": "JWT"}).encode())


def create_token(
    payload: dict[str, Any],
    secret: str,
    expires_in: int = 3600,
) -> str:
    """Create a signed JWT token."""
    now = int(time.time())
    payload = {**payload, "iat": now, "exp": now + expires_in}
    payload_encoded = _b64url_encode(json.dumps(payload, default=str).encode())
    signing_input = f"{_HEADER}.{payload_encoded}"
    sig = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    return f"{signing_input}.{_b64url_encode(sig)}"


def verify_token(token: str, secret: str) -> dict[str, Any]:
    """Verify and decode a JWT token. Raises ValueError on failure."""
    parts = token.split(".")
    if len(parts) != 3:
        raise ValueError("Invalid token format")

    signing_input = f"{parts[0]}.{parts[1]}"
    expected_sig = hmac.new(secret.encode(), signing_input.encode(), hashlib.sha256).digest()
    actual_sig = _b64url_decode(parts[2])

    if not hmac.compare_digest(expected_sig, actual_sig):
        raise ValueError("Invalid token signature")

    payload = json.loads(_b64url_decode(parts[1]))

    if payload.get("exp", 0) < int(time.time()):
        raise ValueError("Token expired")

    return payload
