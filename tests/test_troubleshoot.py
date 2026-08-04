from osint_nexus.core import constants
from osint_nexus.utils.troubleshoot import troubleshoot_agent_error


def test_troubleshoot_agent_error_timeout() -> None:
    error = TimeoutError("Request timed out")
    provider = "test-provider"
    tip = troubleshoot_agent_error(error, provider)
    assert "Request timed out for test-provider" in tip
    assert constants.COLOR_TIP in tip


def test_troubleshoot_agent_error_unknown() -> None:
    error = ValueError("Something went wrong")
    provider = "test-provider"
    tip = troubleshoot_agent_error(error, provider)
    assert "Unexpected error in test-provider" in tip
