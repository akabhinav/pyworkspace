import pytest

from pyworkspace.k8s.pod_manager import PodManager


class TestPodManager:
    @pytest.mark.asyncio
    async def test_apply_manifest_no_client(self):
        mgr = PodManager(k8s_client=None)
        await mgr.apply_manifest({"kind": "Deployment", "metadata": {"name": "test", "namespace": "ns1"}})

    @pytest.mark.asyncio
    async def test_wait_for_healthy_no_client(self):
        mgr = PodManager(k8s_client=None)
        # Returns True when no K8s client (dev mode)
        assert await mgr.wait_for_healthy("ns1", "svc1") is True

    @pytest.mark.asyncio
    async def test_wait_for_namespace_healthy_no_client(self):
        mgr = PodManager(k8s_client=None)
        assert await mgr.wait_for_namespace_healthy("ns1") is True

    @pytest.mark.asyncio
    async def test_scale_no_client(self):
        mgr = PodManager(k8s_client=None)
        await mgr.scale_namespace_deployments("ns1", 0)

    @pytest.mark.asyncio
    async def test_get_resource_metrics_no_client(self):
        mgr = PodManager(k8s_client=None)
        metrics = await mgr.get_namespace_resource_metrics("ns1")
        assert metrics == {"cpu_cores": 0.0, "memory_gib": 0.0, "disk_gib": 0.0}
