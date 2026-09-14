"""Quality Gates & Validation UI tab."""

import pandas as pd
import streamlit as st

from etl.models import QualityReport
from ui.components import render_empty_state
from ui.controllers import run_full_pipeline_controller


def render_quality_tab() -> None:
    st.subheader("Data Quality Gates & Validation")

    raw_df = st.session_state.raw_dataset
    if raw_df is None:
        render_empty_state(
            "No Dataset Loaded",
            "Please load a dataset in the Data Source tab before evaluating quality gates.",
        )
        return

    is_busy = st.session_state.pipeline_running or st.session_state.ai_active

    col1, _ = st.columns([2, 1])
    with col1:
        if st.button("Run Pipeline Quality Gates", disabled=is_busy):
            run_full_pipeline_controller()

    report: QualityReport = st.session_state.quality_report

    if report:
        st.markdown("---")
        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Quality Score", f"{report.quality_score}/100")
        m2.metric("Passed Checks", report.passed_count)
        m3.metric("Warnings", report.warning_count)
        m4.metric("Failed Checks", report.failed_count)

        if report.gate_decision == "passed":
            st.success("🟢 Quality Gate Passed! Dataset meets all contract requirements.")
        elif report.gate_decision == "passed_with_warnings":
            st.warning("🟡 Quality Gate Passed with Warnings. Review warnings below.")
        else:
            st.error("🚨 Quality Gate BLOCKED. Critical checks failed.")

        st.markdown("##### Detailed Check Results")
        results_data = [r.model_dump() for r in report.results]
        st.dataframe(pd.DataFrame(results_data), use_container_width=True)

        quarantine_df = st.session_state.quarantine_dataset
        if quarantine_df is not None and quarantine_df.height > 0:
            with st.expander(f"⚠️ Quarantined Records ({quarantine_df.height} rows)"):
                st.dataframe(quarantine_df.head(50).to_pandas(), use_container_width=True)
    else:
        render_empty_state(
            "Quality Gates Not Executed",
            "Click 'Run Pipeline Quality Gates' above to validate dataset against contract rules.",
        )
