from osint_nexus.core.evasion_agent import EvasionAgent
from osint_nexus.providers.aparat import AparatProvider
from osint_nexus.providers.base import BaseProvider
from osint_nexus.providers.generic import GenericProvider
from osint_nexus.providers.github import GitHubProvider
from osint_nexus.utils.network import NetworkManager


class ProviderRegistry:
    def __init__(self, evasion_manager: EvasionAgent, network_manager: NetworkManager):
        self.evasion_manager = evasion_manager
        self.network_manager = network_manager

        # Mapping of Name -> URL Template
        platform_map = {
            # Requested Platforms
            "Telegram": "https://t.me/{}",
            "Instagram": "https://www.instagram.com/{}",
            "X": "https://twitter.com/{}",
            "Facebook": "https://www.facebook.com/{}",
            "Bluesky": "https://bsky.app/profile/{}",
            "Threads": "https://www.threads.net/@{}",
            # Other Platforms
            "Discord": "https://discord.com/users/{}",
            "LinkedIn": "https://www.linkedin.com/in/{}",
            "TikTok": "https://www.tiktok.com/@{}",
            "Snapchat": "https://www.snapchat.com/add/{}",
            "Reddit": "https://www.reddit.com/user/{}",
            "Pinterest": "https://www.pinterest.com/{}",
            "Twitch": "https://www.twitch.tv/{}",
            "Medium": "https://medium.com/@{}",
            "GitLab": "https://gitlab.com/{}",
            "StackOverflow": "https://stackoverflow.com/users/{}",
            # Iranian Platforms
            "Rubika": "https://rubika.ir/{}",
            "Bale": "https://ble.ir/{}",
            "Eitaa": "https://eitaa.com/{}",
            "Soroush+": "https://splus.ir/{}",
            "Shad": "https://shad.ir/{}",
            "Gap": "https://gap.im/{}",
            "IGap": "https://igap.net/{}",
            "Virasty": "https://virasty.com/{}",
            "Nashenas": "https://nashenas.com/{}",
        }

        self.providers: list[BaseProvider] = [
            GenericProvider(name, url, network_manager) for name, url in platform_map.items()
        ]

        # Add specialized providers
        self.providers.append(GitHubProvider(network_manager))
        self.providers.append(AparatProvider(network_manager))

    def get_providers(self) -> list[BaseProvider]:
        return self.providers
