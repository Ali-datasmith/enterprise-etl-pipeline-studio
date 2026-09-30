"""UI controllers for executing guarded pipeline operations."""

import time
import uuid
from typing import Any
from urllib.parse import urlparse

import polars as pl
import streamlit as st
from loguru import logger

from ai.advisor_engine import run_contract_advisor
from ai.enrichment_engine import run_dataset_enrichment
from etl.contracts import infer_contract_from_profile
from etl.ingestion import fetch_url_content, ingest_data_source, normalize_url
from etl.lineage import LineageTracker
from etl.models import PipelineConfig, RunMetadata
from etl.profiling import profile_dataset
from etl.sample_data import (
    get_sample_customers_csv,
    get_sample_dirty_transactions_csv,
    get_sample_parquet_bytes,
)
from etl.transforms import apply_transformations
from etl.validation import run_quality_gates
from ui.state import clear_stale_outputs, reset_ai_state, reset_pipeline_state


def handle_file_upload(uploaded_file: Any) -> None:
    if not uploaded_file:
        return

    st.session_state.pipeline_running = True
    try:
        content = uploaded_file.getvalue()
        file_name = uploaded_file.name
        df, meta = ingest_data_source(content, file_name, source_type="file_upload")

        clear_stale_outputs()
        st.session_state.raw_dataset = df
        st.session_state.data_source_meta = meta

        profile = profile_dataset(df)
        contracts = infer_contract_from_profile(profile)

        st.session_state.profile_report = profile
        st.session_state.contract_data = contracts
        st.session_state.pipeline_config = PipelineConfig(
            pipeline_name=f"pipeline_{meta.file_name}"
        )

        st.success(
            f"Successfully ingested {meta.file_name} ({df.height} rows, {df.width} columns)."
        )
    except Exception as e:
        logger.error(f"Ingestion controller failure: {e}")
        st.session_state.pipeline_error_message = f"File Parsing Error: {e}"
    finally:
        reset_pipeline_state()


def handle_sample_load(sample_key: str) -> None:
    st.session_state.pipeline_running = True
    try:
        if sample_key == "customers":
            content = get_sample_customers_csv()
            file_name = "sample_customers_geospatial.csv"
        elif sample_key == "dirty_txns":
            content = get_sample_dirty_transactions_csv()
            file_name = "sample_dirty_transactions.csv"
        else:
            content = get_sample_parquet_bytes()
            file_name = "sample_products.parquet"

        df, meta = ingest_data_source(content, file_name, source_type="sample_dataset")

        clear_stale_outputs()
        st.session_state.raw_dataset = df
        st.session_state.data_source_meta = meta

        profile = profile_dataset(df)
        contracts = infer_contract_from_profile(profile)

        st.session_state.profile_report = profile
        st.session_state.contract_data = contracts
        st.session_state.pipeline_config = PipelineConfig(pipeline_name=f"pipeline_{sample_key}")

        st.success(f"Loaded sample dataset '{file_name}' ({df.height} rows).")
    except Exception as e:
        logger.error(f"Sample load controller failure: {e}")
        st.session_state.pipeline_error_message = f"Sample Load Error: {e}"
    finally:
        reset_pipeline_state()


def handle_url_fetch(url: str) -> None:
    if not url or not url.strip():
        st.warning("Please enter a valid HTTP/HTTPS URL.")
        return

    normalized_url = normalize_url(url)

    st.session_state.pipeline_running = True
    try:
        content = fetch_url_content(normalized_url)

        parsed_target = urlparse(normalized_url)
        candidate_name = parsed_target.path.rstrip("/").split("/")[-1]
        file_name = candidate_name if "." in candidate_name else "url_download.csv"

        df, meta = ingest_data_source(
            content,
            file_name,
            source_type="url_fetch",
            notes=f"Fetched from {normalized_url}",
        )

        clear_stale_outputs()
        st.session_state.raw_dataset = df
        st.session_state.data_source_meta = meta

        profile = profile_dataset(df)
        contracts = infer_contract_from_profile(profile)

        st.session_state.profile_report = profile
        st.session_state.contract_data = contracts
        st.session_state.pipeline_config = PipelineConfig(pipeline_name="pipeline_url_fetch")

        st.success(f"Successfully fetched dataset from URL ({df.height} rows).")
    except Exception as e:
        logger.error(f"URL fetch controller failure: {e}")
        st.session_state.pipeline_error_message = (
            f"{e}\n\nHint: check that the host name resolves (for example, "
            "'raw.githubusercontent.com' needs the full 'user/repo/branch/path' route)."
        )
    finally:
        reset_pipeline_state()


