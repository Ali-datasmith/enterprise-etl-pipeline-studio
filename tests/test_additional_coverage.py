"""Comprehensive deterministic tests covering all requirement edge cases."""

import polars as pl
import pytest

from ai.error_taxonomy import (
    AI_POLICY_REFUSAL_ERROR,
    AI_TIMEOUT_UNAVAILABLE,
    UNEXPECTED_SYSTEM_ERROR,
    classify_ai_error,
)
from etl.ingestion import IngestionError, parse_bytes_to_polars
from etl.models import ColumnContract
from etl.transforms import TransformationSpec, apply_transformation
from etl.validation import run_quality_gates


def test_parse_bytes_invalid_format() -> None:
    with pytest.raises(IngestionError):
        parse_bytes_to_polars(b"invalid corrupt content", "parquet")


def test_transformation_cast() -> None:
    df = pl.DataFrame({"_row_id": ["row_0"], "val": ["100"]})
    spec = TransformationSpec(
        transform_id="t1",
        transform_type="cast",
        column="val",
        parameters={"target_type": "integer"},
    )
    res = apply_transformation(df, spec)
    assert res["val"].dtype == pl.Int64


def test_transformation_drop_column() -> None:
    df = pl.DataFrame({"_row_id": ["row_0"], "col_a": [1], "col_b": [2]})
    spec = TransformationSpec(
        transform_id="t1", transform_type="drop_column", parameters={"columns": ["col_a"]}
    )
    res = apply_transformation(df, spec)
    assert "col_a" not in res.columns
    assert "col_b" in res.columns


def test_transformation_fill_null() -> None:
    df = pl.DataFrame({"_row_id": ["row_0", "row_1"], "val": [10.0, None]})
    spec = TransformationSpec(
        transform_id="t1", transform_type="fill_null", column="val", parameters={"strategy": "mean"}
    )
    res = apply_transformation(df, spec)
    assert res["val"][1] == 10.0


def test_transformation_filter_rows() -> None:
    df = pl.DataFrame({"_row_id": ["row_0", "row_1"], "val": [10, 20]})
    spec = TransformationSpec(
        transform_id="t1",
        transform_type="filter_rows",
        column="val",
        parameters={"operator": ">", "value": 15},
    )
    res = apply_transformation(df, spec)
    assert res.height == 1
    assert res["val"][0] == 20


def test_quality_gates_regex_and_allowed_values() -> None:
    df = pl.DataFrame(
        {
            "_row_id": ["row_0", "row_1"],
            "status": ["ACTIVE", "INVALID_STATUS"],
            "code": ["ABC-123", "BADCODE"],
        }
    )
    contracts = [
        ColumnContract(name="status", allowed_values=["ACTIVE", "INACTIVE"]),
        ColumnContract(name="code", regex_pattern=r"^[A-Z]{3}-\d{3}$"),
    ]
    report, _ = run_quality_gates(df, contracts)
    assert report.warning_count == 2


def test_classify_ai_error_heuristics() -> None:
    err_timeout = Exception("Connection timeout while reading from Gemini server")
    assert classify_ai_error(err_timeout).category == AI_TIMEOUT_UNAVAILABLE

    err_refusal = Exception("Content safety policy refusal triggered")
    assert classify_ai_error(err_refusal).category == AI_POLICY_REFUSAL_ERROR

    err_unknown = Exception("Generic unhandled exception")
    assert classify_ai_error(err_unknown).category == UNEXPECTED_SYSTEM_ERROR
