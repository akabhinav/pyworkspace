from fastapi import APIRouter, Depends, FastAPI, Header, HTTPException

from pysandbox.config import settings
from pysandbox.manifest import router as manifest_router
from pysandbox.models import (
    SandboxCreateRequest,
    SandboxCreateResponse,
    SandboxDestroyRequest,
    SandboxDestroyResponse,
    SandboxExecuteRequest,
    SandboxExecuteResponse,
    SandboxListResponse,
)
from pysandbox.sandbox_manager import sandbox_manager
from pysandbox.webhooks import router as webhooks_router

app = FastAPI(title="PySandbox", version="1.0.0")

sandbox_router = APIRouter(prefix="/v1/sandbox")


async def verify_auth(authorization: str = Header(...)):
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Invalid authorization header")
    token = authorization[len("Bearer "):]
    if token != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")


@app.get("/healthz")
async def healthz():
    return {"status": "ok"}


@sandbox_router.post("/create", response_model=SandboxCreateResponse)
async def create_sandbox(
    request: SandboxCreateRequest,
    _auth: None = Depends(verify_auth),
):
    info = sandbox_manager.create_sandbox(
        language=request.language,
        timeout=request.timeout_seconds,
        memory=request.memory_mb,
    )
    return SandboxCreateResponse(
        sandbox_id=info.sandbox_id,
        status=info.status,
        created_at=info.created_at,
    )


@sandbox_router.post("/execute", response_model=SandboxExecuteResponse)
async def execute_code(
    request: SandboxExecuteRequest,
    _auth: None = Depends(verify_auth),
):
    try:
        result = sandbox_manager.execute_code(
            sandbox_id=request.sandbox_id,
            code=request.code,
            stdin=request.stdin,
        )
    except KeyError:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return SandboxExecuteResponse(
        sandbox_id=request.sandbox_id,
        stdout=result.stdout,
        stderr=result.stderr,
        exit_code=result.exit_code,
        execution_time_ms=result.execution_time_ms,
    )


@sandbox_router.post("/destroy", response_model=SandboxDestroyResponse)
async def destroy_sandbox(
    request: SandboxDestroyRequest,
    _auth: None = Depends(verify_auth),
):
    try:
        sandbox_manager.destroy_sandbox(request.sandbox_id)
    except KeyError:
        raise HTTPException(status_code=404, detail="Sandbox not found")
    return SandboxDestroyResponse(
        sandbox_id=request.sandbox_id,
        status="destroyed",
    )


@sandbox_router.get("/list", response_model=SandboxListResponse)
async def list_sandboxes(
    _auth: None = Depends(verify_auth),
):
    sandboxes = sandbox_manager.list_sandboxes()
    return SandboxListResponse(
        sandboxes=[
            {
                "sandbox_id": s.sandbox_id,
                "language": s.language,
                "status": s.status,
                "created_at": s.created_at.isoformat(),
            }
            for s in sandboxes
        ]
    )


app.include_router(sandbox_router)
app.include_router(manifest_router)
app.include_router(webhooks_router)
