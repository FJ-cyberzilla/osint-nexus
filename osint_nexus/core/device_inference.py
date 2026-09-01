from __future__ import annotations

import re
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Iterator, TypedDict, cast

from beartype import beartype
from pydantic import BaseModel, Field

from osint_nexus.core.db.fingerprint_repository import FingerprintRepository
from osint_nexus.core.detectors.base import FingerprintStrategy
from osint_nexus.core.detectors.registry import FingerprintStrategyRegistry
from osint_nexus.core.type_defs import JSONValue, TelemetryDict, TelemetryValue, to_json_value, JSONListContainer
from osint_nexus.utils.data_loader import load_data

# Re-alias for local use or update code
# Since FingerprintStrategy now takes (T_Data, T_Result), I need to update all implementations.
# For now, I will use FingerprintStrategy[T_Data, FingerprintResult]


class PortMapping(TypedDict):
    """Mapping structure for port to OS/role inference."""

    os: list[str]
    role: str


@beartype
@dataclass(frozen=True)
class FingerprintResult(Mapping[str, JSONValue]):
    """Result structure from a fingerprinting strategy."""

    name: str
    data: dict[str, JSONValue]
    confidence: float

    def __getitem__(self, key: str) -> JSONValue:
        if key == "name":
            return self.name
        if key == "data":
            return cast(JSONValue, self.data)
        if key == "confidence":
            return cast(JSONValue, self.confidence)
        raise KeyError(key)

    def __iter__(self) -> Iterator[str]:
        return iter(["name", "data", "confidence"])

    def __len__(self) -> int:
        return 3


class HttpFingerprintStrategy(FingerprintStrategy[dict[str, JSONValue], FingerprintResult]):
    """Strategy for parsing HTTP headers for device info."""

    name: str = "http_headers"

    @beartype
    def extract(self, data: dict[str, JSONValue]) -> FingerprintResult:
        # More precise: ensure all header values are strings
        headers = {k: str(v) for k, v in data.items()}

        # Deep extraction of all Sec-CH-UA headers
        sec_ch_ua_headers = {k: v for k, v in headers.items() if k.lower().startswith("sec-ch-ua")}

        fingerprint: dict[str, JSONValue] = {
            "platform": headers.get("sec-ch-ua-platform"),
            "mobile": headers.get("sec-ch-ua-mobile") == "?1",
            "architecture": headers.get("sec-ch-ua-arch"),
            "language": headers.get("accept-language"),
            "full_headers": cast(JSONValue, sec_ch_ua_headers),
        }

        return FingerprintResult(self.name, fingerprint, 0.85)


class TlsFingerprintStrategy(FingerprintStrategy[str, FingerprintResult]):
    """Strategy for TLS (JA3) fingerprinting."""

    name: str = "tls_ja3"

    def __init__(self, repo: FingerprintRepository | None = None) -> None:
        self.repo = repo or FingerprintRepository()

    @beartype
    def extract(self, data: str) -> FingerprintResult:
        # Expecting data to be the ja3 hash string
        ja3_hash = data

        device_info = self.repo.get_signature("ja3", ja3_hash)

        return FingerprintResult(
            self.name,
            {"ja3_hash": ja3_hash, "inferred_device": cast(JSONValue, device_info)},
            0.90 if device_info is not None else 0.10,
        )


class TcpData(TypedDict):
    ttl: int
    window_size: int
    tcp_options: JSONListContainer


class TcpFingerprintStrategy(FingerprintStrategy[TcpData, FingerprintResult]):
    """Strategy for TCP/IP stack fingerprinting (TTL/Window/Options)."""

    name: str = "tcp_stack"

    @beartype
    def extract(self, data: TcpData) -> FingerprintResult:
        # Expecting data: {"ttl": int, "window_size": int, "tcp_options": list[JSONValue]}
        ttl = data.get("ttl", 0)
        options_container = data.get("tcp_options", JSONListContainer(data=[]))
        options = options_container.data

        fingerprint, confidence = self._detect_os(ttl, options)

        return FingerprintResult(
            "tcp_stack",
            {"inferred_os": cast(JSONValue, fingerprint)},
            confidence,
        )

    def _detect_os(self, ttl: int, options: list[JSONValue]) -> tuple[str | None, float]:
        """Detect OS based on TCP parameters."""
        if ttl == 128:
            return self._detect_windows(options)
        if ttl == 64:
            return self._detect_linux_macos(options)
        if ttl == 255:
            return "Network device (Cisco/Juniper)", 0.9
        return None, 0.1

    def _detect_windows(self, options: list[JSONValue]) -> tuple[str, float]:
        if "wscale" in options:
            return "Windows 10/11", 0.85
        return "Windows (older)", 0.7

    def _detect_linux_macos(self, options: list[JSONValue]) -> tuple[str, float]:
        if "timestamps" in options and "sack" in options:
            return "Linux (modern)", 0.75
        if "timestamps" in options:
            return "macOS/iOS", 0.7
        return "Linux (older)", 0.5


