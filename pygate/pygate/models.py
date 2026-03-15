"""Request and response models for PyGate."""

from pydantic import BaseModel


class CompletionRequest(BaseModel):
    model: str = "claude-sonnet-4-20250514"
    messages: list[dict[str, str]]  # [{"role": "user", "content": "..."}]
    max_tokens: int = 1024
    temperature: float = 0.7
    stream: bool = False


class CompletionResponse(BaseModel):
    id: str
    model: str
    content: str
    usage: dict  # {"prompt_tokens": N, "completion_tokens": N, "total_tokens": N}
    latency_ms: int
    provider: str  # which provider was used


class EmbeddingRequest(BaseModel):
    model: str = "text-embedding-3-small"
    input: str | list[str]


class EmbeddingResponse(BaseModel):
    id: str
    model: str
    embeddings: list[list[float]]
    usage: dict


class ModelInfo(BaseModel):
    name: str
    provider: str
    max_tokens: int
    supports_streaming: bool
    cost_per_1k_input: float
    cost_per_1k_output: float
