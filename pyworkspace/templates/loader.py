"""YAML template parser and validator."""

from __future__ import annotations

import os
from pathlib import Path

import yaml

from pyworkspace.core.specs import WorkspaceSpec

# Paths for built-in templates
_BUILTIN_DIR = Path(__file__).parent / "builtin"
_WORKSPACE_TEMPLATES_DIR = Path(__file__).parent.parent.parent / "workspace_templates" / "builtin"


class TemplateLoader:
    """Loads workspace templates from YAML files."""

    @staticmethod
    def load_template(name: str) -> dict | None:
        """Load a template by name from builtin or workspace_templates dirs."""
        for directory in [_BUILTIN_DIR, _WORKSPACE_TEMPLATES_DIR]:
            path = directory / f"{name}.yaml"
            if path.exists():
                return TemplateLoader._parse_file(path)
            path = directory / f"{name}.yml"
            if path.exists():
                return TemplateLoader._parse_file(path)
        return None

    @staticmethod
    def list_builtin_templates() -> list[dict]:
        """List all builtin templates."""
        templates = []
        for directory in [_BUILTIN_DIR, _WORKSPACE_TEMPLATES_DIR]:
            if not directory.exists():
                continue
            for path in sorted(directory.glob("*.yaml")):
                parsed = TemplateLoader._parse_file(path)
                if parsed:
                    templates.append(parsed)
            for path in sorted(directory.glob("*.yml")):
                parsed = TemplateLoader._parse_file(path)
                if parsed:
                    templates.append(parsed)
        # Deduplicate by name
        seen = set()
        unique = []
        for t in templates:
            name = t.get("name", "")
            if name not in seen:
                seen.add(name)
                unique.append(t)
        return unique

    @staticmethod
    def _parse_file(path: Path) -> dict | None:
        """Parse a YAML template file."""
        try:
            with open(path) as f:
                data = yaml.safe_load(f)
            if not data or not isinstance(data, dict):
                return None
            data.setdefault("is_builtin", True)
            data.setdefault("usage_count", 0)
            return data
        except Exception:
            return None

    @staticmethod
    def validate_template(data: dict) -> WorkspaceSpec:
        """Validate that a template spec is valid by parsing as WorkspaceSpec."""
        return WorkspaceSpec(
            name=data.get("name", "unnamed"),
            owner_id=data.get("owner_id", "template"),
            org_id=data.get("org_id", "template"),
            **{k: v for k, v in data.items() if k not in ("name", "owner_id", "org_id", "display_name", "category", "is_builtin", "usage_count")},
        )
