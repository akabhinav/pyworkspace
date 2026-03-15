"""Health check endpoints."""

from __future__ import annotations

from fastapi import APIRouter

router = APIRouter(tags=["health"])


@router.get("/health")
async def health_check() -> dict:
    return {"status": "healthy", "service": "pyworkspace"}


@router.get("/ready")
async def readiness_check() -> dict:
    return {"status": "ready"}
