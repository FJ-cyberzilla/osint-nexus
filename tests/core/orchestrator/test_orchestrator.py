from unittest.mock import AsyncMock, MagicMock

import pytest

from osint_nexus.core.extractor import PivotExtractor
from osint_nexus.core.fingerprint import FingerprintAgent
from osint_nexus.core.mimicry import HumanMimicryEngine
from osint_nexus.core.orchestrator import OrchestratorDeps, ScanOrchestrator
from osint_nexus.core.orchestrator.type_defs import HealthCheckProtocol
from osint_nexus.core.provider_types import DatabaseManagerProtocol, ValidatorProtocol
from osint_nexus.utils.network import NetworkManager


@pytest.mark.asyncio
async def test_scan_orchestrator_run_scan() -> None:
    # Setup mocks
    mock_health = MagicMock(spec=HealthCheckProtocol)
    mock_health.is_healthy = AsyncMock(return_value=True)
    mock_health.record_success = AsyncMock()
    mock_health.record_failure = AsyncMock()
    mock_validator = MagicMock(spec=ValidatorProtocol)
    mock_db = MagicMock(spec=DatabaseManagerProtocol)
    mock_db.save_result = AsyncMock()  # Must be AsyncMock
    mock_network = MagicMock(spec=NetworkManager)
    mock_mimicry = MagicMock(spec=HumanMimicryEngine)
    mock_extractor = MagicMock(spec=PivotExtractor)
    mock_extractor.extract = AsyncMock(return_value={})
    mock_fingerprint = MagicMock(spec=FingerprintAgent)

    deps = OrchestratorDeps(
        health=mock_health,
        validator=mock_validator,
        db_manager=mock_db,
        network=mock_network,
        mimicry=mock_mimicry,
        extractor=mock_extractor,
        fingerprint=mock_fingerprint,
    )
    mock_detection = MagicMock()
    mock_detection.analyze = AsyncMock(return_value=MagicMock(evasion_score=0.0))  # Must be AsyncMock
    orchestrator = ScanOrchestrator(deps, mock_detection)

    # Mock Provider
    mock_provider = MagicMock()
    mock_provider.name = "TestProvider"
    mock_provider.check_username = AsyncMock(return_value=(True, "found_content"))
    mock_provider.get_dork_query = MagicMock(return_value="dork_query")
    mock_provider.get_metadata = MagicMock(return_value={})

    # Mock validator
    mock_validator.validate = MagicMock(return_value=True)

    # Run scan
    results = []
    async for intel in orchestrator.run_scan("testuser", [mock_provider]):
        results.append(intel)

    assert len(results) == 1
    assert results[0].platform == "testprovider"
    assert results[0].found is True
