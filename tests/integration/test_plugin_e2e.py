"""End-to-end integration tests — pyworkspace with real plugin packages.

These tests import the actual plugin FastAPI apps from the external repos
(plugin-pysandbox, plugin-pygate, plugin-pymem) and validate that
pyworkspace's plugin system integrates correctly with them.

Prerequisites:
    pip install "pyworkspace[plugins]"
    # or individually:
    pip install git+https://github.com/akabhinav/plugin-pysandbox.git@main#subdirectory=pysandbox
    pip install git+https://github.com/akabhinav/plugin-pygate.git@main#subdirectory=pygate
    pip install git+https://github.com/akabhinav/plugin-pymem.git@main#subdirectory=pymem
"""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock

# Skip entire module if plugin packages are not installed
pysandbox = pytest.importorskip("pysandbox", reason="pysandbox package not installed")
pygate = pytest.importorskip("pygate", reason="pygate package not installed")
pymem = pytest.importorskip("pymem", reason="pymem package not installed")

from httpx import ASGITransport, AsyncClient

from pysandbox.main import app as pysandbox_app
from pygate.main import app as pygate_app
from pymem.main import app as pymem_app

from pyworkspace.plugins.manifest import PluginManifest
from pyworkspace.plugins.registry import PluginRegistry
from pyworkspace.plugins.loader import PluginLoader
from pyworkspace.events.bus import EventBus
from pyworkspace.events.types import Event, EventType
from pyworkspace.agent.tool_registry import RemoteTool
from pyworkspace.catalog.plugin_adapter import PluginServiceAdapter


# ---------------------------------------------------------------------------
# Fixtures — real plugin TestClients
# ---------------------------------------------------------------------------


@pytest.fixture
def sandbox_client():
    """TestClient for the real PySandbox FastAPI app."""
    from fastapi.testclient import TestClient

    return TestClient(pysandbox_app)


@pytest.fixture
def gate_client():
    """TestClient for the real PyGate FastAPI app."""
    from fastapi.testclient import TestClient

    return TestClient(pygate_app)


@pytest.fixture
def mem_client():
    """TestClient for the real PyMem FastAPI app."""
    from fastapi.testclient import TestClient

    return TestClient(pymem_app)


@pytest.fixture
def fresh_registry():
    return PluginRegistry()


@pytest.fixture
def fresh_event_bus():
    return EventBus()


# ---------------------------------------------------------------------------
# 1. Plugin Health Checks — verify each plugin app boots and responds
# ---------------------------------------------------------------------------


class TestPluginHealthChecks:
    """Verify each plugin's FastAPI app is importable and responds to health."""

    def test_pysandbox_healthz(self, sandbox_client):
        resp = sandbox_client.get("/healthz")
        assert resp.status_code == 200
        assert resp.json()["status"] == "ok"

    def test_pygate_health(self, gate_client):
        resp = gate_client.get("/health")
        assert resp.status_code == 200

    def test_pymem_docs(self, mem_client):
        """PyMem app is reachable — check the OpenAPI docs endpoint."""
        resp = mem_client.get("/openapi.json")
        assert resp.status_code == 200
        assert resp.json()["info"]["title"] == "PyMem"


# ---------------------------------------------------------------------------
# 2. Plugin Manifest Discovery — fetch manifest from each plugin
# ---------------------------------------------------------------------------


