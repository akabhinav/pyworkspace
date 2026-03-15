"""Event webhooks (minimal)."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/webhooks/events")
async def receive_event(event: dict) -> dict:
    """Receive an event webhook (no-op for standalone plugin)."""
    return {"status": "ignored", "reason": "PyGate does not subscribe to events"}
