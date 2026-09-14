"""Tests for AI components, models, sanitizers, error taxonomy, and engines."""

from unittest.mock import MagicMock, patch

import polars as pl
import pytest

from ai.advisor_engine import run_contract_advisor
from ai.config import resolve_ai_config
from ai.enrichment_engine import run_dataset_enrichment
from ai.error_taxonomy import (
    AI_AUTHENTICATION_ERROR,
    AI_QUOTA_EXHAUSTION,
    classify_ai_error,
)
from ai.models import AIAdvisorReport, AIEnrichmentReport, EnrichedRecord, RecommendedColumn
from ai.sanitizer import prepare_advisor_payload, prepare_enrichment_payload


def test_ai_advisor_report_validation() -> None:
    report = AIAdvisorReport(
        overview="Good dataset quality.",
        estimated_data_quality_score=90,
        recommended_columns=[
            RecommendedColumn(
                name="user_id",
                logical_type="identifier",
                nullable=False,
                unique=True,
                sensitive=False,
                rationale="PK",
            )
        ],
        governance_notes="All clear",
    )
    assert report.estimated_data_quality_score == 90
    assert len(report.recommended_columns) == 1


def test_prepare_advisor_payload() -> None:
    profile = {
        "total_rows": 100,
        "total_columns": 2,
        "columns": [
            {
                "name": "id",
                "logical_type": "integer",
                "null_percentage": 0.0,
                "is_sensitive": False,
            },
            {"name": "ssn", "logical_type": "string", "null_percentage": 0.0, "is_sensitive": True},
        ],
    }
    payload = prepare_advisor_payload(profile, "User notes")
    assert payload["total_rows"] == 100
    assert len(payload["columns"]) == 2


def test_prepare_enrichment_payload() -> None:
    df = pl.DataFrame(
        {
            "_row_id": ["row_0", "row_1"],
            "comment": ["Great product!", "Bad service."],
            "email": ["a@example.com", "b@example.com"],
        }
    )
    rows, meta = prepare_enrichment_payload(
        df, "comment", sensitive_columns=["email"], redact_sensitive=True
    )
    assert len(rows) == 2
    assert rows[0]["email"] == "[REDACTED]"
    assert meta["redacted_fields_count"] == 2


def test_classify_ai_error() -> None:
    class MockHttpError(Exception):
        status_code = 429

    err_429 = MockHttpError("Resource exhausted")
    classified_429 = classify_ai_error(err_429)
    assert classified_429.category == AI_QUOTA_EXHAUSTION

    class MockAuthError(Exception):
        status_code = 401

    err_401 = MockAuthError("Invalid API Key")
    classified_401 = classify_ai_error(err_401)
    assert classified_401.category == AI_AUTHENTICATION_ERROR


def test_ai_disabled_when_no_api_key(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.delenv("GOOGLE_API_KEY", raising=False)
    cfg = resolve_ai_config()
    assert cfg.is_available is False

    profile = {"total_rows": 10, "total_columns": 1, "columns": []}
    with pytest.raises(RuntimeError, match="GOOGLE_API_KEY is missing"):
        run_contract_advisor(profile)


@patch("google.genai.Client")
def test_mocked_contract_advisor_single_call(
    mock_genai_client: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "fake_key_12345")

    mock_client_instance = MagicMock()
    mock_genai_client.return_value = mock_client_instance

    mock_report = AIAdvisorReport(
        overview="Mocked overview",
        estimated_data_quality_score=95,
        governance_notes="Mocked notes",
    )

    mock_response = MagicMock()
    mock_response.parsed = mock_report
    mock_client_instance.models.generate_content.return_value = mock_response

    profile = {"total_rows": 50, "total_columns": 2, "columns": []}
    report, telemetry = run_contract_advisor(profile, "test desc")

    assert report.estimated_data_quality_score == 95
    assert telemetry["validation_status"] == "success"
    assert mock_client_instance.models.generate_content.call_count == 1


@patch("google.genai.Client")
def test_mocked_dataset_enrichment_single_call(
    mock_genai_client: MagicMock, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setenv("GOOGLE_API_KEY", "fake_key_12345")

    mock_client_instance = MagicMock()
    mock_genai_client.return_value = mock_client_instance

    mock_enrich_report = AIEnrichmentReport(
        task="sentiment classification",
        target_column="comment",
        enrichment_type="classification",
        enriched_records=[EnrichedRecord(row_id="row_0", label="positive", confidence=0.98)],
        governance_notes="Mocked enrichment notes",
    )

    mock_response = MagicMock()
    mock_response.parsed = mock_enrich_report
    mock_client_instance.models.generate_content.return_value = mock_response

    df = pl.DataFrame({"_row_id": ["row_0"], "comment": ["Awesome!"]})
    report, telemetry = run_dataset_enrichment(df, "comment", "Classify sentiment")

    assert report.enriched_records[0].label == "positive"
    assert mock_client_instance.models.generate_content.call_count == 1
