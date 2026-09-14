"""Tests for profiling, contracts, validation, transforms, lineage, sample data, security, and export."""

import polars as pl

from etl.contracts import infer_contract_from_profile, update_contract
from etl.export import export_dataframe, export_json_artifact
from etl.lineage import LineageTracker
from etl.models import ColumnContract, TransformationSpec
from etl.profiling import infer_logical_type, profile_dataset
from etl.sample_data import (
    get_sample_customers_csv,
    get_sample_dirty_transactions_csv,
    get_sample_parquet_bytes,
)
from etl.security import detect_sensitive_column, sanitize_filename
from etl.transforms import apply_transformations
from etl.validation import run_quality_gates


def test_infer_logical_type() -> None:
    s_int = pl.Series("age", [25, 30, 35])
    assert infer_logical_type(s_int) == "integer"

    s_id = pl.Series("user_id", [101, 102, 103])
    assert infer_logical_type(s_id) == "identifier"

    s_float = pl.Series("price", [19.99, 29.99])
    assert infer_logical_type(s_float) == "float"


def test_profile_dataset(sample_customers_df: pl.DataFrame) -> None:
    profile = profile_dataset(sample_customers_df)
    assert profile["total_rows"] == 3
    assert profile["has_geospatial"] is True
    assert len(profile["columns"]) == 6


def test_infer_and_update_contract(sample_customers_df: pl.DataFrame) -> None:
    profile = profile_dataset(sample_customers_df)
    contracts = infer_contract_from_profile(profile)
    assert len(contracts) == 6

    updated = update_contract(contracts, "full_name", nullable=False)
    target = next(c for c in updated if c.name == "full_name")
    assert target.nullable is False


def test_quality_gates_pass(
    sample_customers_df: pl.DataFrame, sample_contracts: list[ColumnContract]
) -> None:
    report, quarantine = run_quality_gates(sample_customers_df, sample_contracts)
    assert report.quality_score == 100.0
    assert report.gate_decision == "passed"
    assert quarantine.height == 0


def test_quality_gates_dirty_data() -> None:
    df = pl.DataFrame(
        {
            "_row_id": ["row_0", "row_1"],
            "user_id": ["U101", "U101"],
            "amount": [10.0, -50.0],
        }
    )
    contracts = [
        ColumnContract(name="user_id", primary_key=True),
        ColumnContract(name="amount", min_value=0.0),
    ]
    report, quarantine = run_quality_gates(df, contracts)
    assert report.quality_score < 100.0
    assert report.failed_count > 0 or report.warning_count > 0


def test_transformations() -> None:
    df = pl.DataFrame({"_row_id": ["row_0"], "name": [" Alice "], "age": [25]})
    spec_trim = TransformationSpec(
        transform_id="t1", transform_type="trim_whitespace", column="name"
    )
    spec_rename = TransformationSpec(
        transform_id="t2", transform_type="rename", column="name", target_column="full_name"
    )

    res_df, audit = apply_transformations(df, [spec_trim, spec_rename])
    assert "full_name" in res_df.columns
    assert res_df["full_name"][0] == "Alice"
    assert len(audit) == 2


def test_lineage_tracker() -> None:
    tracker = LineageTracker(run_id="run_100")
    tracker.record_stage("raw", "input.csv", "raw_df", "ingest", 10, 10)
    recs = tracker.get_records()
    assert len(recs) == 1
    assert recs[0].stage == "raw"


def test_sample_data_generators() -> None:
    csv_cust = get_sample_customers_csv()
    csv_dirty = get_sample_dirty_transactions_csv()
    pq_bytes = get_sample_parquet_bytes()

    assert len(csv_cust) > 0
    assert len(csv_dirty) > 0
    assert len(pq_bytes) > 0


def test_security_utilities() -> None:
    assert detect_sensitive_column("user_email") is True
    assert detect_sensitive_column("social_security_number") is True
    assert detect_sensitive_column("account_balance") is False

    assert sanitize_filename("../etc/passwd.csv") == "passwd.csv"


def test_export_utilities(sample_customers_df: pl.DataFrame) -> None:
    content, filename, mime = export_dataframe(sample_customers_df, "csv", "test_export")
    assert filename == "test_export.csv"
    assert mime == "text/csv"
    assert b"Alice Smith" in content

    json_bytes, j_name, j_mime = export_json_artifact({"status": "ok"}, "report")
    assert j_name == "report.json"
    assert b"status" in json_bytes
