"""Export module for generating download artifacts in various formats."""

import io
import json
from typing import Any

import polars as pl

from etl.security import sanitize_filename


def export_dataframe(
    df: pl.DataFrame,
    export_format: str = "csv",
    base_name: str = "curated_data",
) -> tuple[bytes, str, str]:
    clean_name = sanitize_filename(base_name)

    if export_format == "csv":
        buf = io.BytesIO()
        df.write_csv(buf)
        return buf.getvalue(), f"{clean_name}.csv", "text/csv"

    if export_format == "json":
        pdf = df.to_pandas()
        json_str = pdf.to_json(orient="records", indent=2)
        return (
            (json_str or "[]").encode("utf-8"),
            f"{clean_name}.json",
            "application/json",
        )

    if export_format == "parquet":
        buf = io.BytesIO()
        df.write_parquet(buf)
        return buf.getvalue(), f"{clean_name}.parquet", "application/octet-stream"

    raise ValueError(f"Unsupported export format: {export_format}")


def export_json_artifact(
    data: Any,
    base_name: str,
) -> tuple[bytes, str, str]:
    clean_name = sanitize_filename(base_name)
    if hasattr(data, "model_dump"):
        serializable = data.model_dump()
    elif isinstance(data, list) and data and hasattr(data[0], "model_dump"):
        serializable = [item.model_dump() for item in data]
    else:
        serializable = data

    json_bytes = json.dumps(serializable, indent=2, default=str).encode("utf-8")
    return json_bytes, f"{clean_name}.json", "application/json"
