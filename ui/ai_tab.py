"""AI Assistant UI tab for Contract Advisor and Record Enrichment."""

import pandas as pd
import streamlit as st

from ai.config import resolve_ai_config
from ui.components import render_ai_availability_banner, render_empty_state
from ui.controllers import run_ai_advisor_controller, run_ai_enrichment_controller


def render_ai_tab() -> None:
    st.subheader("AI Assistance & Governed Intelligence")

    render_ai_availability_banner()

    ai_cfg = resolve_ai_config()
    is_busy = st.session_state.pipeline_running or st.session_state.ai_active
    ai_disabled = not ai_cfg.is_available or is_busy

    raw_df = st.session_state.raw_dataset
    if raw_df is None:
        render_empty_state(
            "No Dataset Loaded",
            "Please load a dataset in the Data Source tab to use AI features.",
        )
        return

    tab1, tab2 = st.tabs(["AI Contract Advisor", "AI Dataset Enrichment"])

    with tab1:
        st.markdown("##### Governed Schema & Quality Contract Advisor")
        st.caption(
            "Sends sanitized schema metadata and statistics to Google Gemini to recommend contracts and checks."
        )

        user_desc = st.text_area(
            "Business Context / Notes (Optional)",
            placeholder="e.g. E-commerce customer transactions dataset for compliance auditing...",
            disabled=ai_disabled,
        )

        if st.button("Run AI Contract Advisor", disabled=ai_disabled, key="btn_advisor"):
            run_ai_advisor_controller(user_desc)

        res = st.session_state.ai_advisor_result
        if res:
            rep = res["report"]
            st.markdown("---")
            st.markdown(f"### Quality Rating: {rep.estimated_data_quality_score}/100")
            st.markdown(f"**Overview:** {rep.overview}")

            with st.expander("Recommended Column Contracts", expanded=True):
                st.dataframe(
                    pd.DataFrame([c.model_dump() for c in rep.recommended_columns]),
                    width="stretch",
                )

            with st.expander("Recommended Quality Checks"):
                st.dataframe(
                    pd.DataFrame([chk.model_dump() for chk in rep.recommended_checks]),
                    width="stretch",
                )

            with st.expander("Identified Production Risks"):
                st.dataframe(
                    pd.DataFrame([r.model_dump() for r in rep.production_risks]),
                    width="stretch",
                )

    with tab2:
        st.markdown("##### Sanitized Sample Record Enrichment")
        st.caption(
            "Enriches a sanitized sample of records with sentiment, classification, or entity tags."
        )

        c1, c2 = st.columns(2)
        with c1:
            target_col = st.selectbox(
                "Target Column to Enrich", options=raw_df.columns, disabled=ai_disabled
            )
            enrich_type = st.selectbox(
                "Enrichment Type",
                options=[
                    "classification",
                    "summarization",
                    "entity_extraction",
                    "normalization",
                    "risk_flagging",
                ],
                disabled=ai_disabled,
            )
        with c2:
            task_desc = st.text_input(
                "Enrichment Task Instructions",
                value="Classify sentiment or risk category for each text value.",
                disabled=ai_disabled,
            )
            sample_limit = st.slider(
                "Sanitized Sample Limit", min_value=5, max_value=20, value=10, disabled=ai_disabled
            )

        sensitive_cols = [c for c in raw_df.columns if "email" in c or "ssn" in c or "name" in c]
        st.caption(f"🔒 Auto-detected sensitive columns for redaction: {sensitive_cols}")

        if st.button("Run AI Sample Enrichment", disabled=ai_disabled, key="btn_enrichment"):
            run_ai_enrichment_controller(
                target_column=target_col,
                task_desc=task_desc,
                enrich_type=enrich_type,
                sensitive_cols=sensitive_cols,
                sample_limit=sample_limit,
            )

        res_en = st.session_state.ai_enrichment_result
        if res_en:
            rep_en = res_en["report"]
            st.markdown("---")
            st.markdown(f"**Governance Notes:** {rep_en.governance_notes}")
            records_data = [rec.model_dump() for rec in rep_en.enriched_records]
            st.dataframe(pd.DataFrame(records_data), width="stretch")
