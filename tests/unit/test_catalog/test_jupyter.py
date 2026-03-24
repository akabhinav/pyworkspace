from pyworkspace.catalog.runtime.jupyter import JupyterService


class TestJupyterService:
    def setup_method(self):
        self.svc = JupyterService()

    def test_service_type(self):
        assert self.svc.service_type == "jupyter"

    def test_default_port(self):
        assert self.svc.default_port == 8888

    def test_docker_image(self):
        assert "scipy-notebook" in self.svc.get_docker_image()

    def test_env_vars(self):
        creds = {"token": "abc123"}
        env = self.svc.get_env_vars("jup1", "ws.local", creds, {})
        assert env["JUPYTER_TOKEN"] == "abc123"
        assert "8888" in env["JUPYTER_URL"]

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "jupyter_execute" in tools
        assert len(tools) == 3

    def test_health_check(self):
        hc = self.svc.get_health_check("jup1", "ws.local")
        assert hc["httpGet"]["path"] == "/api/status"

    def test_init_commands_with_packages(self):
        cmds = self.svc.get_init_commands({"pip_packages": ["numpy", "pandas"]})
        assert len(cmds) == 1
        assert "numpy" in cmds[0]

    def test_init_commands_empty(self):
        assert self.svc.get_init_commands({}) == []

    def test_generate_credentials(self):
        creds = self.svc.generate_credentials({})
        assert "token" in creds
