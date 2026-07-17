import pytest
import asyncio
from unittest.mock import AsyncMock, MagicMock
from osint_nexus.core.agent import OSINTAgent

@pytest.mark.asyncio
async def test_run_scan_awaits_save_result():
    # Setup
    agent = OSINTAgent(username="testuser")
    
    # Mock provider
    mock_provider = MagicMock()
    mock_provider.name = "test_platform"
    mock_provider.check_username = AsyncMock(return_value=(True, "content"))
    mock_provider.get_dork_query = MagicMock(return_value="dork")
    
    # Mock registry to return our mock provider
    agent.subsystems.registry.get_providers = MagicMock(return_value=[mock_provider])
    
    # Spy on save_result
    agent.subsystems.db.save_result = AsyncMock()
    
    # Mock validator to return True
    agent.subsystems.validator.validate = MagicMock(return_value=True)

    # Execute
    async for _ in agent.run_scan(username="testuser"):
        pass

    # Assert
    agent.subsystems.db.save_result.assert_awaited_once_with("testuser", "test_platform", True)
