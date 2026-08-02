import json
from pathlib import Path

from osint_nexus.core.dork import DorkEngine
from osint_nexus.core.evasion_agent import EvasionAgent
from osint_nexus.providers.aparat import AparatProvider
from osint_nexus.providers.base import BaseProvider
from osint_nexus.providers.generic import GenericProvider, SiteConfig
from osint_nexus.providers.github import GitHubProvider
from osint_nexus.utils.network import NetworkManager


class ProviderRegistry:
    def __init__(
        self,
        evasion_manager: EvasionAgent,
        network_manager: NetworkManager,
        dork_engine: DorkEngine | None = None,
    ):
        self.evasion_manager = evasion_manager
        self.network_manager = network_manager
        self.dork_engine = dork_engine or DorkEngine()
        self.providers = self._load_providers()

    def _load_providers(self) -> list[BaseProvider]:
        providers: list[BaseProvider] = []

        # Load dynamic providers
        sites_file = Path("data/sites.json")
        if sites_file.exists():
            with open(sites_file) as f:
                try:
                    sites_data = json.load(f)
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
                    import logging

                    logging.getLogger("osint_nexus.registry").error(f"Failed to load sites.json: {e}")

        # Add specialized providers
        providers.append(GitHubProvider(self.network_manager))
        providers.append(AparatProvider(self.network_manager))
        return providers

    def get_providers(self) -> list[BaseProvider]:
        return self.providers
