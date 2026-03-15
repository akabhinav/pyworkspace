"""Agent tool registry — combines compile-time tools with runtime plugin tools.

Built-in tools (postgres_tools, redis_tools, etc.) are registered via @register_tool.
Plugin tools are discovered at runtime from the plugin registry and invoked via HTTP.
The agent doesn't need to know the difference — both implement the same interface.
"""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

import structlog

logger = structlog.get_logger()

_tool_registry: dict[str, Callable] = {}

def register_tool(name: str):
    """Decorator to register an agent tool implementation (compile-time, in-process)."""
    def decorator(fn: Callable) -> Callable:
        _tool_registry[name] = fn
        return fn
    return decorator

def get_tool(name: str) -> Callable | None:
    return _tool_registry.get(name)

def list_tools() -> list[str]:
    """List all tool names (built-in + plugin-provided)."""
    names = list(_tool_registry.keys())
    try:
        from pyworkspace.plugins.registry import plugin_registry
        for entry in plugin_registry.list_tools():
            if entry["name"] not in names:
                names.append(entry["name"])
    except ImportError:
        pass
    return names


@dataclass
class ConfiguredTool:
    """A tool bound to a specific service instance (in-process execution)."""
    name: str
    host: str
    port: int
    credentials: dict[str, str]
    implementation: Callable

    async def execute(self, **kwargs: Any) -> Any:
        return await self.implementation(
            host=self.host,
            port=self.port,
            credentials=self.credentials,
            **kwargs,
        )


@dataclass
class RemoteTool:
    """A tool provided by an external plugin, invoked via HTTP.

    This is the key to loose coupling: plugin teams define tools in their
    manifest, PyOz agent calls them via HTTP. No code import needed.
    """
    name: str
    plugin_name: str
    base_url: str
    endpoint: str
    method: str = "POST"
    timeout_seconds: int = 30
    credentials: dict[str, str] = field(default_factory=dict)

    async def execute(self, **kwargs: Any) -> Any:
        import httpx

        url = f"{self.base_url.rstrip('/')}{self.endpoint}"
        headers = {"Content-Type": "application/json"}

        # Pass credentials as auth header if available
        if api_key := self.credentials.get("api_key"):
            headers["Authorization"] = f"Bearer {api_key}"

        async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
            if self.method == "POST":
                response = await client.post(url, json=kwargs, headers=headers)
            else:
                response = await client.get(url, params=kwargs, headers=headers)

            response.raise_for_status()
            return response.json()


async def build_tool_registry(services: list[dict]) -> list[ConfiguredTool | RemoteTool]:
    """Build configured tools for all healthy services.

    Combines:
      1. Built-in tools (in-process, from @register_tool)
      2. Plugin tools (HTTP, from plugin manifests)
    """
    from pyworkspace.catalog import get_service_definition

    tools: list[ConfiguredTool | RemoteTool] = []
    seen_tools: set[str] = set()

    # 1. Built-in tools from compile-time registry
    for service in services:
        if service.get("status") not in ("healthy", "starting"):
            continue

        svc_type = service.get("service_type", "")
        try:
            definition = get_service_definition(svc_type)
        except Exception:
            continue

        tool_names = definition.get_agent_tools()
        for tool_name in tool_names:
            if tool_name in seen_tools:
                continue

            # Try built-in implementation first
            impl = get_tool(tool_name)
            if impl:
                tools.append(ConfiguredTool(
                    name=tool_name,
                    host=service.get("internal_dns", ""),
                    port=service.get("internal_port", 0),
                    credentials=service.get("credentials", {}),
                    implementation=impl,
                ))
                seen_tools.add(tool_name)
                continue

            # Fall back to plugin-provided remote tool
            try:
                from pyworkspace.plugins.registry import plugin_registry
                result = plugin_registry.get_tool(tool_name)
                if result:
                    manifest, tool_spec = result
                    tools.append(RemoteTool(
                        name=tool_name,
                        plugin_name=manifest.name,
                        base_url=manifest.base_url,
                        endpoint=tool_spec.endpoint,
                        method=tool_spec.method,
                        timeout_seconds=tool_spec.timeout_seconds,
                        credentials=service.get("credentials", {}),
                    ))
                    seen_tools.add(tool_name)
            except ImportError:
                pass

    # 2. Plugin-only tools (not tied to a workspace service)
    try:
        from pyworkspace.plugins.registry import plugin_registry
        for entry in plugin_registry.list_tools():
            tool_name = entry["name"]
            if tool_name in seen_tools:
                continue
            result = plugin_registry.get_tool(tool_name)
            if result:
                manifest, tool_spec = result
                tools.append(RemoteTool(
                    name=tool_name,
                    plugin_name=manifest.name,
                    base_url=manifest.base_url,
                    endpoint=tool_spec.endpoint,
                    method=tool_spec.method,
                    timeout_seconds=tool_spec.timeout_seconds,
                ))
                seen_tools.add(tool_name)
    except ImportError:
        pass

    logger.info(
        "tool_registry_built",
        builtin_count=sum(1 for t in tools if isinstance(t, ConfiguredTool)),
        remote_count=sum(1 for t in tools if isinstance(t, RemoteTool)),
    )

    return tools
