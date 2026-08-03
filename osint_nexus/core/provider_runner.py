"""
Handles the execution lifecycle of provider-specific OSINT checks.
"""

from __future__ import annotations

import logging
from typing import Any

from osint_nexus.core.extractor import PivotExtractor
from osint_nexus.core.intelligence import IntelligenceObject
from osint_nexus.core.mimicry import HumanMimicryEngine
from osint_nexus.providers.base import BaseProvider
from osint_nexus.utils.network import NetworkManager

logger = logging.getLogger("osint_nexus.provider_runner")


class ProviderRunner:
    """Executes provider check logic and manages the result lifecycle."""

    def __init__(
        self,
        validator: Any,
        db_manager: Any,
        network: NetworkManager,
        mimicry: HumanMimicryEngine,
        extractor: PivotExtractor,
        device_inference: Any | None = None,
    ) -> None:
        self.validator = validator
        self.db_manager = db_manager
        self.network = network
        self.mimicry = mimicry
        self.extractor = extractor
        self.device_inference = device_inference

    async def run(
        self, provider: BaseProvider, username: str, **microlink_options: Any
    ) -> IntelligenceObject:
        """Executes the provider check logic."""
        raw_found, content = await provider.check_username(username, **microlink_options)
        dork = provider.get_dork_query(username)

        final_found = raw_found and self.validator.validate(content, provider.name)

        # Harvest secondary identifiers if found
        pivots: dict[str, Any] = {}
        if final_found:
            pivots = await self.extractor.extract(str(content))

        metadata = await self._infer_metadata(provider, username, content, final_found)
        metadata.update(pivots)

        await self.db_manager.save_result(username, provider.name, final_found)

        intel = IntelligenceObject(
            platform=provider.name,
            username=username,
            found=final_found,
            dork=dork,
            confidence=1.0 if final_found else 0.0,
            metadata=metadata,
            raw_data=str(content) if final_found else None,
        )

        return intel

    async def _infer_metadata(
        self, provider: BaseProvider, username: str, content: Any, final_found: bool
    ) -> dict[str, Any]:
        """Infers metadata for a provider result."""
        metadata: dict[str, Any] = {}
        if final_found and self.device_inference:
            profile = await self.device_inference.infer(str(content), provider.get_metadata(username))
            metadata["device_inference"] = profile.model_dump(mode="json")
            logger.info("Inferred device for %s: %s", provider.name, metadata["device_inference"])
        return metadata
