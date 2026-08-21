from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import Field
from rich.panel import Panel
from rich.table import Table

if TYPE_CHECKING:
    from osint_nexus.core.database import DatabaseManager


from typing import Protocol, runtime_checkable


@runtime_checkable
class BrowserProtocol(Protocol):
    user_agent: str
    headless: bool
    webdriver: bool
    automation_plugins: bool


@dataclass
class TelemetryPayload:
    browser: BrowserProtocol | None = None
    raw_metadata: dict[str, object] = Field(default_factory=dict)
    pipeline_status: str = ""


@dataclass
class IntelligenceReport:
    """Structured container for aggregated intelligence scan results."""

    username: str
    results: list[dict[str, str | int]]
    # Add other fields (telemetry, inference) here as needed


class AdvancedReportGenerator:
    """Consolidates cross-subsystem telemetry and returns aesthetic structural threat summaries."""

    def __init__(self, db_manager: DatabaseManager) -> None:
        self.db_manager = db_manager

    async def generate(self, target_username: str) -> Panel:
        """Generates the final report as a Rich Panel with actual database data."""
        # Query results from database
        results = await self.db_manager.query_results(username=target_username)

        # Build Table
        table = Table(
            title=f"Scan Results for {target_username}", show_header=True, header_style="bold magenta"
        )
        table.add_column("Platform", style="dim")
        table.add_column("Found", style="bold")
        table.add_column("Timestamp")

        for row in results:
            found_str = "✅ Yes" if row.get("found") else "❌ No"
            table.add_row(str(row.get("platform")), found_str, str(row.get("timestamp")))

        return Panel(
            table,
            title="[bold orange3] OSINT Nexus Intelligence Report [/bold orange3]",
            border_style="orange3",
            padding=(1, 2),
        )
