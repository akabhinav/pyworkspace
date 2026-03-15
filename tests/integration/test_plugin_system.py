"""Integration tests — validate that external plugins integrate correctly
with PyWorkspace's plugin system, event bus, tool registry, and catalog.

These tests simulate the full lifecycle:
  1. Plugin registers via manifest (file, dict, or API)
  2. PyWorkspace discovers tools and wires up event subscriptions
  3. Agent tool registry builds RemoteTool instances
  4. Event bus delivers events to plugin webhooks
  5. Plugin unregisters cleanly

Each test uses fresh registry/bus instances to avoid cross-test pollution.
"""
import asyncio
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path
import tempfile
import yaml
import json

from pyworkspace.plugins.manifest import (
    PluginManifest,
    PluginToolSpec,
    PluginServiceSpec,
    PluginEventSpec,
    PluginHealthCheck,
    PluginResourceSpec,
)
from pyworkspace.plugins.registry import PluginRegistry, PluginNotFoundError
from pyworkspace.plugins.loader import PluginLoader
from pyworkspace.events.bus import EventBus
from pyworkspace.events.types import Event, EventType
from pyworkspace.agent.tool_registry import RemoteTool
from pyworkspace.catalog.plugin_adapter import PluginServiceAdapter


# ---------------------------------------------------------------------------
# Fixtures — real manifests matching PySandbox, PyGate, PyMem
# ---------------------------------------------------------------------------

@pytest.fixture
def pysandbox_manifest():
    """PySandbox manifest — matches the real pysandbox plugin."""
    return PluginManifest(
        kind="PyWorkspacePlugin",
        name="pysandbox",
        version="1.0.0",
        display_name="PySandbox",
        description="Isolated code execution with gVisor/Firecracker",
        team="sandbox-team",
        categories=["runtime", "security"],
        base_url="http://pysandbox.internal:8080",
        api_version="v1",
        auth_type="api_key",
        service=PluginServiceSpec(
            image="yourorg/pysandbox:1.0.0",
            port=8080,
            health_check=PluginHealthCheck(endpoint="/healthz", interval_seconds=15, timeout_seconds=5),
            resources=PluginResourceSpec(cpu="1.0", memory="2Gi", disk="10Gi"),
            env={"SANDBOX_RUNTIME": "gvisor", "SANDBOX_MAX_EXECUTION_TIME": "300"},
        ),
        tools=[
            PluginToolSpec(
                name="sandbox_create",
                description="Create a new isolated sandbox environment",
                endpoint="/v1/sandbox/create",
                method="POST",
                timeout_seconds=30,
                input_schema={"type": "object", "properties": {"language": {"type": "string"}}},
            ),
            PluginToolSpec(
                name="sandbox_execute",
                description="Execute code in an existing sandbox",
                endpoint="/v1/sandbox/execute",
                method="POST",
                timeout_seconds=120,
                input_schema={"type": "object", "properties": {"sandbox_id": {"type": "string"}, "code": {"type": "string"}}, "required": ["sandbox_id", "code"]},
            ),
            PluginToolSpec(
                name="sandbox_destroy",
                description="Destroy a sandbox and cleanup resources",
                endpoint="/v1/sandbox/destroy",
                method="POST",
                timeout_seconds=10,
            ),
        ],
        events=PluginEventSpec(
            publishes=["sandbox.created", "sandbox.completed", "sandbox.failed", "sandbox.timeout"],
            subscribes=["workspace.created", "workspace.destroyed"],
            callback_url="http://pysandbox.internal:8080/webhooks/events",
        ),
    )


@pytest.fixture
def pygate_manifest():
    """PyGate manifest — standalone LLM router (no sidecar service)."""
    return PluginManifest(
        kind="PyWorkspacePlugin",
        name="pygate",
        version="1.0.0",
        display_name="PyGate",
        description="Unified LLM routing engine",
        team="ai-platform-team",
        categories=["ai", "infrastructure"],
        base_url="http://pygate.internal:8443",
        api_version="v1",
        auth_type="api_key",
        service=None,  # Standalone — no sidecar
        tools=[
            PluginToolSpec(
                name="llm_complete",
                description="Generate text completion via LLM",
                endpoint="/v1/completions",
                method="POST",
                timeout_seconds=120,
            ),
            PluginToolSpec(
                name="llm_embed",
                description="Generate text embeddings",
                endpoint="/v1/embeddings",
                method="POST",
                timeout_seconds=30,
            ),
        ],
        events=PluginEventSpec(
            publishes=["llm.completion.finished", "llm.rate_limit.hit"],
            subscribes=[],
        ),
    )


