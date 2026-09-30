"""Data ingestion module for Enterprise ETL Pipeline Studio."""

import hashlib
import io
import ipaddress
from urllib.parse import urlparse

import httpx
import pandas as pd
import polars as pl
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential

from etl.models import DataSourceMetadata


class IngestionError(Exception):
    pass


class SSRFValidationError(IngestionError):
    pass


def compute_checksum(content: bytes) -> str:
    return hashlib.sha256(content).hexdigest()


# Well-known public hosts that require the "www." subdomain to resolve.
_WWW_REQUIRED_HOSTS = frozenset({"github.com", "gist.github.com"})


def normalize_url(url: str) -> str:
    """Return a normalized, fetchable form of ``url`` without changing intent.

    Light-touch fixes only: trim surrounding whitespace and add the missing
    "www." subdomain for hosts that are known not to resolve without it
    (e.g. "raw.githubusercontent.com" style typos or bare "github.com").
    """
    normalized = url.strip()

    parsed = urlparse(normalized)
    hostname = parsed.hostname or ""

    needs_www = hostname in _WWW_REQUIRED_HOSTS or (
        hostname.startswith("raw-") and ".githubusercontent.com" in hostname
    )
    if needs_www and not hostname.startswith("www."):
        replaced_host = f"www.{hostname}"
        # Preserve any userinfo (@) and port while swapping only the host part.
        netloc = parsed.netloc.replace(hostname, replaced_host, 1)
        normalized = parsed._replace(netloc=netloc).geturl()

    return normalized


def validate_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.scheme not in ("http", "https"):
        raise SSRFValidationError(
            f"Invalid URL scheme: '{parsed.scheme}'. Only HTTP/HTTPS allowed."
        )

    hostname = parsed.hostname
    if not hostname:
        raise SSRFValidationError("URL host cannot be empty.")

    if hostname in ("localhost", "127.0.0.1", "::1", "0.0.0.0"):
        raise SSRFValidationError("Requests to localhost/loopback addresses are prohibited.")

    try:
        ip = ipaddress.ip_address(hostname)
        if ip.is_private or ip.is_loopback or ip.is_link_local:
            raise SSRFValidationError(f"Access to private IP space '{hostname}' is prohibited.")
    except ValueError as err:
        if "metadata.google.internal" in hostname or "169.254.169.254" in hostname:
            raise SSRFValidationError("Access to cloud metadata endpoints is prohibited.") from err

    return url


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=4),
    reraise=True,
)
def fetch_url_content(url: str) -> bytes:
    normalized_url = normalize_url(url)
    validated_url = validate_url(normalized_url)
    try:
        with httpx.Client(timeout=10.0, follow_redirects=False) as client:
            response = client.get(validated_url)
            response.raise_for_status()
            return response.content
    except httpx.ConnectError as err:
        logger.error(f"Could not resolve/connect to host for URL {validated_url}: {err}")
        raise IngestionError(
            f"Unable to reach host for '{validated_url}'. "
            "Please verify the URL is correct and publicly accessible."
        ) from err
    except httpx.HTTPError as err:
        logger.error(f"Network error fetching URL {validated_url}: {err}")
        raise IngestionError(f"Data source network error: {err}") from err


def detect_format(file_name: str, content: bytes | None = None) -> str:
    lower_name = file_name.lower()
    if lower_name.endswith(".csv") or lower_name.endswith(".txt"):
        return "csv"
    if lower_name.endswith(".json"):
        return "json"
    if lower_name.endswith(".parquet") or lower_name.endswith(".pq"):
        return "parquet"

    if content:
        stripped = content.strip()
        if stripped.startswith(b"{") or stripped.startswith(b"["):
            return "json"
        if stripped.startswith(b"PAR1"):
            return "parquet"
        if b"," in stripped[:500] or b"\t" in stripped[:500]:
            return "csv"

    return "unknown"


def parse_bytes_to_polars(content: bytes, file_format: str) -> pl.DataFrame:
    buf = io.BytesIO(content)
    try:
        if file_format == "csv":
            return pl.read_csv(buf)
        if file_format == "json":
            try:
                return pl.read_json(buf)
            except Exception:
                buf.seek(0)
                pdf = pd.read_json(buf)
                return pl.from_pandas(pdf)
        if file_format == "parquet":
            return pl.read_parquet(buf)
        raise IngestionError(f"Unsupported file format for parsing: {file_format}")
    except Exception as e:
        if isinstance(e, IngestionError):
            raise
        logger.error(f"Failed to parse {file_format} file: {e}")
        raise IngestionError(
            f"File Parsing Error: Failed to parse {file_format} dataset. {e}"
        ) from e


def add_stable_row_id(df: pl.DataFrame) -> pl.DataFrame:
    if "_row_id" in df.columns:
        return df
    row_ids = [f"row_{i}" for i in range(df.height)]
    return df.with_columns(pl.Series("_row_id", row_ids))


def ingest_data_source(
    content: bytes,
    file_name: str,
    source_type: str = "file_upload",
    notes: str | None = None,
    fetch_method: str | None = None,
) -> tuple[pl.DataFrame, DataSourceMetadata]:
    checksum = compute_checksum(content)
    file_fmt = detect_format(file_name, content)
    raw_df = parse_bytes_to_polars(content, file_fmt)
    df_with_id = add_stable_row_id(raw_df)

    meta = DataSourceMetadata(
        source_name=file_name,
        source_type=source_type,  # type: ignore
        file_name=file_name,
        file_format=file_fmt,  # type: ignore
        row_count=df_with_id.height,
        column_count=df_with_id.width,
        size_bytes=len(content),
        checksum=checksum,
        fetch_method=fetch_method,
        notes=notes,
    )

    return df_with_id, meta
