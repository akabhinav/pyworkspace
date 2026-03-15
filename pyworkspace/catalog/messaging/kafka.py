from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class KafkaService(ServiceDefinition):
    service_type = "kafka"
    display_name = "Apache Kafka"
    description = "Distributed event-streaming platform running in KRaft mode (no ZooKeeper)."
    default_version = "7.5"
    supported_versions = ["7.3", "7.4", "7.5"]
    docker_image_template = "confluentinc/cp-kafka:{version}"
    default_port = 9092
    default_resources = ResourceSpec(cpu="1", memory="2Gi", disk="10Gi")
    categories = ["messaging", "streaming"]

    def get_env_vars(
        self,
        service_name: str,
        workspace_dns_zone: str,
        credentials: dict,
        config: dict,
    ) -> dict[str, str]:
        host = f"{service_name}.{workspace_dns_zone}"
        port = str(self.default_port)
        return {
            "KAFKA_BOOTSTRAP_SERVERS": f"{host}:{port}",
            "KAFKA_REST_URL": f"http://{host}:8082",
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "kafka_produce",
            "kafka_consume",
            "kafka_list_topics",
            "kafka_create_topic",
            "kafka_describe_topic",
            "kafka_consumer_groups",
            "kafka_lag",
            "kafka_delete_topic",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {"tcpSocket": {"host": host, "port": self.default_port}}

    def get_init_commands(self, config: dict) -> list[str]:
        commands: list[str] = []
        topics = config.get("topics", [])
        for topic in topics:
            name = topic if isinstance(topic, str) else topic.get("name", "")
            partitions = topic.get("partitions", 1) if isinstance(topic, dict) else 1
            replication = topic.get("replication_factor", 1) if isinstance(topic, dict) else 1
            commands.append(
                f"kafka-topics --bootstrap-server localhost:{self.default_port} "
                f"--create --if-not-exists --topic {name} "
                f"--partitions {partitions} --replication-factor {replication}"
            )
        return commands

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {
            "cluster_id": secrets_mod.token_urlsafe(16),
        }

    def get_k8s_manifests(
        self,
        service_name: str,
        workspace_id: str,
        namespace: str,
        credentials: dict,
        config: dict,
        resources: ResourceSpec,
    ) -> list[dict]:
        manifests = super().get_k8s_manifests(
            service_name, workspace_id, namespace, credentials, config, resources
        )
        deployment = manifests[0]
        container = deployment["spec"]["template"]["spec"]["containers"][0]
        cluster_id = credentials.get("cluster_id", secrets_mod.token_urlsafe(16))
        env = container.get("env", [])
        env.extend([
            {"name": "KAFKA_NODE_ID", "value": "1"},
            {"name": "KAFKA_PROCESS_ROLES", "value": "broker,controller"},
            {"name": "KAFKA_CONTROLLER_QUORUM_VOTERS", "value": "1@localhost:9093"},
            {"name": "KAFKA_LISTENERS", "value": "PLAINTEXT://:9092,CONTROLLER://:9093"},
            {"name": "KAFKA_ADVERTISED_LISTENERS", "value": f"PLAINTEXT://{service_name}.{namespace}.svc.cluster.local:9092"},
            {"name": "KAFKA_CONTROLLER_LISTENER_NAMES", "value": "CONTROLLER"},
            {"name": "KAFKA_INTER_BROKER_LISTENER_NAME", "value": "PLAINTEXT"},
            {"name": "KAFKA_OFFSETS_TOPIC_REPLICATION_FACTOR", "value": "1"},
            {"name": "CLUSTER_ID", "value": cluster_id},
        ])
        container["env"] = env
        # Also expose controller port
        container["ports"].append({"containerPort": 9093})
        return manifests
