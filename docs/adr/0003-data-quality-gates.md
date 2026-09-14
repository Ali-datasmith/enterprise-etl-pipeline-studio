# ADR 0003: Data Quality Gates

## Status
Accepted

## Context
Data quality failures must be detected before data is published or transformed further.

## Decision
Implement explicit schema contracts and deterministic quality gates. Gate decisions (`passed`, `passed_with_warnings`, `blocked`) govern publishing readiness.

## Consequences
- Prevents dirty or malformed records from reaching downstream curated outputs.
- Quarantines invalid records for review and audit.
