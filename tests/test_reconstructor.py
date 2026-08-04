from unittest.mock import MagicMock, patch

from osint_nexus.core.reconstructor import (
    DigitalFootprintReconstructor,
    InteractionStrategy,
    Neo4jConnection,
    SharedDeviceStrategy,
    SharedEmailStrategy,
    SharedPhoneStrategy,
)


def test_reconstructor_init() -> None:
    reconstructor = DigitalFootprintReconstructor()
    assert len(reconstructor.inference_strategies) == 4


def test_reconstruct_identity() -> None:
    reconstructor = DigitalFootprintReconstructor()
    # Mocking external calls
    with patch.object(reconstructor, "discover_all_accounts", return_value=[{"id": 1}, {"id": 2}]):
        profile = reconstructor.reconstruct_identity("testuser")

        assert profile.username == "testuser"
        assert len(profile.accounts) == 2
        assert profile.relationships == {"nodes": [], "edges": []}


def test_inference_strategies() -> None:
    mock_db = MagicMock(spec=Neo4jConnection)
    accounts = [{"id": 1}, {"id": 2}]

    email_strategy = SharedEmailStrategy()
    email_strategy.infer(accounts[0], accounts, mock_db)
    mock_db.add_relationship.assert_called_with("SAME_EMAIL", accounts[0])

    phone_strategy = SharedPhoneStrategy()
    phone_strategy.infer(accounts[0], accounts, mock_db)
    mock_db.add_relationship.assert_called_with("SAME_PHONE", accounts[0])

    device_strategy = SharedDeviceStrategy()
    device_strategy.infer(accounts[0], accounts, mock_db)
    mock_db.add_relationship.assert_called_with("SAME_DEVICE", accounts[0])

    interaction_strategy = InteractionStrategy()
    interaction_strategy.infer(accounts[0], accounts, mock_db)
    mock_db.add_relationship.assert_called_with("INTERACTS", accounts[0])
