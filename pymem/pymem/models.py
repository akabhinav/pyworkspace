"""Request and response models for PyMem."""

from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class IngestRequest(BaseModel):
    content: str
    source: str = "manual"  # "manual", "url", "file", "github"
    source_url: str | None = None
    metadata: dict[str, Any] = {}
    chunk_size: int = 500  # characters per chunk
    overlap: int = 50


class IngestResponse(BaseModel):
    document_id: str
    chunks_created: int
    source: str
    status: str


class SearchRequest(BaseModel):
    query: str
    top_k: int = 5
    min_score: float = 0.0
    filters: dict[str, Any] = {}


class SearchResult(BaseModel):
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: dict[str, Any]


class SearchResponse(BaseModel):
    query: str
    results: list[SearchResult]
    total_results: int


class ContextRequest(BaseModel):
    query: str
    max_tokens: int = 2000
    top_k: int = 5


class ContextResponse(BaseModel):
    query: str
    context: str  # assembled context string
    sources: list[dict]  # source references
    total_tokens_approx: int


class DocumentInfo(BaseModel):
    document_id: str
    source: str
    source_url: str | None
    chunks: int
    created_at: datetime
    metadata: dict[str, Any]
