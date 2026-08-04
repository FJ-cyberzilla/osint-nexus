import pytest
from osint_nexus.utils.security import SecurityUtility

@pytest.mark.asyncio
async def test_sanitize_input() -> None:
    # Should strip invalid chars and escape
    assert SecurityUtility.sanitize_input("user<script>name") == "userscriptname"
    assert SecurityUtility.sanitize_input("user.name!@#$") == "user.name"
    assert SecurityUtility.sanitize_input("valid_user.123") == "valid_user.123"

@pytest.mark.asyncio
async def test_health_check() -> None:
    assert await SecurityUtility.health_check() is True
