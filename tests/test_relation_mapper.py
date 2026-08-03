from dataclasses import dataclass

from osint_nexus.core.correlation import RelationMapper


@dataclass
class Account:
    username: str
    type: str


@dataclass
class Connection:
    email: str | None = None
    phone: str | None = None


@dataclass
class UsernameData:
    username: str
    accounts: list[Account]
    emails: list[Connection]
    phones: list[Connection]


def test_relation_mapper() -> None:
    mapper = RelationMapper()

    data = UsernameData(
        username="testuser",
        accounts=[Account("acc1", "type1"), Account("acc2", "type2")],
        emails=[Connection(email="test@example.com")],
        phones=[Connection(phone="1234567890")],
    )

    graph = mapper.generate_network_graph(data)

    # 1 primary + 2 accounts + 1 email + 1 phone = 5 nodes
    assert len(graph["nodes"]) == 5
    # Edges:
    # 2 owns edges (testuser -> acc1, testuser -> acc2)
    # 2 * 1 uses_email edges (acc1->email, acc2->email)
    # 2 * 1 uses_phone edges (acc1->phone, acc2->phone)
    # 2 interacts edges (acc1->acc2, acc2->acc1)
    # Total = 2 + 2 + 2 + 2 = 8 edges
    assert len(graph["edges"]) == 8
