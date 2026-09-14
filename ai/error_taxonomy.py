"""Status-code-first error taxonomy and classification for AI and pipeline operations."""

import json

from pydantic import ValidationError

AI_QUOTA_EXHAUSTION = "AI Quota Exhaustion"
AI_AUTHENTICATION_ERROR = "AI Authentication Error"
AI_TIMEOUT_UNAVAILABLE = "AI Timeout / Server Unavailable"
AI_SCHEMA_VALIDATION_FAILURE = "AI Schema Validation Failure"
AI_POLICY_REFUSAL_ERROR = "AI Policy or Refusal Error"
FILE_PARSING_ERROR = "File Parsing Error"
DATA_SOURCE_NETWORK_ERROR = "Data Source Network Error"
CONTRACT_VALIDATION_ERROR = "Contract Validation Error"
QUALITY_GATE_FAILURE = "Quality Gate Failure"
PIPELINE_PROCESSING_ERROR = "Pipeline Processing Error"
EXPORT_ERROR = "Export Error"
UNEXPECTED_SYSTEM_ERROR = "Unexpected System Error"


class CategorizedError(Exception):
    def __init__(self, category: str, user_message: str, details: str | None = None) -> None:
        self.category = category
        self.user_message = user_message
        self.details = details
        super().__init__(f"[{category}] {user_message}")


def classify_ai_error(err: Exception) -> CategorizedError:
    if isinstance(err, ValidationError | json.JSONDecodeError):
        return CategorizedError(
            category=AI_SCHEMA_VALIDATION_FAILURE,
            user_message="AI response failed schema validation. Output was incomplete or malformed.",
            details=str(err),
        )

    err_str = str(err)
    status_code = getattr(err, "code", None) or getattr(err, "status_code", None)

    if status_code == 429:
        return CategorizedError(
            category=AI_QUOTA_EXHAUSTION,
            user_message="Gemini API rate limit or quota exceeded. Please wait or check your API quota.",
            details=err_str,
        )
    if status_code in (401, 403):
        return CategorizedError(
            category=AI_AUTHENTICATION_ERROR,
            user_message="Gemini API authentication failed. Please verify your GOOGLE_API_KEY.",
            details=err_str,
        )
    if status_code in (500, 502, 503, 504):
        return CategorizedError(
            category=AI_TIMEOUT_UNAVAILABLE,
            user_message="Gemini API service is temporarily unavailable or timed out.",
            details=err_str,
        )

    err_lower = err_str.lower()
    if "429" in err_lower or "quota" in err_lower or "resource_exhausted" in err_lower:
        return CategorizedError(
            category=AI_QUOTA_EXHAUSTION,
            user_message="Gemini API quota or rate limit exceeded.",
            details=err_str,
        )
    if (
        "401" in err_lower
        or "403" in err_lower
        or "api_key" in err_lower
        or "unauthorized" in err_lower
    ):
        return CategorizedError(
            category=AI_AUTHENTICATION_ERROR,
            user_message="Gemini API key is invalid or missing permission.",
            details=err_str,
        )
    if "timeout" in err_lower or "503" in err_lower or "unavailable" in err_lower:
        return CategorizedError(
            category=AI_TIMEOUT_UNAVAILABLE,
            user_message="AI request timed out or service unavailable.",
            details=err_str,
        )
    if "refusal" in err_lower or "safety" in err_lower or "policy" in err_lower:
        return CategorizedError(
            category=AI_POLICY_REFUSAL_ERROR,
            user_message="AI request was blocked by safety policy or content guardrails.",
            details=err_str,
        )

    return CategorizedError(
        category=UNEXPECTED_SYSTEM_ERROR,
        user_message="An unexpected AI execution error occurred.",
        details=err_str,
    )
