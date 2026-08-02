from unittest.mock import MagicMock

from rich.progress import Progress
from rich.table import Table

from osint_nexus.cli.main import _format_intel_row, get_layout


def test_get_layout() -> None:
    progress = Progress()
    results_table = Table()
    layout = get_layout(progress, "testuser", "status", results_table)
    assert layout is not None


def test_format_intel_row_match() -> None:
    intel = MagicMock()
    intel.metadata = {"device_inference": {}}
    intel.found = True
    intel.confidence = 0.8

    status, conf, details = _format_intel_row(intel)
    assert "Match Found" in status
    assert "80%" in conf


def test_format_intel_row_error() -> None:
    intel = MagicMock()
    intel.metadata = {"error": "Connection Timeout"}
    intel.found = False

    status, conf, details = _format_intel_row(intel)
    assert "Error" in status
    assert details == "Connection Timeout"
