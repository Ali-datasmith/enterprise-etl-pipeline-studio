"""Tests for UI components, state initialization, guards, and controllers."""

import polars as pl
import streamlit as st

from ui.controllers import handle_sample_load, run_full_pipeline_controller
from ui.state import clear_stale_outputs, init_session_state, reset_ai_state, reset_pipeline_state


def test_init_session_state() -> None:
    init_session_state()
    assert st.session_state.app_initialized is True
    assert st.session_state.pipeline_running is False
    assert st.session_state.ai_active is False
    assert isinstance(st.session_state.lineage_records, list)


def test_reset_and_clear_state_helpers() -> None:
    init_session_state()
    st.session_state.pipeline_running = True
    st.session_state.ai_active = True
    st.session_state.pipeline_error_message = "error"
    st.session_state.ai_error_message = "error"

    reset_pipeline_state()
    assert st.session_state.pipeline_running is False
    assert st.session_state.pipeline_error_message is None

    reset_ai_state()
    assert st.session_state.ai_active is False
    assert st.session_state.ai_error_message is None

    st.session_state.curated_dataset = pl.DataFrame({"a": [1]})
    clear_stale_outputs()
    assert st.session_state.curated_dataset is None


def test_handle_sample_load() -> None:
    init_session_state()
    handle_sample_load("customers")
    assert st.session_state.raw_dataset is not None
    assert st.session_state.data_source_meta is not None
    assert st.session_state.data_source_meta.source_name == "sample_customers_geospatial.csv"
    assert st.session_state.pipeline_running is False


def test_run_full_pipeline_controller() -> None:
    init_session_state()
    handle_sample_load("customers")
    run_full_pipeline_controller()

    assert st.session_state.quality_report is not None
    assert st.session_state.curated_dataset is not None
    assert len(st.session_state.lineage_records) > 0
    assert st.session_state.run_meta is not None
    assert st.session_state.pipeline_running is False
