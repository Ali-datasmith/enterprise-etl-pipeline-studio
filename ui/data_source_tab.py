"""Data Source ingestion UI tab."""

import streamlit as st

from ui.components import render_empty_state
from ui.controllers import handle_file_upload, handle_sample_load, handle_url_fetch


def render_data_source_tab() -> None:
    st.subheader("Data Intake & Ingestion")

    is_busy = st.session_state.pipeline_running or st.session_state.ai_active

    col1, col2 = st.columns([1, 1])

    with col1:
        st.markdown("##### 1. Upload Local Data File")
        uploaded_file = st.file_uploader(
            "Upload CSV, JSON, or Parquet dataset",
            type=["csv", "json", "parquet"],
            disabled=is_busy,
        )
        if uploaded_file is not None:
            if st.button("Process Uploaded File", disabled=is_busy):
                handle_file_upload(uploaded_file)

        st.markdown("---")
        st.markdown("##### 3. Explicit URL Retrieval")
        url_input = st.text_input("Enter HTTPS CSV/JSON URL", disabled=is_busy)
        if st.button("Fetch Remote Dataset", disabled=is_busy):
            handle_url_fetch(url_input)

    with col2:
        st.markdown("##### 2. Load Synthetic Built-in Samples")
        st.caption("Select a pre-built synthetic dataset to test ETL pipelines immediately:")

        c1, c2, c3 = st.columns(3)
        with c1:
            if st.button("Customers (Geospatial)", disabled=is_busy):
                handle_sample_load("customers")
        with c2:
            if st.button("Dirty Transactions", disabled=is_busy):
                handle_sample_load("dirty_txns")
        with c3:
            if st.button("Products (Parquet)", disabled=is_busy):
                handle_sample_load("products")

    st.markdown("---")

    raw_df = st.session_state.raw_dataset
    meta = st.session_state.data_source_meta

    if raw_df is not None and meta is not None:
        st.markdown("#### Ingested Raw Dataset Preview")

        m1, m2, m3, m4 = st.columns(4)
        m1.metric("Rows", f"{meta.row_count:,}")
        m2.metric("Columns", meta.column_count)
        m3.metric("Format", meta.file_format.upper())
        m4.metric("Size", f"{round((meta.size_bytes or 0) / 1024, 1)} KB")

        st.dataframe(raw_df.head(100).to_pandas(), use_container_width=True)
    else:
        render_empty_state(
            "No Dataset Loaded",
            "Upload a file or select a synthetic sample dataset above to begin profiling and pipeline execution.",
        )
