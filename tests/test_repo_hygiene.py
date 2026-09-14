"""Tests for repository hygiene, required files, workflows, and secret safety."""

import re
from pathlib import Path


def test_required_files_exist() -> None:
    required_files = [
        "app.py",
        "requirements.txt",
        "requirements-dev.txt",
        "pyproject.toml",
        "pytest.ini",
        "Makefile",
        "README.md",
        "LICENSE",
        "CHANGELOG.md",
        "CONTRIBUTING.md",
        "CODE_OF_CONDUCT.md",
        "SECURITY.md",
        ".gitignore",
        ".gitattributes",
        ".editorconfig",
        ".streamlit/config.toml",
        ".github/CODEOWNERS",
        ".github/dependabot.yml",
        ".github/PULL_REQUEST_TEMPLATE.md",
        ".github/workflows/ci.yml",
        ".github/workflows/codeql.yml",
        ".github/workflows/dependency-review.yml",
        "docs/ARCHITECTURE.md",
        "docs/DEPLOYMENT.md",
        "docs/TESTING.md",
        "docs/DATA_GOVERNANCE.md",
        "docs/GITHUB_SETUP.md",
        "docs/adr/0001-single-call-structured-ai.md",
        "docs/adr/0002-state-driven-ui.md",
        "docs/adr/0003-data-quality-gates.md",
        "docs/adr/0004-streamlit-community-cloud-constraints.md",
    ]

    for rel_path in required_files:
        p = Path(rel_path)
        assert p.exists(), f"Required repository file '{rel_path}' is missing."


def test_no_hardcoded_secrets_in_py_files() -> None:
    secret_pattern = re.compile(
        r"""(AIzaSy[A-Za-z0-9_-]{33})|(sk-[a-zA-Z0-9]{32,})""", re.MULTILINE
    )

    py_files = list(Path(".").rglob("*.py"))
    assert len(py_files) > 0

    for py_file in py_files:
        if ".venv" in str(py_file) or ".pytest_cache" in str(py_file):
            continue
        content = py_file.read_text(encoding="utf-8")
        matches = secret_pattern.findall(content)
        assert not matches, f"Potential hardcoded secret found in '{py_file}'"
