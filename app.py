"""Main application entrypoint for Enterprise ETL Pipeline Studio."""

import streamlit as st

from ui.ai_tab import render_ai_tab
from ui.components import render_error_banner, render_header
from ui.contract_tab import render_contract_tab
from ui.data_source_tab import render_data_source_tab
from ui.export_tab import render_export_tab
from ui.observability_tab import render_observability_tab
from ui.quality_tab import render_quality_tab
from ui.state import init_session_state
from ui.theme import inject_theme_css
from ui.transform_tab import render_transform_tab

st.set_page_config(
    page_title="Enterprise ETL Pipeline Studio",
    page_icon="⚡",
    layout="wide",
    initial_sidebar_state="expanded",
)


def main() -> None:
    init_session_state()
    inject_theme_css()
    render_header()

    pipeline_err = st.session_state.pipeline_error_message
    if pipeline_err:
        render_error_banner("Pipeline Processing Error", pipeline_err)

    ai_err = st.session_state.ai_error_message
    if ai_err:
        render_error_banner("AI Processing Error", ai_err)

    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs(
        [
            "📁 Data Source",
            "📜 Data Contract",
            "🛡️ Quality Gates",
            "⚙️ Transformations",
            "🤖 AI Assistance",
            "📊 Observability",
            "📥 Export",
        ]
    )

    with tab1:
        render_data_source_tab()
    with tab2:
        render_contract_tab()
    with tab3:
        render_quality_tab()
    with tab4:
        render_transform_tab()
    with tab5:
        render_ai_tab()
    with tab6:
        render_observability_tab()
    with tab7:
        render_export_tab()


if __name__ == "__main__":
    main()
