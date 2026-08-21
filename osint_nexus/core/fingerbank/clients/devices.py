from __future__ import annotations

from typing import TYPE_CHECKING

from osint_nexus.core.fingerbank.models import Device, DeviceVulnerabilities

if TYPE_CHECKING:
    from osint_nexus.core.fingerbank.client import FingerbankClient


class DevicesClient:
    def __init__(self, client: FingerbankClient) -> None:
        self.client = client

    async def get_device(self, device_id: int) -> Device:
        response = await self.client._get(f"devices/{device_id}")
        if response is None:
            raise ValueError("No response from Fingerbank")
        return Device.model_validate(response.json())

    async def get_vulnerabilities(self, device_id: int) -> DeviceVulnerabilities:
        response = await self.client._get(f"devices/{device_id}/vulnerabilities")
        if response is None:
            raise ValueError("No response from Fingerbank")
        return DeviceVulnerabilities.model_validate(response.json())
