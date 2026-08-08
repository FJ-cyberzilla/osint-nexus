from unittest.mock import MagicMock, patch

from osint_nexus.core.models import Account, Neo4jConnection, RelationshipGraph
from osint_nexus.core.reconstructor import (
    DigitalFootprintReconstructor,
    InteractionStrategy,
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
    accounts: list[Account] = [Account(id="1"), Account(id="2")]
    with patch.object(reconstructor, "discover_all_accounts", return_value=accounts):
        profile = reconstructor.reconstruct_identity("testuser")

        assert profile.username == "testuser"
        assert len(profile.accounts) == 2
        assert profile.relationships == RelationshipGraph(nodes=[], edges=[])


def test_inference_strategies() -> None:
    # Creating a mock for Neo4jConnection and typing it
    mock_db: Neo4jConnection = MagicMock(spec=Neo4jConnection)
    accounts: list[Account] = [Account(id="1"), Account(id="2")]

    email_strategy = SharedEmailStrategy()
    email_strategy.infer(accounts[0], accounts, mock_db)
    # mypy might still complain about MagicMock methods, but let's test if it's the right approach
    # We can cast or ignore if necessary. For now, try ignoring the specific mock call.
    # The actual issue is that MagicMock doesn't have the attribute in the eyes of mypy,
    # even with spec=Neo4jConnection.

    # Try using type: ignore to focus on fixing the core type errors first
    mock_db.add_relationship.assert_called_with("SAME_EMAIL", accounts[0])  # type: ignore

    phone_strategy = SharedPhoneStrategy()
    phone_strategy.infer(accounts[0], accounts, mock_db)
    mock_db.add_relationship.assert_called_with("SAME_PHONE", accounts[0])  # type: ignore

    device_strategy = SharedDeviceStrategy()
    device_strategy.infer(accounts[0], accounts, mock_db)
    mock_db.add_relationship.assert_called_with("SAME_DEVICE", accounts[0])  # type: ignore

    interaction_strategy = InteractionStrategy()
    interaction_strategy.infer(accounts[0], accounts, mock_db)
    mock_db.add_relationship.assert_called_with("INTERACTS", accounts[0])  # type: ignore
