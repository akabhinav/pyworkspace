from pyworkspace.catalog.runtime.code_executor import CodeExecutorService


class TestCodeExecutorService:
    def setup_method(self):
        self.svc = CodeExecutorService()

    def test_service_type(self):
        assert self.svc.service_type == "code_executor"

    def test_default_port(self):
        assert self.svc.default_port == 8080

    def test_env_vars(self):
        creds = {"token": "tok"}
        env = self.svc.get_env_vars("exec1", "ws.local", creds, {})
        assert env["CODE_EXECUTOR_TOKEN"] == "tok"
        assert "http://" in env["CODE_EXECUTOR_URL"]

    def test_agent_tools(self):
        tools = self.svc.get_agent_tools()
        assert "execute_python" in tools
        assert "execute_node" in tools
        assert "run_tests" in tools
        assert len(tools) == 8

    def test_health_check(self):
        hc = self.svc.get_health_check("exec1", "ws.local")
        assert hc["httpGet"]["path"] == "/health"

    def test_init_commands_pip(self):
        cmds = self.svc.get_init_commands({"pip_packages": ["flask"]})
        assert "pip install flask" in cmds[0]

    def test_init_commands_npm(self):
        cmds = self.svc.get_init_commands({"npm_packages": ["express"]})
        assert "npm install -g express" in cmds[0]

    def test_init_commands_both(self):
        cmds = self.svc.get_init_commands({"pip_packages": ["a"], "npm_packages": ["b"]})
        assert len(cmds) == 2

    def test_generate_credentials(self):
        creds = self.svc.generate_credentials({})
        assert "token" in creds
