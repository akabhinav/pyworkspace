from __future__ import annotations

import secrets as secrets_mod

from pyworkspace.catalog.base import ServiceDefinition
from pyworkspace.catalog.registry import register_service
from pyworkspace.core.specs import ResourceSpec


@register_service
class LocalStackService(ServiceDefinition):
    service_type = "localstack"
    display_name = "LocalStack"
    description = "Local AWS cloud emulator supporting S3, SQS, SNS, Lambda, DynamoDB, and more."
    default_version = "latest"
    supported_versions = ["latest"]
    docker_image_template = "localstack/localstack-pro:{version}"
    default_port = 4566
    default_resources = ResourceSpec(cpu="1", memory="2Gi", disk="5Gi")
    categories = ["cloud", "aws"]

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
        region = config.get("region", "us-east-1")
        return {
            "AWS_ENDPOINT_URL": endpoint,
            "AWS_ACCESS_KEY_ID": credentials.get("access_key_id", "test"),
            "AWS_SECRET_ACCESS_KEY": credentials.get("secret_access_key", "test"),
            "AWS_DEFAULT_REGION": region,
            "S3_ENDPOINT_URL": endpoint,
            "SQS_ENDPOINT_URL": endpoint,
            "SNS_ENDPOINT_URL": endpoint,
            "DYNAMODB_ENDPOINT_URL": endpoint,
            "LAMBDA_ENDPOINT_URL": endpoint,
            "SECRETSMANAGER_ENDPOINT_URL": endpoint,
            "SES_ENDPOINT_URL": endpoint,
        }

    def get_agent_tools(self) -> list[str]:
        return [
            "s3_list_buckets",
            "s3_create_bucket",
            "s3_put_object",
            "s3_get_object",
            "s3_delete_object",
            "s3_list_objects",
            "sqs_create_queue",
            "sqs_send_message",
            "sqs_receive_message",
            "sqs_list_queues",
            "sns_create_topic",
            "sns_publish",
            "sns_subscribe",
            "sns_list_topics",
            "lambda_create_function",
            "lambda_invoke",
            "lambda_list_functions",
            "dynamodb_create_table",
            "dynamodb_put_item",
            "dynamodb_get_item",
            "dynamodb_query",
            "dynamodb_scan",
            "dynamodb_list_tables",
            "secretsmanager_create_secret",
            "secretsmanager_get_secret",
            "ses_send_email",
        ]

    def get_health_check(self, service_name: str, workspace_dns_zone: str) -> dict:
        host = f"{service_name}.{workspace_dns_zone}"
        return {
            "httpGet": {
                "host": host,
                "port": self.default_port,
                "path": "/_localstack/health",
            }
        }

    def get_init_commands(self, config: dict) -> list[str]:
        commands: list[str] = []
        buckets = config.get("s3_buckets", [])
        for bucket in buckets:
            commands.append(
                f"awslocal s3 mb s3://{bucket}"
            )
        queues = config.get("sqs_queues", [])
        for queue in queues:
            commands.append(
                f"awslocal sqs create-queue --queue-name {queue}"
            )
        return commands

    def generate_credentials(self, config: dict) -> dict[str, str]:
        return {
            "access_key_id": "test",
            "secret_access_key": "test",
            "region": config.get("region", "us-east-1"),
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

        # Use OSS image when no pro key is configured
        pro_key = config.get("localstack_pro_key")
        if not pro_key:
            version = config.get("version", self.default_version)
            container["image"] = f"localstack/localstack:{version}"

        services = config.get("services", "s3,sqs,sns,lambda,dynamodb,secretsmanager,ses")
        env = container.get("env", [])
        env.extend([
            {"name": "SERVICES", "value": services},
            {"name": "DEFAULT_REGION", "value": config.get("region", "us-east-1")},
            {"name": "DEBUG", "value": config.get("debug", "0")},
        ])
        if pro_key:
            env.append({"name": "LOCALSTACK_API_KEY", "value": pro_key})
        container["env"] = env
        return manifests