@pytest.fixture
def pymem_manifest():
    """PyMem manifest — knowledge memory with sidecar service."""
    return PluginManifest(
        kind="PyWorkspacePlugin",
        name="pymem",
        version="1.0.0",
        display_name="PyMem",
        description="Knowledge memory layer — ingest, search, RAG",
        team="knowledge-team",
        categories=["ai", "search"],
        base_url="http://pymem.internal:8090",
        api_version="v1",
        auth_type="api_key",
        service=PluginServiceSpec(
            image="yourorg/pymem:1.0.0",
            port=8090,
            resources=PluginResourceSpec(cpu="0.5", memory="1Gi", disk="5Gi"),
        ),
        tools=[
            PluginToolSpec(
                name="knowledge_ingest",
                description="Ingest document or URL into knowledge base",
                endpoint="/v1/ingest",
                method="POST",
                timeout_seconds=60,
            ),
            PluginToolSpec(
                name="knowledge_search",
                description="Semantic search across knowledge base",
                endpoint="/v1/search",
                method="POST",
                timeout_seconds=10,
            ),
            PluginToolSpec(
                name="knowledge_context",
                description="Assemble RAG context for a query",
                endpoint="/v1/context",
                method="POST",
                timeout_seconds=15,
            ),
        ],
        events=PluginEventSpec(
            publishes=["knowledge.ingested", "knowledge.index.updated"],
            subscribes=["workspace.destroyed"],
            callback_url="http://pymem.internal:8090/webhooks/events",
        ),
    )


@pytest.fixture
def fresh_registry():
    """Fresh plugin registry for each test."""
    return PluginRegistry()


@pytest.fixture
def fresh_event_bus():
    """Fresh event bus for each test."""
    return EventBus()


# ---------------------------------------------------------------------------
# 1. Plugin Registry Tests
# ---------------------------------------------------------------------------

