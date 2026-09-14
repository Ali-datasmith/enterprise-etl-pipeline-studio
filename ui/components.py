"""Reusable UI components for header, banners, metrics, and empty states."""

import streamlit as st

from ai.config import resolve_ai_config


def render_header() -> None:
    col1, col2 = st.columns([3, 1])

    with col1:
        st.markdown(
            "<h1 class='main-title-canary'>Enterprise ETL Pipeline Studio</h1>",
            unsafe_allow_html=True,
        )
        st.caption(
            "Governed, observable, schema-first ETL and AI data pipeline studio for Streamlit Community Cloud."
        )

    with col2:
        ai_cfg = resolve_ai_config()
        if ai_cfg.is_available:
            st.success("🟢 AI Engine Active", icon="🤖")
        else:
            st.warning("🟠 AI Engine Disabled (Key Missing)", icon="🔒")


def render_ai_availability_banner() -> None:
    ai_cfg = resolve_ai_config()
    if not ai_cfg.is_available:
        st.info(
            "**AI Assistance Unavailable:** `GOOGLE_API_KEY` was not found in Streamlit secrets or environment variables. "
            "All core ETL features (ingestion, profiling, quality gates, transformations, lineage, export) remain fully operational.",
            icon="ℹ️",
        )


def render_empty_state(title: str, message: str) -> None:
    st.markdown(
        f"""
        <div style="text-align: center; padding: 2.5rem; border: 1px dashed rgba(255,255,255,0.15); border-radius: 12px; background: rgba(255,255,255,0.02);">
            <h3 style="color: #A0A7B8; margin-bottom: 0.5rem;">{title}</h3>
            <p style="color: #6C727F; font-size: 0.95rem;">{message}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_error_banner(error_category: str | None, error_message: str | None) -> None:
    if error_category and error_message:
        st.error(
            f"**[{error_category}]**\n\n{error_message}",
            icon="🚨",
        )
