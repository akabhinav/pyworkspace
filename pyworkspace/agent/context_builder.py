"""Build agent context from workspace state — the agent's view of the world."""
from __future__ import annotations
from dataclasses import dataclass, field

@dataclass
class AgentTool:
    name: str
    description: str
    service_name: str
    service_type: str

@dataclass
class AgentWorkspaceContext:
    workspace_id: str
    workspace_name: str
    dns_zone: str
    environment: dict[str, str]
    available_tools: list[AgentTool]
    services_summary: str
    workspace_root: str = "/workspace"
    service_health: dict[str, bool] = field(default_factory=dict)

class ContextBuilder:
    """Builds the complete agent context from workspace state."""

    @staticmethod
    def build(
        workspace_id: str,
        workspace_name: str,
        dns_zone: str,
        services: list[dict],
    ) -> AgentWorkspaceContext:
        environment: dict[str, str] = {}
        tools: list[AgentTool] = []
        service_lines: list[str] = []
        health: dict[str, bool] = {}

        for svc in services:
            svc_name = svc.get("service_name", "")
            svc_type = svc.get("service_type", "")
            svc_dns = svc.get("internal_dns", "")
            svc_port = svc.get("internal_port", 0)

            # Merge env vars
            for k, v in svc.get("env_vars", {}).items():
                environment[k] = str(v)

            # Register tools
            for tool_name in svc.get("agent_tools", []):
                tools.append(AgentTool(
                    name=tool_name,
                    description=f"{tool_name} for {svc_type}",
                    service_name=svc_name,
                    service_type=svc_type,
                ))

            # Build summary line
            tool_names = ", ".join(svc.get("agent_tools", [])[:5])
            if len(svc.get("agent_tools", [])) > 5:
                tool_names += ", ..."
            service_lines.append(
                f"- {svc_type.title()} at {svc_dns}:{svc_port}\n"
                f"  Tools: {tool_names}"
            )

            health[svc_name] = svc.get("status") == "healthy"

        summary = ContextBuilder._build_system_prompt(
            workspace_name, workspace_id, dns_zone, service_lines
        )

        return AgentWorkspaceContext(
            workspace_id=workspace_id,
            workspace_name=workspace_name,
            dns_zone=dns_zone,
            environment=environment,
            available_tools=tools,
            services_summary=summary,
            service_health=health,
        )

    @staticmethod
    def _build_system_prompt(
        workspace_name: str,
        workspace_id: str,
        dns_zone: str,
        service_lines: list[str],
    ) -> str:
        services_block = "\n".join(service_lines) if service_lines else "No services provisioned."
        return (
            f"You are PyOz, an autonomous software engineering agent running inside "
            f"a PyWorkspace enterprise development environment.\n\n"
            f"WORKSPACE: {workspace_name} ({workspace_id})\n"
            f"DNS ZONE: {dns_zone}\n"
            f"WORKING DIRECTORY: /workspace\n\n"
            f"AVAILABLE SERVICES:\n{services_block}\n\n"
            f"All connection strings are available as environment variables.\n"
            f"You have full filesystem access, shell execution, and Docker build capability.\n"
            f"Build production-quality code with tests."
        )
