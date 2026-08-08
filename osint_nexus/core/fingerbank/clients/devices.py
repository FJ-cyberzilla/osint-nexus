from __future__ import annotations

from typing import Any

from osint_nexus.core.fingerbank.models import Device, DeviceVulnerabilities


class DevicesClient:
    def __init__(self, client: Any) -> None:
        self.client = client

    async def get_device(self, device_id: int) -> Device:
        response = await self.client._get(f"devices/{device_id}")
        return Device.from_dict(response.json())

    async def get_vulnerabilities(self, device_id: int) -> DeviceVulnerabilities:
        response = await self.client._get(f"devices/{device_id}/vulnerabilities")
        return DeviceVulnerabilities.from_dict(response.json())
