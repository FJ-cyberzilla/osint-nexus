"""
Centralized exception hierarchy for OSINT Nexus.

Defines a structured approach to error handling across the framework,
improving debugging and enabling better API responses.
"""

from __future__ import annotations


class NexusError(Exception):
    """Base exception for all OSINT Nexus framework errors."""

    pass


class ConfigurationError(NexusError):
    """Raised when framework configuration is invalid."""

    pass


class ProviderError(NexusError):
    """Raised when an OSINT provider fails to execute correctly."""

    pass


class NetworkError(NexusError):
    """Raised when a network request fails."""

    pass


class ValidationError(NexusError):
    """Raised when result validation fails."""

    pass


class DatabaseError(NexusError):
    """Raised when database operations fail."""

    pass
