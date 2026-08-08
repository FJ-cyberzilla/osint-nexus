from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from osint_nexus.core.agent import OSINTAgent


@pytest.mark.asyncio
async def test_run_scan_awaits_save_result() -> None:
    # Setup
    agent = OSINTAgent(username="testuser")

    # Mock provider
    mock_provider = MagicMock()
    mock_provider.name = "test_platform"
    mock_provider.check_username = AsyncMock(return_value=(True, "content"))
    mock_provider.get_dork_query = MagicMock(return_value="dork")

    # Spy on save_result
    with (
        patch.object(agent.subsystems.registry, "get_providers", return_value=[mock_provider]),
        patch.object(agent.subsystems.db, "save_result", new_callable=AsyncMock) as mock_save,
        patch.object(agent.subsystems.validator, "validate", return_value=True),
    ):
        # Execute
        async for _ in agent.run_scan(username="testuser"):
            pass

        # Assert
        mock_save.assert_awaited_once_with("testuser", "test_platform", True)
