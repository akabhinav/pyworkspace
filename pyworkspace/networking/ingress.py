"""External access to workspace services via K8s Ingress."""
from __future__ import annotations
import structlog

logger = structlog.get_logger()

def build_ingress(
    service_name: str,
    workspace_id: str,
    namespace: str,
    service_port: int,
    domain: str = "pyworkspace.io",
) -> dict:
    """Build K8s Ingress for external access to a workspace service."""
    host = f"{service_name}.{workspace_id[:8]}.{domain}"
    return {
        "apiVersion": "networking.k8s.io/v1",
        "kind": "Ingress",
        "metadata": {
            "name": f"{service_name}-ingress",
            "namespace": namespace,
            "labels": {"workspace": workspace_id},
            "annotations": {
                "nginx.ingress.kubernetes.io/ssl-redirect": "true",
                "nginx.ingress.kubernetes.io/rate-limit": "100",
            },
        },
        "spec": {
            "rules": [{
                "host": host,
                "http": {
                    "paths": [{
                        "path": "/",
                        "pathType": "Prefix",
                        "backend": {
                            "service": {
                                "name": service_name,
                                "port": {"number": service_port},
                            }
                        },
                    }],
                },
            }],
            "tls": [{"hosts": [host], "secretName": f"{service_name}-tls"}],
        },
    }
