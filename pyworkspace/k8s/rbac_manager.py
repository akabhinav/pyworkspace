"""RBAC management for workspace service accounts."""
from __future__ import annotations
import structlog

logger = structlog.get_logger()

class RBACManager:
    """Creates service accounts and RBAC roles per workspace."""

    def build_service_account(self, namespace: str, workspace_id: str) -> dict:
        return {
            "apiVersion": "v1",
            "kind": "ServiceAccount",
            "metadata": {
                "name": "workspace-agent",
                "namespace": namespace,
                "labels": {"workspace": workspace_id},
            },
        }

    def build_role(self, namespace: str, workspace_id: str) -> dict:
        return {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "Role",
            "metadata": {
                "name": "workspace-role",
                "namespace": namespace,
                "labels": {"workspace": workspace_id},
            },
            "rules": [
                {
                    "apiGroups": [""],
                    "resources": ["pods", "pods/log", "services", "configmaps"],
                    "verbs": ["get", "list", "watch"],
                },
                {
                    "apiGroups": ["apps"],
                    "resources": ["deployments"],
                    "verbs": ["get", "list", "watch"],
                },
            ],
        }

    def build_role_binding(self, namespace: str, workspace_id: str) -> dict:
        return {
            "apiVersion": "rbac.authorization.k8s.io/v1",
            "kind": "RoleBinding",
            "metadata": {
                "name": "workspace-role-binding",
                "namespace": namespace,
                "labels": {"workspace": workspace_id},
            },
            "roleRef": {
                "apiGroup": "rbac.authorization.k8s.io",
                "kind": "Role",
                "name": "workspace-role",
            },
            "subjects": [
                {"kind": "ServiceAccount", "name": "workspace-agent", "namespace": namespace},
            ],
        }
