from pyworkspace.networking.network_policy import build_network_policy


class TestBuildNetworkPolicy:
    def test_basic_policy(self):
        policy = build_network_policy("pyws-ws1", "ws-1")
        assert policy["kind"] == "NetworkPolicy"
        assert policy["metadata"]["namespace"] == "pyws-ws1"
        assert policy["metadata"]["labels"]["workspace"] == "ws-1"

    def test_egress_allowed(self):
        policy = build_network_policy("ns1", "ws-1", egress_allowed=True)
        egress = policy["spec"]["egress"]
        # Should have intra-namespace + internet egress
        assert len(egress) == 2

    def test_egress_blocked(self):
        policy = build_network_policy("ns1", "ws-1", egress_allowed=False)
        egress = policy["spec"]["egress"]
        # Only intra-namespace
        assert len(egress) == 1

    def test_ingress_allows_control_plane(self):
        policy = build_network_policy("ns1", "ws-1")
        ingress_from = policy["spec"]["ingress"][0]["from"]
        labels = [f["namespaceSelector"]["matchLabels"] for f in ingress_from]
        assert any("pyworkspace-control-plane" in str(l) for l in labels)

    def test_policy_types(self):
        policy = build_network_policy("ns1", "ws-1")
        assert "Ingress" in policy["spec"]["policyTypes"]
        assert "Egress" in policy["spec"]["policyTypes"]
