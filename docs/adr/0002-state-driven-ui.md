# ADR 0002: State-Driven UI Rendering

## Status
Accepted

## Context
Streamlit reruns the entire python script on every widget interaction. Rendering UI directly from API calls causes duplicate network requests and inconsistent state.

## Decision
All UI views, charts, and metrics render exclusively from persisted `st.session_state` keys initialized before conditional logic.

## Consequences
- Clean separation of UI rendering and data controller processing.
- Reruns are fast, deterministic, and idempotent.
