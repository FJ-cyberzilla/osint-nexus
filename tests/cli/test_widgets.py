from unittest.mock import MagicMock, patch

from osint_nexus.cli.widgets import IntelligenceDashboard, MetricsGraph


def test_intelligence_dashboard_update_data():
    dashboard = IntelligenceDashboard()
    dashboard.table = MagicMock()  # Manually set the table attribute

    mock_intel = MagicMock()
    mock_intel.found = True
    mock_intel.metadata = {"fingerprint": "f1", "footprint": "f2"}
    mock_intel.visuals = None

    dashboard.update_data(mock_intel)

    assert dashboard.data["Fingerprint"] == "No Data"
    assert dashboard.data["Footprint"] == "f2"
    assert dashboard.data["Canvas"] == "Text/Data Only"
    dashboard.table.clear.assert_called_once()


def test_metrics_graph_update_metrics():
    graph = MetricsGraph()

    graph.update_metrics(1, 1)
    assert graph.successes == 1
    assert graph.failures == 1

    # Mocking _refresh_graph to verify call
    with patch.object(graph, "_refresh_graph") as mock_refresh:
        graph.update_metrics(1, 1)
        mock_refresh.assert_called_once()
