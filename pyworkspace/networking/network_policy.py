"""K8s NetworkPolicy generation for workspace isolation."""
from __future__ import annotations

def build_network_policy(namespace: str, workspace_id: str, egress_allowed: bool = True) -> dict:
    """Build K8s NetworkPolicy for workspace isolation."""
    egress_rules = [
        # Allow intra-namespace
        {"to": [{"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": namespace}}}]},
    ]

    if egress_allowed:
        # Allow internet egress (HTTP/HTTPS/DNS only)
        egress_rules.append({
            "to": [{}],
            "ports": [
                {"port": 443, "protocol": "TCP"},
                {"port": 80, "protocol": "TCP"},
                {"port": 53, "protocol": "UDP"},
                {"port": 53, "protocol": "TCP"},
            ],
        })

    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "NetworkPolicy",
        "metadata": {
            "name": "workspace-isolation",
            "namespace": namespace,
            "labels": {"workspace": workspace_id},
        },
        "spec": {
            "podSelector": {},
            "policyTypes": ["Ingress", "Egress"],
            "ingress": [
                # Allow intra-namespace
                {
                    "from": [
                        {"namespaceSelector": {"matchLabels": {"kubernetes.io/metadata.name": namespace}}},
                        {"namespaceSelector": {"matchLabels": {"app": "pyworkspace-control-plane"}}},
                    ]
                },
            ],
            "egress": egress_rules,
        },
    }
