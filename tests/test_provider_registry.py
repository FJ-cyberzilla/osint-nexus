from unittest.mock import MagicMock

from osint_nexus.providers.registry import ProviderRegistry


def test_provider_registry_initialization() -> None:
    mock_evasion = MagicMock()
    mock_network = MagicMock()

    registry = ProviderRegistry(mock_evasion, mock_network)
    providers = registry.get_providers()

    # Check if a known provider exists
    names = [p.name for p in providers]
    assert "GitHub" in names
    assert "Telegram" in names
    assert "Aparat" in names
