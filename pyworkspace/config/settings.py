"""Application settings loaded from environment variables."""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import SecretStr
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """All configuration via environment variables. No magic defaults that hide in code."""

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Platform
    PYWORKSPACE_MASTER_KEY: SecretStr = SecretStr("change-me")
    PYWORKSPACE_ENV: Literal["dev", "staging", "prod"] = "dev"
    PYWORKSPACE_VERSION: str = "1.0.0"

    # Database (platform metadata)
    DATABASE_URL: SecretStr = SecretStr(
        "postgresql+asyncpg://pyworkspace:pyworkspace@localhost:5432/pyworkspace"
    )
    DATABASE_POOL_SIZE: int = 20

    # Redis (platform cache + task queue)
    REDIS_URL: str = "redis://localhost:6379/0"
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"

    # Kubernetes
    K8S_IN_CLUSTER: bool = False
    K8S_KUBECONFIG_PATH: str = "~/.kube/config"
    K8S_WORKSPACE_NAMESPACE_PREFIX: str = "pyws"
    K8S_DEFAULT_STORAGE_CLASS: str = "standard"
    K8S_FIRECRACKER_RUNTIME: str = "kata-containers"

    # Vault
    VAULT_ADDR: str = "http://localhost:8200"
    VAULT_TOKEN: SecretStr = SecretStr("dev-root-token")
    VAULT_WORKSPACE_PATH: str = "secret/workspaces"

    # MinIO (snapshots + artifacts)
    MINIO_ENDPOINT: str = "localhost:9000"
    MINIO_ACCESS_KEY: SecretStr = SecretStr("minioadmin")
    MINIO_SECRET_KEY: SecretStr = SecretStr("minioadmin")
    MINIO_BUCKET_SNAPSHOTS: str = "pyworkspace-snapshots"

    # Resource defaults per workspace tier
    DEFAULT_CPU_LIMIT: str = "4"
    DEFAULT_MEMORY_LIMIT: str = "8Gi"
    DEFAULT_DISK_LIMIT: str = "50Gi"
    DEFAULT_WORKSPACE_TTL_HOURS: int = 24
    MAX_SERVICES_PER_WORKSPACE: int = 20

    # Networking
    WORKSPACE_DNS_DOMAIN: str = "workspace.local"
    PORT_RANGE_START: int = 30000
    PORT_RANGE_END: int = 40000

    # Agent (PyOz integration)
    PYOZ_IMAGE: str = "pyworkspace/pyoz-agent:latest"
    PYOZ_CPU: str = "2"
    PYOZ_MEMORY: str = "4Gi"

    # PyGate integration
    PYGATE_URL: str | None = None
    PYGATE_API_KEY: SecretStr | None = None

    # Plugin system
    PLUGIN_MANIFEST_DIR: str = "/etc/pyworkspace/plugins"  # load manifests from YAML files on startup
    PLUGIN_DISCOVERY_URLS: str = ""  # comma-separated URLs for HTTP-based plugin discovery
    PLUGIN_WEBHOOK_TIMEOUT: int = 10  # seconds for webhook delivery to plugins

    # LocalStack (cloud emulation)
    LOCALSTACK_IMAGE: str = "localstack/localstack-pro:latest"
    LOCALSTACK_PRO_KEY: SecretStr | None = None
    DEFAULT_AWS_REGION: str = "us-east-1"

    # Observability
    OTEL_ENDPOINT: str | None = None
    PROMETHEUS_ENABLED: bool = True
    LOG_LEVEL: str = "INFO"


@lru_cache
def get_settings() -> Settings:
    """Singleton settings instance."""
    return Settings()