class InferenceResult(BaseModel):
    """Structured data payload containing inferred device signatures."""

    target: str
    manufacturer: str | None = Field(default=None, description="Inferred from MAC OUI mapping")
    possible_os: list[str] = Field(default_factory=list, description="Inferred OS fingerprints")
    detected_roles: list[str] = Field(default_factory=list, description="Inferred device functionalities")
    confidence_score: int = Field(default=50, ge=0, le=100)


class DeviceProfile(TypedDict):
    device_model: str | None
    hardware_tier: str | None
    anomaly_detected: bool
    throttle_status: str | None
    raw_telemetry: Mapping[str, TelemetryValue]


class DeviceInferenceNetworkEngine:
    """Provides production-grade device context signatures based on network heuristics."""

    # Static SOTA fingerprint matrices for performance mapping
    COMMON_PORT_MAP: dict[int, PortMapping] = {
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

    OUI_DATABASE: dict[str, str] = load_data("oui.json")

    def __init__(self) -> None:
        pass

    def _get_os_from_mappings(self, mappings: list[PortMapping]) -> list[str]:
        """Extract OS from mappings."""
        inferred = {os_name for m in mappings for os_name in m["os"]}
        return list(inferred)

    def _get_roles_from_mappings(self, mappings: list[PortMapping]) -> list[str]:
        """Extract roles from mappings."""
        roles = [m["role"] for m in mappings]
        return roles

    def _calculate_confidence(self, mappings: list[PortMapping], open_ports: list[int]) -> int:
        """Calculate confidence score."""
        if not mappings:
            return 0
        return min(50 + len(mappings) * 10, 95)

    async def infer_by_ports(self, target_host: str, open_ports: list[int]) -> InferenceResult:
        """Analyzes a sequence of open target ports to map likely OS and system profiles."""
        mappings = [self.COMMON_PORT_MAP[p] for p in open_ports if p in self.COMMON_PORT_MAP]

        return InferenceResult(
            target=target_host,
            manufacturer=None,
            possible_os=self._get_os_from_mappings(mappings),
            detected_roles=self._get_roles_from_mappings(mappings),
            confidence_score=self._calculate_confidence(mappings, open_ports),
        )

    async def infer(self, content: str, metadata: dict[str, list[int] | str]) -> InferenceResult:
        """Helper to infer device profile based on metadata presence."""
        if "ports" in metadata and isinstance(metadata["ports"], list):
            return await self.infer_by_ports("target", metadata["ports"])
        if "mac_address" in metadata and isinstance(metadata["mac_address"], str):
            # MAC address is present, prioritize OUI-based manufacturer inference.
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

    def __init__(self, registry: FingerprintStrategyRegistry | None = None) -> None:
        self.registry = registry or FingerprintStrategyRegistry()

    @beartype
    def infer(self, raw_data: JSONValue) -> Mapping[str, Mapping[str, JSONValue]]:
        """Aggregate results from all registered strategies."""
        results: dict[str, Mapping[str, JSONValue]] = {}
        for strategy in self.registry.get_all():
            # Cast to the common base strategy type for inference.
            typed_strategy = cast(FingerprintStrategy[JSONValue, FingerprintResult], strategy)
            result = typed_strategy.extract(raw_data)
            results[strategy.name] = {
                "data": result.data,
                "confidence": cast(JSONValue, result.confidence),
            }
        return results

    def analyze(self, data: TelemetryDict) -> DeviceProfile:
        """
        Analyzes telemetry and returns a structured DeviceProfile.
        """
        aggregated_results = self.infer(to_json_value(data))

        # Heuristics-based profile construction
        tcp_result = aggregated_results.get("tcp_stack", {"data": {"inferred_os": None}, "confidence": 0})

        # Determine model/OS based on high-confidence inference
        # Cast to dict[str, JSONValue] to access "data" and "inferred_os"
        tcp_data = cast(dict[str, JSONValue], tcp_result.get("data", {}))
        model = tcp_data.get("inferred_os")

        # Simple tier heuristic
        hardware_tier = None
        if isinstance(model, str):
            hardware_tier = "Standard"
            if model.lower().startswith("network"):
                hardware_tier = "Enterprise"
            elif model.lower().startswith("windows"):
                hardware_tier = "High-Performance"

        return DeviceProfile(
            device_model=model if isinstance(model, str) else None,
            hardware_tier=hardware_tier,
            anomaly_detected=self._detect_anomaly(data),
            throttle_status=None,
            raw_telemetry=data,
        )

    def _detect_anomaly(self, data: TelemetryDict) -> bool:
        """Heuristic check for telemetry anomalies."""
        # Check for extreme TTL values indicative of spoofing
        ttl = data.get("ttl")
        return isinstance(ttl, int) and (ttl < 1 or ttl > 255)
