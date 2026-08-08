from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass(frozen=True)
class ParentDevice:
    created_at: str
    id: int
    name: str
    parent_id: int | None
    updated_at: str
    virtual_parent_id: int | None

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> ParentDevice:
        return cls(
            created_at=data["created_at"],
            id=data["id"],
            name=data["name"],
            parent_id=data.get("parent_id"),
            updated_at=data["updated_at"],
            virtual_parent_id=data.get("virtual_parent_id"),
        )


@dataclass(frozen=True)
class Device:
    created_at: str
    id: int
    name: str
    parent_id: int | None
    updated_at: str
    virtual_parent_id: int | None
    parents: list[ParentDevice] = field(default_factory=list)
    can_be_more_precise: bool = False
    child_devices_count: int = 0
    child_virtual_devices_count: int = 0

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Device:
        return cls(
            created_at=data["created_at"],
            id=data["id"],
            name=data["name"],
            parent_id=data.get("parent_id"),
            updated_at=data["updated_at"],
            virtual_parent_id=data.get("virtual_parent_id"),
            parents=[ParentDevice.from_dict(p) for p in data.get("parents", [])],
            can_be_more_precise=data.get("can_be_more_precise", False),
            child_devices_count=data.get("child_devices_count", 0),
            child_virtual_devices_count=data.get("child_virtual_devices_count", 0),
        )


@dataclass(frozen=True)
class Vulnerabilities:
    cve_devices: dict[str, Any]
    cve_os: dict[str, Any]
    message: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> Vulnerabilities:
        return cls(
            cve_devices=data.get("cve_devices", {}),
            cve_os=data.get("cve_os", {}),
            message=data.get("message", ""),
        )


@dataclass(frozen=True)
class InterrogateResponse:
    device: Device
    device_name: str
    manufacturer: Device
    operating_system: Device
    request_id: str
    score: int
    version: str
    vulnerabilities: Vulnerabilities

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> InterrogateResponse:
        return cls(
            device=Device.from_dict(data["device"]),
            device_name=data["device_name"],
            manufacturer=Device.from_dict(data["manufacturer"]),
            operating_system=Device.from_dict(data["operating_system"]),
            request_id=data["request_id"],
            score=data["score"],
            version=data["version"],
            vulnerabilities=Vulnerabilities.from_dict(data["vulnerabilities"]),
        )


@dataclass(frozen=True)
class DeviceVulnerabilities:
    cve_devices: dict[str, Any]
    cve_os: dict[str, Any]
    message: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> DeviceVulnerabilities:
        return cls(
            cve_devices=data.get("cve_devices", {}),
            cve_os=data.get("cve_os", {}),
            message=data.get("message", ""),
        )


@dataclass(frozen=True)
class AccountInfo:
    id: int
    username: str
    email: str

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> AccountInfo:
        return cls(
            id=data["id"],
            username=data["username"],
            email=data["email"],
        )
