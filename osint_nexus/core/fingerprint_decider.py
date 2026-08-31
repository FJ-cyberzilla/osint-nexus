"""Detection decision engine for client fingerprint analysis."""

from dataclasses import dataclass
from enum import StrEnum
from typing import TypedDict, cast

from beartype import beartype

from osint_nexus.core.type_defs import JSONDict, JSONValue

# Define a flexible but safer type for evidence
type FingerprintEvidence = JSONValue


class RiskLevel(StrEnum):
    """Risk level classification."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class RecommendedAction(StrEnum):
    """Recommended action based on risk assessment."""

    ALLOW = "allow"
    CHALLENGE = "challenge"  # Show CAPTCHA or 2FA
    BLOCK = "block"
    MONITOR = "monitor"  # Log but don't block


@dataclass
class DetectionResult:
    """Result of a single detection check."""

    flag: str
    description: str
    risk_level: RiskLevel
    confidence: float  # 0.0 - 1.0
    evidence: FingerprintEvidence = None


@dataclass
class DecisionResult:
    """Final decision result."""

    is_suspicious: bool
    risk_score: float  # 0.0 - 1.0
    risk_level: RiskLevel
    recommended_action: RecommendedAction
    flags: list[DetectionResult]
    summary: str


class ClientMetrics(TypedDict, total=False):
    """Client metrics extracted from browser."""

    font_fingerprint: str | None
    canvas_hash: str | None
    webgl_vendor: str | None
    timezone_offset: int | None
    screen_width: int | None
    screen_height: int | None
    color_depth: int | None
    audio_hash: str | None
    device_memory: float | None
    user_agent: str | None
    os_from_ua: str | None
    os_from_metrics: str | None
    languages: list[str] | None
    ip_country: str | None
    ip_timezone: str | None
    max_touch_points: int | None
    resolution: str | None


class FingerprintDecider:
    """Decision engine for fingerprint detection."""

    def __init__(self) -> None:
        self.risk_weights = {
            RiskLevel.CRITICAL: 1.0,
            RiskLevel.HIGH: 0.8,
            RiskLevel.MEDIUM: 0.5,
            RiskLevel.LOW: 0.2,
        }

    def decide(self, metrics: ClientMetrics) -> DecisionResult:
        """Make a decision based on client metrics."""
        detection_flags = self._detect_anomalies(metrics)

        # Calculate risk score
        total_risk = sum(self.risk_weights[flag.risk_level] * flag.confidence for flag in detection_flags)
        # Normalize to 0-1 with diminishing returns
        risk_score = min(1.0, total_risk / 2.0)  # Cap at 1.0

        # Determine risk level
        risk_level = self._get_risk_level(risk_score)

        # Determine action
        action = self._get_recommended_action(risk_level, detection_flags)

        # Build summary
        summary = self._build_summary(detection_flags)

        return DecisionResult(
            is_suspicious=risk_score > 0.3,
            risk_score=risk_score,
            risk_level=risk_level,
            recommended_action=action,
            flags=detection_flags,
            summary=summary,
        )

    def _detect_anomalies(self, metrics: ClientMetrics) -> list[DetectionResult]:
        """Detect all anomalies in client metrics."""
        checks = [
            self._check_font,
            self._check_canvas,
            self._check_timezone,
            self._check_resolution,
            self._check_zero_resolution,
            self._check_webgl,
            self._check_audio,
            self._check_os_mismatch,
            self._check_language_mismatch,
            self._check_device_memory,
            self._check_touch_support,
        ]
        flags = []
        for check in checks:
            result = check(metrics)
            if result:
                flags.append(result)
        return flags

    def _check_font(self, metrics: ClientMetrics) -> DetectionResult | None:
        if not metrics.get("font_fingerprint"):
            return DetectionResult(
                flag="missing_font_fingerprint",
                description="No font fingerprint collected (headless browser)",
                risk_level=RiskLevel.HIGH,
                confidence=0.9,
                evidence=metrics.get("font_fingerprint"),
            )
        return None

    def _check_canvas(self, metrics: ClientMetrics) -> DetectionResult | None:
        canvas_hash = metrics.get("canvas_hash", "")
        if canvas_hash in ["", "no-canvas", "webgl-disabled", "canvas-error"]:
            return DetectionResult(
                flag="generic_canvas_hash",
                description="Generic or missing canvas hash (browser spoofing)",
                risk_level=RiskLevel.HIGH,
                confidence=0.85,
                evidence=canvas_hash,
            )
        return None

    def _check_timezone(self, metrics: ClientMetrics) -> DetectionResult | None:
        tz_offset = metrics.get("timezone_offset")
        if tz_offset is not None and tz_offset == 0:
            return DetectionResult(
                flag="utc_timezone",
                description="UTC timezone detected (VPN/proxy/bot)",
                risk_level=RiskLevel.MEDIUM,
                confidence=0.6,
                evidence=f"{tz_offset} (UTC)",
            )
        return None

    def _check_resolution(self, metrics: ClientMetrics) -> DetectionResult | None:
        resolution = metrics.get("resolution", "")
        if resolution in ["800x600", "1024x768", "0x0"]:
            return DetectionResult(
                flag="suspicious_resolution",
                description=f"Headless browser resolution: {resolution}",
                risk_level=RiskLevel.HIGH,
                confidence=0.8,
                evidence=resolution,
            )
        return None

    def _check_zero_resolution(self, metrics: ClientMetrics) -> DetectionResult | None:
        screen_width = metrics.get("screen_width")
        screen_height = metrics.get("screen_height")
        if (
            screen_width is not None
            and screen_height is not None
            and (screen_width == 0 or screen_height == 0)
        ):
            return DetectionResult(
                flag="zero_resolution",
                description="Zero screen size detected",
                risk_level=RiskLevel.HIGH,
                confidence=0.9,
                evidence=f"{screen_width}x{screen_height}",
            )
        return None

    def _check_webgl(self, metrics: ClientMetrics) -> DetectionResult | None:
        webgl_vendor = metrics.get("webgl_vendor", "")
        if webgl_vendor in ["", "unknown", "disabled"]:
            return DetectionResult(
                flag="webgl_disabled",
                description="WebGL disabled or missing",
                risk_level=RiskLevel.HIGH,
                confidence=0.85,
                evidence=webgl_vendor,
            )
        return None

    def _check_audio(self, metrics: ClientMetrics) -> DetectionResult | None:
        audio_hash = metrics.get("audio_hash")
        if audio_hash is None or audio_hash == "":
            return DetectionResult(
                flag="missing_audio_context",
                description="No audio fingerprint (headless browser)",
                risk_level=RiskLevel.HIGH,
                confidence=0.8,
                evidence=audio_hash,
            )

    def _check_os_mismatch(self, metrics: ClientMetrics) -> DetectionResult | None:
        os_from_ua = metrics.get("os_from_ua", "")
        os_from_metrics = metrics.get("os_from_metrics", "")
        if os_from_ua and os_from_metrics and os_from_ua.lower() != os_from_metrics.lower():
            return DetectionResult(
                flag="os_mismatch",
                description=f"OS mismatch: UA says {os_from_ua}, metrics say {os_from_metrics}",
                risk_level=RiskLevel.CRITICAL,
                confidence=0.95,
                evidence=JSONDict(data={"user_agent": os_from_ua, "metrics": os_from_metrics}),
            )
        return None

    def _check_language_mismatch(self, metrics: ClientMetrics) -> DetectionResult | None:
        languages = metrics.get("languages", [])
        ip_country = metrics.get("ip_country", "")
        if languages and ip_country:
            country_code = ip_country.lower()
            if not any(country_code in lang.lower() for lang in languages):
                return DetectionResult(
                    flag="language_country_mismatch",
                    description=f"Language ({', '.join(languages)}) doesn't match IP country ({ip_country})",
                    risk_level=RiskLevel.MEDIUM,
                    confidence=0.6,
                    evidence=cast(dict[str, JSONValue], {"languages": languages, "ip_country": ip_country}),
                )
        return None

    def _check_device_memory(self, metrics: ClientMetrics) -> DetectionResult | None:
        device_memory = metrics.get("device_memory")
        if device_memory is None or device_memory == 0:
            return DetectionResult(
                flag="missing_device_memory",
                description="No device memory reported (automation)",
                risk_level=RiskLevel.MEDIUM,
                confidence=0.5,
                evidence=device_memory,
            )
        return None

    def _check_touch_support(self, metrics: ClientMetrics) -> DetectionResult | None:
        max_touch_points = metrics.get("max_touch_points", 1)
        if max_touch_points == 0:
            return DetectionResult(
                flag="no_touch_support",
                description="No touch support (headless browser)",
                risk_level=RiskLevel.MEDIUM,
                confidence=0.5,
                evidence=max_touch_points,
            )
        return None

    def _get_risk_level(self, risk_score: float) -> RiskLevel:
        """Convert risk score to risk level."""
        if risk_score >= 0.8:
            return RiskLevel.CRITICAL
        elif risk_score >= 0.5:
            return RiskLevel.HIGH
        elif risk_score >= 0.25:
            return RiskLevel.MEDIUM
        else:
            return RiskLevel.LOW

    def _get_recommended_action(
        self, risk_level: RiskLevel, flags: list[DetectionResult]
    ) -> RecommendedAction:
        """Determine recommended action based on risk level and flags."""
        # Critical risk - block immediately
        if risk_level == RiskLevel.CRITICAL:
            return RecommendedAction.BLOCK

        # High risk - challenge with CAPTCHA/2FA
        if risk_level == RiskLevel.HIGH:
            # Check if there's an OS mismatch - block instead
            if any(f.flag == "os_mismatch" for f in flags):
                return RecommendedAction.BLOCK
            return RecommendedAction.CHALLENGE

        # Medium risk - challenge or monitor
        if risk_level == RiskLevel.MEDIUM:
            # Multiple medium flags -> challenge
            medium_flags = [f for f in flags if f.risk_level == RiskLevel.MEDIUM]
            if len(medium_flags) >= 3:
                return RecommendedAction.CHALLENGE
            return RecommendedAction.MONITOR

        # Low risk - allow
        return RecommendedAction.ALLOW

    def _build_summary(self, flags: list[DetectionResult]) -> str:
        """Build human-readable summary."""
        if not flags:
            return "All client metrics appear legitimate"

        high_priority = [f for f in flags if f.risk_level in [RiskLevel.CRITICAL, RiskLevel.HIGH]]

        if high_priority:
            descriptions = [f.description for f in high_priority[:3]]
            return f"Suspicious activity detected: {', '.join(descriptions)}"

        return f"{len(flags)} minor anomalies detected (monitoring)"


# ============================================
# Integration with your existing code
# ============================================


class ClientFingerprintValidator:
    """Validator for client-side rendered metrics with detection."""

    name: str = "client_metrics"

    def __init__(self) -> None:
        self.decider = FingerprintDecider()

    @beartype
    def extract(self, data: Mapping[str, JSONValue]) -> Mapping[str, JSONValue]:
        return cast(Mapping[str, JSONValue], self._extract_internal(data))

    def _extract_internal(self, data: Mapping[str, JSONValue]) -> dict[str, JSONValue]:
        # Extract metrics
        from osint_nexus.core.type_defs import ensure_type

        metrics: ClientMetrics = {
            "font_fingerprint": ensure_type(data.get("font_fingerprint"), str),
            "canvas_hash": ensure_type(data.get("canvas_hash"), str),
            "webgl_vendor": ensure_type(data.get("webgl_vendor"), str),
            "timezone_offset": ensure_type(data.get("timezone_offset"), int),
            "screen_width": ensure_type(data.get("screen_width"), int),
            "screen_height": ensure_type(data.get("screen_height"), int),
            "color_depth": ensure_type(data.get("color_depth"), int),
            "audio_hash": ensure_type(data.get("audio_hash"), str),
            "device_memory": ensure_type(data.get("device_memory"), (int, float)),
            "user_agent": ensure_type(data.get("user_agent"), str),
            "os_from_ua": ensure_type(data.get("os_from_ua"), str),
            "os_from_metrics": ensure_type(data.get("os_from_metrics"), str),
            "languages": ensure_type(data.get("languages"), list),
            "ip_country": ensure_type(data.get("ip_country"), str),
            "ip_timezone": ensure_type(data.get("ip_timezone"), str),
            "max_touch_points": ensure_type(data.get("max_touch_points"), int),
            "resolution": ensure_type(data.get("resolution"), str),
        }

        # Make decision
        decision = self.decider.decide(metrics)
        return {
            "name": self.name,
            "data": self.to_telemetry_dict(decision),
            "confidence": decision.risk_score,
        }

    def to_telemetry_dict(self, decision: DecisionResult) -> dict[str, JSONValue]:
        """Convert decision to a telemetry-friendly format."""
        return {
            "suspicious": decision.is_suspicious,
            "risk_score": decision.risk_score,
            "risk_level": decision.risk_level.value,
            "flags": cast(
                list[JSONValue],
                [
                    {
                        "id": f.flag,
                        "description": f.description,
                        "risk_level": f.risk_level.value,
                        "confidence": f.confidence,
                    }
                    for f in decision.flags
                ],
            ),
            "recommended_action": decision.recommended_action.value,
            "summary": decision.summary,
        }
