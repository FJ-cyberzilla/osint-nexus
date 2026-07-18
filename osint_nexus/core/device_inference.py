"""
Advanced device inference capabilities based on MAC OUI, port heuristics,
banners, and Nmap CPE (Common Platform Enumeration) analysis.
"""

import logging
import re
from collections import defaultdict
from typing import Any

from pydantic import BaseModel, ConfigDict, Field

logger = logging.getLogger("osint_nexus.device_inference")


class DeviceProfile(BaseModel):
    """Structured inference result representing the most likely device state."""

    model_config = ConfigDict(frozen=True)

    device_type: str = Field(default="Unknown", description="e.g., Router, Linux Server, IoT Camera")
    os_guess: str = Field(default="Unknown", description="e.g., Linux, Windows, Cisco IOS")
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    signals: list[str] = Field(default_factory=list, description="Audit trail of matched heuristics")


class DeviceInferenceService:
    def __init__(self) -> None:
        # In production, this should be loaded from the Wireshark `manuf` file or an API.
        self.oui_map = {
            "00:1A:2B": ("Cisco", "Network Equipment"),
            "52:54:00": ("QEMU/KVM", "Virtual Machine"),
            "B8:27:EB": ("Raspberry Pi Foundation", "IoT/SBC"),
            "DC:A6:32": ("Raspberry Pi Foundation", "IoT/SBC"),
            "00:11:32": ("Synology", "NAS"),
        }

    def _normalize_oui(self, mac: str) -> str | None:
        """Extracts a standard XX:XX:XX OUI from any MAC format."""
        cleaned = re.sub(r"[^A-Fa-f0-9]", "", mac).upper()
        if len(cleaned) >= 6:
            return f"{cleaned[0:2]}:{cleaned[2:4]}:{cleaned[4:6]}"
        return None

    def _parse_cpe(self, cpe_str: str) -> dict[str, str] | None:
        """Parses CPE v2.2 and v2.3 strings into their core components."""
        cpe_str = cpe_str.lower().strip()

        # Strip the prefix to align the arrays
        if cpe_str.startswith("cpe:2.3:"):
            parts = cpe_str[8:].split(":")
        elif cpe_str.startswith("cpe:/"):
            parts = cpe_str[5:].split(":")
        else:
            return None

        if len(parts) < 3:
            return None

        part_type_map = {"o": "os", "h": "hardware", "a": "application"}

        return {
            "part": part_type_map.get(parts[0], "unknown"),
            "vendor": parts[1].replace("_", " ").title(),
            "product": parts[2].replace("_", " ").title(),
        }

    def _process_cpes(
        self,
        metadata: dict[str, Any],
        os_scores: dict[str, float],
        type_scores: dict[str, float],
        signals: list[str],
    ) -> None:
        cpes = metadata.get("cpes", [])
        for cpe_str in cpes:
            cpe = self._parse_cpe(cpe_str)
            if not cpe:
                continue

            if cpe["part"] == "os":
                if cpe["vendor"] == "Linux" and "Kernel" in cpe["product"]:
                    os_name = "Linux"
                else:
                    os_name = f"{cpe['vendor']} {cpe['product']}"

                os_scores[os_name] += 0.9
                signals.append(f"OS CPE match: {os_name}")

            elif cpe["part"] == "hardware":
                hw_name = f"{cpe['vendor']} {cpe['product']}"
                type_scores[hw_name] += 0.9
                signals.append(f"Hardware CPE match: {hw_name}")

            elif cpe["part"] == "application":
                app_prod = cpe["product"].lower()
                if app_prod in ["apache", "nginx", "http server", "iis"]:
                    type_scores["Web Server"] += 0.4
                    signals.append(f"Web App CPE ({cpe['product']}) -> leans Web Server")
                elif app_prod in ["openssh", "dropbear"]:
                    type_scores["Server"] += 0.2
                    signals.append(f"SSH App CPE ({cpe['product']}) -> leans Server")
                elif app_prod in ["routeros", "ios"]:
                    type_scores["Network Equipment"] += 0.6
                    signals.append(f"Routing App CPE ({cpe['product']}) -> leans Network Equipment")

    def _process_mac(
        self,
        metadata: dict[str, Any],
        os_scores: dict[str, float],
        type_scores: dict[str, float],
        signals: list[str],
    ) -> None:
        mac = metadata.get("mac_address", "")
        if mac:
            oui = self._normalize_oui(mac)
            if oui and oui in self.oui_map:
                vendor, hw_type = self.oui_map[oui]
                type_scores[hw_type] += 0.4
                signals.append(f"OUI Match: {vendor} ({hw_type})")

                if vendor == "Cisco":
                    os_scores["Cisco IOS"] += 0.5
                elif "Raspberry" in vendor:
                    os_scores["Linux"] += 0.5

    def _process_ports(
        self,
        metadata: dict[str, Any],
        os_scores: dict[str, float],
        type_scores: dict[str, float],
        signals: list[str],
    ) -> None:
        ports = metadata.get("ports", [])
        if isinstance(ports, list):
            if 22 in ports:
                os_scores["Linux"] += 0.3
                type_scores["Server"] += 0.2
                signals.append("Port 22 (SSH) open -> leans Linux Server")
            if 3389 in ports or 445 in ports:
                os_scores["Windows"] += 0.5
                type_scores["Server/Workstation"] += 0.3
                signals.append("Port 3389/445 open -> leans Windows")
            if 80 in ports or 443 in ports:
                type_scores["Web Server"] += 0.2
            if 554 in ports or 8000 in ports:
                type_scores["IoT Camera"] += 0.4
                signals.append("RTSP/Camera ports detected")

    def _process_content(
        self,
        content: str,
        os_scores: dict[str, float],
        type_scores: dict[str, float],
        signals: list[str],
    ) -> None:
        if content:
            content_lower = content.lower()
            if "ubuntu" in content_lower or "debian" in content_lower:
                os_scores["Linux"] += 0.6
                signals.append("Linux distro signature found in banner")
            if "iis/" in content_lower:
                os_scores["Windows"] += 0.6
                type_scores["Web Server"] += 0.4
                signals.append("IIS Server signature found -> Windows")
            if "mikrotik" in content_lower or "routeros" in content_lower:
                os_scores["RouterOS"] += 0.8
                type_scores["Network Equipment"] += 0.6
                signals.append("MikroTik signature found in banner")

    def infer(self, content: str, metadata: dict[str, Any]) -> DeviceProfile:
        """
        Accumulates evidence from CPEs, MAC, ports, and banners to infer device profile.
        """
        signals: list[str] = []
        os_scores: dict[str, float] = defaultdict(float)
        type_scores: dict[str, float] = defaultdict(float)

        try:
            self._process_cpes(metadata, os_scores, type_scores, signals)
            self._process_mac(metadata, os_scores, type_scores, signals)
            self._process_ports(metadata, os_scores, type_scores, signals)
            self._process_content(content, os_scores, type_scores, signals)

            # Resolve Winners
            best_os = max(os_scores.items(), key=lambda x: x[1], default=("Unknown", 0.0))
            best_type = max(type_scores.items(), key=lambda x: x[1], default=("Unknown", 0.0))

            raw_confidence = best_os[1] + best_type[1]
            final_confidence = min(1.0, raw_confidence)

            if final_confidence == 0.0:
                signals.append("No heuristics matched")

            return DeviceProfile(
                device_type=best_type[0],
                os_guess=best_os[0],
                confidence=round(final_confidence, 2),
                signals=signals,
            )

        except (TypeError, ValueError, AttributeError) as e:
            logger.error("Data parsing error during device inference: %s", e)
            return DeviceProfile(signals=[f"Inference failed: {str(e)}"])
