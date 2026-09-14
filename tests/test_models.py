"""Tests for core Pydantic models in etl.models."""

import pytest
from pydantic import ValidationError

from etl.models import (
    ColumnContract,
    DataSourceMetadata,
    PipelineConfig,
    QualityReport,
    TransformationSpec,
)


def test_data_source_metadata_creation() -> None:
    meta = DataSourceMetadata(source_name="test.csv", source_type="file_upload", row_count=100)
    assert meta.source_name == "test.csv"
    assert meta.row_count == 100
    assert meta.file_format == "unknown"


def test_column_contract_defaults() -> None:
    contract = ColumnContract(name="user_id")
    assert contract.name == "user_id"
    assert contract.logical_type == "string"
    assert contract.nullable is True
    assert contract.sensitive is False


def test_pipeline_config_defaults() -> None:
    cfg = PipelineConfig()
    assert cfg.pipeline_name == "default_pipeline"
    assert cfg.quality_gate_policy == "block_on_failure"


def test_transformation_spec_validation() -> None:
    spec = TransformationSpec(
        transform_id="tf_1", transform_type="rename", column="old", target_column="new"
    )
    assert spec.transform_type == "rename"

    with pytest.raises(ValidationError):
        TransformationSpec(transform_id="tf_1", transform_type="invalid_type")  # type: ignore[arg-type]


def test_quality_report_score_bounds() -> None:
    report = QualityReport(run_id="run_1", quality_score=85.5)
    assert report.quality_score == 85.5

    with pytest.raises(ValidationError):
        QualityReport(run_id="run_1", quality_score=150.0)
