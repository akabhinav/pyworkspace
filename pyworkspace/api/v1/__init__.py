"""API v1 router — aggregates all endpoint modules."""

from __future__ import annotations

from fastapi import APIRouter

from pyworkspace.api.v1.workspaces import router as workspaces_router
from pyworkspace.api.v1.templates import router as templates_router
from pyworkspace.api.v1.services import router as services_router
from pyworkspace.api.v1.agent import router as agent_router
from pyworkspace.api.v1.snapshots import router as snapshots_router
from pyworkspace.api.v1.billing import router as billing_router

v1_router = APIRouter(prefix="/v1")
v1_router.include_router(workspaces_router)
v1_router.include_router(templates_router)
v1_router.include_router(services_router)
v1_router.include_router(agent_router)
v1_router.include_router(snapshots_router)
v1_router.include_router(billing_router)
