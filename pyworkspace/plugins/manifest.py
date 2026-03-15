"""Plugin manifest schema — the contract between PyWorkspace and external components.

Each external component (PyGate, PySandbox, PyMem, PyTrace, PyTool, PyReview, etc.)
publishes a manifest describing what it provides. PyWorkspace discovers and loads
these at runtime. Teams own their own manifests — no code imports across repos.

Manifest can be loaded from:
  - YAML/JSON files on disk (local dev, mounted ConfigMaps)
  - HTTP endpoint (component self-describes at GET /plugin/manifest)
  - Plugin registry API (central catalog)
"""

from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


class PluginHealthCheck(BaseModel):
    """How PyWorkspace checks if the plugin is alive."""
    endpoint: str = "/healthz"
    interval_seconds: int = 30
    timeout_seconds: int = 5


class PluginResourceSpec(BaseModel):
    """Resource requirements when running as a workspace sidecar."""
    cpu: str = "0.5"
    memory: str = "512Mi"
    disk: str = "1Gi"


class PluginToolSpec(BaseModel):
    """A tool this plugin exposes for the PyOz agent to call.

    Tools are invoked via HTTP — the agent sends a POST to the plugin's
    endpoint with the tool parameters. No code import needed.
    """
    name: str
    description: str
    endpoint: str  # e.g., "/v1/tools/sql_query"
    method: Literal["POST", "GET"] = "POST"
    input_schema: dict[str, Any] = Field(default_factory=dict)
    output_schema: dict[str, Any] = Field(default_factory=dict)
    requires_auth: bool = True
    timeout_seconds: int = 30


class PluginServiceSpec(BaseModel):
    """If the plugin can run as a workspace service (sidecar/pod)."""
    image: str  # e.g., "yourorg/pysandbox:2.1.0"
    port: int
    health_check: PluginHealthCheck = Field(default_factory=PluginHealthCheck)
    resources: PluginResourceSpec = Field(default_factory=PluginResourceSpec)
    env: dict[str, str] = Field(default_factory=dict)
    volumes: list[dict[str, Any]] = Field(default_factory=list)
    security_context: dict[str, Any] = Field(default_factory=lambda: {
        "runAsUser": 1000,
        "readOnlyRootFilesystem": True,
        "allowPrivilegeEscalation": False,
    })


class PluginEventSpec(BaseModel):
    """Events this plugin publishes or subscribes to."""
    publishes: list[str] = Field(default_factory=list)
    subscribes: list[str] = Field(default_factory=list)
    callback_url: str | None = None  # webhook for event delivery


class PluginManifest(BaseModel):
    """The contract a plugin publishes for PyWorkspace to discover.

    Example YAML:
        kind: PyWorkspacePlugin
        metadata:
          name: pysandbox
          version: 2.1.0
          team: sandbox-team
        api:
          base_url: http://pysandbox.internal:8080
        service:
          image: yourorg/pysandbox:2.1.0
          port: 8080
        tools:
          - name: sandbox_execute
            endpoint: /v1/sandbox/execute
            ...
        events:
          publishes: [sandbox.completed, sandbox.failed]
          subscribes: [workspace.created]
        depends_on: []
    """
    # Identity
    kind: str = "PyWorkspacePlugin"
    name: str
    version: str = "0.0.0"
    display_name: str = ""
    description: str = ""
    team: str = ""
    categories: list[str] = Field(default_factory=list)

    # API contract — how to reach this plugin
    base_url: str  # e.g., "http://pysandbox.internal:8080"
    api_version: str = "v1"
    auth_type: Literal["api_key", "mtls", "jwt", "none"] = "api_key"

    # Optional: run as workspace sidecar
    service: PluginServiceSpec | None = None

    # Tools exposed to PyOz agent
    tools: list[PluginToolSpec] = Field(default_factory=list)

    # Event integration
    events: PluginEventSpec = Field(default_factory=PluginEventSpec)

    # Dependencies on other plugins
    depends_on: list[str] = Field(default_factory=list)

    # Plugin-specific config passed at registration
    config: dict[str, Any] = Field(default_factory=dict)

    @property
    def tool_names(self) -> list[str]:
        return [t.name for t in self.tools]
