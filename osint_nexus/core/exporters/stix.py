"""
STIX 2.1 JSON Exporter.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import TypedDict


class STIXIdentity(TypedDict):
    type: str
    id: str
    created: str
    name: str
    description: str
    identity_class: str


class STIXBundle(TypedDict):
    type: str
    id: str
    objects: list[STIXIdentity]


class STIXExporter:
    """
    Exports scan data to STIX 2.1 format.
    """

    def export(self, data: dict[str, str]) -> STIXBundle:
        """
        Converts internal representation to STIX 2.1.
        """
        identity = self._create_identity(data)

        stix_payload: STIXBundle = {
            "type": "bundle",
            "id": f"bundle--{uuid.uuid4()}",
            "objects": [identity],
        }
        return stix_payload

    def _create_identity(self, data: dict[str, str]) -> STIXIdentity:
        """Creates a STIX 2.1 Identity object."""
        return {
            "type": "identity",
            "id": f"identity--{uuid.uuid4()}",
            "created": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "name": data.get("username", "unknown"),
            "description": data.get("bio", ""),
            "identity_class": "individual",
        }
