"""Template management endpoints."""

from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException, Query
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from pyworkspace.auth.middleware import CurrentUser
from pyworkspace.db.models import WorkspaceTemplate
from pyworkspace.db.repositories.template_repo import TemplateRepository
from pyworkspace.db.session import get_db

router = APIRouter(prefix="/templates", tags=["templates"])


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
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    category: str | None = Query(None),
    offset: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
) -> list[dict]:
    """List all templates (builtin + org custom)."""
    from pyworkspace.templates.loader import TemplateLoader

    builtins = TemplateLoader.list_builtin_templates()

    # Load custom templates from DB
    repo = TemplateRepository(db)
    if category:
        db_templates = await repo.list_by_category(category, offset=0, limit=100)
    else:
        db_templates = await repo.list_all(offset=0, limit=100)

    custom = [
        {
            "id": t.id,
            "name": t.name,
            "display_name": t.display_name,
            "description": t.description,
            "category": t.category,
            "is_builtin": False,
            "usage_count": t.usage_count,
        }
        for t in db_templates
    ]

    all_templates = builtins + custom
    if category:
        all_templates = [t for t in all_templates if t.get("category") == category]
    return all_templates[offset : offset + limit]


@router.get("/{name}", response_model=TemplateResponse)
async def get_template(
    name: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get template by name."""
    from pyworkspace.templates.loader import TemplateLoader

    template = TemplateLoader.load_template(name)
    if template:
        return template

    repo = TemplateRepository(db)
    db_template = await repo.get_by_name(name)
    if db_template:
        return {
            "id": db_template.id,
            "name": db_template.name,
            "display_name": db_template.display_name,
            "description": db_template.description,
            "category": db_template.category,
            "is_builtin": False,
            "usage_count": db_template.usage_count,
        }

    raise HTTPException(status_code=404, detail="Template not found")


@router.post("", response_model=TemplateResponse, status_code=201)
async def create_template(
    req: CreateTemplateRequest,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Create a custom template."""
    repo = TemplateRepository(db)
    template = WorkspaceTemplate(
        name=req.name,
        display_name=req.display_name,
        description=req.description,
        category=req.category,
        spec_yaml=req.spec_yaml,
        org_id=req.org_id,
        created_by=user.user_id,
    )
    created = await repo.create(template)
    return {
        "id": created.id,
        "name": created.name,
        "display_name": created.display_name,
        "description": created.description,
        "category": created.category,
        "is_builtin": False,
        "usage_count": 0,
    }


@router.post("/{name}/fork", response_model=TemplateResponse, status_code=201)
async def fork_template(
    name: str,
    user: CurrentUser,
    db: AsyncSession = Depends(get_db),
    new_name: str = Query(...),
) -> dict:
    """Fork a template for customization."""
    from pyworkspace.templates.loader import TemplateLoader

    source = TemplateLoader.load_template(name)
    if not source:
        repo = TemplateRepository(db)
        db_template = await repo.get_by_name(name)
        if db_template:
            source = {
                "name": db_template.name,
                "display_name": db_template.display_name,
                "description": db_template.description,
                "category": db_template.category,
                "spec_yaml": db_template.spec_yaml,
            }
    if not source:
        raise HTTPException(status_code=404, detail="Template not found")

    repo = TemplateRepository(db)
    forked = WorkspaceTemplate(
        name=new_name,
        display_name=f"{source.get('display_name', name)} (fork)",
        description=source.get("description", ""),
        category=source.get("category", "general"),
        spec_yaml=source.get("spec_yaml", ""),
        org_id=user.org_id,
        created_by=user.user_id,
    )
    created = await repo.create(forked)
    return {
        "id": created.id,
        "name": created.name,
        "display_name": created.display_name,
        "description": created.description,
        "category": created.category,
        "is_builtin": False,
        "usage_count": 0,
    }


@router.post("/from-template", status_code=201)
async def create_workspace_from_template(
    user: CurrentUser,
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
