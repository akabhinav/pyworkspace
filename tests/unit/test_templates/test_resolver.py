"""Tests for dependency resolver."""
import pytest
from pyworkspace.templates.resolver import resolve_dependencies, DependencyResolutionError
from pyworkspace.core.specs import ServiceSpec

class TestResolver:
    def test_no_dependencies(self):
        services = [
            ServiceSpec(name="a", type="postgres"),
            ServiceSpec(name="b", type="redis"),
        ]
        layers = resolve_dependencies(services)
        assert len(layers) == 1

    def test_linear_dependencies(self):
        services = [
            ServiceSpec(name="a", type="postgres"),
            ServiceSpec(name="b", type="redis", depends_on=["a"]),
            ServiceSpec(name="c", type="kafka", depends_on=["b"]),
        ]
        layers = resolve_dependencies(services)
        assert len(layers) == 3

    def test_circular_dependency(self):
        services = [
            ServiceSpec(name="a", type="postgres", depends_on=["b"]),
            ServiceSpec(name="b", type="redis", depends_on=["a"]),
        ]
        with pytest.raises(DependencyResolutionError, match="Circular"):
            resolve_dependencies(services)

    def test_missing_dependency(self):
        services = [
            ServiceSpec(name="a", type="postgres", depends_on=["nonexistent"]),
        ]
        with pytest.raises(DependencyResolutionError, match="not defined"):
            resolve_dependencies(services)
