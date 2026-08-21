from osint_nexus.core.correlation import AccountData, ConnectionData, RelationMapper, UserData


def test_relation_mapper() -> None:
    mapper = RelationMapper()

    data: UserData = {
        "username": "testuser",
        "accounts": [
            AccountData(username="acc1", type="type1"),
            AccountData(username="acc2", type="type2"),
        ],
        "emails": [ConnectionData(email="test@example.com")],
        "phones": [ConnectionData(phone="1234567890")],
    }

    graph = mapper.generate_network_graph(data)

    # 1 primary + 2 accounts + 1 email + 1 phone = 5 nodes
    assert len(graph.nodes) == 5
    # Edges:
    # 2 owns edges (testuser -> acc1, testuser -> acc2)
    # 2 * 1 uses_email edges (acc1->email, acc2->email)
    # 2 * 1 uses_phone edges (acc1->phone, acc2->phone)
    # 2 interacts edges (acc1->acc2, acc2->acc1)
    # Total = 2 + 2 + 2 + 2 = 8 edges
    assert len(graph.edges) == 8
