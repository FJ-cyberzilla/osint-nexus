"""Provider registry and base provider interface for OSINT Nexus."""

from .base import BaseProvider
from .registry import ProviderRegistry

__all__ = ["ProviderRegistry", "BaseProvider"]
