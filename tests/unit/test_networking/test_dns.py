"""Tests for DNS management."""
import pytest
from pyworkspace.networking.dns import DNSManager

class TestDNSManager:
    @pytest.mark.asyncio
    async def test_register_entry(self):
        dns = DNSManager()
        await dns.register("abc.workspace.local", "postgres", "postgres.abc.workspace.local")
        entries = dns.get_zone_entries("abc.workspace.local")
        assert "postgres" in entries
        assert entries["postgres"] == "postgres.abc.workspace.local"

    @pytest.mark.asyncio
    async def test_remove_entry(self):
        dns = DNSManager()
        await dns.register("abc.workspace.local", "postgres", "postgres.abc.workspace.local")
        await dns.remove_entry("abc.workspace.local", "postgres")
        entries = dns.get_zone_entries("abc.workspace.local")
        assert "postgres" not in entries

    @pytest.mark.asyncio
    async def test_remove_zone(self):
        dns = DNSManager()
        await dns.register("abc.workspace.local", "postgres", "postgres.abc.workspace.local")
        await dns.remove_zone("abc.workspace.local")
        entries = dns.get_zone_entries("abc.workspace.local")
        assert len(entries) == 0

    def test_build_zone_config(self):
        config = DNSManager._build_zone_config("abc.workspace.local", {"postgres": "postgres.abc.workspace.local"})
        assert "abc.workspace.local" in config
        assert "postgres" in config
