from __future__ import annotations

from typing import TYPE_CHECKING

from osint_nexus.core.fingerbank.models import AccountInfo

if TYPE_CHECKING:
    from osint_nexus.core.fingerbank.client import FingerbankClient


class UsersClient:
    def __init__(self, client: FingerbankClient) -> None:
        self.client = client

    async def get_account_info(self, account_key: str) -> AccountInfo:
        response = await self.client._get(f"users/account_info/{account_key}")
        if response is None:
            raise ValueError("No response from Fingerbank")
        return AccountInfo.model_validate(response.json())
