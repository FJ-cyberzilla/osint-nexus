import math
from collections import Counter
from typing import Any

from osint_nexus.core.detectors.base import BaseDetector


class TimingEntropyDetector(BaseDetector):
    @property
    def name(self) -> str:
        return "timing_entropy"

    async def analyze(self, telemetry: dict[str, Any]) -> float:
        """
        Calculates Shannon entropy for timing intervals to detect automated patterns.

        Automated scripts often exhibit highly repetitive timing intervals, leading
        to lower entropy compared to genuine human interaction.
        """
        intervals = telemetry.get("timing_intervals")
        if not isinstance(intervals, list) or not intervals:
            # Fallback to a basic check if advanced metrics are missing
            pixel_entropy = telemetry.get("pixel_entropy_distribution", 0.0)
            return 1.0 if isinstance(pixel_entropy, (int, float)) and pixel_entropy > 4.2 else 0.0

        # Calculate Shannon Entropy
        data_len = len(intervals)
        counts = Counter(intervals)
        entropy = -sum((count / data_len) * math.log2(count / data_len) for count in counts.values())

        # Normalize entropy
        normalized_entropy = entropy / math.log2(data_len) if data_len > 1 else 0.0

        # Heuristic: low normalized entropy indicates highly predictable (automated) timing
        return 1.0 if normalized_entropy < 0.6 else 0.0
