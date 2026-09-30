"""Tests for data ingestion module."""

import pytest

from etl.ingestion import (
    SSRFValidationError,
    compute_checksum,
    detect_format,
    ingest_data_source,
    normalize_url,
    validate_url,
)
from etl.sample_data import get_sample_customers_csv, get_sample_parquet_bytes


def test_compute_checksum() -> None:
    data = b"hello world"
    checksum = compute_checksum(data)
    assert isinstance(checksum, str)
    assert len(checksum) == 64


def test_detect_format() -> None:
    assert detect_format("data.csv") == "csv"
    assert detect_format("data.json") == "json"
    assert detect_format("data.parquet") == "parquet"
    assert detect_format("unknown.bin", b'{"key": "val"}') == "json"


def test_validate_url_ssrf_protection() -> None:
    assert validate_url("https://example.com/data.csv") == "https://example.com/data.csv"

    with pytest.raises(SSRFValidationError):
        validate_url("http://localhost:8000/data.csv")

    with pytest.raises(SSRFValidationError):
        validate_url("http://127.0.0.1/data.csv")

    with pytest.raises(SSRFValidationError):
        validate_url("http://169.254.169.254/latest/meta-data/")

    with pytest.raises(SSRFValidationError):
        validate_url("file:///etc/passwd")


def test_ingest_csv_bytes() -> None:
    content = get_sample_customers_csv()
    df, meta = ingest_data_source(content, "customers.csv")
    assert df.height == 5
    assert "_row_id" in df.columns
    assert meta.file_format == "csv"
    assert meta.row_count == 5


def test_ingest_parquet_bytes() -> None:
    content = get_sample_parquet_bytes()
    df, meta = ingest_data_source(content, "products.parquet")
    assert df.height == 3
    assert meta.file_format == "parquet"
    assert meta.column_count == 5


def test_normalize_url_trims_whitespace() -> None:
    assert normalize_url("  https://example.com/data.csv  ") == "https://example.com/data.csv"


def test_normalize_url_adds_www_for_github_hosts() -> None:
    assert (
        normalize_url("https://github.com/user/repo/raw/main/data.csv")
        == "https://www.github.com/user/repo/raw/main/data.csv"
    )


def test_normalize_url_leaves_valid_public_urls_untouched() -> None:
    url = "https://raw.githubusercontent.com/user/repo/main/data.csv"
    assert normalize_url(url) == url


def test_normalize_url_preserves_port_and_path() -> None:
    assert (
        normalize_url("http://github.com:8080/a/b.csv?x=1")
        == "http://www.github.com:8080/a/b.csv?x=1"
    )
