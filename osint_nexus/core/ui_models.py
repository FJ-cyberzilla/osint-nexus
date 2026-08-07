"""Structured data models for UI components to ensure type safety."""

from pydantic import BaseModel, Field


class TelemetryData(BaseModel):
    """Structured telemetry information."""

    dns_leak: str = Field(..., description="DNS leak status")
    connection_type: str = Field(..., description="Detected connection type")
    hardware_fingerprint: str = Field(..., description="Hardware fingerprint hash")


class ActivityLevel(BaseModel):
    """Structured activity level data."""

    level: str = Field(..., description="Detected activity intensity (Low, Medium, High)")
    trend: str = Field(..., description="Activity trend (Upward, Downward, Stable)")
