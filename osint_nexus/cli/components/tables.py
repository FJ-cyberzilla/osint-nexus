from enum import Enum
from typing import Self

from beartype import beartype
from rich.table import Table


class AccountStatus(Enum):
    ACTIVE = "ACTIVE"
    DORMANT = "DORMANT"
    NOT_FOUND = "NOT_FOUND"


@beartype
class TableRenderer:
    def __init__(self: Self) -> None:
        self.title: str = "Target Intelligence Correlation"

    @beartype
    def build_findings_table(self: Self, results: list[tuple[str, str, AccountStatus, float, str]]) -> Table:
        table: Table = Table(title=self.title, show_header=True, header_style="bold cyan")
        table.add_column(header="Platform", style="bold white")
        table.add_column(header="Handle", style="bold magenta")
        table.add_column(header="Status", style="bold")
        table.add_column(header="Confidence", justify="right")
        table.add_column(header="Escalation Tier", style="dim yellow")

        for platform, handle, status, confidence, tier in results:
            status_style: str = "bold green"
            if status == AccountStatus.DORMANT:
                status_style = "bold yellow"
            elif status == AccountStatus.NOT_FOUND:
                status_style = "bold red"

            conf_str: str = f"{confidence * 100:.1f}%"
            table.add_row(
                platform, handle, f"[{status_style}]{status.value}[/{status_style}]", conf_str, tier
            )

        return table
