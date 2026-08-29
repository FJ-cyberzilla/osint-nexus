from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from osint_nexus.core.fingerbank.client import FingerbankClient


class StaticDataClient:
    def __init__(self, client: FingerbankClient) -> None:
        self.client = client

    async def download_db(self) -> bytes:
        response = await self.client._get("download/db")
        return response[1].encode("utf-8") if response else b""

    async def download_on_prem_db(self) -> bytes:
        response = await self.client._get("download/on-prem-db")
        return response[1].encode("utf-8") if response else b""

    async def download_ip_blacklist(self) -> bytes:
        response = await self.client._get("download/ip-blacklist")
        return response[1].encode("utf-8") if response else b""

    async def download_destination_hosts(self) -> bytes:
        response = await self.client._get("download/destination-hosts")
        return response[1].encode("utf-8") if response else b""
