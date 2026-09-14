"""Constants and defaults for Enterprise ETL Pipeline Studio."""

from typing import Final

DEFAULT_SAMPLE_ROW_LIMIT: Final[int] = 100_000
AI_ENRICHMENT_SAMPLE_LIMIT: Final[int] = 20
PREVIEW_TABLE_LIMIT: Final[int] = 1_000
FAILED_SAMPLE_LIMIT: Final[int] = 20

COLOR_BASE_BG: Final[str] = "#0B0F19"
COLOR_SURFACE_BG: Final[str] = "#121620"
COLOR_PRIMARY_TEXT: Final[str] = "#FFFFFF"
COLOR_MUTED_TEXT: Final[str] = "#A0A7B8"
COLOR_ACCENT: Final[str] = "#00E5FF"
COLOR_SUCCESS: Final[str] = "#34D399"
COLOR_WARNING: Final[str] = "#FBBF24"
COLOR_DANGER: Final[str] = "#F87171"
COLOR_HAIRLINE_BORDER: Final[str] = "rgba(255, 255, 255, 0.08)"
COLOR_GLASS_SURFACE: Final[str] = "rgba(255, 255, 255, 0.03)"

GATE_POLICY_BLOCK: Final[str] = "block_on_failure"
GATE_POLICY_WARN: Final[str] = "warn_only"
GATE_POLICY_MANUAL: Final[str] = "manual_review"

SUPPORTED_FILE_FORMATS: Final[list[str]] = ["csv", "json", "parquet"]

STAGE_SOURCE: Final[str] = "source"
STAGE_RAW: Final[str] = "raw"
STAGE_PROFILE: Final[str] = "profile"
STAGE_CONTRACT: Final[str] = "contract"
STAGE_VALIDATION: Final[str] = "validation"
STAGE_TRANSFORMATION: Final[str] = "transformation"
STAGE_ENRICHMENT: Final[str] = "enrichment"
STAGE_PUBLISH: Final[str] = "publish"
STAGE_EXPORT: Final[str] = "export"

ALL_STAGES: Final[list[str]] = [
    STAGE_SOURCE,
    STAGE_RAW,
    STAGE_PROFILE,
    STAGE_CONTRACT,
    STAGE_VALIDATION,
    STAGE_TRANSFORMATION,
    STAGE_ENRICHMENT,
    STAGE_PUBLISH,
    STAGE_EXPORT,
]

LOGICAL_TYPES: Final[list[str]] = [
    "string",
    "integer",
    "float",
    "boolean",
    "date",
    "datetime",
    "category",
    "identifier",
    "text",
    "unknown",
]
