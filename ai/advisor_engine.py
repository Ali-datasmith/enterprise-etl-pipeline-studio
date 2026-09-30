"""AI Contract Advisor engine using single-call structured Google Gemini inference."""

import time
from typing import Any

from google import genai
from google.genai import types
from loguru import logger

from ai.config import resolve_ai_config
from ai.error_taxonomy import classify_ai_error
from ai.models import AIAdvisorReport, get_clean_response_schema
from ai.prompt_templates import ADVISOR_PROMPT_VERSION, build_advisor_prompt
from ai.sanitizer import prepare_advisor_payload


def run_contract_advisor(
    profile: dict[str, Any], user_description: str = ""
) -> tuple[AIAdvisorReport, dict[str, Any]]:
    ai_cfg = resolve_ai_config()
    if not ai_cfg.is_available or not ai_cfg.api_key:
        raise RuntimeError("AI features are unavailable because GOOGLE_API_KEY is missing.")

    payload = prepare_advisor_payload(profile, user_description)
    prompt = build_advisor_prompt(payload)

    client = genai.Client(api_key=ai_cfg.api_key)
    start_time = time.time()

    clean_schema = get_clean_response_schema(AIAdvisorReport)

    try:
        response = client.models.generate_content(
            model=ai_cfg.model_name,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
                response_schema=clean_schema,
                temperature=0.1,
                system_instruction="You are an expert Data Governance and ETL Architect. Respond with JSON matching schema.",
            ),
        )
        latency = time.time() - start_time

        if hasattr(response, "parsed") and response.parsed is not None:
            if isinstance(response.parsed, AIAdvisorReport):
                report = response.parsed
            else:
                report = AIAdvisorReport.model_validate(response.parsed)
        else:
            raw_text = response.text or "{}"
            report = AIAdvisorReport.model_validate_json(raw_text)

        telemetry = {
            "model_name": ai_cfg.model_name,
            "latency_seconds": round(latency, 3),
            "prompt_version": ADVISOR_PROMPT_VERSION,
            "sample_columns_count": len(payload.get("columns", [])),
            "validation_status": "success",
        }

        logger.info(f"AI Contract Advisor completed in {latency:.2f}s.")
        return report, telemetry

    except Exception as e:
        logger.error(f"AI Contract Advisor failed: {e}")
        raise classify_ai_error(e) from e
