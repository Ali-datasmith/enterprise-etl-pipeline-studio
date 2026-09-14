"""AI configuration resolution for Streamlit secrets and environment variables."""

import os
from typing import NamedTuple


class AIConfig(NamedTuple):
    api_key: str | None
    model_name: str
    is_available: bool


def resolve_ai_config() -> AIConfig:
    api_key = None
    model_name = "gemini-2.5-flash"

    try:
        import streamlit as st

        if hasattr(st, "secrets") and st.secrets is not None:
            if "GOOGLE_API_KEY" in st.secrets:
                api_key = str(st.secrets["GOOGLE_API_KEY"])
            if "GEMINI_MODEL" in st.secrets:
                model_name = str(st.secrets["GEMINI_MODEL"])
    except Exception as err:
        import logging

        logging.debug(f"Streamlit secrets resolution skipped: {err}")

    if not api_key:
        api_key = os.environ.get("GOOGLE_API_KEY")
    if os.environ.get("GEMINI_MODEL"):
        model_name = os.environ["GEMINI_MODEL"]

    is_available = bool(api_key and len(api_key.strip()) > 0)
    return AIConfig(
        api_key=api_key if is_available else None,
        model_name=model_name,
        is_available=is_available,
    )
