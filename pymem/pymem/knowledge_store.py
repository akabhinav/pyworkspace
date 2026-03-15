"""In-memory vector store with keyword-based search simulation."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any


@dataclass
class ChunkRecord:
    chunk_id: str
    document_id: str
    content: str
    metadata: dict[str, Any]


@dataclass
class DocumentRecord:
    document_id: str
    source: str
    source_url: str | None
    chunk_ids: list[str]
    created_at: datetime
    metadata: dict[str, Any]


@dataclass
class SearchHit:
    chunk_id: str
    document_id: str
    content: str
    score: float
    metadata: dict[str, Any]


@dataclass
class IngestResult:
    document_id: str
    chunks_created: int
    source: str


@dataclass
class ContextResult:
    context: str
    sources: list[dict[str, Any]]
    total_tokens_approx: int


class KnowledgeStore:
    """Simulated vector store with keyword-based search."""

    def __init__(self) -> None:
        self._documents: dict[str, DocumentRecord] = {}
        self._chunks: dict[str, ChunkRecord] = {}  # chunk_id -> chunk

    def ingest(
        self,
        content: str,
        source: str,
        source_url: str | None,
        metadata: dict[str, Any],
        chunk_size: int,
        overlap: int,
    ) -> IngestResult:
        """Ingest a document: chunk it and store."""
        document_id = str(uuid.uuid4())
        chunks = self._chunk_text(content, chunk_size, overlap)
        chunk_ids: list[str] = []

        for chunk_text in chunks:
            chunk_id = str(uuid.uuid4())
            chunk_ids.append(chunk_id)
            self._chunks[chunk_id] = ChunkRecord(
                chunk_id=chunk_id,
                document_id=document_id,
                content=chunk_text,
                metadata=metadata,
            )

        self._documents[document_id] = DocumentRecord(
            document_id=document_id,
            source=source,
            source_url=source_url,
            chunk_ids=chunk_ids,
            created_at=datetime.now(timezone.utc),
            metadata=metadata,
        )

        return IngestResult(
            document_id=document_id,
            chunks_created=len(chunks),
            source=source,
        )

    def search(
        self,
        query: str,
        top_k: int,
        min_score: float,
        filters: dict[str, Any],
    ) -> list[SearchHit]:
        """Simulate semantic search with keyword matching."""
        hits: list[SearchHit] = []

        for chunk in self._chunks.values():
            # Apply metadata filters
            if filters:
                skip = False
                for key, value in filters.items():
                    if chunk.metadata.get(key) != value:
                        skip = True
                        break
                if skip:
                    continue

            score = self._score(query, chunk.content)
            if score >= min_score:
                hits.append(
                    SearchHit(
                        chunk_id=chunk.chunk_id,
                        document_id=chunk.document_id,
                        content=chunk.content,
                        score=score,
                        metadata=chunk.metadata,
                    )
                )

        # Sort by score descending
        hits.sort(key=lambda h: h.score, reverse=True)
        return hits[:top_k]

    def assemble_context(
        self, query: str, max_tokens: int, top_k: int
    ) -> ContextResult:
        """Search and assemble context for RAG."""
        hits = self.search(query, top_k=top_k, min_score=0.0, filters={})
        context_parts: list[str] = []
        sources: list[dict[str, Any]] = []
        total_chars = 0
        max_chars = max_tokens * 4  # approximate: 1 token ~ 4 chars

        for hit in hits:
            if total_chars + len(hit.content) > max_chars:
                # Add partial content if there's room
                remaining = max_chars - total_chars
                if remaining > 50:  # only add if meaningful
                    context_parts.append(hit.content[:remaining])
                    sources.append(
                        {
                            "chunk_id": hit.chunk_id,
                            "document_id": hit.document_id,
                            "score": hit.score,
                        }
                    )
                break

            context_parts.append(hit.content)
            sources.append(
                {
                    "chunk_id": hit.chunk_id,
                    "document_id": hit.document_id,
                    "score": hit.score,
                }
            )
            total_chars += len(hit.content)

        assembled = "\n\n---\n\n".join(context_parts)
        return ContextResult(
            context=assembled,
            sources=sources,
            total_tokens_approx=len(assembled) // 4,
        )

    def list_documents(self) -> list[DocumentRecord]:
        """List all documents."""
        return list(self._documents.values())

    def get_document(self, doc_id: str) -> DocumentRecord | None:
        """Get a document by ID."""
        return self._documents.get(doc_id)

    def delete_document(self, doc_id: str) -> bool:
        """Delete a document and all its chunks."""
        doc = self._documents.get(doc_id)
        if doc is None:
            return False

        for chunk_id in doc.chunk_ids:
            self._chunks.pop(chunk_id, None)

        del self._documents[doc_id]
        return True

    def _chunk_text(self, text: str, chunk_size: int, overlap: int) -> list[str]:
        """Split text into overlapping chunks."""
        chunks: list[str] = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunks.append(text[start:end])
            start = end - overlap
        return chunks

    def _score(self, query: str, content: str) -> float:
        """Score content against query using keyword matching."""
        query_words = set(query.lower().split())
        content_lower = content.lower()
        if not query_words:
            return 0.0
        matches = sum(1 for w in query_words if w in content_lower)
        return matches / len(query_words)
