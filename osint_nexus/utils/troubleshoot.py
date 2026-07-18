"""
Actionable troubleshooting tips for agent failures.

Provides human-readable diagnostic messages based on exception type,
helping users and operators quickly identify root causes.
"""

from __future__ import annotations

import logging

from osint_nexus.core import constants

logger = logging.getLogger("osint_nexus.troubleshoot")


def troubleshoot_agent_error(error: BaseException, provider_name: str = "") -> str:
    """
    Convert an exception into a user-friendly troubleshooting tip.

    Args:
        error: The exception that occurred.
        provider_name: Optional name of the provider that raised the error.

    Returns:
        A Rich-markup string containing an actionable tip.
    """
    # Build the tip based on exception characteristics
    error_str = str(error).lower()
    tip: str

    if isinstance(error, TimeoutError) or "timeout" in error_str:
        tip = (
            f"Request timed out for {provider_name}. "
            "Check network latency or increase the HTTP timeout in config."
        )
    elif isinstance(error, ConnectionError) or "connection" in error_str:
        tip = f"Could not connect to {provider_name}. Verify proxy settings and internet connectivity."
    elif "ssl" in error_str or "certificate" in error_str:
        tip = (
            f"SSL certificate error for {provider_name}. Ensure your system’s CA certificates are up to date."
        )
    elif hasattr(error, "response") and error.response is not None:
        status_code = error.response.status_code
        tip = (
            f"HTTP {status_code} from {provider_name}. "
            "Possible rate‑limiting or block – consider rotating proxy / User‑Agent."
        )
    else:
        tip = f"Unexpected error in {provider_name}. Review the logs for full details."

    # Log the underlying error for diagnostics
    logger.error("Agent failure in %s: %s", provider_name, error, exc_info=True)

    return f"[{constants.COLOR_TIP}]Tip: {tip}[/]"
