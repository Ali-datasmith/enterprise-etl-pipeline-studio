"""State management and initialization contract for Streamlit session state."""

from typing import Any

import streamlit as st


def init_session_state() -> None:
    default_state: dict[str, Any] = {
        "app_initialized": True,
        "pipeline_running": False,
        "ai_active": False,
        "data_source_meta": None,
        "raw_dataset": None,
        "profile_report": None,
        "pipeline_config": None,
        "contract_data": None,
        "quality_report": None,
        "transformed_dataset": None,
        "enriched_dataset": None,
        "curated_dataset": None,
        "quarantine_dataset": None,
        "lineage_records": [],
        "run_meta": None,
        "ai_advisor_result": None,
        "ai_enrichment_result": None,
        "ai_error_message": None,
        "pipeline_error_message": None,
        "ai_enrichment_acknowledged": False,
    }

    for key, default_val in default_state.items():
        if key not in st.session_state:
            st.session_state[key] = default_val


def reset_pipeline_state() -> None:
    st.session_state.pipeline_running = False
    st.session_state.pipeline_error_message = None


def reset_ai_state() -> None:
    st.session_state.ai_active = False
    st.session_state.ai_error_message = None


def clear_stale_outputs() -> None:
    st.session_state.transformed_dataset = None
    st.session_state.enriched_dataset = None
    st.session_state.curated_dataset = None
    st.session_state.quarantine_dataset = None
    st.session_state.quality_report = None
    st.session_state.lineage_records = []
    st.session_state.ai_advisor_result = None
    st.session_state.ai_enrichment_result = None
    st.session_state.pipeline_error_message = None
    st.session_state.ai_error_message = None
