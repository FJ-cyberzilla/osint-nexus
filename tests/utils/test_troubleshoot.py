from unittest.mock import MagicMock, patch

from osint_nexus.utils import troubleshoot

# --- Existing Tests ---


def test_troubleshoot_agent_error_timeout() -> None:
    error = TimeoutError("Request timed out")
    provider = "test-provider"
    tip = troubleshoot.troubleshoot_agent_error(error, provider)
    assert "Request timed out for test-provider" in tip
    assert "Tip:" in tip


def test_troubleshoot_agent_error_unknown() -> None:
    error = ValueError("Something went wrong")
    provider = "test-provider"
    tip = troubleshoot.troubleshoot_agent_error(error, provider)
    assert "Unexpected error in test-provider" in tip


# --- New Tests for Increased Coverage ---


def test_troubleshoot_agent_error_connection() -> None:
    error = ConnectionError("Connection failed")
    tip = troubleshoot.troubleshoot_agent_error(error, "provider")
    assert "Could not connect to provider" in tip


def test_troubleshoot_agent_error_json() -> None:
    import json

    error = json.JSONDecodeError("msg", "doc", 0)
    tip = troubleshoot.troubleshoot_agent_error(error, "provider")
    assert "Failed to parse response from provider" in tip


def test_troubleshoot_agent_error_ssl() -> None:
    error = Exception("ssl error occurred")
    tip = troubleshoot.troubleshoot_agent_error(error, "provider")
    assert "SSL certificate error for provider" in tip


@patch("osint_nexus.utils.troubleshoot.Console")
@patch("osint_nexus.utils.troubleshoot.sqlite3")
def test_inspect_database_schema_no_tables(mock_sqlite: MagicMock, mock_console_class: MagicMock) -> None:
    mock_console = MagicMock()
    mock_console_class.return_value = mock_console

    mock_conn = MagicMock()
    mock_sqlite.connect.return_value = mock_conn
    mock_conn.cursor.return_value.fetchall.return_value = []

    troubleshoot.inspect_database_schema()

    mock_console.print.assert_any_call(
        "[bold yellow]⚠ Database is empty or no tables have been initialized yet.[/bold yellow]"
    )


@patch("osint_nexus.utils.troubleshoot.Console")
@patch("osint_nexus.utils.troubleshoot.sqlite3")
def test_inspect_database_schema_with_tables(mock_sqlite: MagicMock, mock_console_class: MagicMock) -> None:
    mock_console = MagicMock()
    mock_console_class.return_value = mock_console

    mock_conn = MagicMock()
    mock_sqlite.connect.return_value = mock_conn

    # Simulate one table "results"
    mock_conn.cursor.return_value.fetchall.return_value = [("results", "CREATE TABLE results...")]
    mock_conn.cursor.return_value.fetchone.return_value = [5]  # Row count

    troubleshoot.inspect_database_schema()

    # Should print the panel
    assert mock_console.print.called


@patch("osint_nexus.utils.troubleshoot.Console")
def test_print_latest_scan_results_empty(mock_console_class: MagicMock) -> None:
    mock_console = MagicMock()
    mock_console_class.return_value = mock_console

    with patch("osint_nexus.utils.troubleshoot._fetch_latest_scan_results", return_value=[]):
        troubleshoot.print_latest_scan_results()
        mock_console.print.assert_called_with("[dim]No scan logs recorded yet.[/dim]")


@patch("osint_nexus.utils.troubleshoot.Console")
def test_run_health_check(mock_console_class: MagicMock) -> None:
    mock_console = MagicMock()
    mock_console_class.return_value = mock_console

    troubleshoot.run_health_check()
    assert mock_console.print.called
    assert "Health check requires an active scan context" in str(mock_console.print.call_args_list[0])
