from __future__ import annotations

from typing import Any


class StaticDataClient:
    def __init__(self, client: Any) -> None:
        self.client = client

    async def download_db(self) -> bytes:
        response = await self.client._get("download/db")
        return response.content

    async def download_on_prem_db(self) -> bytes:
        response = await self.client._get("download/on-prem-db")
        return response.content

    async def download_ip_blacklist(self) -> bytes:
        response = await self.client._get("download/ip-blacklist")
        return response.content

    async def download_destination_hosts(self) -> bytes:
        response = await self.client._get("download/destination-hosts")
        return response.content
