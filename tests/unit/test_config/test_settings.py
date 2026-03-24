from pyworkspace.config.settings import Settings, get_settings


class TestSettings:
    def test_defaults(self):
        s = Settings()
        assert s.PYWORKSPACE_ENV == "dev"
        assert s.K8S_IN_CLUSTER is False
        assert s.PROMETHEUS_ENABLED is True
        assert s.MAX_SERVICES_PER_WORKSPACE == 20
        assert s.DEFAULT_WORKSPACE_TTL_HOURS == 24

    def test_port_range(self):
        s = Settings()
        assert s.PORT_RANGE_START == 30000
        assert s.PORT_RANGE_END == 40000
        assert s.PORT_RANGE_START < s.PORT_RANGE_END

    def test_agent_defaults(self):
        s = Settings()
        assert s.PYOZ_CPU == "2"
        assert s.PYOZ_MEMORY == "4Gi"

    def test_get_settings_singleton(self):
        s1 = get_settings()
        s2 = get_settings()
        assert s1 is s2
