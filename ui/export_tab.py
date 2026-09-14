"""Export Artifacts UI tab."""

import streamlit as st

from etl.export import export_dataframe, export_json_artifact
from ui.components import render_empty_state


def render_export_tab() -> None:
    st.subheader("Curated Dataset & Artifact Export")

    curated_df = st.session_state.curated_dataset
    q_report = st.session_state.quality_report
    lineage_records = st.session_state.lineage_records
    contracts = st.session_state.contract_data

    if curated_df is None:
        render_empty_state(
            "No Curated Dataset Ready",
            "Please execute the pipeline in Quality Gates tab to publish a curated dataset for export.",
        )
        return

    st.markdown("##### Download Published Curated Dataset")
    fmt = st.selectbox("Export Dataset Format", options=["csv", "json", "parquet"])

    content_bytes, file_name, mime_type = export_dataframe(
        curated_df, export_format=fmt, base_name="curated_dataset"
    )

    st.download_button(
        label=f"Download Curated Dataset ({fmt.upper()})",
        data=content_bytes,
        file_name=file_name,
        mime=mime_type,
        key="btn_dl_dataset",
    )

    st.markdown("---")
    st.markdown("##### Download Governance & Pipeline Artifacts")

    c1, c2, c3 = st.columns(3)

    with c1:
        if q_report:
            q_bytes, q_name, q_mime = export_json_artifact(q_report, "quality_report")
            st.download_button(
                "Download Quality Report (JSON)",
                data=q_bytes,
                file_name=q_name,
                mime=q_mime,
                key="btn_dl_quality",
            )

    with c2:
        if lineage_records:
            l_bytes, l_name, l_mime = export_json_artifact(lineage_records, "lineage_report")
            st.download_button(
                "Download Lineage Report (JSON)",
                data=l_bytes,
                file_name=l_name,
                mime=l_mime,
                key="btn_dl_lineage",
            )

    with c3:
        if contracts:
            c_bytes, c_name, c_mime = export_json_artifact(contracts, "data_contract")
            st.download_button(
                "Download Schema Contract (JSON)",
                data=c_bytes,
                file_name=c_name,
                mime=c_mime,
                key="btn_dl_contract",
            )
