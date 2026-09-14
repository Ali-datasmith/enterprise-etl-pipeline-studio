# Testing Strategy & Guidelines

## Overview
Enterprise ETL Pipeline Studio maintains a deterministic, network-free test suite. All tests must pass locally and in GitHub Actions CI.

## Key Principles
1. **No External Network Calls**: Network APIs (Google Gemini, HTTP URLs) are strictly mocked using `unittest.mock` or `monkeypatch`.
2. **No Real Credentials Required**: Tests operate with synthetic data and mocked responses.
3. **Deterministic Execution**: Tests use stable row IDs and fixed random seeds.

## Running Tests
```bash
make test
# Or directly with pytest:
pytest --cov=etl --cov=ai --cov=ui
```
