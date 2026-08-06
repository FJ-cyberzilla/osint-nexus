from osint_nexus.core.exporters.stix import STIXExporter


def test_stix_exporter() -> None:
    exporter = STIXExporter()
    data: dict[str, str] = {"username": "test_user", "bio": "test bio"}
    result = exporter.export(data)

    assert result["type"] == "bundle"
    assert "id" in result
    assert len(result["objects"]) == 1
    # STIXIdentity access is safe via TypedDict
    identity = result["objects"][0]
    assert identity["type"] == "identity"
    assert "id" in identity
    assert identity["name"] == "test_user"
    assert identity["description"] == "test bio"


def test_stix_exporter_defaults() -> None:
    exporter = STIXExporter()
    # Cast to match the expected input dict[str, str]
    data: dict[str, str] = {}
    result = exporter.export(data)

    identity = result["objects"][0]
    assert identity["name"] == "unknown"
    assert identity["description"] == ""
