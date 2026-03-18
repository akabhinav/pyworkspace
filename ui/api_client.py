"""API client for PyWorkspace backend — used by the Streamlit UI.

Falls back to simulated data when the backend is not running, so the
UI can always be demonstrated standalone.
"""

from __future__ import annotations

import random
import uuid
from datetime import datetime, timedelta, timezone

import httpx

DEFAULT_BASE = "http://localhost:8000/v1"


class PyWorkspaceClient:
    """Thin HTTP wrapper around the PyWorkspace REST API."""

    def __init__(self, base_url: str = DEFAULT_BASE, token: str | None = None):
        self.base = base_url.rstrip("/")
        self.token = token
        self._headers = {"Authorization": f"Bearer {token}"} if token else {}

    # ── health ───────────────────────────────────────────────────────
    def health(self) -> dict:
        try:
            r = httpx.get(f"{self.base.replace('/v1', '')}/health", timeout=3)
            return r.json()
        except Exception:
            return {"status": "unreachable"}

    # ── workspaces ───────────────────────────────────────────────────
    def list_workspaces(self) -> list[dict]:
        try:
            r = httpx.get(f"{self.base}/workspaces", headers=self._headers, timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception:
            return _DEMO_WORKSPACES

    def get_workspace(self, wid: str) -> dict | None:
        try:
            r = httpx.get(f"{self.base}/workspaces/{wid}", headers=self._headers, timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception:
            return next((w for w in _DEMO_WORKSPACES if w["id"] == wid), None)

    def create_workspace(self, payload: dict) -> dict:
        try:
            r = httpx.post(
                f"{self.base}/workspaces",
                json=payload,
                headers=self._headers,
                timeout=10,
            )
            r.raise_for_status()
            return r.json()
        except Exception:
            return {
                "id": str(uuid.uuid4())[:8],
                "name": payload.get("name", "new-ws"),
                "status": "provisioning",
                "tier": payload.get("tier", "standard"),
                "owner_id": payload.get("owner_id", "demo"),
                "org_id": payload.get("org_id", "demo-org"),
                "created_at": datetime.now(timezone.utc).isoformat(),
            }

    def delete_workspace(self, wid: str) -> dict:
        try:
            r = httpx.delete(
                f"{self.base}/workspaces/{wid}", headers=self._headers, timeout=5
            )
            return r.json()
        except Exception:
            return {"status": "destroying", "workspace_id": wid}

    def pause_workspace(self, wid: str) -> dict:
        try:
            r = httpx.post(
                f"{self.base}/workspaces/{wid}/pause", headers=self._headers, timeout=5
            )
            return r.json()
        except Exception:
            return {"status": "paused", "workspace_id": wid}

    def resume_workspace(self, wid: str) -> dict:
        try:
            r = httpx.post(
                f"{self.base}/workspaces/{wid}/resume", headers=self._headers, timeout=5
            )
            return r.json()
        except Exception:
            return {"status": "running", "workspace_id": wid}

    # ── catalog ──────────────────────────────────────────────────────
    def list_catalog(self) -> list[dict]:
        try:
            r = httpx.get(f"{self.base}/catalog", timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception:
            return _DEMO_CATALOG

    def get_catalog_service(self, stype: str) -> dict | None:
        try:
            r = httpx.get(f"{self.base}/catalog/{stype}", timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception:
            return next((s for s in _DEMO_CATALOG if s["type"] == stype), None)

    # ── templates ────────────────────────────────────────────────────
    def list_templates(self) -> list[dict]:
        try:
            r = httpx.get(f"{self.base}/templates", headers=self._headers, timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception:
            return _DEMO_TEMPLATES

    # ── plugins ──────────────────────────────────────────────────────
    def list_plugins(self) -> list[dict]:
        try:
            r = httpx.get(f"{self.base}/plugins", headers=self._headers, timeout=5)
            r.raise_for_status()
            return r.json()
        except Exception:
            return _DEMO_PLUGINS

    def get_plugin(self, name: str) -> dict | None:
        try:
            r = httpx.get(
                f"{self.base}/plugins/{name}", headers=self._headers, timeout=5
            )
            r.raise_for_status()
            return r.json()
        except Exception:
            return next((p for p in _DEMO_PLUGINS if p["name"] == name), None)

    # ── snapshots ────────────────────────────────────────────────────
    def list_snapshots(self, wid: str) -> list[dict]:
        try:
            r = httpx.get(
                f"{self.base}/workspaces/{wid}/snapshots",
                headers=self._headers,
                timeout=5,
            )
            r.raise_for_status()
            return r.json()
        except Exception:
            return _DEMO_SNAPSHOTS

    # ── billing ──────────────────────────────────────────────────────
    def get_workspace_usage(self, wid: str) -> dict:
        try:
            r = httpx.get(
                f"{self.base}/workspaces/{wid}/usage",
                headers=self._headers,
                timeout=5,
            )
            return r.json()
        except Exception:
            return {
                "workspace_id": wid,
                "cpu_core_hours": round(random.uniform(2, 80), 1),
                "memory_gib_hours": round(random.uniform(5, 120), 1),
                "disk_gib_hours": round(random.uniform(10, 200), 1),
                "network_egress_gb": round(random.uniform(0.1, 5), 2),
            }

    def get_workspace_cost(self, wid: str) -> dict:
        try:
            r = httpx.get(
                f"{self.base}/workspaces/{wid}/cost",
                headers=self._headers,
                timeout=5,
            )
            return r.json()
        except Exception:
            return {
                "workspace_id": wid,
                "estimated_cost_usd": round(random.uniform(5, 150), 2),
                "actual_cost_usd": round(random.uniform(3, 120), 2),
                "period": "current_month",
            }


# ── Demo data (used when backend is unreachable) ─────────────────────

_now = datetime.now(timezone.utc)

_DEMO_WORKSPACES = [
    {
        "id": "ws-abc123",
        "name": "ml-training-pipeline",
        "owner_id": "alice",
        "org_id": "acme-corp",
        "tier": "enterprise",
        "status": "running",
        "k8s_namespace": "ws-abc123",
        "dns_zone": "ws-abc123.pyworkspace.internal",
        "created_at": (_now - timedelta(hours=12)).isoformat(),
        "error_message": None,
    },
    {
        "id": "ws-def456",
        "name": "ecommerce-staging",
        "owner_id": "bob",
        "org_id": "acme-corp",
        "tier": "standard",
        "status": "running",
        "k8s_namespace": "ws-def456",
        "dns_zone": "ws-def456.pyworkspace.internal",
        "created_at": (_now - timedelta(days=2)).isoformat(),
        "error_message": None,
    },
    {
        "id": "ws-ghi789",
        "name": "data-analytics-dev",
        "owner_id": "carol",
        "org_id": "acme-corp",
        "tier": "dev",
        "status": "paused",
        "k8s_namespace": "ws-ghi789",
        "dns_zone": "ws-ghi789.pyworkspace.internal",
        "created_at": (_now - timedelta(days=5)).isoformat(),
        "error_message": None,
    },
    {
        "id": "ws-jkl012",
        "name": "microservices-test",
        "owner_id": "dave",
        "org_id": "acme-corp",
        "tier": "standard",
        "status": "provisioning",
        "k8s_namespace": "ws-jkl012",
        "dns_zone": None,
        "created_at": (_now - timedelta(minutes=5)).isoformat(),
        "error_message": None,
    },
    {
        "id": "ws-mno345",
        "name": "fintech-api-sandbox",
        "owner_id": "eve",
        "org_id": "acme-corp",
        "tier": "enterprise",
        "status": "error",
        "k8s_namespace": "ws-mno345",
        "dns_zone": "ws-mno345.pyworkspace.internal",
        "created_at": (_now - timedelta(days=1)).isoformat(),
        "error_message": "OOMKilled: postgres exceeded memory limit",
    },
]

_DEMO_CATALOG = [
    {"type": "postgres", "display_name": "PostgreSQL", "description": "Relational database with full SQL support", "default_version": "16", "categories": ["database"], "versions": ["16", "15", "14", "13"], "source": "builtin"},
    {"type": "redis", "display_name": "Redis", "description": "In-memory key-value store and cache", "default_version": "7", "categories": ["cache", "database"], "versions": ["7", "6"], "source": "builtin"},
    {"type": "kafka", "display_name": "Apache Kafka", "description": "Distributed event streaming platform", "default_version": "3.7", "categories": ["messaging"], "versions": ["3.7", "3.6"], "source": "builtin"},
    {"type": "mongodb", "display_name": "MongoDB", "description": "Document-oriented NoSQL database", "default_version": "7", "categories": ["database"], "versions": ["7", "6"], "source": "builtin"},
    {"type": "elasticsearch", "display_name": "Elasticsearch", "description": "Distributed search and analytics engine", "default_version": "8", "categories": ["search", "database"], "versions": ["8", "7"], "source": "builtin"},
    {"type": "mysql", "display_name": "MySQL", "description": "Popular open-source relational database", "default_version": "8.0", "categories": ["database"], "versions": ["8.0", "5.7"], "source": "builtin"},
    {"type": "rabbitmq", "display_name": "RabbitMQ", "description": "Message broker with AMQP support", "default_version": "3.13", "categories": ["messaging"], "versions": ["3.13", "3.12"], "source": "builtin"},
    {"type": "minio", "display_name": "MinIO", "description": "S3-compatible object storage", "default_version": "latest", "categories": ["cloud", "storage"], "versions": ["latest"], "source": "builtin"},
    {"type": "prometheus", "display_name": "Prometheus", "description": "Metrics collection and alerting", "default_version": "2.53", "categories": ["monitoring"], "versions": ["2.53"], "source": "builtin"},
    {"type": "grafana", "display_name": "Grafana", "description": "Dashboarding and visualization", "default_version": "11", "categories": ["monitoring"], "versions": ["11", "10"], "source": "builtin"},
    {"type": "neo4j", "display_name": "Neo4j", "description": "Graph database for connected data", "default_version": "5", "categories": ["database"], "versions": ["5", "4.4"], "source": "builtin"},
    {"type": "cassandra", "display_name": "Apache Cassandra", "description": "Wide-column distributed database", "default_version": "4.1", "categories": ["database"], "versions": ["4.1", "4.0"], "source": "builtin"},
    {"type": "localstack", "display_name": "LocalStack", "description": "Local AWS cloud emulator", "default_version": "3", "categories": ["cloud"], "versions": ["3", "2"], "source": "builtin"},
    {"type": "jaeger", "display_name": "Jaeger", "description": "Distributed tracing backend", "default_version": "1.58", "categories": ["monitoring"], "versions": ["1.58"], "source": "builtin"},
    {"type": "nats", "display_name": "NATS", "description": "Cloud-native messaging system", "default_version": "2.10", "categories": ["messaging"], "versions": ["2.10"], "source": "builtin"},
    {"type": "jupyter", "display_name": "JupyterLab", "description": "Interactive notebook environment", "default_version": "4", "categories": ["runtime"], "versions": ["4"], "source": "builtin"},
]

_DEMO_TEMPLATES = [
    {"name": "blank", "display_name": "Blank Workspace", "description": "Empty workspace — add services manually", "category": "general", "is_builtin": True, "usage_count": 342},
    {"name": "fastapi-full-stack", "display_name": "FastAPI Full Stack", "description": "FastAPI + PostgreSQL + Redis + Kafka + MinIO + Monitoring", "category": "backend", "is_builtin": True, "usage_count": 891},
    {"name": "django-postgres-redis", "display_name": "Django + Postgres + Redis", "description": "Django web framework with database and cache", "category": "backend", "is_builtin": True, "usage_count": 567},
    {"name": "ml-platform", "display_name": "ML Platform", "description": "JupyterLab + PostgreSQL + Redis + MinIO for ML workloads", "category": "data-science", "is_builtin": True, "usage_count": 723},
    {"name": "microservices-full", "display_name": "Microservices Suite", "description": "Kafka + Redis + PostgreSQL + Jaeger + Prometheus + Grafana", "category": "backend", "is_builtin": True, "usage_count": 445},
    {"name": "data-engineering", "display_name": "Data Engineering", "description": "Kafka + ClickHouse + Redis + MinIO + Grafana pipeline", "category": "data-science", "is_builtin": True, "usage_count": 312},
    {"name": "ecommerce-full", "display_name": "E-Commerce Platform", "description": "Full e-commerce stack with search, cache, DB, and storage", "category": "backend", "is_builtin": True, "usage_count": 234},
    {"name": "spring-boot-enterprise", "display_name": "Spring Boot Enterprise", "description": "Enterprise Java stack with full observability", "category": "backend", "is_builtin": True, "usage_count": 198},
    {"name": "fintech-banking", "display_name": "Fintech / Banking", "description": "Secure fintech stack with Kafka, Cassandra, and Vault", "category": "enterprise", "is_builtin": True, "usage_count": 156},
]

_DEMO_PLUGINS = [
    {"name": "pysandbox", "version": "2.1.0", "display_name": "PySandbox", "description": "Secure code execution sandbox", "base_url": "http://pysandbox:8081", "team": "sandbox-team", "categories": ["runtime", "security"], "tools": [{"name": "sandbox_create"}, {"name": "sandbox_execute"}, {"name": "sandbox_destroy"}], "events": {"publishes": ["sandbox.created", "sandbox.completed"], "subscribes": ["workspace.destroyed"]}},
    {"name": "pygate", "version": "1.3.0", "display_name": "PyGate", "description": "AI model gateway and proxy", "base_url": "http://pygate:8443", "team": "ai-platform", "categories": ["ai", "gateway"], "tools": [{"name": "llm_complete"}, {"name": "llm_embed"}, {"name": "model_list"}], "events": {"publishes": [], "subscribes": []}},
    {"name": "pymem", "version": "0.8.0", "display_name": "PyMem", "description": "Semantic memory and RAG engine", "base_url": "http://pymem:8090", "team": "ai-platform", "categories": ["ai", "memory"], "tools": [{"name": "mem_ingest"}, {"name": "mem_search"}, {"name": "mem_context"}], "events": {"publishes": ["document.indexed"], "subscribes": ["workspace.destroyed"]}},
]

_DEMO_SNAPSHOTS = [
    {"id": "snap-001", "workspace_id": "ws-abc123", "name": "pre-migration", "type": "manual", "minio_path": "snapshots/ws-abc123/snap-001.tar.gz", "services_included": ["postgres", "redis"], "size_bytes": 524288000, "status": "ready", "created_at": (_now - timedelta(hours=6)).isoformat()},
    {"id": "snap-002", "workspace_id": "ws-abc123", "name": "auto-daily", "type": "auto", "minio_path": "snapshots/ws-abc123/snap-002.tar.gz", "services_included": ["postgres", "redis", "minio"], "size_bytes": 1073741824, "status": "ready", "created_at": (_now - timedelta(hours=1)).isoformat()},
]