class TestManifestDiscovery:
    """Validate that each plugin exposes a /plugin/manifest endpoint
    that pyworkspace's PluginLoader can consume."""

    def test_pysandbox_manifest_endpoint(self, sandbox_client):
        resp = sandbox_client.get("/plugin/manifest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "pysandbox"
        assert len(data["tools"]) == 3
        tool_names = {t["name"] for t in data["tools"]}
        assert "sandbox_create" in tool_names
        assert "sandbox_execute" in tool_names
        assert "sandbox_destroy" in tool_names

    def test_pygate_manifest_endpoint(self, gate_client):
        resp = gate_client.get("/plugin/manifest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "pygate"
        assert len(data["tools"]) == 2

    def test_pymem_manifest_endpoint(self, mem_client):
        resp = mem_client.get("/plugin/manifest")
        assert resp.status_code == 200
        data = resp.json()
        assert data["name"] == "pymem"
        assert len(data["tools"]) == 3
        tool_names = {t["name"] for t in data["tools"]}
        assert "knowledge_ingest" in tool_names
        assert "knowledge_search" in tool_names
        assert "knowledge_context" in tool_names


# ---------------------------------------------------------------------------
# 3. PySandbox E2E — create, execute, list, destroy
# ---------------------------------------------------------------------------


class TestPySandboxE2E:
    """Test the full PySandbox lifecycle via its real FastAPI app."""

    AUTH = {"Authorization": "Bearer sandbox-dev-key"}

    def test_create_and_execute_sandbox(self, sandbox_client):
        # Create
        resp = sandbox_client.post(
            "/v1/sandbox/create",
            json={"language": "python", "timeout_seconds": 60, "memory_mb": 256},
            headers=self.AUTH,
        )
        assert resp.status_code == 200
        data = resp.json()
        sandbox_id = data["sandbox_id"]
        assert data["status"] == "running"

        # Execute
        resp = sandbox_client.post(
            "/v1/sandbox/execute",
            json={"sandbox_id": sandbox_id, "code": "print('hello world')"},
            headers=self.AUTH,
        )
        assert resp.status_code == 200
        result = resp.json()
        assert result["sandbox_id"] == sandbox_id
        assert "hello world" in result["stdout"]
        assert result["exit_code"] == 0

    def test_list_sandboxes(self, sandbox_client):
        # Create one first
        sandbox_client.post(
            "/v1/sandbox/create",
            json={"language": "python"},
            headers=self.AUTH,
        )
        resp = sandbox_client.get("/v1/sandbox/list", headers=self.AUTH)
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["sandboxes"]) >= 1

    def test_destroy_sandbox(self, sandbox_client):
        # Create
        resp = sandbox_client.post(
            "/v1/sandbox/create",
            json={"language": "python"},
            headers=self.AUTH,
        )
        sandbox_id = resp.json()["sandbox_id"]

        # Destroy
        resp = sandbox_client.post(
            "/v1/sandbox/destroy",
            json={"sandbox_id": sandbox_id},
            headers=self.AUTH,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "destroyed"

    def test_auth_required(self, sandbox_client):
        resp = sandbox_client.post(
            "/v1/sandbox/create",
            json={"language": "python"},
        )
        assert resp.status_code in (401, 422)

    def test_webhook_workspace_destroyed(self, sandbox_client):
        """PySandbox handles workspace.destroyed webhook."""
        resp = sandbox_client.post(
            "/webhooks/events",
            json={
                "event_type": "workspace.destroyed",
                "workspace_id": "ws-e2e-test",
            },
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "received"


# ---------------------------------------------------------------------------
# 4. PyGate E2E — completions, embeddings, models
# ---------------------------------------------------------------------------


class TestPyGateE2E:
    """Test the full PyGate lifecycle via its real FastAPI app."""

    AUTH = {"Authorization": "Bearer pygate-dev-key"}

    def test_list_models(self, gate_client):
        resp = gate_client.get("/v1/models", headers=self.AUTH)
        assert resp.status_code == 200
        models = resp.json()
        assert isinstance(models, list)
        assert len(models) > 0

    def test_completion(self, gate_client):
        resp = gate_client.post(
            "/v1/completions",
            json={
                "model": "claude-sonnet-4-20250514",
                "messages": [{"role": "user", "content": "test"}],
                "max_tokens": 100,
            },
            headers=self.AUTH,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "content" in data
        assert "id" in data
        assert data["provider"] == "anthropic"

    def test_embedding(self, gate_client):
        resp = gate_client.post(
            "/v1/embeddings",
            json={"model": "echo", "input": "test embedding"},
            headers=self.AUTH,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "embeddings" in data

    def test_auth_required(self, gate_client):
        resp = gate_client.post(
            "/v1/completions",
            json={"model": "echo", "messages": [{"role": "user", "content": "hi"}]},
        )
        assert resp.status_code in (401, 422)


# ---------------------------------------------------------------------------
# 5. PyMem E2E — ingest, search, context, documents
# ---------------------------------------------------------------------------


class TestPyMemE2E:
    """Test the full PyMem lifecycle via its real FastAPI app."""

    AUTH = {"Authorization": "Bearer pymem-dev-key"}

    def test_ingest_and_search(self, mem_client):
        # Ingest
        resp = mem_client.post(
            "/v1/ingest",
            json={
                "content": "Python is a high-level programming language known for readability.",
                "source": "test",
                "metadata": {"topic": "programming"},
            },
            headers=self.AUTH,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["status"] == "ingested"
        assert data["chunks_created"] >= 1

        # Search
        resp = mem_client.post(
            "/v1/search",
            json={"query": "Python programming", "top_k": 5},
            headers=self.AUTH,
        )
        assert resp.status_code == 200
        results = resp.json()
        assert results["total_results"] >= 1
        assert len(results["results"]) >= 1

    def test_context_assembly(self, mem_client):
        # Ingest first
        mem_client.post(
            "/v1/ingest",
            json={"content": "FastAPI is a modern web framework for building APIs with Python."},
            headers=self.AUTH,
        )

        # Assemble context
        resp = mem_client.post(
            "/v1/context",
            json={"query": "FastAPI web framework", "max_tokens": 1000},
            headers=self.AUTH,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "context" in data
        assert len(data["context"]) > 0

    def test_list_documents(self, mem_client):
        resp = mem_client.get("/v1/documents", headers=self.AUTH)
        assert resp.status_code == 200
        assert isinstance(resp.json(), list)

    def test_webhook_workspace_destroyed(self, mem_client):
        """PyMem handles workspace.destroyed webhook."""
        resp = mem_client.post(
            "/webhooks/events",
            json={
                "event_type": "workspace.destroyed",
                "workspace_id": "ws-mem-e2e",
            },
        )
        assert resp.status_code == 200


# ---------------------------------------------------------------------------
# 6. Cross-Plugin Integration — pyworkspace registry with real manifests
# ---------------------------------------------------------------------------


class TestCrossPluginIntegration:
    """Register all 3 real plugin manifests into pyworkspace's registry
    and validate tool discovery, event wiring, and service adaptation."""

    @pytest.fixture
    def real_manifests(self, sandbox_client, gate_client, mem_client):
        """Fetch manifests from real plugin apps and normalize for pyworkspace."""
        manifests = {}
        for name, client in [
            ("pysandbox", sandbox_client),
            ("pygate", gate_client),
            ("pymem", mem_client),
        ]:
            resp = client.get("/plugin/manifest")
            data = resp.json()
            # Normalize — ensure required fields for PluginManifest
            data.setdefault("kind", "PyWorkspacePlugin")
            data.setdefault("base_url", f"http://{name}.internal:8080")
            data.setdefault("api_version", "v1")
            data.setdefault("auth_type", "api_key")
            data.setdefault("events", {"publishes": [], "subscribes": []})
            data.setdefault("tools", [])
            data.setdefault("depends_on", [])
            # Normalize tool specs — ensure each tool has required fields
            for tool in data["tools"]:
                if "endpoint" in tool and isinstance(tool["endpoint"], str) and " " in tool["endpoint"]:
                    # Handle "POST /v1/completions" format
                    parts = tool["endpoint"].split(" ", 1)
                    tool["method"] = parts[0]
                    tool["endpoint"] = parts[1]
                tool.setdefault("method", "POST")
                tool.setdefault("timeout_seconds", 30)
            manifests[name] = data
        return manifests

    def test_register_all_real_plugins(self, fresh_registry, real_manifests):
        """All 3 real plugin manifests can be loaded into pyworkspace registry."""
        loader = PluginLoader(registry=fresh_registry)
        for name, data in real_manifests.items():
            loader.load_from_dict(data)
            assert fresh_registry.has_plugin(name)

        plugins = fresh_registry.list_plugins()
        assert len(plugins) == 3

    def test_tool_discovery_across_real_plugins(self, fresh_registry, real_manifests):
        """All tools from real plugins are indexed correctly."""
        loader = PluginLoader(registry=fresh_registry)
        for data in real_manifests.values():
            loader.load_from_dict(data)

        tools = fresh_registry.list_tools()
        tool_names = {t["name"] for t in tools}

        # PySandbox tools
        assert "sandbox_create" in tool_names
        assert "sandbox_execute" in tool_names
        assert "sandbox_destroy" in tool_names

        # PyGate tools
        assert "llm_complete" in tool_names
        assert "llm_embed" in tool_names

        # PyMem tools
        assert "knowledge_ingest" in tool_names
        assert "knowledge_search" in tool_names
        assert "knowledge_context" in tool_names

        assert len(tool_names) == 8

    def test_build_remote_tools_from_real_plugins(self, fresh_registry, real_manifests):
        """Build RemoteTool instances from real plugin manifests."""
        loader = PluginLoader(registry=fresh_registry)
        for data in real_manifests.values():
            loader.load_from_dict(data)

        remote_tools = []
        for entry in fresh_registry.list_tools():
            result = fresh_registry.get_tool(entry["name"])
            if result:
                manifest, spec = result
                remote_tools.append(
                    RemoteTool(
                        name=spec.name,
                        plugin_name=manifest.name,
                        base_url=manifest.base_url,
                        endpoint=spec.endpoint,
                        method=spec.method,
                        timeout_seconds=spec.timeout_seconds,
                    )
                )

        assert len(remote_tools) == 8

        # Verify a specific tool's endpoint
        sandbox_exec = next(t for t in remote_tools if t.name == "sandbox_execute")
        assert sandbox_exec.endpoint == "/v1/sandbox/execute"
        assert sandbox_exec.method == "POST"

    def test_event_wiring_from_real_manifests(self, fresh_registry, fresh_event_bus, real_manifests):
        """Wire event subscriptions from real manifest data."""
        loader = PluginLoader(registry=fresh_registry)
        for data in real_manifests.values():
            manifest = loader.load_from_dict(data)
            if manifest.events.callback_url:
                for event_type in manifest.events.subscribes:
                    fresh_event_bus.subscribe_webhook(event_type, manifest.events.callback_url)

        # PySandbox subscribes to workspace.created and workspace.destroyed
        pysandbox = fresh_registry.get("pysandbox")
        if "workspace.created" in pysandbox.events.subscribes:
            assert pysandbox.events.callback_url is not None

    def test_register_via_pyworkspace_api(self, real_manifests):
        """Register real plugin manifests via pyworkspace's /v1/plugins API."""
        from pyworkspace.plugins.registry import plugin_registry

        # Clear global registry
        names = [p["name"] for p in plugin_registry.list_plugins()]
        for name in names:
            try:
                plugin_registry.unregister(name)
            except Exception:
                pass

        from fastapi.testclient import TestClient
        from pyworkspace.main import app

        client = TestClient(app)

        try:
            for name, data in real_manifests.items():
                resp = client.post("/v1/plugins/register", json=data)
                assert resp.status_code == 201, f"Failed to register {name}: {resp.json()}"
                assert resp.json()["plugin"] == name

            # Verify all registered
            resp = client.get("/v1/plugins")
            assert resp.status_code == 200
            registered_names = {p["name"] for p in resp.json()}
            assert registered_names == {"pysandbox", "pygate", "pymem"}

            # Verify tools discoverable
            for name, expected_count in [("pysandbox", 3), ("pygate", 2), ("pymem", 3)]:
                resp = client.get(f"/v1/plugins/{name}/tools")
                assert resp.status_code == 200
                assert len(resp.json()) == expected_count
        finally:
            # Cleanup
            for name in ["pysandbox", "pygate", "pymem"]:
                try:
                    plugin_registry.unregister(name)
                except Exception:
                    pass


# ---------------------------------------------------------------------------
# 7. Full Lifecycle E2E — register, use plugin, publish event
# ---------------------------------------------------------------------------


class TestFullLifecycleE2E:
    """End-to-end: register real plugins → use tools → deliver events → unregister."""

    AUTH_SANDBOX = {"Authorization": "Bearer sandbox-dev-key"}
    AUTH_MEM = {"Authorization": "Bearer pymem-dev-key"}

    def test_register_use_unregister(self, sandbox_client, mem_client, fresh_registry, fresh_event_bus):
        """Full lifecycle with real PySandbox and PyMem."""
        loader = PluginLoader(registry=fresh_registry)

        # Fetch and register manifests from real plugin apps
        for name, client in [("pysandbox", sandbox_client), ("pymem", mem_client)]:
            resp = client.get("/plugin/manifest")
            data = resp.json()
            data.setdefault("kind", "PyWorkspacePlugin")
            data.setdefault("base_url", f"http://{name}.internal:8080")
            data.setdefault("api_version", "v1")
            data.setdefault("auth_type", "api_key")
            data.setdefault("events", {"publishes": [], "subscribes": []})
            data.setdefault("depends_on", [])
            for tool in data.get("tools", []):
                if "endpoint" in tool and isinstance(tool["endpoint"], str) and " " in tool["endpoint"]:
                    parts = tool["endpoint"].split(" ", 1)
                    tool["method"] = parts[0]
                    tool["endpoint"] = parts[1]
                tool.setdefault("method", "POST")
                tool.setdefault("timeout_seconds", 30)
            manifest = loader.load_from_dict(data)
            if manifest.events.callback_url:
                for et in manifest.events.subscribes:
                    fresh_event_bus.subscribe_webhook(et, manifest.events.callback_url)

        assert fresh_registry.has_plugin("pysandbox")
        assert fresh_registry.has_plugin("pymem")

        # Use PySandbox — create and execute
        resp = sandbox_client.post(
            "/v1/sandbox/create",
            json={"language": "python"},
            headers=self.AUTH_SANDBOX,
        )
        assert resp.status_code == 200
        sandbox_id = resp.json()["sandbox_id"]

        resp = sandbox_client.post(
            "/v1/sandbox/execute",
            json={"sandbox_id": sandbox_id, "code": "print('hello from lifecycle')"},
            headers=self.AUTH_SANDBOX,
        )
        assert resp.status_code == 200
        assert "hello from lifecycle" in resp.json()["stdout"]

        # Use PyMem — ingest
        resp = mem_client.post(
            "/v1/ingest",
            json={"content": "End-to-end test document for lifecycle validation."},
            headers=self.AUTH_MEM,
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "ingested"

        # Unregister PySandbox
        fresh_registry.unregister("pysandbox")
        assert not fresh_registry.has_plugin("pysandbox")
        assert fresh_registry.has_plugin("pymem")

        # PyMem tools still accessible
        assert fresh_registry.get_tool("knowledge_search") is not None
        # PySandbox tools gone
        assert fresh_registry.get_tool("sandbox_execute") is None
