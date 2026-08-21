import math
from collections import Counter

from osint_nexus.core.detectors.base import BaseDetector
from osint_nexus.core.type_defs import JSONObject


class TimingEntropyDetector(BaseDetector):
    name: str = "timing_entropy"

    def _get_intervals(self, telemetry: JSONObject) -> list[float]:
        intervals_raw = telemetry.get("timing_intervals")
        if not isinstance(intervals_raw, list):
            return []
        return [float(x) for x in intervals_raw if isinstance(x, (int, float))]

    def _fallback_check(self, telemetry: JSONObject) -> float:
        pixel_entropy = telemetry.get("pixel_entropy_distribution", 0.0)
        if isinstance(pixel_entropy, (int, float)) and pixel_entropy > 4.2:
            return 1.0
        return 0.0

    def _calculate_from_intervals(self, intervals: list[float]) -> float:
        data_len = len(intervals)
        counts: Counter[float] = Counter(intervals)
        entropy = -sum((count / data_len) * math.log2(count / data_len) for count in counts.values())
        normalized_entropy = entropy / math.log2(data_len) if data_len > 1 else 0.0
        return 1.0 if normalized_entropy < 0.6 else 0.0

    async def analyze(self, telemetry: JSONObject) -> float:
        """
        Calculates Shannon entropy for timing intervals to detect automated patterns.

        Automated scripts often exhibit highly repetitive timing intervals, leading
        to lower entropy compared to genuine human interaction.
        """
        intervals = self._get_intervals(telemetry)
        if not intervals:
            return self._fallback_check(telemetry)
        return self._calculate_from_intervals(intervals)
