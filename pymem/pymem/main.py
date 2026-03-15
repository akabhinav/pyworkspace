"""PyMem FastAPI application."""

from __future__ import annotations

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

from pymem.config import settings
from pymem.knowledge_store import KnowledgeStore
from pymem.manifest import router as manifest_router
from pymem.models import (
    ContextRequest,
    ContextResponse,
    DocumentInfo,
    IngestRequest,
    IngestResponse,
    SearchRequest,
    SearchResponse,
    SearchResult,
)
from pymem.webhooks import router as webhooks_router

app = FastAPI(title="PyMem", version="1.0.0")

# Global knowledge store instance
knowledge_store = KnowledgeStore()

# Attach to app state so webhooks can access it
app.state.knowledge_store = knowledge_store

# Include routers
app.include_router(manifest_router)
app.include_router(webhooks_router)

# Auth
security = HTTPBearer()


def verify_auth(
    credentials: HTTPAuthorizationCredentials = Depends(security),
) -> str:
    if credentials.credentials != settings.api_key:
        raise HTTPException(status_code=403, detail="Invalid API key")
    return credentials.credentials


@app.post("/v1/ingest", response_model=IngestResponse)
def ingest_document(
    req: IngestRequest,
    _auth: str = Depends(verify_auth),
) -> IngestResponse:
    """Ingest a document into the knowledge store."""
    result = knowledge_store.ingest(
        content=req.content,
        source=req.source,
        source_url=req.source_url,
        metadata=req.metadata,
        chunk_size=req.chunk_size,
        overlap=req.overlap,
    )
    return IngestResponse(
        document_id=result.document_id,
        chunks_created=result.chunks_created,
        source=result.source,
        status="ingested",
    )


@app.post("/v1/search", response_model=SearchResponse)
def search_knowledge(
    req: SearchRequest,
    _auth: str = Depends(verify_auth),
) -> SearchResponse:
    """Search the knowledge store."""
    hits = knowledge_store.search(
        query=req.query,
        top_k=req.top_k,
        min_score=req.min_score,
        filters=req.filters,
    )
    results = [
        SearchResult(
            chunk_id=h.chunk_id,
            document_id=h.document_id,
            content=h.content,
            score=h.score,
            metadata=h.metadata,
        )
        for h in hits
    ]
    return SearchResponse(
        query=req.query,
        results=results,
        total_results=len(results),
    )


@app.post("/v1/context", response_model=ContextResponse)
def assemble_context(
    req: ContextRequest,
    _auth: str = Depends(verify_auth),
) -> ContextResponse:
    """Assemble RAG context from the knowledge store."""
    result = knowledge_store.assemble_context(
        query=req.query,
        max_tokens=req.max_tokens,
        top_k=req.top_k,
    )
    return ContextResponse(
        query=req.query,
        context=result.context,
        sources=result.sources,
        total_tokens_approx=result.total_tokens_approx,
    )


@app.get("/v1/documents", response_model=list[DocumentInfo])
def list_documents(
    _auth: str = Depends(verify_auth),
) -> list[DocumentInfo]:
    """List all ingested documents."""
    docs = knowledge_store.list_documents()
    return [
        DocumentInfo(
            document_id=d.document_id,
            source=d.source,
            source_url=d.source_url,
            chunks=len(d.chunk_ids),
            created_at=d.created_at,
            metadata=d.metadata,
        )
        for d in docs
    ]


@app.get("/v1/documents/{doc_id}", response_model=DocumentInfo)
def get_document(
    doc_id: str,
    _auth: str = Depends(verify_auth),
) -> DocumentInfo:
    """Get info about a specific document."""
    doc = knowledge_store.get_document(doc_id)
    if doc is None:
        raise HTTPException(status_code=404, detail="Document not found")
    return DocumentInfo(
        document_id=doc.document_id,
        source=doc.source,
        source_url=doc.source_url,
        chunks=len(doc.chunk_ids),
        created_at=doc.created_at,
        metadata=doc.metadata,
    )


@app.delete("/v1/documents/{doc_id}")
def delete_document(
    doc_id: str,
    _auth: str = Depends(verify_auth),
) -> dict:
    """Delete a document and its chunks."""
    deleted = knowledge_store.delete_document(doc_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Document not found")
    return {"status": "deleted", "document_id": doc_id}
