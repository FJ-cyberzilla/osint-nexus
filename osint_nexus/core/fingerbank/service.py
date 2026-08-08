from __future__ import annotations

from osint_nexus.core.fingerbank.client import FingerbankClient
from osint_nexus.core.fingerbank.models import InterrogateResponse
from osint_nexus.core.provider_types import MetadataDict
from osint_nexus.utils.network import NetworkManager


class FingerbankInferenceService:
    def __init__(self, network: NetworkManager, api_key: str) -> None:
        self.client = FingerbankClient(network, api_key)

    async def infer(self, content: str, metadata: MetadataDict) -> InterrogateResponse:
        """
        Infer device information using Fingerbank API.
        'content' is ignored here as Fingerbank uses structured parameters in 'metadata'.
        """
        # Based on Fingerbank API docs, extract fields from metadata
        payload = {}
        if "dhcp_fingerprint" in metadata:
            payload["dhcp_fingerprint"] = metadata["dhcp_fingerprint"]
        if "mac" in metadata:
            payload["mac"] = metadata["mac"]
        if "user_agents" in metadata:
            payload["user_agents"] = metadata["user_agents"]

        return await self.client.interrogate(payload)
