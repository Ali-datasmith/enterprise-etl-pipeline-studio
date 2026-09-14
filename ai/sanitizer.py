"""AI payload sanitization and sensitive field redaction module."""

from typing import Any

import polars as pl

from etl.constants import AI_ENRICHMENT_SAMPLE_LIMIT
from etl.security import detect_sensitive_column


def prepare_advisor_payload(profile: dict[str, Any], user_description: str = "") -> dict[str, Any]:
    columns_meta = []
    for col in profile.get("columns", []):
        columns_meta.append(
            {
                "name": col["name"],
                "logical_type": col["logical_type"],
                "null_percentage": col["null_percentage"],
                "unique_percentage": col.get("unique_percentage", 0.0),
                "is_sensitive": col.get("is_sensitive", False),
                "min_val": col.get("min_val") if not col.get("is_sensitive") else None,
                "max_val": col.get("max_val") if not col.get("is_sensitive") else None,
            }
        )

    return {
        "total_rows": profile.get("total_rows", 0),
        "total_columns": profile.get("total_columns", 0),
        "user_description": user_description[:500] if user_description else "",
        "columns": columns_meta,
    }


def prepare_enrichment_payload(
    df: pl.DataFrame,
    target_column: str,
    sensitive_columns: list[str],
    sample_limit: int = AI_ENRICHMENT_SAMPLE_LIMIT,
    redact_sensitive: bool = True,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    sampled_df = df.head(sample_limit)
    rows_data = sampled_df.to_dicts()

    redacted_count = 0
    sanitized_rows = []

    for row in rows_data:
        cleaned_row = {}
        for k, v in row.items():
            if k == "_row_id" or k == target_column:
                cleaned_row[k] = v
            else:
                if redact_sensitive and (k in sensitive_columns or detect_sensitive_column(k)):
                    cleaned_row[k] = "[REDACTED]"
                    redacted_count += 1
                else:
                    cleaned_row[k] = v
        sanitized_rows.append(cleaned_row)

    telemetry = {
        "sample_count": len(sanitized_rows),
        "redacted_fields_count": redacted_count,
        "target_column": target_column,
        "redaction_enabled": redact_sensitive,
    }

    return sanitized_rows, telemetry