class TestPluginRegistry:
    """Test that the plugin registry correctly manages manifests."""

    def test_register_pysandbox(self, fresh_registry, pysandbox_manifest):
        fresh_registry.register(pysandbox_manifest)
        assert fresh_registry.has_plugin("pysandbox")
        manifest = fresh_registry.get("pysandbox")
        assert manifest.name == "pysandbox"
        assert manifest.version == "1.0.0"
        assert manifest.team == "sandbox-team"

    def test_register_pygate(self, fresh_registry, pygate_manifest):
        fresh_registry.register(pygate_manifest)
        assert fresh_registry.has_plugin("pygate")
        assert fresh_registry.get("pygate").service is None  # standalone

    def test_register_pymem(self, fresh_registry, pymem_manifest):
        fresh_registry.register(pymem_manifest)
        assert fresh_registry.has_plugin("pymem")
        assert fresh_registry.get("pymem").service is not None  # sidecar

    def test_register_all_three(self, fresh_registry, pysandbox_manifest, pygate_manifest, pymem_manifest):
        fresh_registry.register(pysandbox_manifest)
        fresh_registry.register(pygate_manifest)
        fresh_registry.register(pymem_manifest)

        plugins = fresh_registry.list_plugins()
        assert len(plugins) == 3
        names = {p["name"] for p in plugins}
        assert names == {"pysandbox", "pygate", "pymem"}

    def test_tool_index_across_plugins(self, fresh_registry, pysandbox_manifest, pygate_manifest, pymem_manifest):
        """All tools from all plugins are indexed correctly."""
        fresh_registry.register(pysandbox_manifest)
        fresh_registry.register(pygate_manifest)
        fresh_registry.register(pymem_manifest)

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

        assert len(tool_names) == 8  # 3 + 2 + 3

    def test_get_tool_returns_correct_plugin(self, fresh_registry, pysandbox_manifest, pygate_manifest):
        fresh_registry.register(pysandbox_manifest)
        fresh_registry.register(pygate_manifest)

        result = fresh_registry.get_tool("sandbox_execute")
        assert result is not None
        manifest, tool_spec = result
        assert manifest.name == "pysandbox"
        assert tool_spec.endpoint == "/v1/sandbox/execute"
        assert tool_spec.timeout_seconds == 120

        result = fresh_registry.get_tool("llm_complete")
        assert result is not None
        manifest, tool_spec = result
        assert manifest.name == "pygate"
        assert tool_spec.endpoint == "/v1/completions"

    def test_get_nonexistent_tool(self, fresh_registry, pysandbox_manifest):
        fresh_registry.register(pysandbox_manifest)
        assert fresh_registry.get_tool("nonexistent_tool") is None

    def test_unregister_plugin(self, fresh_registry, pysandbox_manifest):
        fresh_registry.register(pysandbox_manifest)
        assert fresh_registry.has_plugin("pysandbox")
        assert fresh_registry.get_tool("sandbox_execute") is not None

        fresh_registry.unregister("pysandbox")
        assert not fresh_registry.has_plugin("pysandbox")
        assert fresh_registry.get_tool("sandbox_execute") is None

    def test_unregister_nonexistent_raises(self, fresh_registry):
        with pytest.raises(PluginNotFoundError):
            fresh_registry.unregister("nonexistent")

    def test_get_nonexistent_plugin_raises(self, fresh_registry):
        with pytest.raises(PluginNotFoundError, match="Plugin 'foo' not found"):
            fresh_registry.get("foo")

    def test_update_plugin_version(self, fresh_registry, pysandbox_manifest):
        fresh_registry.register(pysandbox_manifest)
        assert fresh_registry.get("pysandbox").version == "1.0.0"

        # Update with new version
        updated = PluginManifest(
            name="pysandbox",
            version="2.0.0",
            base_url="http://pysandbox.internal:8080",
            tools=pysandbox_manifest.tools,
        )
        fresh_registry.register(updated)
        assert fresh_registry.get("pysandbox").version == "2.0.0"
        assert len(fresh_registry.list_plugins()) == 1  # Not duplicated

    def test_plugins_with_service(self, fresh_registry, pysandbox_manifest, pygate_manifest, pymem_manifest):
        """Only plugins with service spec should be returned."""
        fresh_registry.register(pysandbox_manifest)
        fresh_registry.register(pygate_manifest)
        fresh_registry.register(pymem_manifest)

        sidecar_plugins = fresh_registry.get_plugins_with_service()
        names = {m.name for m in sidecar_plugins}
        assert names == {"pysandbox", "pymem"}
        assert "pygate" not in names  # standalone, no sidecar

    def test_plugins_subscribing_to_event(self, fresh_registry, pysandbox_manifest, pygate_manifest, pymem_manifest):
        fresh_registry.register(pysandbox_manifest)
        fresh_registry.register(pygate_manifest)
        fresh_registry.register(pymem_manifest)

        # workspace.created — only PySandbox subscribes
        subscribers = fresh_registry.get_plugins_subscribing_to("workspace.created")
        assert len(subscribers) == 1
        assert subscribers[0].name == "pysandbox"

        # workspace.destroyed — PySandbox + PyMem
        subscribers = fresh_registry.get_plugins_subscribing_to("workspace.destroyed")
        names = {s.name for s in subscribers}
        assert names == {"pysandbox", "pymem"}

        # No subscribers
        subscribers = fresh_registry.get_plugins_subscribing_to("llm.rate_limit.hit")
        assert len(subscribers) == 0


# ---------------------------------------------------------------------------
# 2. Plugin Loader Tests
# ---------------------------------------------------------------------------

