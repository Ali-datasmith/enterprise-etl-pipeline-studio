"""Transformations Builder UI tab."""

import uuid

import pandas as pd
import streamlit as st

from etl.models import PipelineConfig, TransformationSpec
from ui.components import render_empty_state


def render_transform_tab() -> None:
    st.subheader("Data Transformation Builder")

    raw_df = st.session_state.raw_dataset
    if raw_df is None:
        render_empty_state(
            "No Dataset Loaded",
            "Please load a dataset in the Data Source tab to configure transformations.",
        )
        return

    cfg: PipelineConfig = st.session_state.pipeline_config or PipelineConfig()

    st.markdown("##### Add New Transformation Step")

    c1, c2, c3 = st.columns(3)
    with c1:
        ttype = st.selectbox(
            "Transformation Type",
            options=[
                "rename",
                "cast",
                "trim_whitespace",
                "deduplicate",
                "fill_null",
                "drop_column",
                "filter_rows",
            ],
        )
    with c2:
        col = st.selectbox("Target Column", options=raw_df.columns)
    with c3:
        target_col = st.text_input("New Column Name (if renaming/casting)")

    params: dict = {}
    if ttype == "cast":
        params["target_type"] = st.selectbox(
            "Cast To Type", ["string", "integer", "float", "boolean", "date"]
        )
    elif ttype == "fill_null":
        params["value"] = st.text_input("Fill Value", value="N/A")
    elif ttype == "filter_rows":
        params["operator"] = st.selectbox("Operator", ["==", "!=", ">", "<", "is_not_null"])
        params["value"] = st.text_input("Filter Value")

    if st.button("Add Transformation Step"):
        new_spec = TransformationSpec(
            transform_id=f"tf_{uuid.uuid4().hex[:6]}",
            transform_type=ttype,  # type: ignore
            column=col,
            target_column=target_col or col,
            parameters=params,
        )
        cfg.transformations.append(new_spec)
        st.session_state.pipeline_config = cfg
        st.success(f"Added '{ttype}' transformation step.")

    st.markdown("---")
    st.markdown("##### Configured Transformation Pipeline")

    if cfg.transformations:
        tf_data = [t.model_dump() for t in cfg.transformations]
        st.dataframe(pd.DataFrame(tf_data), use_container_width=True)

        if st.button("Clear All Transformations"):
            cfg.transformations = []
            st.session_state.pipeline_config = cfg
            st.rerun()
    else:
        st.info("No transformations added yet.")

    st.markdown("---")
    transformed_df = st.session_state.transformed_dataset
    if transformed_df is not None:
        st.markdown("##### Transformed Dataset Preview")
        st.dataframe(transformed_df.head(50).to_pandas(), use_container_width=True)
