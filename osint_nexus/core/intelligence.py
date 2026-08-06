import uuid
from datetime import UTC, datetime

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    HttpUrl,
    field_validator,
)

# ---------------------------------------------------------
# Nested Sub-Models (Strong Typing for complex structures)
# ---------------------------------------------------------


class VisualIntelligence(BaseModel):
    """Strongly typed schema for visual OSINT data."""

    model_config = ConfigDict(frozen=True, str_strip_whitespace=True)

    profile_picture: HttpUrl | None = Field(default=None, description="URL to the target's avatar")
    banner_image: HttpUrl | None = Field(default=None, description="URL to the background/banner")
    color_palette: list[str] = Field(default_factory=list, description="List of dominant HEX colors")
    face_detected: bool = Field(default=False, description="Whether a human face was detected by CV")
    ocr_text: str | None = Field(default=None, description="Text extracted from images via OCR")


# ---------------------------------------------------------
# Main Intelligence Model
# ---------------------------------------------------------


class IntelligenceObject(BaseModel):
    """
    Immutable, validated OSINT data object representing a snapshot in time.
    """

    # model_config enforces immutability and cleans incoming strings
    model_config = ConfigDict(frozen=True, str_strip_whitespace=True, populate_by_name=True)

    # --- Traceability & Metadata ---
    id: uuid.UUID = Field(
        default_factory=uuid.uuid4, description="Unique identifier for this intelligence record"
    )
    scraped_at: datetime = Field(
        default_factory=lambda: datetime.now(UTC), description="Time the intelligence was gathered (UTC)"
    )

    # --- Core Identifiers ---
    platform: str = Field(
        ...,  # Ellipsis means required
        min_length=1,
        description="Target platform (e.g., 'github', 'instagram')",
    )
    username: str = Field(..., min_length=1, description="The queried username or handle")

    # --- Results ---
    found: bool = Field(..., description="True if the target was positively identified")
    dork: str = Field(default="", description="Google-style dork query for this platform")
    confidence: float = Field(
        default=0.0, ge=0.0, le=1.0, description="Probability score of exact match (0.0 to 1.0)"
    )

    # --- Extracted Intelligence ---
    # We keep metadata flexible for platform-specific quirks (e.g., repo count vs follower count)
    metadata: dict[str, object] = Field(default_factory=dict)

    # We use a strict nested model for visuals rather than a loose dict
    visuals: VisualIntelligence = Field(default_factory=VisualIntelligence)

    # --- Raw / Debug Data ---
    # exclude=True ensures it is NEVER sent to the DB or API by accident
    # repr=False ensures it doesn't flood your console when printing the object
    raw_data: str | None = Field(
        default=None,
        exclude=True,
        repr=False,
        description="Raw HTML/JSON for debugging. Excluded from serialization.",
    )

    # --- Custom Validations ---
    @field_validator("platform")
    @classmethod
    def normalize_platform(cls, v: str) -> str:
        """Ensure platform names are uniformly lowercase for database indexing."""
        return v.lower()
