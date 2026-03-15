"""SQLAlchemy 2.0 ORM models for PyWorkspace."""

from __future__ import annotations

import uuid
from datetime import datetime
from decimal import Decimal
from typing import List, Optional

from sqlalchemy import (
    ForeignKey,
    Index,
    Numeric,
    Text,
    UniqueConstraint,
    func,
)
from sqlalchemy.dialects.postgresql import JSON
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)


class Base(MappedAsDataclass, DeclarativeBase):
    """Declarative base using dataclass-style mapped columns."""

    pass


class Workspace(Base):
    __tablename__ = "workspaces"

    id: Mapped[str] = mapped_column(
        primary_key=True, default_factory=lambda: str(uuid.uuid4()), init=False
    )
    name: Mapped[str] = mapped_column(unique=True)
    owner_id: Mapped[str] = mapped_column()
    org_id: Mapped[str] = mapped_column(index=True)
    tier: Mapped[str] = mapped_column(default="standard")
    status: Mapped[str] = mapped_column(default="provisioning")
    spec: Mapped[Optional[dict]] = mapped_column(JSON, default=None)
    k8s_namespace: Mapped[Optional[str]] = mapped_column(default=None)
    dns_zone: Mapped[Optional[str]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(
        default=None, init=False, server_default=func.now()
    )
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        default=None, init=False, onupdate=func.now()
    )
    last_active_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    paused_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    snapshot_id: Mapped[Optional[str]] = mapped_column(default=None)
    tags: Mapped[Optional[dict]] = mapped_column(JSON, default_factory=dict)
    error_message: Mapped[Optional[str]] = mapped_column(default=None)

    services: Mapped[List[WorkspaceService]] = relationship(
        back_populates="workspace",
        cascade="all, delete-orphan",
        default_factory=list,
        init=False,
    )


class WorkspaceService(Base):
    __tablename__ = "workspace_services"
    __table_args__ = (
        UniqueConstraint("workspace_id", "service_name", name="uq_ws_service_name"),
    )

    id: Mapped[str] = mapped_column(
        primary_key=True, default_factory=lambda: str(uuid.uuid4()), init=False
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE")
    )
    service_name: Mapped[str] = mapped_column()
    service_type: Mapped[str] = mapped_column()
    status: Mapped[str] = mapped_column(default="starting")
    internal_dns: Mapped[Optional[str]] = mapped_column(default=None)
    internal_port: Mapped[Optional[int]] = mapped_column(default=None)
    external_port: Mapped[Optional[int]] = mapped_column(default=None)
    credentials: Mapped[Optional[str]] = mapped_column(default=None)
    pod_name: Mapped[Optional[str]] = mapped_column(default=None)
    pvc_name: Mapped[Optional[str]] = mapped_column(default=None)
    started_at: Mapped[Optional[datetime]] = mapped_column(default=None)
    health_last_checked: Mapped[Optional[datetime]] = mapped_column(default=None)
    restart_count: Mapped[int] = mapped_column(default=0)

    workspace: Mapped[Workspace] = relationship(
        back_populates="services", default=None, init=False
    )


class WorkspaceTemplate(Base):
    __tablename__ = "workspace_templates"

    id: Mapped[str] = mapped_column(
        primary_key=True, default_factory=lambda: str(uuid.uuid4()), init=False
    )
    name: Mapped[str] = mapped_column(unique=True)
    display_name: Mapped[str] = mapped_column()
    category: Mapped[str] = mapped_column()
    spec_yaml: Mapped[str] = mapped_column(Text)
    description: Mapped[str] = mapped_column(default="")
    is_builtin: Mapped[bool] = mapped_column(default=False)
    org_id: Mapped[Optional[str]] = mapped_column(default=None)
    created_by: Mapped[Optional[str]] = mapped_column(default=None)
    created_at: Mapped[datetime] = mapped_column(
        default=None, init=False, server_default=func.now()
    )
    usage_count: Mapped[int] = mapped_column(default=0)


class WorkspaceSnapshot(Base):
    __tablename__ = "workspace_snapshots"

    id: Mapped[str] = mapped_column(
        primary_key=True, default_factory=lambda: str(uuid.uuid4()), init=False
    )
    workspace_id: Mapped[str] = mapped_column(
        ForeignKey("workspaces.id", ondelete="CASCADE")
    )
    name: Mapped[str] = mapped_column()
    type: Mapped[str] = mapped_column()
    minio_path: Mapped[str] = mapped_column()
    services_included: Mapped[Optional[dict]] = mapped_column(JSON, default=None)
    size_bytes: Mapped[int] = mapped_column(default=0)
    created_at: Mapped[datetime] = mapped_column(
        default=None, init=False, server_default=func.now()
    )
    status: Mapped[str] = mapped_column(default="creating")


class WorkspaceAuditLog(Base):
    __tablename__ = "workspace_audit_logs"

    id: Mapped[str] = mapped_column(
        primary_key=True, default_factory=lambda: str(uuid.uuid4()), init=False
    )
    workspace_id: Mapped[str] = mapped_column(index=True)
    actor_id: Mapped[str] = mapped_column()
    action: Mapped[str] = mapped_column()
    metadata_: Mapped[Optional[dict]] = mapped_column(
        "metadata", JSON, default=None
    )
    ip_address: Mapped[Optional[str]] = mapped_column(default=None)
    timestamp: Mapped[datetime] = mapped_column(
        default=None, init=False, server_default=func.now()
    )


class ResourceUsage(Base):
    __tablename__ = "resource_usage"
    __table_args__ = (
        Index("ix_resource_usage_workspace_id", "workspace_id"),
        Index("ix_resource_usage_org_id", "org_id"),
    )

    id: Mapped[str] = mapped_column(
        primary_key=True, default_factory=lambda: str(uuid.uuid4()), init=False
    )
    workspace_id: Mapped[str] = mapped_column()
    org_id: Mapped[str] = mapped_column()
    period_start: Mapped[datetime] = mapped_column()
    period_end: Mapped[datetime] = mapped_column()
    cpu_core_seconds: Mapped[float] = mapped_column()
    memory_gib_seconds: Mapped[float] = mapped_column()
    disk_gib_hours: Mapped[float] = mapped_column()
    network_egress_gb: Mapped[float] = mapped_column(default=0.0)
    cost_usd: Mapped[Decimal] = mapped_column(
        Numeric(10, 4), default=Decimal("0.0000")
    )
