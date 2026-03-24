import pytest

from pyworkspace.agent.connector import AgentConnector
from pyworkspace.core.specs import AgentSpec


class TestAgentConnector:
    @pytest.mark.asyncio
    async def test_start_without_k8s(self):
        connector = AgentConnector(k8s_manager=None)
        services = [
            {
                "service_name": "pg1",
                "service_type": "postgres",
                "internal_dns": "pg1.test.local",
                "internal_port": 5432,
                "env_vars": {"DATABASE_URL": "postgres://..."},
                "agent_tools": ["sql_query"],
                "status": "healthy",
            },
        ]
        result = await connector.start(
            workspace_id="ws-1",
            namespace="pyws-ws1",
            dns_zone="test.local",
            services=services,
            agent_spec=AgentSpec(),
        )
        assert result["workspace_id"] == "ws-1"
        assert result["pod_name"] == "pyoz-agent"
        assert result["status"] == "starting"

    @pytest.mark.asyncio
    async def test_stop(self):
        connector = AgentConnector(k8s_manager=None)
        await connector.stop("ws-1", "pyws-ws1")

    @pytest.mark.asyncio
    async def test_restart(self):
        connector = AgentConnector(k8s_manager=None)
        result = await connector.restart(
            workspace_id="ws-1",
            namespace="pyws-ws1",
            services=[],
            agent_spec=AgentSpec(),
            dns_zone="test.local",
        )
        assert result["status"] == "starting"
