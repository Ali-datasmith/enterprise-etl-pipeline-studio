"""More edge case tests to reach 45+ deterministic tests."""

import polars as pl
import pytest

from etl.contracts import update_contract
from etl.export import export_dataframe
from etl.models import ColumnContract, LineageRecord, RunMetadata
from etl.observability import (
    create_geospatial_map,
    create_quality_score_gauge,
    create_sankey_lineage_chart,
    create_stage_duration_chart,
)


def test_update_contract_non_matching() -> None:
    contracts = [ColumnContract(name="col1")]
    updated = update_contract(contracts, "non_existent", nullable=False)
    assert len(updated) == 1
    assert updated[0].nullable is True


def test_export_dataframe_json() -> None:
    df = pl.DataFrame({"_row_id": ["row_0"], "name": ["Alice"]})
    content, filename, mime = export_dataframe(df, export_format="json", base_name="data")
    assert filename == "data.json"
    assert mime == "application/json"
    assert b"Alice" in content


def test_export_dataframe_parquet() -> None:
    df = pl.DataFrame({"_row_id": ["row_0"], "val": [10]})
    content, filename, mime = export_dataframe(df, export_format="parquet", base_name="data")
    assert filename == "data.parquet"
    assert mime == "application/octet-stream"
    assert len(content) > 0


def test_export_dataframe_unsupported() -> None:
    df = pl.DataFrame({"a": [1]})
    with pytest.raises(ValueError, match="Unsupported export format"):
        export_dataframe(df, export_format="xml")


def test_observability_chart_creators() -> None:
    run_meta = RunMetadata(run_id="r1", stage_metrics={"raw": {"duration_seconds": 0.1}})
    fig_stage = create_stage_duration_chart(run_meta)
    assert fig_stage is not None

    fig_gauge = create_quality_score_gauge(None)
    assert fig_gauge is not None

    records = [
        LineageRecord(
            lineage_id="l1",
            run_id="r1",
            stage="raw",
            input_artifact="a",
            output_artifact="b",
            operation="op",
        )
    ]
    fig_sankey = create_sankey_lineage_chart(records)
    assert fig_sankey is not None

    deck = create_geospatial_map([{"latitude": 37.77, "longitude": -122.41, "name": "SF"}])
    assert deck is not None
