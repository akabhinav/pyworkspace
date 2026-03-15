"""Auto-generate strong credentials for workspace services."""
from __future__ import annotations
import secrets

class CredentialGenerator:
    """Generates strong random credentials per service type."""

    @staticmethod
    def generate(service_type: str, config: dict | None = None) -> dict[str, str]:
        config = config or {}
        generator = getattr(CredentialGenerator, f"_{service_type}", None)
        if generator:
            return generator(config)
        return CredentialGenerator._default(config)

    @staticmethod
    def _default(config: dict) -> dict[str, str]:
        return {
            "user": f"pyws_{secrets.token_hex(4)}",
            "password": secrets.token_urlsafe(32),
        }

    @staticmethod
    def _postgres(config: dict) -> dict[str, str]:
        return {
            "user": f"pyws_{secrets.token_hex(4)}",
            "password": secrets.token_urlsafe(32),
            "database": config.get("db", config.get("database", "pyws_db")),
        }

    @staticmethod
    def _mysql(config: dict) -> dict[str, str]:
        return {
            "user": f"pyws_{secrets.token_hex(4)}",
            "password": secrets.token_urlsafe(32),
            "root_password": secrets.token_urlsafe(32),
            "database": config.get("db", config.get("database", "pyws_db")),
        }

    @staticmethod
    def _mongodb(config: dict) -> dict[str, str]:
        return {
            "user": f"pyws_{secrets.token_hex(4)}",
            "password": secrets.token_urlsafe(32),
            "database": config.get("db", config.get("database", "pyws_db")),
        }

    @staticmethod
    def _redis(config: dict) -> dict[str, str]:
        return {"password": secrets.token_urlsafe(32)}

    @staticmethod
    def _redis_cache(config: dict) -> dict[str, str]:
        return {"password": secrets.token_urlsafe(32)}

    @staticmethod
    def _kafka(config: dict) -> dict[str, str]:
        return {
            "username": f"pyws_{secrets.token_hex(4)}",
            "password": secrets.token_urlsafe(32),
            "sasl_mechanism": "SCRAM-SHA-256",
        }

    @staticmethod
    def _rabbitmq(config: dict) -> dict[str, str]:
        return {
            "user": f"pyws_{secrets.token_hex(4)}",
            "password": secrets.token_urlsafe(32),
            "vhost": config.get("vhost", "/"),
        }

    @staticmethod
    def _elasticsearch(config: dict) -> dict[str, str]:
        return {
            "user": "elastic",
            "password": secrets.token_urlsafe(32),
        }

    @staticmethod
    def _neo4j(config: dict) -> dict[str, str]:
        return {
            "user": "neo4j",
            "password": secrets.token_urlsafe(32),
        }

    @staticmethod
    def _grafana(config: dict) -> dict[str, str]:
        return {
            "user": "admin",
            "password": secrets.token_urlsafe(16),
        }

    @staticmethod
    def _jupyter(config: dict) -> dict[str, str]:
        return {"token": secrets.token_urlsafe(32)}

    @staticmethod
    def _minio(config: dict) -> dict[str, str]:
        return {
            "access_key": f"pyws_{secrets.token_hex(8)}",
            "secret_key": secrets.token_urlsafe(32),
        }

    @staticmethod
    def _localstack(config: dict) -> dict[str, str]:
        return {
            "access_key": "localstack",
            "secret_key": "localstack",
        }
