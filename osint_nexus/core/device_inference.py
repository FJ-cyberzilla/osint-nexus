import re
from typing import Any, TypedDict

from pydantic import BaseModel, Field


class InferenceResult(BaseModel):
    """Structured data payload containing inferred device signatures."""

    target: str
    manufacturer: str | None = Field(default=None, description="Inferred from MAC OUI mapping")
    possible_os: list[str] = Field(default_factory=list, description="Inferred OS fingerprints")
    detected_roles: list[str] = Field(default_factory=list, description="Inferred device functionalities")
    confidence_score: int = Field(default=50, ge=0, le=100)


class DeviceProfile(TypedDict):
    device_model: str
    hardware_tier: str
    anomaly_detected: bool
    throttle_status: str | None
    raw_telemetry: dict[str, Any]


class DeviceInferenceService:
    """Provides production-grade device context signatures based on network heuristics."""

    # Static SOTA fingerprint matrices for performance mapping
    COMMON_PORT_MAP: dict[int, dict[str, Any]] = {
        21: {"os": ["Linux", "Unix"], "role": "File Transfer (FTP)"},
        22: {"os": ["Linux", "Unix"], "role": "Remote Management (SSH)"},
        25: {"os": ["Linux", "Unix"], "role": "Mail Transfer (SMTP)"},
        80: {"os": ["Linux", "Windows Server"], "role": "Web Host (HTTP)"},
        443: {"os": ["Linux", "Windows Server"], "role": "Secure Web Host (HTTPS)"},
        445: {"os": ["Windows"], "role": "File Server (SMB)"},
        3306: {"os": ["Linux", "Unix"], "role": "Database (MySQL)"},
        3389: {"os": ["Windows"], "role": "Remote Desktop (RDP)"},
        5432: {"os": ["Linux", "Unix"], "role": "Database (PostgreSQL)"},
        5555: {"os": ["Android (ADB)"], "role": "Mobile Debug Node"},
    }

    OUI_DATABASE: dict[str, str] = {
        "00:1A:11": "Google LLC",
        "00:25:90": "Super Micro Computer, Inc.",
        "A4:77:33": "Apple, Inc.",
        "2C:F0:EE": "Intel Corporation",
        "D4:A1:48": "Ubiquiti Networks",
    }

    def __init__(self) -> None:
        pass

    def _get_os_from_mappings(self, mappings: list[dict[str, Any]]) -> list[str]:
        """Extract OS from mappings."""
        inferred = {os for m in mappings for os in m["os"]}
        return list(inferred) or ["Unknown OS"]

    def _get_roles_from_mappings(self, mappings: list[dict[str, Any]]) -> list[str]:
        """Extract roles from mappings."""
        roles = [m["role"] for m in mappings]
        return roles or ["No clear exposed roles"]

    def _calculate_confidence(self, mappings: list[dict[str, Any]], open_ports: list[int]) -> int:
        """Calculate confidence score."""
        if not mappings:
            return 0
        return min(50 + len(mappings) * 10, 95)

    async def infer_by_ports(self, target_host: str, open_ports: list[int]) -> InferenceResult:
        """Analyzes a sequence of open target ports to map likely OS and system profiles."""
        mappings = [self.COMMON_PORT_MAP[p] for p in open_ports if p in self.COMMON_PORT_MAP]

        return InferenceResult(
            target=target_host,
            manufacturer="Unknown Host",
            possible_os=self._get_os_from_mappings(mappings),
            detected_roles=self._get_roles_from_mappings(mappings),
            confidence_score=self._calculate_confidence(mappings, open_ports),
        )

    async def infer(self, content: str, metadata: dict[str, Any]) -> InferenceResult:
        """Helper to infer device profile based on metadata presence."""
        if "ports" in metadata:
            return await self.infer_by_ports("target", metadata["ports"])
        if "mac_address" in metadata:
            # Fallback for now if mac_address is present
            return InferenceResult(
                target="target", manufacturer=await self.infer_by_mac(metadata["mac_address"])
            )
        return InferenceResult(target="target")

    async def infer_by_mac(self, mac_address: str) -> str | None:
        """Extracts manufacturer context out of a target MAC address string via OUI mapping.

        Supports standard colon, hyphen, or packed hex string formats cleanly.
        """
        # Standardize formatting down to an uppercase colon-separated layout
        clean_mac = re.sub(r"[^a-fA-F0-9]", "", mac_address).upper()
        if len(clean_mac) < 6:
            return "Invalid Address Segment"

        # Isolate the Organizationally Unique Identifier (First 3 bytes)
        oui_segment = f"{clean_mac[0:2]}:{clean_mac[2:4]}:{clean_mac[4:6]}"
        return self.OUI_DATABASE.get(oui_segment, "Generic/Unregistered Manufacturer")


class DeviceInferenceEngine:
    """Parses raw hardware telemetry and maps them against known device profiles."""

    def __init__(self) -> None:
        self.gpu_database: dict[str, dict[str, str]] = {
            "Adreno (TM) 740": {
                "model": "Snapdragon 8 Gen 2 (Galaxy S23 / Pixel 8)",
                "tier": "High-End",
            },
            "Adreno (TM) 650": {
                "model": "Snapdragon 865 (Galaxy S20)",
                "tier": "Mid-High",
            },
            "Mali-G710": {
                "model": "MediaTek Dimensity / Tensor G2",
                "tier": "Flagship",
            },
        }

    def analyze(self, telemetry_data: dict[str, Any]) -> DeviceProfile:
        result: DeviceProfile = {
            "device_model": "Unknown",
            "hardware_tier": "Unknown",
            "anomaly_detected": False,
            "throttle_status": None,
            "raw_telemetry": telemetry_data,
        }

        renderer = str(telemetry_data.get("webgl_renderer", ""))

        for signature, details in self.gpu_database.items():
            if signature in renderer:
                result["device_model"] = details["model"]
                result["hardware_tier"] = details["tier"]
                break

        cpu_time = float(telemetry_data.get("cpu_benchmark_ms", 0.0))
        if cpu_time > 50.0:
            result["anomaly_detected"] = True
            result["throttle_status"] = "Active thermal or power saving state detected"

        return result
