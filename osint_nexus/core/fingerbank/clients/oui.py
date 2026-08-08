from __future__ import annotations

from typing import Any


class OuiClient:
    def __init__(self, client: Any) -> None:
        self.client = client

    async def get_device_id(self, oui: str) -> int:
        response = await self.client._get(f"oui/{oui}/to_device_id")
        return response.json()["device_id"]
