from unittest.mock import AsyncMock, MagicMock

import pytest

from osint_nexus.core.fingerbank.client import FingerbankClient


@pytest.mark.asyncio
async def test_fingerbank_interrogation():
    mock_network = MagicMock()
    mock_network.session_manager = AsyncMock()
    mock_network.config = MagicMock()
    mock_network.config.user_agents = ["Mozilla/5.0"]
    mock_network.evasion = MagicMock()
    mock_network.monitor = MagicMock()
    mock_network.rate_limiter = MagicMock()

    client = FingerbankClient(mock_network, "fake_key")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "device": {
            "created_at": "2014-09-09T15:09:51.000Z",
            "id": 33,
            "name": "Microsoft Windows Kernel 6.0",
            "parent_id": 7536,
            "updated_at": "2015-09-18T12:53:32.000Z",
            "virtual_parent_id": None,
            "can_be_more_precise": False,
            "child_devices_count": 0,
            "child_virtual_devices_count": 0,
        },
        "device_name": "Operating System/Windows OS/Microsoft Windows Kernel 6.x/Microsoft Windows Kernel 6.0",
        "manufacturer": {
            "created_at": "2017-09-04T16:41:59.000Z",
            "id": 0,
            "name": "",
            "parent_id": None,
            "updated_at": "2023-05-05T12:17:53.000Z",
            "virtual_parent_id": None,
            "can_be_more_precise": False,
            "child_devices_count": 0,
            "child_virtual_devices_count": 0,
        },
        "operating_system": {
            "created_at": "2017-09-18T16:56:41.000Z",
            "id": 0,
            "name": "",
            "parent_id": None,
            "updated_at": "2023-05-05T12:18:54.000Z",
            "virtual_parent_id": None,
            "can_be_more_precise": True,
            "child_devices_count": 3,
            "child_virtual_devices_count": 3,
        },
        "request_id": "abcd1234efgh5678ijkl9012mnop3456",
        "score": 75,
        "version": "Vista/Server 2008",
        "vulnerabilities": {"cve_devices": {}, "cve_os": {}, "message": "Thanks for using Fingerbank."},
    }

    client.fetcher._execute_http_request = AsyncMock(return_value=mock_response)

    response = await client.interrogate({"dhcp_fingerprint": "1,15"})

    assert response is not None
    assert response.score == 75
    assert response.device.name == "Microsoft Windows Kernel 6.0"


@pytest.mark.asyncio
async def test_fingerbank_interrogation_fallback():
    mock_network = MagicMock()
    client = FingerbankClient(mock_network, None)  # No key, fallback mode

    response = await client.interrogate({"dhcp_fingerprint": "1,15"})
    assert response is None


@pytest.mark.asyncio
async def test_fingerbank_devices_client():
    mock_network = MagicMock()
    mock_network.session_manager = AsyncMock()
    mock_network.config = MagicMock()
    mock_network.config.user_agents = ["Mozilla/5.0"]
    mock_network.evasion = MagicMock()
    mock_network.monitor = MagicMock()
    mock_network.rate_limiter = MagicMock()

    client = FingerbankClient(mock_network, "fake_key")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {
        "created_at": "2014-09-09T15:09:51.000Z",
        "id": 33,
        "name": "Microsoft Windows Kernel 6.0",
        "parent_id": 7536,
        "updated_at": "2015-09-18T12:53:32.000Z",
        "virtual_parent_id": None,
        "can_be_more_precise": False,
        "child_devices_count": 0,
        "child_virtual_devices_count": 0,
    }

    client.fetcher._execute_http_request = AsyncMock(return_value=mock_response)

    device = await client.devices.get_device(33)

    assert device.id == 33
    assert device.name == "Microsoft Windows Kernel 6.0"


@pytest.mark.asyncio
async def test_fingerbank_oui_client():
    mock_network = MagicMock()
    mock_network.session_manager = AsyncMock()
    mock_network.config = MagicMock()
    mock_network.evasion = MagicMock()
    mock_network.monitor = MagicMock()
    mock_network.rate_limiter = MagicMock()

    client = FingerbankClient(mock_network, "fake_key")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = {"device_id": 123}

    client.fetcher._execute_http_request = AsyncMock(return_value=mock_response)

    device_id = await client.oui.get_device_id("00:11:22:33:44:55")

    assert device_id == 123


@pytest.mark.asyncio
async def test_fingerbank_static_client():
    mock_network = MagicMock()
    mock_network.session_manager = AsyncMock()
    mock_network.config = MagicMock()
    mock_network.evasion = MagicMock()
    mock_network.monitor = MagicMock()
    mock_network.rate_limiter = MagicMock()

    client = FingerbankClient(mock_network, "fake_key")

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.content = b"fake_db_content"

    client.fetcher._execute_http_request = AsyncMock(return_value=mock_response)

    db_content = await client.static.download_db()

    assert db_content == b"fake_db_content"
