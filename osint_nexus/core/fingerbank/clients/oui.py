import json
from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from osint_nexus.core.fingerbank.client import FingerbankClient


class OuiClient:
    def __init__(self, client: FingerbankClient) -> None:
        self.client = client

    async def get_device_id(self, oui: str) -> int:
        response = await self.client._get(f"oui/{oui}/to_device_id")
        if response is None:
            raise ValueError("No response from Fingerbank")
        data: dict[str, Any] = json.loads(response[1])
        return int(data["device_id"])
