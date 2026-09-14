"""Data transformation engine using Polars."""

from typing import Any

import polars as pl
from loguru import logger

from etl.models import TransformationSpec


class TransformationError(Exception):
    pass


def apply_transformation(df: pl.DataFrame, spec: TransformationSpec) -> pl.DataFrame:
    if not spec.enabled:
        return df

    ttype = spec.transform_type
    col = spec.column
    target_col = spec.target_column or col
    params = spec.parameters or {}

    try:
        if ttype == "rename":
            if col and col in df.columns and target_col:
                return df.rename({col: target_col})
            return df

        if ttype == "cast":
            if col and col in df.columns:
                target_type_str = params.get("target_type", "string").lower()
                dtype_map = {
                    "string": pl.Utf8,
                    "integer": pl.Int64,
                    "float": pl.Float64,
                    "boolean": pl.Boolean,
                    "date": pl.Date,
                    "datetime": pl.Datetime,
                }
                pl_type = dtype_map.get(target_type_str, pl.Utf8)
                return df.with_columns(pl.col(col).cast(pl_type, strict=False))
            return df

        if ttype == "trim_whitespace":
            if col and col in df.columns:
                if df[col].dtype == pl.Utf8:
                    return df.with_columns(pl.col(col).str.strip_chars())
            else:
                str_cols = [c for c in df.columns if df[c].dtype == pl.Utf8]
                if str_cols:
                    return df.with_columns([pl.col(c).str.strip_chars() for c in str_cols])
            return df

        if ttype == "normalize_timestamp":
            if col and col in df.columns:
                fmt = params.get("format", "%Y-%m-%d %H:%M:%S")
                return df.with_columns(
                    pl.col(col).str.to_datetime(fmt, strict=False).alias(target_col or col)
                )
            return df

        if ttype == "deduplicate":
            subset = params.get("subset_columns") or ([col] if col else None)
            if subset:
                valid_subset = [c for c in subset if c in df.columns]
                if valid_subset:
                    return df.unique(subset=valid_subset)
            return df.unique()

        if ttype == "fill_null":
            if col and col in df.columns:
                fill_val = params.get("value", "")
                strategy = params.get("strategy")
                if strategy == "mean" and df[col].dtype.is_numeric():
                    mean_v = df[col].mean()
                    return df.with_columns(pl.col(col).fill_null(mean_v))
                if strategy == "median" and df[col].dtype.is_numeric():
                    median_v = df[col].median()
                    return df.with_columns(pl.col(col).fill_null(median_v))
                return df.with_columns(pl.col(col).fill_null(fill_val))
            return df

        if ttype == "drop_column":
            cols_to_drop = params.get("columns") or ([col] if col else [])
            valid_drops = [c for c in cols_to_drop if c in df.columns and c != "_row_id"]
            if valid_drops:
                return df.drop(valid_drops)
            return df

        if ttype == "filter_rows":
            if col and col in df.columns:
                op = params.get("operator", "==")
                val = params.get("value")
                if op == "==":
                    return df.filter(pl.col(col) == val)
                if op == "!=":
                    return df.filter(pl.col(col) != val)
                if op == ">":
                    return df.filter(pl.col(col) > val)
                if op == "<":
                    return df.filter(pl.col(col) < val)
                if op == "is_not_null":
                    return df.filter(pl.col(col).is_not_null())
            return df

        if ttype == "aggregate":
            group_by_cols = params.get("group_by", [])
            valid_groups = [c for c in group_by_cols if c in df.columns]
            agg_col = col or (valid_groups[0] if valid_groups else None)
            agg_func = params.get("function", "count")

            if valid_groups and agg_col and agg_col in df.columns:
                if agg_func == "sum":
                    return df.group_by(valid_groups).agg(pl.col(agg_col).sum())
                if agg_func == "mean":
                    return df.group_by(valid_groups).agg(pl.col(agg_col).mean())
                if agg_func == "min":
                    return df.group_by(valid_groups).agg(pl.col(agg_col).min())
                if agg_func == "max":
                    return df.group_by(valid_groups).agg(pl.col(agg_col).max())
                return df.group_by(valid_groups).agg(pl.len().alias("count"))

        return df

    except Exception as e:
        logger.error(f"Transformation '{ttype}' failed on column '{col}': {e}")
        raise TransformationError(
            f"Pipeline Processing Error: Transformation '{ttype}' failed. {e}"
        ) from e


def apply_transformations(
    df: pl.DataFrame, specs: list[TransformationSpec]
) -> tuple[pl.DataFrame, list[dict[str, Any]]]:
    current_df = df
    audit_log: list[dict[str, Any]] = []

    for spec in specs:
        if not spec.enabled:
            continue
        rows_before = current_df.height
        current_df = apply_transformation(current_df, spec)
        rows_after = current_df.height

        audit_log.append(
            {
                "transform_id": spec.transform_id,
                "transform_type": spec.transform_type,
                "column": spec.column,
                "rows_before": rows_before,
                "rows_after": rows_after,
            }
        )

    return current_df, audit_log
