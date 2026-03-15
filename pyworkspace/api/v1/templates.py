"""Template management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

router = APIRouter(prefix="/templates", tags=["templates"])

_templates: dict[str, dict] = {}


class CreateTemplateRequest(BaseModel):
    name: str
    display_name: str
    description: str = ""
    category: str = "general"
    spec_yaml: str
    org_id: str | None = None


class TemplateResponse(BaseModel):
    id: str | None = None
    name: str
    display_name: str
    description: str = ""
    category: str = ""
    is_builtin: bool = False
    usage_count: int = 0


@router.get("", response_model=list[TemplateResponse])
async def list_templates(
    category: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[dict]:
    """List all templates (builtin + org custom)."""
    from pyworkspace.templates.loader import TemplateLoader

    # Load builtins
    builtins = TemplateLoader.list_builtin_templates()

    # Merge with custom templates
    all_templates = builtins + list(_templates.values())
    if category:
        all_templates = [t for t in all_templates if t.get("category") == category]
    return all_templates[offset : offset + limit]


@router.get("/{name}", response_model=TemplateResponse)
async def get_template(name: str) -> dict:
    """Get template by name."""
    from pyworkspace.templates.loader import TemplateLoader

    template = TemplateLoader.load_template(name)
    if not template:
        template = _templates.get(name)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")
    return template


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(req: CreateTemplateRequest) -> dict:
    """Create a custom template."""
    import uuid

    template = {
        "id": str(uuid.uuid4()),
        "name": req.name,
        "display_name": req.display_name,
        "description": req.description,
        "category": req.category,
        "spec_yaml": req.spec_yaml,
        "is_builtin": False,
        "org_id": req.org_id,
        "usage_count": 0,
    }
    _templates[req.name] = template
    return template


@router.post("/{name}/fork", response_model=TemplateResponse, status_code=201)
async def fork_template(name: str, new_name: str = Query(...)) -> dict:
    """Fork a template for customization."""
    from pyworkspace.templates.loader import TemplateLoader
    import uuid

    source = TemplateLoader.load_template(name) or _templates.get(name)
    if not source:
        raise HTTPException(status_code=404, detail="Template not found")

    forked = dict(source)
    forked["id"] = str(uuid.uuid4())
    forked["name"] = new_name
    forked["display_name"] = f"{source.get('display_name', name)} (fork)"
    forked["is_builtin"] = False
    forked["usage_count"] = 0
    _templates[new_name] = forked
    return forked


@router.post("/from-template", status_code=201)
async def create_workspace_from_template(
    template_name: str = Query(...),
    workspace_name: str = Query(...),
    owner_id: str = Query(...),
    org_id: str = Query(...),
) -> dict:
    """Create workspace from a template name."""
    from pyworkspace.templates.loader import TemplateLoader

    template = TemplateLoader.load_template(template_name)
    if not template:
        raise HTTPException(status_code=404, detail="Template not found")

    return {
        "status": "provisioning",
        "template": template_name,
        "workspace_name": workspace_name,
    }
