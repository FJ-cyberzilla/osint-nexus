"""
Handles the execution lifecycle of provider-specific OSINT checks.
"""

from __future__ import annotations

import logging
import typing

from osint_nexus.core.extractor import ExtractedPivots, PivotExtractor
from osint_nexus.core.fingerprint import FingerprintAgent
from osint_nexus.core.intelligence import IntelligenceObject
from osint_nexus.core.mimicry import HumanMimicryEngine
from osint_nexus.core.provider_types import (
    DatabaseManagerProtocol,
    DeviceInferenceProtocol,
    JSONValue,
    MetadataDict,
    ProviderExecutionResult,
    ValidatorProtocol,
)
from osint_nexus.providers.base import BaseProvider
from osint_nexus.utils.network import NetworkManager

logger = logging.getLogger("osint_nexus.provider_runner")


class ProviderRunner:
    """Production-ready orchestrator for provider execution lifecycles."""

    def __init__(
        self,
        validator: ValidatorProtocol,
        db_manager: DatabaseManagerProtocol,
        network: NetworkManager,
        mimicry: HumanMimicryEngine,
        extractor: PivotExtractor,
        device_inference: DeviceInferenceProtocol | None = None,
        fingerprint_agent: FingerprintAgent | None = None,
    ) -> None:
        self._validator = validator
        self._db_manager = db_manager
        self._network = network
        self._mimicry = mimicry
        self._extractor = extractor
        self._device_inference = device_inference
        self._fingerprint_agent = fingerprint_agent

    async def run(
        self, provider: BaseProvider, username: str, **microlink_options: JSONValue
    ) -> IntelligenceObject:
        """Executes the provider check logic."""
        result = await self._perform_check(provider, username, **microlink_options)

        final_found = result.found and self._validator.validate(result.content, provider.name)

        # Harvest secondary identifiers if found
        pivots: ExtractedPivots = {
            "emails": [],
            "pgp_keys": [],
            "external_links": [],
            "social_handles": [],
            "bio": None,
        }
        if final_found:
            pivots = await self._extractor.extract(result.content)

        metadata = await self._infer_metadata(provider, username, result.content, final_found)

        # Include fingerprinting results in metadata
        if self._fingerprint_agent:
            metadata["fingerprint_results"] = self._fingerprint_agent.collect_all_fingerprints(result.content)

        # Cast pivots to MetadataDict for update, ensuring compatibility with JSONValue
        metadata.update(typing.cast(MetadataDict, pivots))

        await self._db_manager.save_result(username, provider.name, final_found)

        return IntelligenceObject(
            platform=provider.name,
            username=username,
            found=final_found,
            dork=provider.get_dork_query(username),
            confidence=1.0 if final_found else 0.0,
            metadata=metadata,
            raw_data=result.content if final_found else None,
        )

    async def _perform_check(
        self, provider: BaseProvider, username: str, **microlink_options: JSONValue
    ) -> ProviderExecutionResult:
        """Executes the provider-specific check."""
        try:
            found, content = await provider.check_username(username, **microlink_options)
            return ProviderExecutionResult(found=found, content=str(content))
        except Exception as e:
            logger.exception("Provider check failed for %s", provider.name)
            return ProviderExecutionResult(found=False, content="", error=e)

    async def _infer_metadata(
        self, provider: BaseProvider, username: str, content: str, final_found: bool
    ) -> MetadataDict:
        """Infers metadata for a provider result."""
        metadata: MetadataDict = {}
        if final_found and self._device_inference:
            profile = await self._device_inference.infer(content, provider.get_metadata(username))
            metadata["device_inference"] = profile.model_dump(mode="json")
            logger.info("Inferred device for %s: %s", provider.name, metadata["device_inference"])
        return metadata
