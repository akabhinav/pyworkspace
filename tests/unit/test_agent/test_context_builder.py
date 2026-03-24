from pyworkspace.agent.context_builder import AgentTool, AgentWorkspaceContext, ContextBuilder


class TestAgentTool:
    def test_fields(self):
        tool = AgentTool(name="sql_query", description="Run SQL", service_name="pg1", service_type="postgres")
        assert tool.name == "sql_query"
        assert tool.service_type == "postgres"


class TestContextBuilder:
    def test_build_empty_services(self):
        ctx = ContextBuilder.build(
            workspace_id="ws-1",
            workspace_name="test-ws",
            dns_zone="test.local",
            services=[],
        )
        assert isinstance(ctx, AgentWorkspaceContext)
        assert ctx.workspace_id == "ws-1"
        assert ctx.environment == {}
        assert ctx.available_tools == []
        assert "No services provisioned" in ctx.services_summary

    def test_build_with_services(self):
        services = [
            {
                "service_name": "pg1",
                "service_type": "postgres",
                "internal_dns": "pg1.test.local",
                "internal_port": 5432,
                "env_vars": {"DATABASE_URL": "postgres://..."},
                "agent_tools": ["sql_query", "sql_migrate"],
                "status": "healthy",
            },
        ]
        ctx = ContextBuilder.build("ws-1", "test-ws", "test.local", services)
        assert "DATABASE_URL" in ctx.environment
        assert len(ctx.available_tools) == 2
        assert ctx.available_tools[0].name == "sql_query"
        assert ctx.service_health["pg1"] is True

    def test_build_unhealthy_service(self):
        services = [
            {
                "service_name": "pg1",
                "service_type": "postgres",
                "internal_dns": "pg1.test.local",
                "internal_port": 5432,
                "env_vars": {},
                "agent_tools": [],
                "status": "starting",
            },
        ]
        ctx = ContextBuilder.build("ws-1", "test-ws", "test.local", services)
        assert ctx.service_health["pg1"] is False

    def test_system_prompt_contains_workspace_info(self):
        ctx = ContextBuilder.build("ws-1", "myworkspace", "test.local", [])
        assert "myworkspace" in ctx.services_summary
        assert "ws-1" in ctx.services_summary
        assert "test.local" in ctx.services_summary
        assert "PyOz" in ctx.services_summary
