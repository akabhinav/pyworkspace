"""Shell execution agent tools."""
from __future__ import annotations
from pyworkspace.agent.tool_registry import register_tool
from pyworkspace.config.constants import BLOCKED_SHELL_PATTERNS

@register_tool("shell_exec")
async def shell_exec(host: str, port: int, credentials: dict, command: str = "", **kwargs) -> dict:
    """Execute a shell command with security validation."""
    for pattern in BLOCKED_SHELL_PATTERNS:
        if pattern in command:
            return {"tool": "shell_exec", "error": f"Blocked: command matches dangerous pattern", "status": "blocked"}
    return {"tool": "shell_exec", "command": command, "status": "ready"}

@register_tool("execute_python")
async def execute_python(host: str, port: int, credentials: dict, code: str = "", **kwargs) -> dict:
    return {"tool": "execute_python", "status": "ready"}

@register_tool("execute_node")
async def execute_node(host: str, port: int, credentials: dict, code: str = "", **kwargs) -> dict:
    return {"tool": "execute_node", "status": "ready"}

@register_tool("execute_shell")
async def execute_shell(host: str, port: int, credentials: dict, command: str = "", **kwargs) -> dict:
    return {"tool": "execute_shell", "command": command, "status": "ready"}
