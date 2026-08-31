from typing import TypedDict, cast

from beartype import beartype

from osint_nexus.core.detectors.registry import FingerprintStrategyRegistry
from osint_nexus.core.type_defs import JSONDict, JSONObject, MetadataDict, to_json_value


class FingerprintResult(TypedDict):
    name: str
    data: MetadataDict
    confidence: float


class FullFingerprintEngine:
    """Aggregates strategy results and calculates weighted confidence."""

    @beartype
    def __init__(self, registry: FingerprintStrategyRegistry) -> None:
        self.registry = registry
        self.weights = {
            "tls_ja3": 0.4,
            "http_headers": 0.3,
            "tcp_stack": 0.2,
            "http2_3_stack": 0.1,
            "dns_patterns": 0.1,
            "timezone_ntp": 0.05,
            "extension_load": 0.05,
            "cdn_headers": 0.05,
        }

    @beartype
    def aggregate(self, telemetry_data: MetadataDict) -> MetadataDict:
        """Aggregate results and compute weighted score."""
        aggregated_data: MetadataDict = {}
        total_weighted_confidence = 0.0
        total_weight = 0.0

        for strategy in self.registry.get_all():
            # Extract data relevant to the strategy
            # T_Data bound is dict[str, JSONValue]
            raw_data = telemetry_data.get(strategy.name, {})
            if not isinstance(raw_data, dict):
                strategy_data: JSONObject = JSONDict(data={})
            else:
                strategy_data = cast(JSONObject, raw_data)

            # Cast result to match expected FingerprintResult
            result = cast(FingerprintResult, strategy.extract(strategy_data))

            name = result["name"]
            data = result["data"]
            confidence = result["confidence"]

            aggregated_data[name] = data

            weight = self.weights.get(name, 0.1)
            total_weighted_confidence += confidence * weight
            total_weight += weight

        final_confidence = total_weighted_confidence / total_weight if total_weight > 0 else 0.0

        return cast(
            MetadataDict,
            to_json_value(
                {
                    "aggregated_data": aggregated_data,
                    "final_confidence": final_confidence,
                }
            ),
        )
