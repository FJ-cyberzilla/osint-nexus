import json
import logging
from pathlib import Path
from typing import Any

from osint_nexus.core.dork import DorkEngine
from osint_nexus.core.evasion_agent import EvasionAgent
from osint_nexus.providers.base import BaseProvider
from osint_nexus.providers.generic import GenericProvider, SiteConfig
from osint_nexus.utils.network import NetworkManager

logger = logging.getLogger("osint_nexus.registry")


class ProviderRegistry:
    """Registry to manage and initialize all supported OSINT providers."""

    def __init__(
        self,
        evasion_manager: EvasionAgent,
        network_manager: NetworkManager,
        dork_engine: DorkEngine | None = None,
    ) -> None:
        """
        Initializes the ProviderRegistry.

        Args:
            evasion_manager: The evasion manager instance.
            network_manager: The network manager instance.
            dork_engine: Optional dork engine instance.
        """
        self.evasion_manager = evasion_manager
        self.network_manager = network_manager
        self.dork_engine = dork_engine or DorkEngine()
        self.providers = self._load_providers()

    def _load_providers(self) -> list[BaseProvider]:
        """
        Loads and initializes all configured OSINT providers.

        Returns:
            A list of initialized provider instances.
        """
        from osint_nexus.providers.aparat import AparatProvider
        from osint_nexus.providers.github import GitHubProvider

        providers: list[BaseProvider] = []

        # Load dynamic providers
        sites_file = Path("data/sites.json")
        if sites_file.exists():
            with open(sites_file) as f:
                try:
                    sites_data: list[dict[str, Any]] = json.load(f)
                    for site_entry in sites_data:
                        config = SiteConfig(**site_entry)
                        providers.append(
                            GenericProvider(
                                config,
                                self.network_manager,
                                self.dork_engine,
                            )
                        )
                except Exception as e:
                    logger.error("Failed to load sites.json: %s", e)

        # Add specialized providers
        providers.append(GitHubProvider(self.network_manager))
        providers.append(AparatProvider(self.network_manager))
        return providers

    def get_providers(self) -> list[BaseProvider]:
        """
        Returns the list of initialized providers.

        Returns:
            A list of provider instances.
        """
        return self.providers
