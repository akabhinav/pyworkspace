"""Tests for PostgreSQL service definition."""
import pytest
from pyworkspace.catalog.databases.postgres import PostgresService

class TestPostgresService:
    def setup_method(self):
        self.svc = PostgresService()

    def test_service_type(self):
        assert self.svc.service_type == "postgres"

    def test_default_port(self):
        assert self.svc.default_port == 5432

    def test_default_version(self):
        assert self.svc.default_version == "16"

    def test_supported_versions(self):
        assert "16" in self.svc.supported_versions
        assert "15" in self.svc.supported_versions

    def test_docker_image(self):
        assert self.svc.get_docker_image("16") == "postgres:16"

    def test_env_vars(self):
        env = self.svc.get_env_vars(
            service_name="postgres",
            workspace_dns_zone="abc.workspace.local",
            credentials={"user": "testuser", "password": "testpass", "database": "testdb"},
            config={"db": "testdb"},
        )
        assert "POSTGRES_URL" in env
        assert "POSTGRES_HOST" in env
        assert "POSTGRES_PORT" in env
        assert "testuser" in env["POSTGRES_URL"]
        assert "testdb" in env["POSTGRES_URL"]

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "sql_query" in tools
        assert "sql_migrate" in tools
        assert "db_list_tables" in tools

    def test_health_check(self):
        check = self.svc.get_health_check("postgres", "abc.workspace.local")
        assert "tcpSocket" in check
        assert check["tcpSocket"]["port"] == 5432

    def test_generate_credentials(self):
        creds = self.svc.generate_credentials({"db": "mydb"})
        assert "user" in creds
        assert "password" in creds
        assert creds["database"] == "mydb"
        assert len(creds["password"]) > 16

    def test_init_commands(self):
        cmds = self.svc.get_init_commands({"extensions": ["uuid-ossp", "pgcrypto"]})
        assert len(cmds) > 0

    def test_k8s_manifests(self):
        from pyworkspace.core.specs import ResourceSpec
        manifests = self.svc.get_k8s_manifests(
            service_name="postgres",
            workspace_id="test-id",
            namespace="pyws-test",
            credentials={"POSTGRES_USER": "user", "POSTGRES_PASSWORD": "pass"},
            config={"db": "testdb"},
            resources=ResourceSpec(cpu="1", memory="1Gi", disk="10Gi"),
        )
        assert len(manifests) >= 2  # At least Deployment + Service
        kinds = [m["kind"] for m in manifests]
        assert "Deployment" in kinds
        assert "Service" in kinds
