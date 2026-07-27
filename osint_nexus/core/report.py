from typing import Any

from pydantic import BaseModel
from rich.console import Console
from rich.panel import Panel
from rich.table import Table


class TelemetryPayload(BaseModel):
    browser: Any = None
    raw_metadata: dict[str, Any]
    pipeline_status: str


class AdvancedReportGenerator:
    """Consolidates cross-subsystem telemetry and prints aesthetic structural threat summaries."""

    def __init__(self) -> None:
        self.console = Console()

    def render_hardware_intelligence(self, target_username: str, anti_spoof_data: dict[str, Any]) -> None:
        """Generates a premium operational layout wrapping device integrity and footprint anomalies."""
        self._render_banner(target_username, anti_spoof_data)

        # 2. Heuristic Metric Evaluation Table
        metrics_table = Table(
            title="📊 Telemetry Layer Verification",
            title_style="bold dim",
            show_header=True,
            header_style="bold orange3",
        )
        metrics_table.add_column("Vector Attribute", style="cyan")
        metrics_table.add_column("Observed Value", justify="center")
        metrics_table.add_column("Engine Status Assessment", justify="left")

        self._add_metrics_rows(metrics_table, anti_spoof_data)

        self.console.print(metrics_table)
        self.console.print("\n")

    def _render_banner(self, target_username: str, anti_spoof_data: dict[str, Any]) -> None:
        is_poisoned = anti_spoof_data.get("is_poisoned", False)
        status_color = "bold red" if is_poisoned else "bold green"
        verdict_text = "⚠️ DECEPTIVE PROFILE" if is_poisoned else "✅ CONSISTENT (AUTHENTIC)"

        banner_content = (
            f"Target Identifier : [bold orange3]{target_username}[/bold orange3]\n"
            f"Hardware Integrity : [{status_color}]{verdict_text}[/{status_color}]\n"
            f"Anomalous Vector   : [dim]{anti_spoof_data.get('anomaly_type', 'N/A')}[/dim]"
        )

        self.console.print(
            Panel(
                banner_content,
                title="[bold orange3] ░█▀█░█▀▀░█░█░█░█░█▀▀ ░░░ ▀█▀░█▀█░█▀▀░█░█░▀█▀ [/bold orange3]",
                border_style="orange3",
                expand=False,
            )
        )

    def _add_metrics_rows(self, table: Table, anti_spoof_data: dict[str, Any]) -> None:
        entropy = anti_spoof_data.get("shannon_entropy", 0.0)
        entropy_status = (
            "[red]CRITICAL (Noise Injected)[/red]"
            if entropy > 4.2
            else "[green]NORMAL (Native Subpixel)[/green]"
        )
        table.add_row("Canvas Shannon Entropy", f"{entropy:.2f}", entropy_status)

        latency = anti_spoof_data.get("render_time_ms", 0.0)
        latency_status = (
            "[red]SUSPICIOUS (Bot/Cache)[/red]" if latency < 1.0 else "[green]NORMAL (Hardware Delay)[/green]"
        )
        table.add_row("Execution Latency", f"{latency} ms", latency_status)

        ua_status = (
            "[yellow]MISMATCH (Header Altered)[/yellow]"
            if "Mismatch" in anti_spoof_data.get("anomaly_type", "")
            else "[green]VERIFIED[/green]"
        )
        table.add_row(
            "User-Agent Crosscheck", anti_spoof_data.get("reported_user_agent", "Unknown"), ua_status
        )
