"""
STIX 2.1 JSON Exporter.
"""

from __future__ import annotations

import uuid
from datetime import UTC, datetime
from typing import Any


class STIXExporter:
    """
    Exports scan data to STIX 2.1 format.
    """

    def export(self, data: dict[str, Any]) -> dict[str, Any]:
        """
        Converts internal representation to STIX 2.1.
        """
        identity = self._create_identity(data)

        stix_payload = {
            "type": "bundle",
            "id": f"bundle--{uuid.uuid4()}",
            "objects": [identity],
        }
        return stix_payload

    def _create_identity(self, data: dict[str, Any]) -> dict[str, Any]:
        """Creates a STIX 2.1 Identity object."""
        return {
            "type": "identity",
            "id": f"identity--{uuid.uuid4()}",
            "created": datetime.now(UTC).isoformat().replace("+00:00", "Z"),
            "name": data.get("username", "unknown"),
            "description": data.get("bio", ""),
            "identity_class": "individual",
        }
