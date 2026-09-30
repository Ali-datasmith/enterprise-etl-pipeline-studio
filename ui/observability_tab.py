"""Observability & Telemetry UI tab."""

import streamlit as st

from etl.observability import (
    create_geospatial_map,
    create_quality_score_gauge,
    create_sankey_lineage_chart,
    create_stage_duration_chart,
)
from ui.components import render_empty_state


def render_observability_tab() -> None:
    st.subheader("Pipeline Observability & Lineage Governance")

    raw_df = st.session_state.raw_dataset
    if raw_df is None:
        render_empty_state(
            "No Telemetry Available",
            "Run a dataset through quality gates to view observability dashboards and lineage graphs.",
        )
        return

    run_meta = st.session_state.run_meta
    q_report = st.session_state.quality_report
    lineage_records = st.session_state.lineage_records

    c1, c2 = st.columns([1, 1])
    with c1:
        st.plotly_chart(create_quality_score_gauge(q_report), width="stretch")
    with c2:
        st.plotly_chart(create_stage_duration_chart(run_meta), width="stretch")

    st.markdown("---")
    st.markdown("##### Lineage Sankey Diagram")
    st.plotly_chart(create_sankey_lineage_chart(lineage_records), width="stretch")

    profile = st.session_state.profile_report
    if profile and profile.get("has_geospatial"):
        st.markdown("---")
        st.markdown("##### Geospatial Record Distribution Map")
        deck_map = create_geospatial_map(raw_df.head(500).to_dicts())
        st.pydeck_chart(deck_map)
