from pyworkspace.k8s.pvc_manager import PVCManager


class TestPVCManager:
    def setup_method(self):
        self.mgr = PVCManager()

    def test_build_pvc(self):
        pvc = self.mgr.build_pvc("pg-data", "pyws-ws1", "ws-1")
        assert pvc["kind"] == "PersistentVolumeClaim"
        assert pvc["metadata"]["name"] == "pg-data"
        assert pvc["metadata"]["namespace"] == "pyws-ws1"
        assert pvc["metadata"]["labels"]["workspace"] == "ws-1"
        assert pvc["spec"]["resources"]["requests"]["storage"] == "10Gi"

    def test_build_pvc_custom_storage(self):
        pvc = self.mgr.build_pvc("data", "ns1", "ws-1", storage="50Gi", storage_class="ssd")
        assert pvc["spec"]["resources"]["requests"]["storage"] == "50Gi"
        assert pvc["spec"]["storageClassName"] == "ssd"
