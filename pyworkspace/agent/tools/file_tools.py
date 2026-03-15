"""File system agent tools."""
from __future__ import annotations
from pyworkspace.agent.tool_registry import register_tool

@register_tool("file_read")
async def file_read(host: str, port: int, credentials: dict, path: str = "", **kwargs) -> dict:
    return {"tool": "file_read", "path": path, "status": "ready"}

@register_tool("file_write")
async def file_write(host: str, port: int, credentials: dict, path: str = "", content: str = "", **kwargs) -> dict:
    return {"tool": "file_write", "path": path, "status": "ready"}

@register_tool("file_tree")
async def file_tree(host: str, port: int, credentials: dict, path: str = "/workspace", **kwargs) -> dict:
    return {"tool": "file_tree", "path": path, "status": "ready"}
