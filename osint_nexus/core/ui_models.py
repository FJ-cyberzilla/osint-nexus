"""Structured data models for UI components to ensure type safety."""

from typing import Any

from pydantic import BaseModel, Field


class FingerprintData(BaseModel):
    """Structured fingerprinting intelligence."""

    suspicious: bool
    risk_score: float
    risk_level: str
    recommended_action: str
    summary: str


class TelemetryData(BaseModel):
    """Structured telemetry information."""

    dns_leak: str = Field(..., description="DNS leak status")
    connection_type: str = Field(..., description="Detected connection type")
    hardware_fingerprint: str = Field(..., description="Hardware fingerprint hash")
    fingerprint_results: FingerprintData | None = Field(
        default=None, description="Passive fingerprinting results"
    )


class ActivityLevel(BaseModel):
    """Structured activity level data."""

    level: str = Field(..., description="Detected activity intensity (Low, Medium, High)")
    trend: str = Field(..., description="Activity trend (Upward, Downward, Stable)")


class DeviceProfile(BaseModel):
    """UI model for Fingerbank device profiling results."""

    device_name: str
    manufacturer: str
    os_name: str
    version: str
    confidence_score: int
    vulnerability_message: str
    cve_devices: dict[str, Any]
    cve_os: dict[str, Any]
