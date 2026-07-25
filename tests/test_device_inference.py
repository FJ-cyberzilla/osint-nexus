import pytest
from osint_nexus.core.device_inference import DeviceInferenceService

@pytest.mark.asyncio
async def test_infer_by_ports_windows_profile():
    service = DeviceInferenceService()
    # Mocking standard Active Directory / Windows Server exposed ports
    result = await service.infer_by_ports("192.168.1.50", [445, 3389])
    
    assert "Windows" in result.possible_os
    assert "Remote Desktop (RDP)" in result.detected_roles
    assert result.confidence_score > 50

@pytest.mark.asyncio
async def test_infer_by_mac_apple_lookup():
    service = DeviceInferenceService()
    manufacturer = await service.infer_by_mac("A4-77-33-FF-12-34")
    assert manufacturer == "Apple, Inc."
