"""Data Contract Definition UI tab."""

from typing import Any, cast

import pandas as pd
import streamlit as st

from etl.contracts import ColumnContract
from ui.components import render_empty_state


def render_contract_tab() -> None:
    st.subheader("Data Contract Schema Definition")

    contracts: list[ColumnContract] = st.session_state.contract_data

    if not contracts:
        render_empty_state(
            "No Contract Defined",
            "Please load a dataset in the Data Source tab to infer an initial schema contract.",
        )
        return

    st.markdown(
        "Review and edit inferred logical column contracts, nullability, uniqueness, and sensitivity flags."
    )

    contract_dicts = [c.model_dump() for c in contracts]
    df_contracts = pd.DataFrame(contract_dicts)

    edited_df = st.data_editor(
        df_contracts[
            [
                "name",
                "logical_type",
                "nullable",
                "unique",
                "primary_key",
                "sensitive",
                "description",
            ]
        ],
        column_config={
            "name": st.column_config.TextColumn("Column Name", disabled=True),
            "logical_type": st.column_config.SelectboxColumn(
                "Logical Type",
                options=[
                    "string",
                    "integer",
                    "float",
                    "boolean",
                    "date",
                    "datetime",
                    "category",
                    "identifier",
                    "text",
                ],
            ),
            "nullable": st.column_config.CheckboxColumn("Nullable?"),
            "unique": st.column_config.CheckboxColumn("Unique?"),
            "primary_key": st.column_config.CheckboxColumn("Primary Key?"),
            "sensitive": st.column_config.CheckboxColumn("Sensitive (Redact)?"),
            "description": st.column_config.TextColumn("Description"),
        },
        width="stretch",
        key="contract_editor",
    )

    if st.button("Save Contract Changes"):
        updated_contracts = []
        rows = cast(list[dict[str, Any]], edited_df.to_dict(orient="records"))
        for row in rows:
            updated_contracts.append(ColumnContract(**row))
        st.session_state.contract_data = updated_contracts
        st.success("Data contract updated successfully!")
