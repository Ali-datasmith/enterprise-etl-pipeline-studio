"""Pydantic response models for AI contract advisor and enrichment outputs."""

from typing import Any, Literal

from pydantic import BaseModel, Field


class RecommendedColumn(BaseModel):
    name: str
    logical_type: str
    nullable: bool
    unique: bool
    sensitive: bool
    rationale: str


class RecommendedCheck(BaseModel):
    check_name: str
    column: str | None = None
    severity: Literal["info", "warning", "critical"] = "warning"
    parameters: dict[str, Any] = Field(default_factory=dict)
    rationale: str


class RecommendedTransformation(BaseModel):
    transform_type: str
    column: str | None = None
    target_column: str | None = None
    parameters: dict[str, Any] = Field(default_factory=dict)
    rationale: str


class ProductionRisk(BaseModel):
    title: str
    description: str


class AIAdvisorReport(BaseModel):
    overview: str
    estimated_data_quality_score: int = Field(ge=0, le=100)
    recommended_columns: list[RecommendedColumn] = Field(default_factory=list)
    recommended_checks: list[RecommendedCheck] = Field(default_factory=list)
    recommended_transformations: list[RecommendedTransformation] = Field(default_factory=list)
    production_risks: list[ProductionRisk] = Field(default_factory=list)
    governance_notes: str


class EnrichedRecord(BaseModel):
    row_id: str
    label: str | None = None
    confidence: float = Field(default=1.0, ge=0.0, le=1.0)
    summary: str | None = None
    entities: list[str] = Field(default_factory=list)
    normalized_value: str | None = None
    warnings: list[str] = Field(default_factory=list)


class AIEnrichmentReport(BaseModel):
    task: str
    target_column: str
    enrichment_type: Literal[
        "classification", "summarization", "entity_extraction", "normalization", "risk_flagging"
    ]
    enriched_records: list[EnrichedRecord] = Field(default_factory=list)
    refused: bool = False
    refusal_reason: str | None = None
    governance_notes: str
