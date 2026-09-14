# ADR 0004: Streamlit Community Cloud Constraints

## Status
Accepted

## Context
Streamlit Community Cloud has ephemeral filesystems, resource limits, and memory limits.

## Decision
Design the app to run strictly in memory within session state. Avoid permanent server-side storage, local background workers, or external database requirements.

## Consequences
- App deploys effortlessly on Streamlit Community Cloud.
- Zero server-side state persistence across sessions.
