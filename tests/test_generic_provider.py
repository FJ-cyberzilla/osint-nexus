from unittest.mock import AsyncMock

import pytest

from osint_nexus.providers.generic import GenericProvider, SiteConfig


@pytest.fixture
def mock_network():
    return AsyncMock()


@pytest.fixture
def site_config():
    return SiteConfig(
        name="TestSite", url_template="https://testsite.com/{username}", error_indicator="Not Found"
    )


def test_site_config_validation():
    # Valid config
    config = SiteConfig(name="Site", url_template="https://site.com/{username}")
    assert config.name == "Site"

    # Invalid template
    with pytest.raises(ValueError, match="must contain the '{username}' placeholder"):
        SiteConfig(name="Site", url_template="https://site.com/invalid")

    # Invalid regex
    with pytest.raises(ValueError, match="Invalid regex pattern"):
        SiteConfig(name="Site", url_template="https://site.com/{username}", regex_pattern="[")


@pytest.mark.asyncio
async def test_generic_provider_check_username_success(mock_network, site_config):
    mock_network.fetch = AsyncMock(return_value=(True, "User found"))
    provider = GenericProvider(site_config, mock_network)

    found, content = await provider.check_username("testuser")

    assert found is True
    assert content == "User found"
    mock_network.fetch.assert_awaited_once()


@pytest.mark.asyncio
async def test_generic_provider_check_username_network_error(mock_network, site_config):
    mock_network.fetch = AsyncMock(side_effect=Exception("Network down"))
    provider = GenericProvider(site_config, mock_network)

    found, content = await provider.check_username("testuser")

    assert found is False
    assert "NetworkError" in content


@pytest.mark.asyncio
async def test_generic_provider_check_username_error_indicator(mock_network, site_config):
    mock_network.fetch = AsyncMock(return_value=(True, "Not Found"))
    provider = GenericProvider(site_config, mock_network)

    found, content = await provider.check_username("testuser")

    assert found is False
    assert content == "Not Found"


@pytest.mark.asyncio
async def test_generic_provider_check_username_regex_success(mock_network):
    config = SiteConfig(
        name="Site", url_template="https://site.com/{username}", regex_pattern=r"profile: (?P<name>.*)"
    )
    mock_network.fetch = AsyncMock(return_value=(True, "profile: testuser"))
    provider = GenericProvider(config, mock_network)

    found, content = await provider.check_username("testuser")

    assert found is True


@pytest.mark.asyncio
async def test_generic_provider_check_username_regex_failure(mock_network):
    config = SiteConfig(
        name="Site", url_template="https://site.com/{username}", regex_pattern=r"profile: (?P<name>.*)"
    )
    mock_network.fetch = AsyncMock(return_value=(True, "No profile here"))
    provider = GenericProvider(config, mock_network)

    found, content = await provider.check_username("testuser")

    assert found is False


def test_generic_provider_get_dork_query(mock_network, site_config):
    provider = GenericProvider(site_config, mock_network)
    assert provider.get_dork_query("testuser") == 'site:testsite.com "testuser"'

    config_with_dork = SiteConfig(
        name="Site", url_template="https://site.com/{username}", dork_query="site:site.com/{username}"
    )
    provider_dork = GenericProvider(config_with_dork, mock_network)
    assert provider_dork.get_dork_query("testuser") == "site:site.com/testuser"
