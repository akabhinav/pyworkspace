"""Shared test fixtures."""
import pytest
from pyworkspace.core.specs import WorkspaceSpec, ServiceSpec, AgentSpec, ResourceSpec

@pytest.fixture
def sample_workspace_spec():
    return WorkspaceSpec(
        name="test-workspace",
        owner_id="user-123",
        org_id="org-456",
        tier="standard",
        services=[
            ServiceSpec(name="postgres", type="postgres", version="16", config={"db": "testdb"}),
            ServiceSpec(name="redis", type="redis", version="7"),
        ],
        agent=AgentSpec(enabled=True),
    )

@pytest.fixture
def sample_service_spec():
    return ServiceSpec(name="postgres", type="postgres", version="16", config={"db": "testdb"})

@pytest.fixture
def enterprise_workspace_spec():
    return WorkspaceSpec(
        name="enterprise-test",
        owner_id="user-123",
        org_id="org-456",
        tier="enterprise",
        services=[
            ServiceSpec(name="postgres", type="postgres", version="16", config={"db": "payments", "extensions": ["uuid-ossp", "pgcrypto"]}),
            ServiceSpec(name="redis", type="redis", version="7", config={"mode": "standalone", "maxmemory": "512mb"}),
            ServiceSpec(name="kafka", type="kafka", version="7.5", config={"topics": [{"name": "payment.events", "partitions": 3}]}),
            ServiceSpec(name="elasticsearch", type="elasticsearch", version="8.11.0"),
            ServiceSpec(name="localstack", type="localstack", config={"services": ["s3", "sqs", "sns"]}),
            ServiceSpec(name="prometheus", type="prometheus"),
            ServiceSpec(name="grafana", type="grafana", depends_on=["prometheus"]),
        ],
    )
