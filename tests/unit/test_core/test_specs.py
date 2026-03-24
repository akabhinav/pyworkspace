from pyworkspace.core.specs import AgentSpec, ResourceSpec, ServiceSpec, WorkspaceSpec


class TestResourceSpec:
    def test_defaults(self):
        r = ResourceSpec()
        assert r.cpu == "1"
        assert r.memory == "1Gi"
        assert r.disk == "10Gi"

    def test_custom(self):
        r = ResourceSpec(cpu="4", memory="16Gi", disk="100Gi")
        assert r.cpu == "4"


class TestServiceSpec:
    def test_defaults(self):
        s = ServiceSpec(name="pg1", type="postgres")
        assert s.version == "latest"
        assert s.depends_on == []
        assert s.expose_port is False
        assert s.persistent is True

    def test_with_deps(self):
        s = ServiceSpec(name="graf", type="grafana", depends_on=["prometheus"])
        assert s.depends_on == ["prometheus"]


class TestAgentSpec:
    def test_defaults(self):
        a = AgentSpec()
        assert a.enabled is True
        assert a.auto_connect is True
        assert a.image is None

    def test_disabled(self):
        a = AgentSpec(enabled=False)
        assert a.enabled is False


class TestWorkspaceSpec:
    def test_minimal(self):
        ws = WorkspaceSpec(name="test", owner_id="u1", org_id="org1")
        assert ws.tier == "standard"
        assert ws.egress_allowed is True
        assert ws.ttl_hours == 24
        assert ws.auto_snapshot is True

    def test_enterprise(self):
        ws = WorkspaceSpec(
            name="prod",
            owner_id="u1",
            org_id="org1",
            tier="enterprise",
            services=[
                ServiceSpec(name="pg1", type="postgres"),
                ServiceSpec(name="redis1", type="redis"),
            ],
        )
        assert ws.tier == "enterprise"
        assert len(ws.services) == 2
