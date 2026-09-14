"""Custom CSS theme injection for premium dark minimalist enterprise UI."""

import streamlit as st


def inject_theme_css() -> None:
    custom_css = """
    <style>
    .stApp {
        background-color: #0B0F19;
        color: #FFFFFF;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }

    .main-title-canary {
        text-shadow: 0 0 12px rgba(0, 229, 255, 0.4);
        color: #FFFFFF;
        font-weight: 700;
        letter-spacing: -0.02em;
    }

    div[data-testid="stMetricValue"], div[data-testid="metric-container"], .glass-card {
        background: rgba(255, 255, 255, 0.03);
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 12px;
        backdrop-filter: blur(12px);
        padding: 1rem;
    }

    .stButton > button {
        background: rgba(0, 229, 255, 0.1);
        color: #00E5FF;
        border: 1px solid rgba(0, 229, 255, 0.3);
        border-radius: 8px;
        font-weight: 600;
        transition: all 0.2s ease;
    }
    .stButton > button:hover {
        background: rgba(0, 229, 255, 0.2);
        border-color: #00E5FF;
        color: #FFFFFF;
        box-shadow: 0 0 10px rgba(0, 229, 255, 0.3);
    }

    button[data-baseweb="tab"] {
        background-color: transparent !important;
        color: #A0A7B8 !important;
        border-bottom: 2px solid transparent !important;
        font-weight: 500;
    }
    button[data-baseweb="tab"][aria-selected="true"] {
        color: #00E5FF !important;
        border-bottom: 2px solid #00E5FF !important;
        font-weight: 600;
    }

    div[data-testid="stDataFrame"] {
        border: 1px solid rgba(255, 255, 255, 0.08);
        border-radius: 8px;
        overflow: hidden;
    }

    .stAlert {
        border-radius: 8px;
        background-color: rgba(18, 22, 32, 0.8);
        border: 1px solid rgba(255, 255, 255, 0.08);
    }

    footer {visibility: hidden;}
    </style>
    """
    st.markdown(custom_css, unsafe_allow_html=True)
