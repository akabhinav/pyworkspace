"""S3/MinIO agent tools."""
from __future__ import annotations
from pyworkspace.agent.tool_registry import register_tool

@register_tool("s3_upload")
async def s3_upload(host: str, port: int, credentials: dict, bucket: str = "", key: str = "", **kwargs) -> dict:
    return {"tool": "s3_upload", "bucket": bucket, "key": key, "status": "ready"}

@register_tool("s3_download")
async def s3_download(host: str, port: int, credentials: dict, bucket: str = "", key: str = "", **kwargs) -> dict:
    return {"tool": "s3_download", "bucket": bucket, "key": key, "status": "ready"}

@register_tool("s3_list")
async def s3_list(host: str, port: int, credentials: dict, bucket: str = "", prefix: str = "", **kwargs) -> dict:
    return {"tool": "s3_list", "bucket": bucket, "prefix": prefix, "status": "ready"}

@register_tool("s3_delete")
async def s3_delete(host: str, port: int, credentials: dict, bucket: str = "", key: str = "", **kwargs) -> dict:
    return {"tool": "s3_delete", "bucket": bucket, "key": key, "status": "ready"}
