"""Tests for Kafka service definition."""
import pytest
from pyworkspace.catalog.messaging.kafka import KafkaService

class TestKafkaService:
    def setup_method(self):
        self.svc = KafkaService()

    def test_service_type(self):
        assert self.svc.service_type == "kafka"

    def test_default_port(self):
        assert self.svc.default_port == 9092

    def test_env_vars(self):
        env = self.svc.get_env_vars(
            service_name="kafka",
            workspace_dns_zone="abc.workspace.local",
            credentials={},
            config={},
        )
        assert "KAFKA_BOOTSTRAP_SERVERS" in env

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "kafka_produce" in tools
        assert "kafka_consume" in tools
        assert "kafka_list_topics" in tools

    def test_health_check(self):
        check = self.svc.get_health_check("kafka", "abc.workspace.local")
        assert check is not None

    def test_init_commands_with_topics(self):
        cmds = self.svc.get_init_commands({"topics": [{"name": "test.events", "partitions": 3}]})
        assert len(cmds) > 0
