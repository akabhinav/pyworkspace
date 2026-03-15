"""Event webhook handlers."""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter, Request

from pymem.knowledge_store import KnowledgeStore

router = APIRouter()


def _get_store(request: Request) -> KnowledgeStore:
    return request.app.state.knowledge_store


@router.post("/webhooks/events")
def handle_event(body: dict[str, Any], request: Request) -> dict:
    """Handle incoming webhook events."""
    event_type = body.get("event", "")
    store = _get_store(request)

    if event_type == "workspace.destroyed":
        workspace_id = body.get("workspace_id")
        if workspace_id:
            # Clean up all documents tagged with this workspace
            doc_ids_to_delete = [
                doc.document_id
                for doc in store.list_documents()
                if doc.metadata.get("workspace_id") == workspace_id
            ]
            for doc_id in doc_ids_to_delete:
                store.delete_document(doc_id)

        return {
            "status": "ok",
            "event": event_type,
            "documents_removed": len(doc_ids_to_delete) if workspace_id else 0,
        }

    # Accept unknown events gracefully
    return {"status": "ok", "event": event_type}
