import pytest

from osint_nexus.core.device_inference import DeviceInferenceNetworkEngine


@pytest.mark.asyncio
async def test_infer_by_ports_windows_profile() -> None:
    service = DeviceInferenceNetworkEngine()
    # Mocking standard Active Directory / Windows Server exposed ports
    result = await service.infer_by_ports("192.168.1.50", [445, 3389])

    assert "Windows" in result.possible_os
    assert "Remote Desktop (RDP)" in result.detected_roles
    assert result.confidence_score > 50


@pytest.mark.asyncio
async def test_infer_by_ports_linux_db_profile() -> None:
    service = DeviceInferenceNetworkEngine()
    # Mocking standard Linux Database ports
    result = await service.infer_by_ports("10.0.0.1", [3306, 5432])

    assert "Linux" in result.possible_os
    assert "Database (MySQL)" in result.detected_roles
    assert "Database (PostgreSQL)" in result.detected_roles
    assert result.confidence_score > 50


@pytest.mark.asyncio
async def test_infer_by_ports_empty_and_unknown() -> None:
    service = DeviceInferenceNetworkEngine()

    # Empty ports
    result_empty = await service.infer_by_ports("127.0.0.1", [])
    assert result_empty.possible_os == []

    assert result_empty.detected_roles == []
    assert result_empty.confidence_score == 0

    # Unknown ports
    result_unknown = await service.infer_by_ports("127.0.0.1", [12345, 67890])
    assert result_unknown.possible_os == []
    assert result_unknown.detected_roles == []
    assert result_unknown.confidence_score == 0


@pytest.mark.asyncio
async def test_infer_by_mac_apple_lookup() -> None:
    service = DeviceInferenceNetworkEngine()
    manufacturer = await service.infer_by_mac("A4-77-33-FF-12-34")
    assert manufacturer == "Apple, Inc."
