"""Plugin manifest endpoint."""

from fastapi import APIRouter

router = APIRouter()

MANIFEST = {
    "name": "pygate",
    "version": "1.0.0",
    "description": "Unified LLM routing engine - routes requests to multiple LLM providers",
    "service": None,
    "tools": [
        {
            "name": "llm_complete",
            "description": "Send a completion request to an LLM provider",
            "endpoint": "POST /v1/completions",
        },
        {
            "name": "llm_embed",
            "description": "Generate embeddings for text input",
            "endpoint": "POST /v1/embeddings",
        },
    ],
    "events": {
        "publishes": [
            "llm.completion.finished",
            "llm.rate_limit.hit",
        ],
        "subscribes": [],
    },
}


@router.get("/plugin/manifest")
async def get_manifest() -> dict:
    """Return the plugin manifest."""
    return MANIFEST
