# ADR 0001: Single-Call Structured AI Execution

## Status
Accepted

## Context
AI integrations in data tools often suffer from nondeterminism, latency, prompt-chaining failures, and unparsable output formats.

## Decision
All AI operations (Contract Advisor and Record Enrichment) issue exactly ONE structured inference call to Google Gemini using `response_mime_type="application/json"` and Pydantic response schemas. Multi-turn chat, prompt chaining, and retrieval grounding are prohibited.

## Consequences
- Highly predictable latency and zero risk of broken intermediate chain state.
- Guaranteed Pydantic schema validation.
- Reduced API quota usage.
