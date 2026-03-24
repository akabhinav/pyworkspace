from pyworkspace.catalog.messaging.rabbitmq import RabbitMQService


class TestRabbitMQService:
    def setup_method(self):
        self.svc = RabbitMQService()

    def test_service_type(self):
        assert self.svc.service_type == "rabbitmq"

    def test_default_port(self):
        assert self.svc.default_port == 5672

    def test_docker_image(self):
        assert self.svc.get_docker_image("3.12") == "rabbitmq:3.12-management"

    def test_env_vars(self):
        creds = {"user": "u", "password": "p"}
        env = self.svc.get_env_vars("rmq1", "ws.local", creds, {})
        assert "amqp://u:p@" in env["RABBITMQ_URL"]
        assert "15672" in env["RABBITMQ_MANAGEMENT_URL"]

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "rabbitmq_publish" in tools
        assert len(tools) == 5

    def test_health_check(self):
        hc = self.svc.get_health_check("rmq1", "ws.local")
        assert hc["httpGet"]["port"] == 15672

    def test_init_commands_with_vhosts(self):
        cmds = self.svc.get_init_commands({"vhosts": ["dev", "staging"]})
        assert len(cmds) == 2
        assert "dev" in cmds[0]

    def test_generate_credentials(self):
        creds = self.svc.generate_credentials({})
        assert "user" in creds
        assert "password" in creds
