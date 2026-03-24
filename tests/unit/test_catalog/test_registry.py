import pytest

from pyworkspace.catalog.registry import get_service_definition, list_services


class TestServiceRegistry:
    def test_get_postgres(self):
        svc = get_service_definition("postgres")
        assert svc.service_type == "postgres"

    def test_get_mongodb(self):
        svc = get_service_definition("mongodb")
        assert svc.service_type == "mongodb"

    def test_get_unknown_raises(self):
        with pytest.raises(KeyError, match="Unknown service type"):
            get_service_definition("nonexistent_service_xyz")

    def test_list_services_contains_builtin(self):
        services = list_services()
        types = [s["type"] for s in services]
        assert "postgres" in types
        assert "redis" in types
        assert "mongodb" in types

    def test_list_services_has_source(self):
        services = list_services()
        for svc in services:
            assert "source" in svc

    def test_list_services_metadata(self):
        services = list_services()
        pg = next(s for s in services if s["type"] == "postgres")
        assert pg["display_name"] == "PostgreSQL"
        assert "database" in pg["categories"]
