from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class MinIOService(ServiceDefinition):
    service_type = "minio"
    display_name = "MinIO"
    description = "S3-compatible object storage server."
    default_version = "latest"
    supported_versions = ["latest"]
    docker_image_template = "minio/minio:{version}"
    default_port = 9000
    default_resources = ResourceSpec(cpu="0.5", memory="512Mi", disk="10Gi")
    categories = ["cloud", "storage", "s3"]

    _console_port = 9001

    def get_env_vars(
        self,
        service_name: str,
        workspace_dns_zone: str,
        credentials: dict,
        config: dict,
    ) -> dict[str, str]:
        host = f"{service_name}.{workspace_dns_zone}"
        port = str(self.default_port)
        endpoint = f"http://{host}:{port}"
        return {
            "MINIO_ENDPOINT": f"{host}:{port}",
            "MINIO_ACCESS_KEY": credentials["access_key"],
            "MINIO_SECRET_KEY": credentials["secret_key"],
            "S3_ENDPOINT_URL": endpoint,
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "s3_list_buckets",
            "s3_create_bucket",
            "s3_put_object",
            "s3_get_object",
            "s3_delete_object",
            "s3_list_objects",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {
            "httpGet": {
                "host": host,
                "port": self.default_port,
                "path": "/minio/health/live",
            }
        }

    def get_init_commands(self, config: dict) -> list[str]:
        commands: list[str] = []
        buckets = config.get("buckets", [])
        for bucket in buckets:
            commands.append(f"mc mb local/{bucket} --ignore-existing")
        return commands

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {
            "access_key": config.get("access_key", "minioadmin"),
            "secret_key": config.get("secret_key", secrets_mod.token_urlsafe(24)),
        }
