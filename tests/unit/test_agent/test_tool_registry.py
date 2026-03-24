import pytest

from pyworkspace.agent.tool_registry import (
    ConfiguredTool,
    RemoteTool,
    get_tool,
    list_tools,
    register_tool,
)


class TestRegisterTool:
    def test_register_and_get(self):
        @register_tool("test_tool_xyz")
        async def my_tool(**kwargs):
            return {"ok": True}

        assert get_tool("test_tool_xyz") is my_tool

    def test_get_nonexistent(self):
        assert get_tool("nonexistent_tool_abc") is None


class TestListTools:
    def test_contains_registered_tools(self):
        # Import tool modules to populate registry
        import pyworkspace.agent.tools.postgres_tools  # noqa: F401
        import pyworkspace.agent.tools.redis_tools  # noqa: F401

        tools = list_tools()
        assert "sql_query" in tools
        assert "redis_get" in tools


class TestConfiguredTool:
    @pytest.mark.asyncio
    async def test_execute(self):
        async def impl(host, port, credentials, query=""):
            return {"result": query}

        tool = ConfiguredTool(
            name="sql_query",
            host="localhost",
            port=5432,
            credentials={"user": "u"},
            implementation=impl,
        )
        result = await tool.execute(query="SELECT 1")
        assert result["result"] == "SELECT 1"


class TestRemoteTool:
    def test_fields(self):
        tool = RemoteTool(
            name="sandbox_exec",
            plugin_name="pysandbox",
            base_url="http://sandbox:8080",
            endpoint="/api/v1/exec",
        )
        assert tool.method == "POST"
        assert tool.timeout_seconds == 30


class TestBuiltinTools:
    """Verify all built-in tool modules register correctly."""

    @pytest.mark.asyncio
    async def test_docker_tools(self):
        from pyworkspace.agent.tools.docker_tools import docker_build
        result = await docker_build(host="h", port=0, credentials={}, path=".", tag="t")
        assert result["tool"] == "docker_build"

    @pytest.mark.asyncio
    async def test_file_tools(self):
        from pyworkspace.agent.tools.file_tools import file_read
        result = await file_read(host="h", port=0, credentials={}, path="/test")
        assert result["tool"] == "file_read"

    @pytest.mark.asyncio
    async def test_kafka_tools(self):
        from pyworkspace.agent.tools.kafka_tools import kafka_produce
        result = await kafka_produce(host="h", port=0, credentials={}, topic="t")
        assert result["tool"] == "kafka_produce"

    @pytest.mark.asyncio
    async def test_s3_tools(self):
        from pyworkspace.agent.tools.s3_tools import s3_upload
        result = await s3_upload(host="h", port=0, credentials={}, bucket="b")
        assert result["tool"] == "s3_upload"

    @pytest.mark.asyncio
    async def test_shell_exec_blocked(self):
        from pyworkspace.agent.tools.shell_tools import shell_exec
        result = await shell_exec(host="h", port=0, credentials={}, command="rm -rf /")
        assert result["status"] == "blocked"

    @pytest.mark.asyncio
    async def test_shell_exec_allowed(self):
        from pyworkspace.agent.tools.shell_tools import shell_exec
        result = await shell_exec(host="h", port=0, credentials={}, command="ls -la")
        assert result["status"] == "ready"