class TestPluginLoader:
    """Test loading manifests from files, dicts, and directories."""

    def test_load_from_dict(self, fresh_registry, pysandbox_manifest):
        loader = PluginLoader(registry=fresh_registry)
        data = pysandbox_manifest.model_dump()
        manifest = loader.load_from_dict(data)
        assert manifest.name == "pysandbox"
        assert fresh_registry.has_plugin("pysandbox")

    def test_load_from_yaml_file(self, fresh_registry, pysandbox_manifest):
        loader = PluginLoader(registry=fresh_registry)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
            yaml.dump(pysandbox_manifest.model_dump(), f)
            f.flush()
            manifest = loader.load_from_file(f.name)
        assert manifest.name == "pysandbox"
        assert fresh_registry.has_plugin("pysandbox")

    def test_load_from_json_file(self, fresh_registry, pygate_manifest):
        loader = PluginLoader(registry=fresh_registry)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            json.dump(pygate_manifest.model_dump(), f)
            f.flush()
            manifest = loader.load_from_file(f.name)
        assert manifest.name == "pygate"
        assert fresh_registry.has_plugin("pygate")

    def test_load_from_directory(self, fresh_registry, pysandbox_manifest, pygate_manifest, pymem_manifest):
        loader = PluginLoader(registry=fresh_registry)

        with tempfile.TemporaryDirectory() as tmpdir:
            # Write all 3 manifests as YAML files
            for manifest in [pysandbox_manifest, pygate_manifest, pymem_manifest]:
                path = Path(tmpdir) / f"{manifest.name}.yaml"
                path.write_text(yaml.dump(manifest.model_dump()))

            manifests = loader.load_from_directory(tmpdir)

        assert len(manifests) == 3
        assert fresh_registry.has_plugin("pysandbox")
        assert fresh_registry.has_plugin("pygate")
        assert fresh_registry.has_plugin("pymem")

    def test_load_from_nonexistent_directory(self, fresh_registry):
        loader = PluginLoader(registry=fresh_registry)
        manifests = loader.load_from_directory("/nonexistent/path")
        assert manifests == []

    def test_load_from_example_manifests(self, fresh_registry):
        """Load the actual example manifests from the repo."""
        loader = PluginLoader(registry=fresh_registry)
        examples_dir = Path("/home/user/pyworkspace/examples/plugin-manifests")
        if examples_dir.is_dir():
            manifests = loader.load_from_directory(examples_dir)
            assert len(manifests) >= 3
            for m in manifests:
                assert fresh_registry.has_plugin(m.name)


# ---------------------------------------------------------------------------
# 3. Event Bus Integration Tests
# ---------------------------------------------------------------------------

