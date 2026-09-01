from unittest.mock import MagicMock, patch

from osint_nexus.cli.ui import OSINTApp, ScanConfig
from osint_nexus.cli.widgets import ScanUpdate


class TestOSINTApp:
    def test_init(self):
        mock_agent = MagicMock()
        config = ScanConfig(agent=mock_agent, username="testuser", total=10, timeout=30.0)
        app = OSINTApp(config)
        assert app.agent == mock_agent
        assert app.username == "testuser"
        assert app.total == 10
        assert app.timeout == 30.0

    def test_on_scan_update(self):
        mock_agent = MagicMock()
        config = ScanConfig(agent=mock_agent, username="testuser", total=10, timeout=30.0)
        app = OSINTApp(config)

        # Mock dependencies
        mock_intel = MagicMock()
        mock_intel.found = True
        mock_intel.platform = "testplatform"
        mock_intel.metadata = {}

        mock_dashboard = MagicMock()
        mock_progress = MagicMock()
        mock_progress_bar = MagicMock()
        mock_log_panel = MagicMock()
        mock_metrics_graph = MagicMock()

        # Configure nested query_one
        mock_progress.query_one.return_value = mock_progress_bar

        # Patch query_one
        with patch.object(app, "query_one") as mock_query:

            def side_effect(selector, type_hint=None):
                if selector == "#dashboard":
                    return mock_dashboard
                if selector == "#progress":
                    return mock_progress
                if selector == "#logs":
                    return mock_log_panel
                if selector == "#metrics":
                    return mock_metrics_graph
                return MagicMock()

            mock_query.side_effect = side_effect

            # Execute
            app.on_scan_update(ScanUpdate(mock_intel))

            # Assertions
            mock_dashboard.update.assert_called_once_with(mock_intel)
            mock_progress_bar.advance.assert_called_once_with(1)
            mock_log_panel.update.assert_called_once_with(mock_intel)
            mock_metrics_graph.update.assert_called_once_with(mock_intel)
