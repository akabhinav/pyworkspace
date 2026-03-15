"""Docker agent tools."""
from __future__ import annotations
from pyworkspace.agent.tool_registry import register_tool

@register_tool("docker_build")
async def docker_build(host: str, port: int, credentials: dict, path: str = ".", tag: str = "", **kwargs) -> dict:
    return {"tool": "docker_build", "path": path, "tag": tag, "status": "ready"}

@register_tool("docker_run")
async def docker_run(host: str, port: int, credentials: dict, image: str = "", command: str = "", **kwargs) -> dict:
    return {"tool": "docker_run", "image": image, "command": command, "status": "ready"}

@register_tool("docker_logs")
async def docker_logs(host: str, port: int, credentials: dict, container: str = "", **kwargs) -> dict:
    return {"tool": "docker_logs", "container": container, "status": "ready"}

@register_tool("docker_exec")
async def docker_exec(host: str, port: int, credentials: dict, container: str = "", command: str = "", **kwargs) -> dict:
    return {"tool": "docker_exec", "container": container, "command": command, "status": "ready"}
