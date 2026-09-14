"""Prompt templates with explicit version tracking for AI actions."""

from typing import Any, Final

ADVISOR_PROMPT_VERSION: Final[str] = "v1.0.0"
ENRICHMENT_PROMPT_VERSION: Final[str] = "v1.0.0"


def build_advisor_prompt(payload: dict[str, Any]) -> str:
    return f"""
System: You are an expert Enterprise Data Governance and ETL Architect.
Analyse the dataset metadata profile below and recommend optimal column contracts, quality checks, transformations, and potential production data risks.
You MUST respond strictly with valid JSON conforming to the requested schema. Do not include markdown formatting or extra commentary outside the JSON response.

Dataset Metadata Profile:
Total Rows: {payload.get("total_rows")}
Total Columns: {payload.get("total_columns")}
User Description: {payload.get("user_description")}

Column Profiles:
{payload.get("columns")}
"""


def build_enrichment_prompt(
    task_description: str,
    target_column: str,
    enrichment_type: str,
    sample_records: list[dict[str, Any]],
) -> str:
    return f"""
System: You are an AI Data Enrichment Specialist.
Perform the specified enrichment task on the target column for each record below.
You MUST respond strictly with valid JSON conforming to the requested schema.
Maintain exact stable '_row_id' strings for every enriched record.

Enrichment Task: {task_description}
Target Column: {target_column}
Enrichment Type: {enrichment_type}

Sample Records to Enrich:
{sample_records}
"""
