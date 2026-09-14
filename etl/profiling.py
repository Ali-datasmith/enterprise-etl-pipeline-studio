"""Data profiling module using Polars and DuckDB."""

from typing import Any

import duckdb
import polars as pl
from loguru import logger

from etl.security import detect_sensitive_column


def infer_logical_type(series: pl.Series) -> str:
    dtype = series.dtype
    col_name = series.name.lower()

    if dtype in (pl.Int8, pl.Int16, pl.Int32, pl.Int64, pl.UInt8, pl.UInt16, pl.UInt32, pl.UInt64):
        if col_name.endswith("_id") or col_name == "id":
            return "identifier"
        return "integer"
    if dtype in (pl.Float32, pl.Float64):
        return "float"
    if dtype == pl.Boolean:
        return "boolean"
    if dtype == pl.Date:
        return "date"
    if dtype in (pl.Datetime, pl.Time):
        return "datetime"
    if dtype == pl.Categorical:
        return "category"
    if dtype in (pl.Utf8, pl.String):
        if col_name.endswith("_id") or col_name == "id":
            return "identifier"
        if "date" in col_name or "time" in col_name or "timestamp" in col_name:
            return "datetime"
        n_unique = series.n_unique()
        if n_unique > 0 and n_unique <= 10 and series.len() > 20:
            return "category"
        if series.dtype == pl.Utf8:
            mean_len = series.str.len_chars().mean()
            if mean_len is not None and float(str(mean_len)) > 100:
                return "text"
        return "string"

    return "unknown"


def profile_dataset(df: pl.DataFrame, sample_size: int = 100_000) -> dict[str, Any]:
    total_rows = df.height
    total_cols = df.width

    if total_rows > sample_size:
        sampled_df = df.sample(n=sample_size, seed=42)
        is_sampled = True
    else:
        sampled_df = df
        is_sampled = False

    column_profiles: list[dict[str, Any]] = []
    has_geospatial = False

    for col in sampled_df.columns:
        if col == "_row_id":
            continue

        series = sampled_df[col]
        null_count = series.null_count()
        null_pct = round((null_count / total_rows) * 100, 2) if total_rows > 0 else 0.0
        n_unique = series.n_unique()
        unique_pct = round((n_unique / total_rows) * 100, 2) if total_rows > 0 else 0.0

        logical_type = infer_logical_type(series)
        is_sensitive = detect_sensitive_column(col)

        col_lower = col.lower()
        if col_lower in ("lat", "latitude", "lon", "long", "longitude"):
            has_geospatial = True

        stats: dict[str, Any] = {
            "name": col,
            "physical_type": str(series.dtype),
            "logical_type": logical_type,
            "null_count": null_count,
            "null_percentage": null_pct,
            "unique_count": n_unique,
            "unique_percentage": unique_pct,
            "is_sensitive": is_sensitive,
            "min_val": None,
            "max_val": None,
            "mean_val": None,
        }

        if series.dtype.is_numeric():
            non_null_series = series.drop_nulls()
            if non_null_series.len() > 0:
                min_v = non_null_series.min()
                max_v = non_null_series.max()
                mean_v = non_null_series.mean()
                stats["min_val"] = float(str(min_v)) if min_v is not None else None
                stats["max_val"] = float(str(max_v)) if max_v is not None else None
                stats["mean_val"] = float(str(mean_v)) if mean_v is not None else None

        column_profiles.append(stats)

    con = duckdb.connect()
    con.register("df_view", sampled_df.to_pandas())
    duck_summary = con.execute("SELECT COUNT(*) as cnt FROM df_view").fetchone()
    con.close()

    summary = {
        "total_rows": total_rows,
        "total_columns": total_cols,
        "is_sampled": is_sampled,
        "sample_size": sampled_df.height,
        "has_geospatial": has_geospatial,
        "duckdb_row_check": duck_summary[0] if duck_summary else total_rows,
        "columns": column_profiles,
    }

    logger.info(f"Dataset profiled: {total_rows} rows, {total_cols} columns.")
    return summary
