"""Per-workspace DNS zone management via CoreDNS ConfigMap."""
from __future__ import annotations
import structlog

logger = structlog.get_logger()

class DNSManager:
    """Manages CoreDNS entries for workspace service discovery."""

    def __init__(self, k8s_client=None):
        self.k8s = k8s_client
        self._zones: dict[str, dict[str, str]] = {}  # zone -> {service_name -> dns_name}

    async def register(self, dns_zone: str, service_name: str, dns_entry: str) -> None:
        """Register a service DNS entry in the workspace zone."""
        if dns_zone not in self._zones:
            self._zones[dns_zone] = {}
        self._zones[dns_zone][service_name] = dns_entry

        if self.k8s:
            await self._update_coredns_configmap(dns_zone)

        logger.info("dns_registered", zone=dns_zone, service=service_name, entry=dns_entry)

    async def remove_entry(self, dns_zone: str, service_name: str) -> None:
        if dns_zone in self._zones:
            self._zones[dns_zone].pop(service_name, None)
            if self.k8s:
                await self._update_coredns_configmap(dns_zone)

    async def remove_zone(self, dns_zone: str) -> None:
        self._zones.pop(dns_zone, None)
        if self.k8s:
            await self._remove_coredns_zone(dns_zone)
        logger.info("dns_zone_removed", zone=dns_zone)

    def get_zone_entries(self, dns_zone: str) -> dict[str, str]:
        return dict(self._zones.get(dns_zone, {}))

    async def _update_coredns_configmap(self, dns_zone: str) -> None:
        """Update CoreDNS ConfigMap with zone data."""
        entries = self._zones.get(dns_zone, {})
        # Build CoreDNS zone file content
        zone_config = self._build_zone_config(dns_zone, entries)
        # Apply via K8s API
        if self.k8s:
            await self.k8s.patch_configmap(
                name="coredns-custom",
                namespace="kube-system",
                data={f"{dns_zone}.db": zone_config},
            )

    async def _remove_coredns_zone(self, dns_zone: str) -> None:
        if self.k8s:
            await self.k8s.patch_configmap(
                name="coredns-custom",
                namespace="kube-system",
                data={f"{dns_zone}.db": None},
            )

    @staticmethod
    def _build_zone_config(dns_zone: str, entries: dict[str, str]) -> str:
        lines = [f"{dns_zone}. IN SOA ns.{dns_zone}. admin.{dns_zone}. 1 3600 600 86400 60"]
        for service_name, dns_entry in entries.items():
            # CNAME to K8s service
            lines.append(f"{service_name}.{dns_zone}. IN CNAME {dns_entry}.")
        return "\n".join(lines)
