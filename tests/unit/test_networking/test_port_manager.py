"""Tests for port manager."""
import pytest
from pyworkspace.networking.port_manager import PortManager

class TestPortManager:
    def test_allocate_port(self):
        pm = PortManager()
        port = pm.allocate("ws-1", "postgres")
        assert 30000 <= port <= 40000

    def test_allocate_same_service_returns_same_port(self):
        pm = PortManager()
        p1 = pm.allocate("ws-1", "postgres")
        p2 = pm.allocate("ws-1", "postgres")
        assert p1 == p2

    def test_allocate_different_services_returns_different_ports(self):
        pm = PortManager()
        p1 = pm.allocate("ws-1", "postgres")
        p2 = pm.allocate("ws-1", "redis")
        assert p1 != p2

    def test_release_port(self):
        pm = PortManager()
        port = pm.allocate("ws-1", "postgres")
        pm.release("ws-1", "postgres")
        assert pm.get_port("ws-1", "postgres") is None

    def test_release_workspace(self):
        pm = PortManager()
        pm.allocate("ws-1", "postgres")
        pm.allocate("ws-1", "redis")
        pm.release_workspace("ws-1")
        assert pm.get_port("ws-1", "postgres") is None
        assert pm.get_port("ws-1", "redis") is None
