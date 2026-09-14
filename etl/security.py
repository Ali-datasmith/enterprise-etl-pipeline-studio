"""Security utilities, column sensitivity detection, and redaction logic."""

import re
from pathlib import Path

SENSITIVE_FIELD_PATTERNS = [
    r"ssn",
    r"social_security",
    r"password",
    r"secret",
    r"credit_card",
    r"card_num",
    r"cvv",
    r"phone",
    r"email",
    r"address",
    r"dob",
    r"birth_date",
    r"salary",
    r"tax_id",
]


def detect_sensitive_column(column_name: str) -> bool:
    col_lower = column_name.lower().strip()
    return any(re.search(pattern, col_lower) for pattern in SENSITIVE_FIELD_PATTERNS)


def sanitize_filename(filename: str) -> str:
    name_only = Path(filename).name
    clean = re.sub(r"[^\w\.-]", "_", name_only)
    clean = re.sub(r"\.\.+", ".", clean)
    return clean.strip("._") or "export_file"
