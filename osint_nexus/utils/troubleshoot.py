"""
Actionable troubleshooting tips for agent failures.

Provides human-readable diagnostic messages based on exception type,
helping users and operators quickly identify root causes.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sqlite3
from collections.abc import Callable
from typing import Any, cast

import aiohttp
from rich.console import Console
from rich.logging import RichHandler
from rich.panel import Panel
from rich.syntax import Syntax
from rich.table import Table

from osint_nexus.core import constants
from osint_nexus.core.bootstrap import DATABASE_PATH, LOG_FILE_PATH

logger = logging.getLogger("osint_nexus.troubleshoot")


def setup_logging(verbose: bool = False) -> None:
    log_level = logging.DEBUG if verbose else logging.INFO

    # Root logger config
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)

    # Remove existing handlers to avoid duplicates
    root_logger.handlers.clear()

    # 1. THE AESTHETIC CONSOLE HANDLER (Rich)
    console_handler = RichHandler(
        rich_tracebacks=True,  # Gorgeous syntax-highlighted error tracebacks
        markup=True,  # Allows using [bold red] colors inside custom log messages
        show_path=False,  # Hides file paths to keep logs looking clean and structured
        omit_repeated_times=True,  # Drops timestamp clutter for simultaneous operations
    )
    console_handler.setLevel(log_level)
    root_logger.addHandler(console_handler)

    # 2. THE PERSISTENT FILE HANDLER (Raw text for log analysis)
    file_formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    file_handler = logging.FileHandler(LOG_FILE_PATH, encoding="utf-8")
    file_handler.setFormatter(file_formatter)
    file_handler.setLevel(logging.DEBUG)  # Always record full details to the disk log
    root_logger.addHandler(file_handler)


def inspect_database_schema() -> None:
    console = Console()

    try:
        # Connect to your dynamic database path
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        # 1. Fetch all tables and their explicit SQL creation strings
        cursor.execute("SELECT name, sql FROM sqlite_master WHERE type='table';")
        tables = cursor.fetchall()

        if not tables:
            console.print(
                "[bold yellow]⚠ Database is empty or no tables have been initialized yet.[/bold yellow]"
            )
            return

        console.print(
            Panel(
                "[bold green]📂 OSINT Nexus - Local Storage Architecture[/bold green]",
                expand=False,
                border_style="cyan",
            )
        )

        for table_name, sql_schema in tables:
            # Skip SQLite internal tracking tables to reduce noise
            if table_name.startswith("sqlite_"):
                continue

            # Properly quote table name to prevent SQL injection, though already safe from sqlite_master
            quoted_table_name = f'"{table_name.replace('"', '""')}"'
            cursor.execute(f"SELECT COUNT(*) FROM {quoted_table_name};")  # nosec
            row_count = cursor.fetchone()[0]

            # Syntax highlight the SQL creation statement dynamically
            clean_sql = sql_schema.strip() + ";"
            highlighted_sql = Syntax(clean_sql, "sql", theme="monokai", line_numbers=True)

            # Print each table configuration in its own visual block
            console.print(
                Panel(
                    highlighted_sql,
                    title=f"📦 Table: [bold yellow]{table_name}[/bold yellow]",
                    subtitle=f"[bold]Records: {row_count}[/bold]",
                    subtitle_align="right",
                    border_style="magenta",
                    padding=(1, 2),
                )
            )
            console.print("")  # Space spacer

        conn.close()

    except Exception as e:
        console.print(f"[bold red]❌ Failed to read database schema: {e}[/bold red]")


def print_latest_scan_results(limit: int = 10) -> None:
    console = Console()
    rows = _fetch_latest_scan_results(limit)

    if not rows:
        console.print("[dim]No scan logs recorded yet.[/dim]")
        return

    _render_scan_results_table(console, rows)


def _fetch_latest_scan_results(limit: int) -> list[tuple]:
    try:
        conn = sqlite3.connect(DATABASE_PATH)
        cursor = conn.cursor()

        cursor.execute(
            "SELECT id, username, platform, found, timestamp FROM results ORDER BY id DESC LIMIT ?;", (limit,)
        )
        rows = cursor.fetchall()
        conn.close()
        return rows
    except sqlite3.OperationalError as e:
        if "no such table: results" in str(e):
            return []
        raise


def _render_scan_results_table(console: Console, rows: list[tuple]) -> None:
    # Build clean columns matching your schema footprint
    table = Table(title="📊 Recent Footprint Discoveries", border_style="dim")
    table.add_column("ID", justify="center", style="dim")
    table.add_column("Target Username", style="yellow")
    table.add_column("Platform Target", style="cyan")
    table.add_column("Detection State", justify="center")
    table.add_column("Observed Timestamp", style="green")

    for row in rows:
        id_, username, platform, found, timestamp = row
        status = "[bold green]FOUND[/bold green]" if found == 1 else "[red]ABSENT[/red]"
        table.add_row(str(id_), username, platform, status, timestamp)

    console.print(table)


def troubleshoot_agent_error(error: BaseException, provider_name: str = "") -> str:
    """
    Convert an exception into a user-friendly troubleshooting tip.

    Args:
        error: The exception that occurred.
        provider_name: Optional name of the provider that raised the error.

    Returns:
        A Rich-markup string containing an actionable tip.
    """
    tip = _generate_tip(error, provider_name)

    # Log the underlying error for diagnostics
    logger.error("Agent failure in %s: %s", provider_name, error, exc_info=True)

    return f"[{constants.COLOR_TIP}]Tip: {tip}[/]"


_EXCEPTION_TIPS: dict[
    type[BaseException] | tuple[type[BaseException], ...], Callable[[str, BaseException], str]
] = {
    (TimeoutError, asyncio.TimeoutError): lambda p, _: (
        f"Request timed out for {p}. Check network latency or increase the HTTP timeout in config."
    ),
    (ConnectionError, aiohttp.ClientError): lambda p, _: (
        f"Could not connect to {p}. Verify proxy settings and internet connectivity."
    ),
    json.JSONDecodeError: lambda p, _: (
        f"Failed to parse response from {p}. The site might have returned invalid JSON."
    ),
    PermissionError: lambda p, _: "Permission denied. Check your user privileges and system access.",
}


def _get_type_based_tip(error: BaseException, provider_name: str) -> str | None:
    for types, tip_func in _EXCEPTION_TIPS.items():
        if isinstance(error, cast(type[Any] | tuple[type[Any], ...], types)):
            return tip_func(provider_name, error)

    if hasattr(error, "response") and error.response is not None:
        status_code = error.response.status_code
        return (
            f"HTTP {status_code} from {provider_name}. "
            "Possible rate‑limiting or block – consider rotating proxy / User‑Agent."
        )
    return None


def _get_string_based_tip(error_str: str, provider_name: str) -> str | None:
    if "timeout" in error_str:
        return (
            f"Request timed out for {provider_name}. "
            "Check network latency or increase the HTTP timeout in config."
        )
    if "ssl" in error_str or "certificate" in error_str:
        return (
            f"SSL certificate error for {provider_name}. Ensure your system’s CA certificates are up to date."
        )
    return None


def _generate_tip(error: BaseException, provider_name: str) -> str:
    error_str = str(error).lower()

    tip = _get_type_based_tip(error, provider_name) or _get_string_based_tip(error_str, provider_name)

    return tip or f"Unexpected error in {provider_name}. Review the logs for full details."


def run_health_check() -> None:
    """
    Perform a health check of registered providers.

    This function requires an active scan or agent context to access
    provider registry and network management services.
    """
    console = Console()
    console.print("[bold yellow]Health check requires an active scan context.[/]")
    console.print("Please run this tool within a scan environment or initialize the OSINTAgent.")
