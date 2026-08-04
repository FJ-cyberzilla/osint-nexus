from typing import Any
from osint_nexus.core.exporters.stix import STIXExporter

def test_stix_exporter() -> None:
    exporter = STIXExporter()
    data: dict[str, str] = {"username": "test_user", "bio": "test bio"}
    result = exporter.export(data)
    
    assert result["type"] == "bundle"
    assert len(result["objects"]) == 1
    assert result["objects"][0]["type"] == "identity"
    assert result["objects"][0]["name"] == "test_user"
    assert result["objects"][0]["description"] == "test bio"

def test_stix_exporter_defaults() -> None:
    exporter = STIXExporter()
    data: dict[str, Any] = {}
    result = exporter.export(data)
    
    assert result["objects"][0]["name"] == "unknown"
    assert result["objects"][0]["description"] == ""
