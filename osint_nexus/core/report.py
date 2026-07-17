"""
Handles telemetry collection, data structuring, and report generation for OSINT scans.
Supports structured JSON output and human-readable terminal summaries.
"""
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Union

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("osint_nexus.report")

class ScanReport(BaseModel):
    """Structured representation of a complete OSINT scan."""
    model_config = ConfigDict(frozen=True)

    timestamp: str = Field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    target: str = Field(default="Unknown")
    total_platforms_found: int = Field(default=0)
    platforms: List[str] = Field(default_factory=list)
    confidence_score: float = Field(default=0.0)
    device_intelligence: Dict[str, Any] = Field(default_factory=dict)
    telemetry: Dict[str, Any] = Field(default_factory=dict)
    scan_duration_sec: Optional[float] = Field(default=None)


class ReportGenerator:
    def __init__(
        self, 
        fingerprint_agent: Any, 
        evasion_agent: Any, 
        confidence_engine: Any
    ) -> None:
        self.fingerprint_agent = fingerprint_agent
        self.evasion_agent = evasion_agent
        self.confidence_engine = confidence_engine

    def collect_telemetry(self) -> Dict[str, Any]:
        """
        Safely collects telemetry data. If evasion or fingerprinting fails, 
        it gracefully degrades rather than crashing the final report.
        """
        try:
            # Safely extract evasion metrics (fallback to None if methods are missing)
            proxy = getattr(self.evasion_agent, "get_proxy", lambda: None)()
            user_agent = getattr(self.evasion_agent, "get_user_agent", lambda: "Default/1.0")()

            # Pass to fingerprint agent
            return self.fingerprint_agent.collect_scan_telemetry(proxy, user_agent)
            
        except Exception as exc:
            logger.error("Failed to collect scan telemetry: %s", exc)
            return {"status": "degraded", "error": str(exc)}

    def build_structured_report(
        self, 
        target: str,
        found_platforms: List[str], 
        inferred_device: Union[Dict[str, Any], Any],
        duration: Optional[float] = None
    ) -> ScanReport:
        """
        Builds a comprehensive, strictly-typed Pydantic model of the scan results
        that can be easily exported to an API, Database, or JSON file.
        """
        # Calculate confidence using the external engine
        try:
            confidence_result = self.confidence_engine.calculate_confidence(found_platforms)
            confidence = confidence_result.score
        except Exception as e:
            logger.warning("Confidence calculation failed, defaulting to 0.0: %s", e)
            confidence = 0.0

        # Handle both the old raw Dict and the new Pydantic DeviceProfile
        device_data = {}
        if hasattr(inferred_device, "model_dump"):
            device_data = inferred_device.model_dump(mode="json")
        elif isinstance(inferred_device, dict):
            device_data = inferred_device
        else:
            device_data = {"raw": str(inferred_device)}

        return ScanReport(
            target=target,
            total_platforms_found=len(found_platforms),
            platforms=found_platforms,
            confidence_score=confidence,
            device_intelligence=device_data,
            telemetry=self.collect_telemetry(),
            scan_duration_sec=duration
        )

    def generate_summary(
        self, 
        found_platforms: List[str], 
        inferred_device: Union[Dict[str, Any], Any],
        target: str = "Unknown"
    ) -> str:
        """
        Generates a clean, human-readable terminal/Markdown summary of the scan.
        Maintains backwards compatibility with previous caller signatures.
        """
        # 1. Build the data model
        report = self.build_structured_report(target, found_platforms, inferred_device)

        # 2. Format the Device string intelligently based on the new DeviceProfile
        device_str = "Unknown"
        # Log for debugging
        logger.debug("Formatting device intelligence: %s", report.device_intelligence)
        
        # Check for dictionary keys if report.device_intelligence is a dict
        if isinstance(report.device_intelligence, dict):
            dtype = report.device_intelligence.get('device_type', 'Unknown')
            os_guess = report.device_intelligence.get('os_guess', 'Unknown')
            dev_conf = report.device_intelligence.get('confidence', 0.0)
            
            if dtype != "Unknown" or os_guess != "Unknown":
                device_str = f"{dtype} running {os_guess} (Conf: {dev_conf:.2f})"
            else:
                device_str = "Unknown Device Context"
        elif hasattr(report.device_intelligence, "device_type"):
            # Handle object if returned
            dtype = getattr(report.device_intelligence, 'device_type', 'Unknown')
            os_guess = getattr(report.device_intelligence, 'os_guess', 'Unknown')
            dev_conf = getattr(report.device_intelligence, 'confidence', 0.0)
            
            if dtype != "Unknown" or os_guess != "Unknown":
                device_str = f"{dtype} running {os_guess} (Conf: {dev_conf:.2f})"
            else:
                device_str = "Unknown Device Context"
        else:
            # Last resort fallback
            device_str = str(report.device_intelligence) if report.device_intelligence else "Unknown Device Context"

        # 3. Format Telemetry compactly
        telem_str = ", ".join(f"{k}: {v}" for k, v in report.telemetry.items() if k != "error")
        if not telem_str:
            telem_str = "No telemetry available"

        # 4. Construct the UI representation
        summary = [
            f"[bold orange]=== OSINT Scan Report: {report.target} ===[/]",
            f"[orange]──────────────────────────────────────────[/]",
            f"[bold white]Timestamp:[/]\t[cyan]{report.timestamp}[/]",
            f"[bold white]Platforms:[/]\t[bold {'green' if report.total_platforms_found > 0 else 'red'}]{report.total_platforms_found} found[/]",
            f"[orange]──────────────────────────────────────────[/]",
            f"[bold white]Matches:[/]\t{'[green]' + ', '.join(report.platforms) + '[/]' if report.platforms else '[red]None[/]'}",
            f"[bold white]Confidence:[/]\t[bold {'green' if report.confidence_score > 0.5 else 'yellow'}]{report.confidence_score:.2f}/1.0[/]",
            f"[orange]──────────────────────────────────────────[/]",
            f"[bold white]Device Info:[/]\t[dim]{device_str}[/]",
            f"[bold white]Environment:[/]\t[dim]{telem_str}[/]",
            "[orange]──────────────────────────────────────────[/]"
        ]

        return "\n".join(summary)

    def export_json(self, target: str, found_platforms: List[str], inferred_device: Any) -> str:
        """Helper to quickly generate a JSON string for webhooks or file saving."""
        report = self.build_structured_report(target, found_platforms, inferred_device)
        return report.model_dump_json(indent=2)
