from osint_nexus.core.permutator import UsernamePermutator as Permutator


def test_permutator_basic() -> None:
    permutator = Permutator()
    username = "john_doe"
    results = permutator.generate(username)

    assert "john_doe" in results
    assert "john.doe" in results
    assert "john-doe" in results
    assert "johndoe" in results


def test_permutator_short() -> None:
    permutator = Permutator()
    username = "john"
    results = permutator.generate(username)

    assert "john" in results
    assert "john123" in results
    assert "john_" in results
