from __future__ import annotations

from typing import Any

from osint_nexus.core.fingerbank.models import AccountInfo


class UsersClient:
    def __init__(self, client: Any) -> None:
        self.client = client

    async def get_account_info(self, account_key: str) -> AccountInfo:
        response = await self.client._get(f"users/account_info/{account_key}")
        return AccountInfo.from_dict(response.json())
