from pyworkspace.networking.ingress import build_ingress


class TestBuildIngress:
    def test_basic_ingress(self):
        ing = build_ingress("pg1", "ws-12345678", "pyws-ws1", 5432)
        assert ing["kind"] == "Ingress"
        assert ing["metadata"]["namespace"] == "pyws-ws1"
        assert ing["metadata"]["labels"]["workspace"] == "ws-12345678"

    def test_host_format(self):
        ing = build_ingress("pg1", "ws-12345678-abcd", "ns1", 5432)
        host = ing["spec"]["rules"][0]["host"]
        assert host == "pg1.ws-12345.pyworkspace.io"

    def test_custom_domain(self):
        ing = build_ingress("api", "ws-12345678", "ns1", 8080, domain="example.com")
        host = ing["spec"]["rules"][0]["host"]
        assert "example.com" in host

    def test_backend_port(self):
        ing = build_ingress("svc1", "ws-1", "ns1", 9090)
        backend = ing["spec"]["rules"][0]["http"]["paths"][0]["backend"]
        assert backend["service"]["port"]["number"] == 9090
        assert backend["service"]["name"] == "svc1"

    def test_tls_configured(self):
        ing = build_ingress("svc1", "ws-1", "ns1", 80)
        tls = ing["spec"]["tls"]
        assert len(tls) == 1
        assert tls[0]["secretName"] == "svc1-tls"

    def test_annotations(self):
        ing = build_ingress("svc1", "ws-1", "ns1", 80)
        annotations = ing["metadata"]["annotations"]
        assert "nginx.ingress.kubernetes.io/ssl-redirect" in annotations
