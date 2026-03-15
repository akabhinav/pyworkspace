"""Auto-register agent tools per provisioned service."""
from __future__ import annotations
from dataclasses import dataclass, field
from typing import Any, Callable

_tool_registry: dict[str, Callable] = {}

def register_tool(name: str):
    """Decorator to register an agent tool implementation."""
    def decorator(fn: Callable) -> Callable:
        _tool_registry[name] = fn
        return fn
    return decorator

def get_tool(name: str) -> Callable | None:
    return _tool_registry.get(name)

def list_tools() -> list[str]:
    return list(_tool_registry.keys())

@dataclass
class ConfiguredTool:
    """A tool bound to a specific service instance."""
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

async def build_tool_registry(services: list[dict]) -> list[ConfiguredTool]:
    """Build configured tools for all healthy services."""
    from pyworkspace.catalog import get_service_definition

    tools: list[ConfiguredTool] = []

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
            impl = get_tool(tool_name)
            if impl:
                tools.append(ConfiguredTool(
                    name=tool_name,
                    host=service.get("internal_dns", ""),
                    port=service.get("internal_port", 0),
                    credentials=service.get("credentials", {}),
                    implementation=impl,
                ))

    return tools
