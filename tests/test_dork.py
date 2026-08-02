from osint_nexus.core.dork import DorkEngine


def test_dork_engine_default_templates() -> None:
    """Test DorkEngine uses default templates when no config is provided."""
    engine = DorkEngine()
    assert "github" in engine._templates
    assert len(engine._templates["github"]) > 0


def test_dork_engine_custom_templates() -> None:
    """Test DorkEngine uses custom templates passed directly."""
    templates = {"custom": ["site:custom.com {username}"]}
    engine = DorkEngine(templates=templates)
    assert "custom" in engine._templates
    assert engine._templates["custom"] == ["site:custom.com {username}"]


def test_dork_engine_explicit_templates() -> None:
    """Test DorkEngine uses explicitly provided templates."""
    engine = DorkEngine(templates={"explicit": ["site:explicit.com {username}"]})
    assert "explicit" in engine._templates
    assert engine._templates["explicit"] == ["site:explicit.com {username}"]


def test_get_all_dorks() -> None:
    """Test generating all dorks for a platform."""
    engine = DorkEngine()
    dorks = engine.get_all_dorks("testuser", platform="github")
    assert len(dorks) > 0
    for dork in dorks:
        assert "testuser" in dork
        # Dorks are not valid URLs, check for github.com in the string
        assert "github.com" in dork


def test_get_dork_query_variant() -> None:
    """Test generating a specific dork variant."""
    engine = DorkEngine()
    # GitHub has 3 templates
    dork0 = engine.get_dork_query("user", "github", variant=0)
    dork1 = engine.get_dork_query("user", "github", variant=1)
    assert dork0 != dork1

    # Test wrapping
    dork_wrapped = engine.get_dork_query("user", "github", variant=3)  # 3 % 3 = 0
    assert dork_wrapped == dork0


def test_add_platform_template() -> None:
    """Test adding platform templates at runtime."""
    engine = DorkEngine()
    new_tpl = ['site:new.com "{username}"']
    engine.add_platform_template("new", new_tpl)

    dorks = engine.get_all_dorks("user", "new")
    assert dorks == ['site:new.com "user"']


def test_merge_templates_validation() -> None:
    """Test merging templates with validation."""
    engine = DorkEngine()
    # Should log warning (but not raise) for invalid structure
    engine._merge_templates({"invalid": "not a list"})  # type: ignore

    # Platform should not be added
    assert "invalid" not in engine._templates
