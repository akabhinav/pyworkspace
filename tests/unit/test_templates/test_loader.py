"""Tests for template loader."""
import pytest
from pyworkspace.templates.loader import TemplateLoader

class TestTemplateLoader:
    def test_list_builtin_templates(self):
        templates = TemplateLoader.list_builtin_templates()
        assert isinstance(templates, list)
        # We should have at least the blank template
        names = [t.get("name") for t in templates]
        assert "blank" in names

    def test_load_blank_template(self):
        template = TemplateLoader.load_template("blank")
        assert template is not None
        assert template["name"] == "blank"

    def test_load_nonexistent_template(self):
        template = TemplateLoader.load_template("nonexistent-template-xyz")
        assert template is None