class TestEventBusPluginIntegration:
    """Test event bus wiring with plugin webhook subscriptions."""

    def test_subscribe_plugin_webhooks(self, fresh_event_bus, pysandbox_manifest):
        """Subscribing webhooks from manifest wires up correctly."""
        events = pysandbox_manifest.events
        if events.callback_url:
            for event_type in events.subscribes:
                fresh_event_bus.subscribe_webhook(event_type, events.callback_url)

        # Verify internal state
        assert "http://pysandbox.internal:8080/webhooks/events" in fresh_event_bus._webhooks["workspace.created"]
        assert "http://pysandbox.internal:8080/webhooks/events" in fresh_event_bus._webhooks["workspace.destroyed"]

    def test_multiple_plugins_subscribe_to_same_event(self, fresh_event_bus, pysandbox_manifest, pymem_manifest):
        """Multiple plugins subscribing to workspace.destroyed."""
        for manifest in [pysandbox_manifest, pymem_manifest]:
            events = manifest.events
            if events.callback_url:
                for event_type in events.subscribes:
                    fresh_event_bus.subscribe_webhook(event_type, events.callback_url)

        destroyed_webhooks = fresh_event_bus._webhooks["workspace.destroyed"]
        assert len(destroyed_webhooks) == 2
        assert "http://pysandbox.internal:8080/webhooks/events" in destroyed_webhooks
        assert "http://pymem.internal:8090/webhooks/events" in destroyed_webhooks

    def test_unsubscribe_plugin_webhooks(self, fresh_event_bus, pysandbox_manifest):
        """Unsubscribing removes all webhook entries for a plugin."""
        events = pysandbox_manifest.events
        for event_type in events.subscribes:
            fresh_event_bus.subscribe_webhook(event_type, events.callback_url)

        # Unsubscribe all
        fresh_event_bus.unsubscribe_all_webhooks(events.callback_url)

        assert events.callback_url not in fresh_event_bus._webhooks.get("workspace.created", [])
        assert events.callback_url not in fresh_event_bus._webhooks.get("workspace.destroyed", [])

    @pytest.mark.asyncio
    async def test_publish_calls_in_process_handlers(self, fresh_event_bus):
        """In-process handlers are called when event published."""
        handler = AsyncMock()
        fresh_event_bus.subscribe("workspace.created", handler)

        event = Event(
            event_type=EventType.WORKSPACE_CREATED,
            source="pyworkspace",
            workspace_id="ws-test-123",
        )
        await fresh_event_bus.publish(event)

        handler.assert_called_once()
        received_event = handler.call_args[0][0]
        assert received_event.workspace_id == "ws-test-123"

    @pytest.mark.asyncio
    async def test_publish_delivers_webhooks(self, fresh_event_bus, pysandbox_manifest):
        """Webhook URLs receive POST when event published."""
        events = pysandbox_manifest.events
        for event_type in events.subscribes:
            fresh_event_bus.subscribe_webhook(event_type, events.callback_url)

        event = Event(
            event_type=EventType.WORKSPACE_CREATED,
            source="pyworkspace",
            workspace_id="ws-new-456",
        )

        with patch("pyworkspace.events.bus.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            await fresh_event_bus.publish(event)

            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://pysandbox.internal:8080/webhooks/events"
            body = call_args[1]["json"]
            assert body["event_type"] == "workspace.created"
            assert body["workspace_id"] == "ws-new-456"

    @pytest.mark.asyncio
    async def test_event_published_to_multiple_plugins(self, fresh_event_bus, pysandbox_manifest, pymem_manifest):
        """workspace.destroyed event delivered to both PySandbox and PyMem."""
        for manifest in [pysandbox_manifest, pymem_manifest]:
            events = manifest.events
            if events.callback_url:
                for event_type in events.subscribes:
                    fresh_event_bus.subscribe_webhook(event_type, events.callback_url)

        event = Event(
            event_type=EventType.WORKSPACE_DESTROYED,
            source="pyworkspace",
            workspace_id="ws-dead-789",
        )

        with patch("pyworkspace.events.bus.httpx.AsyncClient") as mock_client_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_cls.return_value = mock_client

            await fresh_event_bus.publish(event)

            # 2 webhook calls — one for each plugin
            assert mock_client.post.call_count == 2
            urls_called = {call[0][0] for call in mock_client.post.call_args_list}
            assert "http://pysandbox.internal:8080/webhooks/events" in urls_called
            assert "http://pymem.internal:8090/webhooks/events" in urls_called

    @pytest.mark.asyncio
    async def test_pygate_no_webhooks(self, fresh_event_bus, pygate_manifest):
        """PyGate subscribes to nothing — no webhooks should be wired."""
        events = pygate_manifest.events
        assert len(events.subscribes) == 0
        # No webhook wiring needed
        assert events.callback_url is None


# ---------------------------------------------------------------------------
# 4. RemoteTool Integration Tests
# ---------------------------------------------------------------------------

class TestRemoteToolIntegration:
    """Test that RemoteTool correctly wraps plugin tools for HTTP execution."""

    def test_build_remote_tool_from_manifest(self, fresh_registry, pysandbox_manifest):
        """Create RemoteTool from plugin registry."""
        fresh_registry.register(pysandbox_manifest)

        result = fresh_registry.get_tool("sandbox_execute")
        assert result is not None
        manifest, tool_spec = result

        tool = RemoteTool(
            name=tool_spec.name,
            plugin_name=manifest.name,
            base_url=manifest.base_url,
            endpoint=tool_spec.endpoint,
            method=tool_spec.method,
            timeout_seconds=tool_spec.timeout_seconds,
        )

        assert tool.name == "sandbox_execute"
        assert tool.plugin_name == "pysandbox"
        assert tool.base_url == "http://pysandbox.internal:8080"
        assert tool.endpoint == "/v1/sandbox/execute"
        assert tool.method == "POST"
        assert tool.timeout_seconds == 120

    def test_build_all_remote_tools(self, fresh_registry, pysandbox_manifest, pygate_manifest, pymem_manifest):
        """Build RemoteTool for every plugin tool across all plugins."""
        for m in [pysandbox_manifest, pygate_manifest, pymem_manifest]:
            fresh_registry.register(m)

        remote_tools = []
        for entry in fresh_registry.list_tools():
            result = fresh_registry.get_tool(entry["name"])
            if result:
                manifest, spec = result
                remote_tools.append(RemoteTool(
                    name=spec.name,
                    plugin_name=manifest.name,
                    base_url=manifest.base_url,
                    endpoint=spec.endpoint,
                    method=spec.method,
                    timeout_seconds=spec.timeout_seconds,
                ))

        assert len(remote_tools) == 8
        tool_names = {t.name for t in remote_tools}
        assert "sandbox_execute" in tool_names
        assert "llm_complete" in tool_names
        assert "knowledge_search" in tool_names

    @pytest.mark.asyncio
    async def test_remote_tool_execute_calls_http(self, fresh_registry, pygate_manifest):
        """RemoteTool.execute() makes correct HTTP call."""
        fresh_registry.register(pygate_manifest)
        result = fresh_registry.get_tool("llm_complete")
        manifest, spec = result

        tool = RemoteTool(
            name=spec.name,
            plugin_name=manifest.name,
            base_url=manifest.base_url,
            endpoint=spec.endpoint,
            method=spec.method,
            timeout_seconds=spec.timeout_seconds,
            credentials={"api_key": "test-key-123"},
        )

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"content": "Hello!", "id": "cmpl-1"}
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            result = await tool.execute(
                messages=[{"role": "user", "content": "Hello"}],
                model="claude-sonnet-4-20250514",
            )

            assert result["content"] == "Hello!"
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert call_args[0][0] == "http://pygate.internal:8443/v1/completions"
            assert call_args[1]["headers"]["Authorization"] == "Bearer test-key-123"

    @pytest.mark.asyncio
    async def test_remote_tool_without_credentials(self, fresh_registry, pygate_manifest):
        """RemoteTool works without credentials (no auth header)."""
        fresh_registry.register(pygate_manifest)
        result = fresh_registry.get_tool("llm_embed")
        manifest, spec = result

        tool = RemoteTool(
            name=spec.name,
            plugin_name=manifest.name,
            base_url=manifest.base_url,
            endpoint=spec.endpoint,
            method=spec.method,
        )

        with patch("httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"embeddings": [[0.1, 0.2]]}
            mock_response.raise_for_status = MagicMock()
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            result = await tool.execute(input="Hello")
            assert "embeddings" in result
            headers = mock_client.post.call_args[1]["headers"]
            assert "Authorization" not in headers


# ---------------------------------------------------------------------------
# 5. PluginServiceAdapter Tests
# ---------------------------------------------------------------------------

class TestPluginServiceAdapter:
    """Test that PluginServiceAdapter correctly bridges manifest → ServiceDefinition."""

    def test_adapter_basic_properties(self, pysandbox_manifest):
        adapter = PluginServiceAdapter(pysandbox_manifest)
        assert adapter.service_type == "pysandbox"
        assert adapter.display_name == "PySandbox"
        assert adapter.default_port == 8080
        assert adapter.default_version == "1.0.0"
        assert adapter.default_resources.cpu == "1.0"
        assert adapter.default_resources.memory == "2Gi"

    def test_adapter_env_vars(self, pysandbox_manifest):
        adapter = PluginServiceAdapter(pysandbox_manifest)
        env = adapter.get_env_vars("pysandbox", "ws-test.workspace.local", {}, {})
        assert env["PYSANDBOX_HOST"] == "pysandbox.ws-test.workspace.local"
        assert env["PYSANDBOX_PORT"] == "8080"
        assert "SANDBOX_RUNTIME" in env
        assert env["SANDBOX_RUNTIME"] == "gvisor"

    def test_adapter_agent_tools(self, pysandbox_manifest):
        adapter = PluginServiceAdapter(pysandbox_manifest)
        tools = adapter.get_agent_tools()
        assert set(tools) == {"sandbox_create", "sandbox_execute", "sandbox_destroy"}

    def test_adapter_health_check(self, pysandbox_manifest):
        adapter = PluginServiceAdapter(pysandbox_manifest)
        hc = adapter.get_health_check("pysandbox", "ws-test.workspace.local")
        assert hc["httpGet"]["path"] == "/healthz"
        assert hc["httpGet"]["port"] == 8080
        assert hc["periodSeconds"] == 15

    def test_adapter_generates_credentials(self, pysandbox_manifest):
        adapter = PluginServiceAdapter(pysandbox_manifest)
        creds = adapter.generate_credentials({})
        assert "api_key" in creds
        assert len(creds["api_key"]) > 20

    def test_adapter_docker_image(self, pysandbox_manifest):
        adapter = PluginServiceAdapter(pysandbox_manifest)
        image = adapter.get_docker_image()
        assert image == "yourorg/pysandbox:1.0.0"

    def test_adapter_k8s_manifests(self, pysandbox_manifest):
        """Generates valid Deployment + Service."""
        from pyworkspace.core.specs import ResourceSpec
        adapter = PluginServiceAdapter(pysandbox_manifest)

        manifests = adapter.get_k8s_manifests(
            service_name="pysandbox",
            workspace_id="ws-test-123",
            namespace="pyws-ws-test-123",
            credentials={"api_key": "test-key"},
            config={},
            resources=ResourceSpec(cpu="1.0", memory="2Gi"),
        )

        assert len(manifests) == 2

        deployment = manifests[0]
        assert deployment["kind"] == "Deployment"
        assert deployment["metadata"]["labels"]["plugin"] == "pysandbox"
        container = deployment["spec"]["template"]["spec"]["containers"][0]
        assert container["image"] == "yourorg/pysandbox:1.0.0"
        assert container["ports"][0]["containerPort"] == 8080
        # Security context
        assert container["securityContext"]["readOnlyRootFilesystem"] is True
        assert container["securityContext"]["allowPrivilegeEscalation"] is False

        service = manifests[1]
        assert service["kind"] == "Service"
        assert service["spec"]["ports"][0]["port"] == 8080

    def test_adapter_pymem_k8s_manifests(self, pymem_manifest):
        """PyMem also generates valid K8s manifests."""
        from pyworkspace.core.specs import ResourceSpec
        adapter = PluginServiceAdapter(pymem_manifest)

        manifests = adapter.get_k8s_manifests(
            service_name="pymem",
            workspace_id="ws-mem-001",
            namespace="pyws-ws-mem-001",
            credentials={"api_key": "mem-key"},
            config={},
            resources=ResourceSpec(cpu="0.5", memory="1Gi"),
        )

        assert len(manifests) == 2
        assert manifests[0]["metadata"]["labels"]["plugin"] == "pymem"
        assert manifests[0]["spec"]["template"]["spec"]["containers"][0]["image"] == "yourorg/pymem:1.0.0"

    def test_standalone_plugin_no_k8s_manifests(self, pygate_manifest):
        """PyGate (standalone) returns empty K8s manifests."""
        from pyworkspace.core.specs import ResourceSpec
        adapter = PluginServiceAdapter(pygate_manifest)
        manifests = adapter.get_k8s_manifests(
            service_name="pygate",
            workspace_id="ws-test",
            namespace="ns",
            credentials={},
            config={},
            resources=ResourceSpec(cpu="1.0", memory="2Gi"),
        )
        assert manifests == []


# ---------------------------------------------------------------------------
# 6. Full Plugin Lifecycle Test (End-to-End)
# ---------------------------------------------------------------------------

class TestPluginLifecycle:
    """End-to-end lifecycle: register → discover tools → wire events → use → unregister."""

    @pytest.mark.asyncio
    async def test_full_lifecycle(self, pysandbox_manifest, pygate_manifest, pymem_manifest):
        """Simulate the complete plugin integration lifecycle."""
        registry = PluginRegistry()
        bus = EventBus()
        loader = PluginLoader(registry=registry)

        # Step 1: Register all plugins (simulating POST /v1/plugins/register)
        for manifest in [pysandbox_manifest, pygate_manifest, pymem_manifest]:
            loader.load_from_dict(manifest.model_dump())
            if manifest.events.callback_url:
                for event_type in manifest.events.subscribes:
                    bus.subscribe_webhook(event_type, manifest.events.callback_url)

        # Verify all registered
        assert len(registry.list_plugins()) == 3

        # Step 2: Verify tool discovery
        all_tools = registry.list_tools()
        assert len(all_tools) == 8

        # Step 3: Build RemoteTools (simulating agent startup)
        remote_tools = []
        for entry in registry.list_tools():
            result = registry.get_tool(entry["name"])
            if result:
                manifest, spec = result
                remote_tools.append(RemoteTool(
                    name=spec.name,
                    plugin_name=manifest.name,
                    base_url=manifest.base_url,
                    endpoint=spec.endpoint,
                    method=spec.method,
                    timeout_seconds=spec.timeout_seconds,
                ))
        assert len(remote_tools) == 8

        # Step 4: Publish event, verify webhook delivery
        event = Event(
            event_type=EventType.WORKSPACE_CREATED,
            source="pyworkspace",
            workspace_id="ws-lifecycle-test",
        )

        with patch("pyworkspace.events.bus.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            await bus.publish(event)

            # Only PySandbox subscribes to workspace.created
            assert mock_client.post.call_count == 1
            assert "pysandbox" in mock_client.post.call_args[0][0]

        # Step 5: Unregister PySandbox
        if pysandbox_manifest.events.callback_url:
            bus.unsubscribe_all_webhooks(pysandbox_manifest.events.callback_url)
        registry.unregister("pysandbox")

        assert not registry.has_plugin("pysandbox")
        assert len(registry.list_plugins()) == 2
        assert registry.get_tool("sandbox_execute") is None
        # PyGate and PyMem tools still work
        assert registry.get_tool("llm_complete") is not None
        assert registry.get_tool("knowledge_search") is not None

        # Step 6: workspace.destroyed should now only go to PyMem
        event2 = Event(
            event_type=EventType.WORKSPACE_DESTROYED,
            source="pyworkspace",
            workspace_id="ws-lifecycle-test",
        )

        with patch("pyworkspace.events.bus.httpx.AsyncClient") as mock_cls:
            mock_client = AsyncMock()
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_client.post.return_value = mock_response
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_cls.return_value = mock_client

            await bus.publish(event2)

            # Only PyMem now (PySandbox was unregistered)
            assert mock_client.post.call_count == 1
            assert "pymem" in mock_client.post.call_args[0][0]


# ---------------------------------------------------------------------------
# 7. API Endpoint Tests (using FastAPI TestClient)
# ---------------------------------------------------------------------------

class TestPluginAPIEndpoints:
    """Test the /v1/plugins API endpoints with real plugin manifests."""

    @pytest.fixture(autouse=True)
    def reset_global_registry(self):
        """Reset global plugin registry before each test."""
        from pyworkspace.plugins.registry import plugin_registry
        # Clear all plugins
        names = [p["name"] for p in plugin_registry.list_plugins()]
        for name in names:
            try:
                plugin_registry.unregister(name)
            except Exception:
                pass
        yield
        # Cleanup after test
        names = [p["name"] for p in plugin_registry.list_plugins()]
        for name in names:
            try:
                plugin_registry.unregister(name)
            except Exception:
                pass

    @pytest.fixture
    def api_client(self):
        from fastapi.testclient import TestClient
        from pyworkspace.main import app
        return TestClient(app)

    def test_register_plugin_via_api(self, api_client, pysandbox_manifest):
        response = api_client.post(
            "/v1/plugins/register",
            json=pysandbox_manifest.model_dump(),
        )
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "registered"
        assert data["plugin"] == "pysandbox"
        assert data["service_available"] is True
        assert "sandbox_execute" in data["tools"]

    def test_list_plugins_via_api(self, api_client, pysandbox_manifest, pygate_manifest):
        api_client.post("/v1/plugins/register", json=pysandbox_manifest.model_dump())
        api_client.post("/v1/plugins/register", json=pygate_manifest.model_dump())

        response = api_client.get("/v1/plugins")
        assert response.status_code == 200
        plugins = response.json()
        assert len(plugins) == 2
        names = {p["name"] for p in plugins}
        assert names == {"pysandbox", "pygate"}

    def test_get_plugin_details_via_api(self, api_client, pymem_manifest):
        api_client.post("/v1/plugins/register", json=pymem_manifest.model_dump())

        response = api_client.get("/v1/plugins/pymem")
        assert response.status_code == 200
        data = response.json()
        assert data["name"] == "pymem"
        assert data["version"] == "1.0.0"

    def test_get_plugin_tools_via_api(self, api_client, pysandbox_manifest):
        api_client.post("/v1/plugins/register", json=pysandbox_manifest.model_dump())

        response = api_client.get("/v1/plugins/pysandbox/tools")
        assert response.status_code == 200
        tools = response.json()
        assert len(tools) == 3
        names = {t["name"] for t in tools}
        assert "sandbox_execute" in names

    def test_unregister_plugin_via_api(self, api_client, pygate_manifest):
        api_client.post("/v1/plugins/register", json=pygate_manifest.model_dump())

        response = api_client.delete("/v1/plugins/pygate")
        assert response.status_code == 200
        assert response.json()["status"] == "unregistered"

        response = api_client.get("/v1/plugins/pygate")
        assert response.status_code == 404

    def test_unregister_nonexistent_plugin(self, api_client):
        response = api_client.delete("/v1/plugins/nonexistent")
        assert response.status_code == 404

    def test_register_all_three_via_api(self, api_client, pysandbox_manifest, pygate_manifest, pymem_manifest):
        """Register all 3 plugins and verify full integration."""
        for manifest in [pysandbox_manifest, pygate_manifest, pymem_manifest]:
            response = api_client.post("/v1/plugins/register", json=manifest.model_dump())
            assert response.status_code == 201

        response = api_client.get("/v1/plugins")
        assert len(response.json()) == 3

        # Check each plugin's tools
        for name, expected_tools in [
            ("pysandbox", ["sandbox_create", "sandbox_execute", "sandbox_destroy"]),
            ("pygate", ["llm_complete", "llm_embed"]),
            ("pymem", ["knowledge_ingest", "knowledge_search", "knowledge_context"]),
        ]:
            response = api_client.get(f"/v1/plugins/{name}/tools")
            tool_names = {t["name"] for t in response.json()}
            assert tool_names == set(expected_tools), f"Mismatch for {name}"
