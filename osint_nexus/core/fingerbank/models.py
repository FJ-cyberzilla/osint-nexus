from __future__ import annotations

from pydantic import BaseModel, Field


class ParentDevice(BaseModel):
    created_at: str
    id: int
    name: str
    parent_id: int | None = None
    updated_at: str
    virtual_parent_id: int | None = None


class Device(BaseModel):
    created_at: str
    id: int
    name: str
    parent_id: int | None = None
    updated_at: str
    virtual_parent_id: int | None = None
    parents: list[ParentDevice] = Field(default_factory=list)
    can_be_more_precise: bool = False
    child_devices_count: int = 0
    child_virtual_devices_count: int = 0


class Vulnerabilities(BaseModel):
    cve_devices: dict[str, str] = Field(default_factory=dict)
    cve_os: dict[str, str] = Field(default_factory=dict)
    message: str = ""


class InterrogateResponse(BaseModel):
    device: Device
    device_name: str
    manufacturer: Device
    operating_system: Device
    request_id: str
    score: int
    version: str
    vulnerabilities: Vulnerabilities


class DeviceVulnerabilities(BaseModel):
    cve_devices: dict[str, str] = Field(default_factory=dict)
    cve_os: dict[str, str] = Field(default_factory=dict)
    message: str = ""


class AccountInfo(BaseModel):
    id: int
    username: str
    email: str
