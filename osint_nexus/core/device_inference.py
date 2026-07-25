import re
from typing import Dict, Any, List, Optional
from pydantic import BaseModel, Field

class InferenceResult(BaseModel):
    """Structured data payload containing inferred device signatures."""
    target: str
    manufacturer: Optional[str] = Field(default=None, description="Inferred from MAC OUI mapping")
    possible_os: List[str] = Field(default_factory=list, description="Inferred OS fingerprints")
    detected_roles: List[str] = Field(default_factory=list, description="Inferred device functionalities")
    confidence_score: int = Field(default=50, ge=0, le=100)


class DeviceInferenceService:
    """Provides production-grade device context signatures based on network heuristics."""

    # Static SOTA fingerprint matrices for performance mapping
    COMMON_PORT_MAP: Dict[int, Dict[str, Any]] = {
        22: {"os": ["Linux", "Unix"], "role": "Remote Management (SSH)"},
        80: {"os": ["Linux", "Windows Server"], "role": "Web Host (HTTP)"},
        443: {"os": ["Linux", "Windows Server"], "role": "Secure Web Host (HTTPS)"},
        445: {"os": ["Windows"], "role": "File Server (SMB)"},
        3389: {"os": ["Windows"], "role": "Remote Desktop (RDP)"},
        5555: {"os": ["Android (ADB)"], "role": "Mobile Debug Node"},
    }

    OUI_DATABASE: Dict[str, str] = {
        "00:1A:11": "Google LLC",
        "00:25:90": "Super Micro Computer, Inc.",
        "A4:77:33": "Apple, Inc.",
        "2C:F0:EE": "Intel Corporation",
        "D4:A1:48": "Ubiquiti Networks",
    }

    def __init__(self) -> None:
        pass

    async def infer_by_ports(self, target_host: str, open_ports: List[int]) -> InferenceResult:
        """Analyzes a sequence of open target ports to map likely OS and system profiles.

        Args:
            target_host: The IP or domain under evaluation.
            open_ports: A list of integers representing verified open network ports.
        """
        inferred_os: set[str] = set()
        roles: list[str] = []
        weight = 50

        for port in open_ports:
            mapping = self.COMMON_PORT_MAP.get(port)
            if mapping:
                inferred_os.update(mapping["os"])
                roles.append(mapping["role"])
                weight = min(weight + 10, 95)  # Cap structural confidence at 95%

        os_list = list(inferred_os) if inferred_os else ["Unknown OS"]
        role_list = roles if roles else ["No clear exposed roles"]
        final_weight = weight if open_ports else 0

        return InferenceResult(
            target=target_host,
            manufacturer="Unknown Host",
            possible_os=os_list,
            detected_roles=role_list,
            confidence_score=final_weight,
        )

    async def infer(self, content: str, metadata: dict[str, Any]) -> InferenceResult:
        """Helper to infer device profile based on metadata presence."""
        if "ports" in metadata:
            return await self.infer_by_ports("target", metadata["ports"])
        if "mac_address" in metadata:
            # Fallback for now if mac_address is present
            return InferenceResult(target="target", manufacturer=await self.infer_by_mac(metadata["mac_address"]))
        return InferenceResult(target="target")

    async def infer_by_mac(self, mac_address: str) -> Optional[str]:
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


