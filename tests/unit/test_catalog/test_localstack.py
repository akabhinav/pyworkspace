"""Tests for LocalStack service definition."""
import pytest
from pyworkspace.catalog.cloud.localstack import LocalStackService

class TestLocalStackService:
    def setup_method(self):
        self.svc = LocalStackService()

    def test_service_type(self):
        assert self.svc.service_type == "localstack"

    def test_default_port(self):
        assert self.svc.default_port == 4566

    def test_env_vars(self):
        env = self.svc.get_env_vars(
            service_name="localstack",
            workspace_dns_zone="abc.workspace.local",
            credentials={"access_key_id": "test", "secret_access_key": "test", "region": "us-east-1"},
            config={"services": ["s3", "sqs"]},
        )
        assert "AWS_ENDPOINT_URL" in env
        assert "AWS_ACCESS_KEY_ID" in env

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "s3_list_buckets" in tools or "s3_upload" in tools
        assert any("sqs" in t for t in tools)

    def test_generate_credentials(self):
        creds = self.svc.generate_credentials({})
        assert "access_key_id" in creds or "access_key" in creds
