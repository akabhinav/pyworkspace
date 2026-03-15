from datetime import datetime

from pydantic import BaseModel, Field


class SandboxCreateRequest(BaseModel):
    language: str = "python"
    timeout_seconds: int = 300
    memory_mb: int = 512


class SandboxCreateResponse(BaseModel):
    sandbox_id: str
    status: str
    created_at: datetime


class SandboxExecuteRequest(BaseModel):
    sandbox_id: str
    code: str
    stdin: str = ""


class SandboxExecuteResponse(BaseModel):
    sandbox_id: str
    stdout: str
    stderr: str
    exit_code: int
    execution_time_ms: int


class SandboxDestroyRequest(BaseModel):
    sandbox_id: str


class SandboxDestroyResponse(BaseModel):
    sandbox_id: str
    status: str


class SandboxListResponse(BaseModel):
    sandboxes: list[dict]
