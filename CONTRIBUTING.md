# Contributing Guide

## Development Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/Ali-datasmith/enterprise-etl-pipeline-studio.git
   cd enterprise-etl-pipeline-studio
   ```

2. Create virtual environment & install dev dependencies:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   make install
   ```

3. Run local quality suite:
   ```bash
   make ci
   ```

## Pull Request Process
- Use Conventional Commits (`feat:`, `fix:`, `docs:`, `ci:`).
- Ensure all tests pass (`make test`).
- Ensure code passes formatting (`make format`), linting (`make lint`), and type checking (`make typecheck`).
