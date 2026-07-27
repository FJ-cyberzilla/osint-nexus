"""
Advanced Google Dork & search query generator.

Provides configurable, platform-aware dork templates to aid manual
or automated cross-platform identity verification.
"""

from __future__ import annotations

import logging

logger = logging.getLogger("osint_nexus.dork")


class DorkEngine:
    """
    Generates Google‑style search queries (dorks) for manual validation.

    Queries can be platform‑specific and may combine multiple search
    operators. Templates are configurable via the Config object or
    can be set at runtime.
    """

    # Default dork templates per platform. Each template can contain
    # the placeholder ``{username}``.
    DEFAULT_TEMPLATES: dict[str, list[str]] = {
        "generic": [
            'site:{platform}.com "{username}"',
            'site:{platform}.com "{username} profile"',
            'site:{platform}.com "{username}" OR "{username} official"',
        ],
        "github": [
            'site:github.com "{username}"',
            'site:github.com "{username}" followers',
            'site:github.com "{username}" repos',
        ],
        "twitter": [
            'site:twitter.com "{username}"',
            'site:twitter.com "{username}" tweets',
        ],
        "instagram": [
            'site:instagram.com "{username}"',
        ],
        "linkedin": [
            'site:linkedin.com/in "{username}"',
            'site:linkedin.com/pub "{username}"',
        ],
    }

    def __init__(self, templates: dict[str, list[str]] | None = None) -> None:
        """
        Initializes the DorkEngine.

        Args:
            templates: Optional explicit dictionary of templates to use/merge.
        """
        self._templates: dict[str, list[str]] = self.DEFAULT_TEMPLATES.copy()

        if templates:
            self._merge_templates(templates)

    def _merge_templates(self, templates: dict[str, list[str]]) -> None:
        """Safely merge templates into the internal registry."""
        for platform, tpls in templates.items():
            if isinstance(tpls, list):
                self._templates[platform] = tpls
            else:
                logger.warning(
                    "Invalid dork templates for platform '%s' - expected list, got %s",
                    platform,
                    type(tpls),
                )

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def get_dork_query(self, username: str, platform: str, variant: int = 0) -> str:
        """
        Generate a dork query for a given platform.

        Args:
            username: The target username (case‑sensitive).
            platform: The platform domain stem (e.g., 'github', 'twitter').
            variant: Which template variant to use (0‑based). Defaults to 0
                (the primary template). If out of range, the first template
                is used.

        Returns:
            A formatted search query string ready for manual use.
        """
        templates = self._templates.get(platform, self._templates.get("generic", []))
        if not templates:
            return f'"{username}"'
        # Clamp variant index
        idx = variant % len(templates)
        template = templates[idx]
        # Render both platform and username placeholders
        return template.format(platform=platform.lower(), username=username)

    def get_all_dorks(self, username: str, platform: str) -> list[str]:
        """
        Return all dork query variants for a platform.

        Args:
            username: The target username.
            platform: The platform domain stem.

        Returns:
            A list of all generated dork strings for the platform.
        """
        templates = self._templates.get(platform, self._templates.get("generic", []))
        return [tpl.format(platform=platform.lower(), username=username) for tpl in templates]

    def add_platform_template(self, platform: str, templates: list[str]) -> None:
        """
        Override or add dork templates for a platform at runtime.

        Args:
            platform: Platform identifier.
            templates: List of template strings (with ``{username}`` placeholder).
        """
        self._templates[platform] = templates
        logger.info("Dork templates for '%s' updated (%d variants).", platform, len(templates))

    # ------------------------------------------------------------------
    # Health check (for hierarchy integration)
    # ------------------------------------------------------------------

    async def health_check(self) -> bool:
        """Dork engine is stateless – always healthy."""
        return True
