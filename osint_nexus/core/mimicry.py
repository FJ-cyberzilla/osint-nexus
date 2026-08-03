"""
Human-behavior mimicry engine for OSINT agents.

Provides realistic interaction delays, typing emulation, and clicking
patterns. Uses log-normal distributions and session-based personas
to evade bot detection by simulating natural human browsing.
"""

from __future__ import annotations

import asyncio
import logging
import random
from collections.abc import Callable
from dataclasses import dataclass
from enum import Enum

from osint_nexus.core.config import Config

logger = logging.getLogger("osint_nexus.mimicry")


class Activity(Enum):
    """Types of human-like actions that can be mimicked."""

    PAGE_LOAD = "page_load"
    CLICK = "click"
    TYPING = "typing"
    SCROLLING = "scrolling"
    IDLE = "idle"
    CHECKBOX = "checkbox"
    CAPTCHA_CLICK = "captcha_click"


@dataclass
class TimingProfile:
    """Parameters for a specific timing behavior."""

    min_delay: float = 0.5
    max_delay: float = 3.0
    burstiness: float = 0.2
    burst_count: int = 2


class HumanMimicryEngine:
    """
    Simulates human-like delays and interaction patterns.

    This engine maintains a persistent 'persona' for the duration of its
    lifecycle to ensure behavioral consistency. It adjusts delays dynamically
    based on network latency to avoid 'impossible' interactions.
    """

    def __init__(self, config: Config, latency_provider: Callable[[], float] | None = None) -> None:
        self.config = config
        self._latency_provider = latency_provider

        # Consistent persona for the session
        self.persona = random.choice(["focused", "distracted", "erratic"])  # nosec B311

        self._profiles: dict[Activity, TimingProfile] = {
            Activity.PAGE_LOAD: TimingProfile(1.0, 5.0, burstiness=0.1),
            Activity.CLICK: TimingProfile(0.2, 1.5, burstiness=0.3, burst_count=3),
            Activity.TYPING: TimingProfile(0.05, 0.3, burstiness=0.8, burst_count=5),
            Activity.SCROLLING: TimingProfile(0.5, 2.0),
            Activity.IDLE: TimingProfile(2.0, 10.0),
            Activity.CHECKBOX: TimingProfile(0.3, 2.0, burstiness=0.05),
            Activity.CAPTCHA_CLICK: TimingProfile(1.5, 4.0, burstiness=0.1),
        }
        self._load_custom_profiles()

        self._hesitation_prob = getattr(config, "CLICK_HESITATION_PROB", 0.4)
        self._misclick_prob = getattr(config, "CLICK_MISCLICK_PROB", 0.08)

    def _get_latency_factor(self) -> float:
        """Calculates a multiplier based on current network RTT."""
        if self._latency_provider:
            # Scale delays by latency: high latency = slower human behavior
            return max(1.0, self._latency_provider() * 0.5)
        return 1.0

    def _sample_delay(self, profile: TimingProfile) -> float:
        """
        Generates a delay using a log-normal distribution.
        This provides a 'long-tail' that is more biologically plausible
        than uniform distribution.
        """
        # Persona modification
        modifier = 0.8 if self.persona == "focused" else 1.2

        # Calculate log-normal params
        mu = ((profile.min_delay + profile.max_delay) / 2) * modifier
        sigma = (profile.max_delay - profile.min_delay) / 4

        delay = random.lognormvariate(mu, sigma)

        # Apply burstiness if applicable
        if random.random() < profile.burstiness:
            return sum(random.uniform(mu * 0.1, mu * 0.3) for _ in range(profile.burst_count))

        return max(profile.min_delay, min(delay, profile.max_delay * 1.5))

    async def human_delay(self, activity: Activity = Activity.PAGE_LOAD) -> float:
        """Sleeps for an activity-appropriate amount of time."""
        profile = self._profiles.get(activity, self._profiles[Activity.PAGE_LOAD])
        latency_mod = self._get_latency_factor()

        delay = self._sample_delay(profile) * latency_mod

        logger.debug("Human delay for %s: %.3fs (latency_mod: %.2f)", activity.value, delay, latency_mod)
        await asyncio.sleep(delay)
        return delay

    async def typing_delay(self, text_length: int) -> float:
        """Simulates human-like typing rhythm."""
        char_min = getattr(self.config, "TYPING_CHAR_MIN", 0.05)
        char_max = getattr(self.config, "TYPING_CHAR_MAX", 0.3)

        total = 0.0
        for _ in range(text_length):
            delay = random.uniform(char_min, char_max) * self._get_latency_factor()
            total += delay
            await asyncio.sleep(delay)

        logger.debug("Typing delay for %d chars: %.3fs", text_length, total)
        return total

    async def click_checkbox(
        self,
        hesitation_multiplier: float = 1.0,
    ) -> float:
        """Simulates checkbox interaction with hesitation."""
        total_delay = 0.0
        latency_mod = self._get_latency_factor()

        if random.random() < self._hesitation_prob:
            hesitation = random.uniform(0.4, 1.5) * hesitation_multiplier * latency_mod
            await asyncio.sleep(hesitation)
            total_delay += hesitation

        if random.random() < self._misclick_prob:
            recovery = random.uniform(0.3, 0.8) * latency_mod
            await asyncio.sleep(recovery)
            total_delay += recovery
            logger.debug("Mis-click simulated, recovery: %.3fs", recovery)

        return total_delay

    async def apply_jitter(self) -> None:
        """
        Adds random, small delays to requests to simulate human unpredictability
        and avoid simple pattern-based rate limiting.
        """
        # Base jitter in seconds
        jitter = random.uniform(0.1, 0.5) * self._get_latency_factor()
        logger.debug("Applying human behavioral jitter: %.3fs", jitter)
        await asyncio.sleep(jitter)

    def _load_custom_profiles(self) -> None:
        """Overrides default profiles with configuration values."""
        custom = getattr(self.config, "MIMICRY_PROFILES", None)
        if isinstance(custom, dict):
            for key, value in custom.items():
                try:
                    activity = Activity(key)
                    self._profiles[activity] = TimingProfile(**value)
                except (ValueError, TypeError) as exc:
                    logger.warning("Invalid custom profile '%s': %s", key, exc)
