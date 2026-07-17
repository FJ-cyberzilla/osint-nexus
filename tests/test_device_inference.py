import pytest
from osint_nexus.core.device_inference import DeviceInferenceService

@pytest.fixture
def service():
    return DeviceInferenceService()

def test_inference_oui(service):
    metadata = {"mac_address": "00:1A:2B:CC:DD:EE"}
    profile = service.infer("some content", metadata)
    assert profile.device_type == "Network Equipment"
    assert profile.os_guess == "Cisco IOS"
    assert profile.confidence == 0.9

def test_inference_ports(service):
    metadata = {"ports": [22, 80]}
    profile = service.infer("some content", metadata)
    # Both "Server" and "Web Server" have 0.2, but "Server" was added first
    assert profile.device_type == "Server"
    assert profile.os_guess == "Linux"
    assert profile.confidence == 0.5

def test_inference_unknown(service):
    metadata = {"mac_address": "AA:BB:CC:DD:EE:FF", "ports": [1234]}
    profile = service.infer("some content", metadata)
    assert profile.device_type == "Unknown"
    assert profile.os_guess == "Unknown"
    assert profile.confidence == 0.0
