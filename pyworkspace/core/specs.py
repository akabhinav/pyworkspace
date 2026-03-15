from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field


class ResourceSpec(BaseModel):
    cpu: str = "1"
    memory: str = "1Gi"
    disk: str = "10Gi"


class ServiceSpec(BaseModel):
    name: str
    type: str
    version: str = "latest"
    config: dict = Field(default_factory=dict)
    resources: ResourceSpec | None = None
    depends_on: list[str] = Field(default_factory=list)
    expose_port: bool = False
    persistent: bool = True


class AgentSpec(BaseModel):
    enabled: bool = True
    image: str | None = None
    auto_connect: bool = True
    initial_prompt: str | None = None
    resources: ResourceSpec | None = None


class WorkspaceSpec(BaseModel):
    name: str
    template: str | None = None
    description: str = ""
    owner_id: str
    org_id: str
    tier: Literal["dev", "standard", "enterprise"] = "standard"
    services: list[ServiceSpec] = Field(default_factory=list)
    agent: AgentSpec = Field(default_factory=AgentSpec)
    resources: ResourceSpec = Field(default_factory=lambda: ResourceSpec(cpu="4", memory="8Gi", disk="50Gi"))
    egress_allowed: bool = True
    expose_services: list[str] = Field(default_factory=list)
    ttl_hours: int | None = 24
    auto_snapshot: bool = True
    tags: dict[str, str] = Field(default_factory=dict)
