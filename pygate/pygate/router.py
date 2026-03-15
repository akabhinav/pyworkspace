"""LLM routing logic with simulated providers."""

import hashlib
import math
import time
import uuid

from .models import (
    CompletionRequest,
    CompletionResponse,
    EmbeddingRequest,
    EmbeddingResponse,
    ModelInfo,
)


class LLMRouter:
    """Simulated LLM routing with model registry and fallback."""

    MODELS: dict[str, dict] = {
        "claude-sonnet-4-20250514": {
            "provider": "anthropic",
            "max_tokens": 200000,
            "supports_streaming": True,
            "cost_per_1k_input": 0.003,
            "cost_per_1k_output": 0.015,
        },
        "gpt-4o": {
            "provider": "openai",
            "max_tokens": 128000,
            "supports_streaming": True,
            "cost_per_1k_input": 0.005,
            "cost_per_1k_output": 0.015,
        },
        "llama-3.1-70b": {
            "provider": "local",
            "max_tokens": 8192,
            "supports_streaming": False,
            "cost_per_1k_input": 0.0,
            "cost_per_1k_output": 0.0,
        },
    }

    EMBEDDING_MODELS: dict[str, dict] = {
        "text-embedding-3-small": {
            "provider": "openai",
            "dimensions": 1536,
        },
        "text-embedding-3-large": {
            "provider": "openai",
            "dimensions": 3072,
        },
    }

    def __init__(self) -> None:
        self._request_count: int = 0
        self._total_prompt_tokens: int = 0
        self._total_completion_tokens: int = 0
        self._rate_limits: dict[str, int] = {}

    async def complete(self, request: CompletionRequest) -> CompletionResponse:
        """Simulate a completion request to an LLM provider."""
        if request.model not in self.MODELS:
            raise ValueError(f"Unknown model: {request.model}")

        model_info = self.MODELS[request.model]
        self._request_count += 1

        start_time = time.monotonic()

        # Get last message content for mock response
        last_message = request.messages[-1]["content"] if request.messages else ""
        content = f"[{request.model}] Mock response to: {last_message[:50]}"

        # Calculate mock token counts
        prompt_text = " ".join(m.get("content", "") for m in request.messages)
        prompt_tokens = max(1, len(prompt_text) // 4)
        completion_tokens = max(1, len(content) // 4)

        self._total_prompt_tokens += prompt_tokens
        self._total_completion_tokens += completion_tokens

        elapsed_ms = int((time.monotonic() - start_time) * 1000)

        return CompletionResponse(
            id=f"cmpl-{uuid.uuid4().hex[:12]}",
            model=request.model,
            content=content,
            usage={
                "prompt_tokens": prompt_tokens,
                "completion_tokens": completion_tokens,
                "total_tokens": prompt_tokens + completion_tokens,
            },
            latency_ms=max(1, elapsed_ms),
            provider=model_info["provider"],
        )

    async def embed(self, request: EmbeddingRequest) -> EmbeddingResponse:
        """Return mock embeddings."""
        inputs = request.input if isinstance(request.input, list) else [request.input]

        # Determine dimensions from model
        embed_model = self.EMBEDDING_MODELS.get(request.model)
        dimensions = embed_model["dimensions"] if embed_model else 1536

        embeddings: list[list[float]] = []
        total_tokens = 0

        for text in inputs:
            total_tokens += max(1, len(text) // 4)
            # Generate deterministic pseudo-random embeddings based on text content
            seed = hashlib.md5(text.encode()).hexdigest()
            vector: list[float] = []
            for i in range(dimensions):
                # Use a simple deterministic formula for mock values
                byte_val = int(seed[(i * 2) % len(seed)], 16)
                val = (byte_val - 8) / 100.0  # small values around 0
                # Add variation based on position
                val += math.sin(i * 0.1) * 0.01
                vector.append(round(val, 6))
            embeddings.append(vector)

        self._request_count += 1

        return EmbeddingResponse(
            id=f"embd-{uuid.uuid4().hex[:12]}",
            model=request.model,
            embeddings=embeddings,
            usage={
                "prompt_tokens": total_tokens,
                "total_tokens": total_tokens,
            },
        )

    def list_models(self) -> list[ModelInfo]:
        """Return all available models."""
        return [
            ModelInfo(
                name=name,
                provider=info["provider"],
                max_tokens=info["max_tokens"],
                supports_streaming=info["supports_streaming"],
                cost_per_1k_input=info["cost_per_1k_input"],
                cost_per_1k_output=info["cost_per_1k_output"],
            )
            for name, info in self.MODELS.items()
        ]

    def get_usage(self) -> dict:
        """Return usage statistics."""
        return {
            "total_requests": self._request_count,
            "total_prompt_tokens": self._total_prompt_tokens,
            "total_completion_tokens": self._total_completion_tokens,
            "total_tokens": self._total_prompt_tokens + self._total_completion_tokens,
        }
