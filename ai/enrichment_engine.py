"""AI Dataset Enrichment engine using single-call structured Google Gemini inference."""

import time
from typing import Any

import polars as pl
from google import genai
from google.genai import types
from loguru import logger

from ai.config import resolve_ai_config
from ai.error_taxonomy import classify_ai_error
from ai.models import AIEnrichmentReport
from ai.prompt_templates import ENRICHMENT_PROMPT_VERSION, build_enrichment_prompt
from ai.sanitizer import prepare_enrichment_payload
from etl.constants import AI_ENRICHMENT_SAMPLE_LIMIT


def run_dataset_enrichment(
    df: pl.DataFrame,
    target_column: str,
    task_description: str,
    enrichment_type: str = "classification",
    sensitive_columns: list[str] | None = None,
    sample_limit: int = AI_ENRICHMENT_SAMPLE_LIMIT,
    redact_sensitive: bool = True,
) -> tuple[AIEnrichmentReport, dict[str, Any]]:
    ai_cfg = resolve_ai_config()
    if not ai_cfg.is_available or not ai_cfg.api_key:
        raise RuntimeError("AI features are unavailable because GOOGLE_API_KEY is missing.")

    sensitive_cols = sensitive_columns or []
    sanitized_rows, sanitization_meta = prepare_enrichment_payload(
        df=df,
        target_column=target_column,
        sensitive_columns=sensitive_cols,
        sample_limit=sample_limit,
        redact_sensitive=redact_sensitive,
    )

    prompt = build_enrichment_prompt(
        task_description=task_description,
        target_column=target_column,
        enrichment_type=enrichment_type,
        sample_records=sanitized_rows,
    )

    client = genai.Client(api_key=ai_cfg.api_key)
    start_time = time.time()

    try:
        response = client.models.generate_content(
            model=ai_cfg.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=AIEnrichmentReport,
                temperature=0.1,
                system_instruction="You are an AI Data Enrichment Specialist. Respond strictly with JSON matching schema.",
            ),
        )
        latency = time.time() - start_time

        if hasattr(response, "parsed") and response.parsed is not None:
            if isinstance(response.parsed, AIEnrichmentReport):
                report = response.parsed
            else:
                report = AIEnrichmentReport.model_validate(response.parsed)
        else:
            raw_text = response.text or "{}"
            report = AIEnrichmentReport.model_validate_json(raw_text)

        telemetry = {
            "model_name": ai_cfg.model_name,
            "latency_seconds": round(latency, 3),
            "prompt_version": ENRICHMENT_PROMPT_VERSION,
            "sample_count": len(sanitized_rows),
            "redaction_meta": sanitization_meta,
            "validation_status": "success",
        }

        logger.info(f"AI Dataset Enrichment completed in {latency:.2f}s.")
        return report, telemetry

    except Exception as e:
        logger.error(f"AI Dataset Enrichment failed: {e}")
        raise classify_ai_error(e) from e
