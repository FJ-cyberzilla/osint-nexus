import pytest
from osint_nexus.core.dork import DorkEngine
from osint_nexus.core.config import Config

def test_dork_engine_default_templates():
    """Test DorkEngine uses default templates when no config is provided."""
    engine = DorkEngine()
    assert "github" in engine._templates
    assert len(engine._templates["github"]) > 0

def test_dork_engine_custom_templates():
    """Test DorkEngine uses custom templates passed directly."""
    templates = {"custom": ["site:custom.com {username}"]}
    engine = DorkEngine(templates=templates)
    assert "custom" in engine._templates
    assert engine._templates["custom"] == ["site:custom.com {username}"]

def test_dork_engine_explicit_templates():
    """Test DorkEngine uses explicitly provided templates."""
    engine = DorkEngine(templates={"explicit": ["site:explicit.com {username}"]})
    assert "explicit" in engine._templates
    assert engine._templates["explicit"] == ["site:explicit.com {username}"]

def test_get_all_dorks():
    """Test generating all dorks for a platform."""
    engine = DorkEngine()
    dorks = engine.get_all_dorks("testuser", platform="github")
    assert len(dorks) > 0
    for dork in dorks:
        assert "testuser" in dork
        assert "github.com" in dork
