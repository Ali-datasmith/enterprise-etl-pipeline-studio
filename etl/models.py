"""Pydantic data models for the Enterprise ETL Pipeline Studio."""

from datetime import datetime, timezone
from typing import Any, Literal

from pydantic import BaseModel, Field


def current_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


class DataSourceMetadata(BaseModel):
    source_name: str
    source_type: Literal["file_upload", "sample_dataset", "url_fetch"]
    file_name: str | None = None
    file_format: Literal["csv", "json", "parquet", "unknown"] = "unknown"
    uploaded_at: str = Field(default_factory=current_utc_iso)
    row_count: int | None = None
    column_count: int | None = None
    size_bytes: int | None = None
    checksum: str | None = None
    fetch_method: str | None = None
    notes: str | None = None


class ColumnContract(BaseModel):
    name: str
    logical_type: str = "string"
    nullable: bool = True
    unique: bool = False
    primary_key: bool = False
    sensitive: bool = False
    allowed_values: list[str] | None = None
    min_value: float | None = None
    max_value: float | None = None
    min_length: int | None = None
    max_length: int | None = None
    regex_pattern: str | None = None
    description: str | None = None
    business_owner: str | None = None


class TransformationSpec(BaseModel):
    transform_id: str
    transform_type: Literal[
        "rename",
        "cast",
        "normalize_timestamp",
        "trim_whitespace",
        "deduplicate",
        "fill_null",
        "drop_column",
        "filter_rows",
        "aggregate",
    ]
    column: str | None = None
    target_column: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    enabled: bool = True
    description: str | None = None


class PipelineConfig(BaseModel):
    pipeline_name: str = "default_pipeline"
    sample_mode_enabled: bool = False
    sample_row_limit: int = 100_000
    primary_key_columns: list[str] = Field(default_factory=list)
    sensitive_columns: list[str] = Field(default_factory=list)
    stages_enabled: list[str] = Field(
        default_factory=lambda: [
            "source",
            "raw",
            "profile",
            "contract",
            "validation",
            "transformation",
            "enrichment",
            "publish",
            "export",
        ]
    )
    quality_gate_policy: Literal["block_on_failure", "warn_only", "manual_review"] = (
        "block_on_failure"
    )
    transformations: list[TransformationSpec] = Field(default_factory=list)
    enrichment_enabled: bool = False
    ai_redaction_enabled: bool = True


class QualityCheckResult(BaseModel):
    check_id: str
    check_name: str
    column: str | None = None
    severity: Literal["info", "warning", "critical"] = "warning"
    status: Literal["passed", "warning", "failed", "skipped"] = "passed"
    passed_count: int | None = None
    failed_count: int | None = None
    threshold: str | None = None
    message: str
    failed_samples: list[Any] = Field(default_factory=list)


class QualityReport(BaseModel):
    run_id: str
    created_at: str = Field(default_factory=current_utc_iso)
    total_checks: int = 0
    passed_count: int = 0
    warning_count: int = 0
    failed_count: int = 0
    skipped_count: int = 0
    quality_score: float = Field(default=100.0, ge=0.0, le=100.0)
    gate_decision: Literal["passed", "passed_with_warnings", "blocked", "manual_review"] = "passed"
    results: list[QualityCheckResult] = Field(default_factory=list)


class LineageRecord(BaseModel):
    lineage_id: str
    run_id: str
    stage: str
    input_artifact: str
    output_artifact: str
    operation: str
    row_count_in: int | None = None
    row_count_out: int | None = None
    status: Literal["success", "warning", "failed", "skipped"] = "success"
    started_at: str = Field(default_factory=current_utc_iso)
    finished_at: str = Field(default_factory=current_utc_iso)
    duration_seconds: float | None = None
    details: dict[str, Any] | None = None


class RunMetadata(BaseModel):
    run_id: str
    started_at: str = Field(default_factory=current_utc_iso)
    finished_at: str | None = None
    duration_seconds: float | None = None
    stage_metrics: dict[str, Any] = Field(default_factory=dict)
    row_count_input: int | None = None
    row_count_output: int | None = None
    error_category: str | None = None
    error_message: str | None = None
    ai_calls_attempted: int = 0
    ai_calls_succeeded: int = 0
    export_artifacts: list[str] = Field(default_factory=list)