def run_full_pipeline_controller() -> None:
    raw_df: pl.DataFrame = st.session_state.raw_dataset
    contracts = st.session_state.contract_data
    cfg: PipelineConfig = st.session_state.pipeline_config or PipelineConfig()

    if raw_df is None or not contracts:
        st.error("Cannot run pipeline without raw data and contract definition.")
        return

    run_id = f"run_{uuid.uuid4().hex[:8]}"
    tracker = LineageTracker(run_id)
    start_time = time.time()

    st.session_state.pipeline_running = True
    stage_metrics: dict[str, Any] = {}

    try:
        s1_start = time.time()
        tracker.record_stage(
            stage="raw_landing",
            input_artifact="source_input",
            output_artifact="raw_snapshot",
            operation="ingest_and_assign_row_id",
            row_count_in=raw_df.height,
            row_count_out=raw_df.height,
        )
        stage_metrics["raw_landing"] = {"duration_seconds": round(time.time() - s1_start, 3)}

        stage_metrics["contract_definition"] = {"duration_seconds": 0.01}

        v_start = time.time()
        q_report, quarantine_df = run_quality_gates(
            df=raw_df,
            contracts=contracts,
            policy=cfg.quality_gate_policy,
            run_id=run_id,
        )
        st.session_state.quality_report = q_report
        st.session_state.quarantine_dataset = quarantine_df

        tracker.record_stage(
            stage="quality_gates",
            input_artifact="raw_snapshot",
            output_artifact="validated_data",
            operation="evaluate_contract_rules",
            row_count_in=raw_df.height,
            row_count_out=raw_df.height - quarantine_df.height
            if quarantine_df is not None
            else raw_df.height,
            status="failed" if q_report.gate_decision == "blocked" else "success",
        )
        stage_metrics["quality_gates"] = {"duration_seconds": round(time.time() - v_start, 3)}

        if q_report.gate_decision == "blocked":
            st.warning("Pipeline publishing blocked due to critical quality gate failures.")
            return

        t_start = time.time()
        transformed_df, _ = apply_transformations(raw_df, cfg.transformations)
        st.session_state.transformed_dataset = transformed_df

        tracker.record_stage(
            stage="transformation",
            input_artifact="validated_data",
            output_artifact="transformed_data",
            operation="apply_user_transformations",
            row_count_in=raw_df.height,
            row_count_out=transformed_df.height,
        )
        stage_metrics["transformation"] = {"duration_seconds": round(time.time() - t_start, 3)}

        curated_df = transformed_df
        st.session_state.curated_dataset = curated_df

        tracker.record_stage(
            stage="publish",
            input_artifact="transformed_data",
            output_artifact="curated_dataset",
            operation="publish_curated_baseline",
            row_count_in=transformed_df.height,
            row_count_out=curated_df.height,
        )

        st.session_state.lineage_records = tracker.get_records()

        total_duration = round(time.time() - start_time, 3)
        st.session_state.run_meta = RunMetadata(
            run_id=run_id,
            duration_seconds=total_duration,
            stage_metrics=stage_metrics,
            row_count_input=raw_df.height,
            row_count_output=curated_df.height,
        )

        st.success(f"Pipeline executed successfully in {total_duration}s!")

    except Exception as e:
        logger.error(f"Pipeline execution error: {e}")
        st.session_state.pipeline_error_message = f"Pipeline Processing Error: {e}"
    finally:
        reset_pipeline_state()


def run_ai_advisor_controller(user_desc: str) -> None:
    profile = st.session_state.profile_report
    if not profile:
        st.error("No profiled dataset available for AI Contract Advisor.")
        return

    st.session_state.ai_active = True
    try:
        report, telemetry = run_contract_advisor(profile, user_desc)
        st.session_state.ai_advisor_result = {
            "report": report,
            "telemetry": telemetry,
        }
        st.success("AI Contract Advisor recommendations received!")
    except Exception as e:
        logger.error(f"AI Advisor controller failure: {e}")
        cat_err = getattr(e, "category", "Unexpected System Error")
        msg = getattr(e, "user_message", str(e))
        st.session_state.ai_error_message = f"[{cat_err}] {msg}"
    finally:
        reset_ai_state()


def run_ai_enrichment_controller(
    target_column: str,
    task_desc: str,
    enrich_type: str,
    sensitive_cols: list[str],
    sample_limit: int,
) -> None:
    df: pl.DataFrame = st.session_state.raw_dataset
    if df is None:
        st.error("No dataset available for AI enrichment.")
        return

    st.session_state.ai_active = True
    try:
        report, telemetry = run_dataset_enrichment(
            df=df,
            target_column=target_column,
            task_description=task_desc,
            enrichment_type=enrich_type,
            sensitive_columns=sensitive_cols,
            sample_limit=sample_limit,
            redact_sensitive=True,
        )
        st.session_state.ai_enrichment_result = {
            "report": report,
            "telemetry": telemetry,
        }
        st.success("AI Enrichment results generated successfully!")
    except Exception as e:
        logger.error(f"AI Enrichment controller failure: {e}")
        cat_err = getattr(e, "category", "Unexpected System Error")
        msg = getattr(e, "user_message", str(e))
        st.session_state.ai_error_message = f"[{cat_err}] {msg}"
    finally:
        reset_ai_state()
