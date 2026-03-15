"""FastAPI application for PyGate LLM routing service."""

from fastapi import Depends, FastAPI, Header, HTTPException

from .config import settings
from .manifest import router as manifest_router
from .models import CompletionRequest, CompletionResponse, EmbeddingRequest, EmbeddingResponse, ModelInfo
from .router import LLMRouter
from .webhooks import router as webhooks_router

app = FastAPI(title="PyGate", version="1.0.0", description="Unified LLM routing engine")

# Shared router instance
llm_router = LLMRouter()

# Include sub-routers
app.include_router(manifest_router)
app.include_router(webhooks_router)


async def verify_api_key(authorization: str = Header(default=None)) -> str:
    """Verify the API key from the Authorization header."""
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid Authorization format")
    token = authorization.removeprefix("Bearer ")
    if token != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return token


@app.post("/v1/completions", response_model=CompletionResponse)
async def create_completion(
    request: CompletionRequest,
    _api_key: str = Depends(verify_api_key),
) -> CompletionResponse:
    """Create a completion using the LLM router."""
    try:
        return await llm_router.complete(request)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))


@app.post("/v1/embeddings", response_model=EmbeddingResponse)
async def create_embedding(
    request: EmbeddingRequest,
    _api_key: str = Depends(verify_api_key),
) -> EmbeddingResponse:
    """Create embeddings using the LLM router."""
    return await llm_router.embed(request)


@app.get("/v1/models", response_model=list[ModelInfo])
async def list_models(
    _api_key: str = Depends(verify_api_key),
) -> list[ModelInfo]:
    """List all available models."""
    return llm_router.list_models()


@app.get("/v1/usage")
async def get_usage(
    _api_key: str = Depends(verify_api_key),
) -> dict:
    """Get usage statistics."""
    return llm_router.get_usage()


@app.get("/health")
async def health() -> dict:
    """Health check endpoint."""
    return {"status": "ok"}
