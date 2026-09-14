"""Pytest fixtures for Enterprise ETL Pipeline Studio tests."""

import polars as pl
import pytest

from etl.models import ColumnContract, PipelineConfig


@pytest.fixture
def sample_customers_df() -> pl.DataFrame:
    return pl.DataFrame(
        {
            "_row_id": ["row_0", "row_1", "row_2"],
            "customer_id": ["C101", "C102", "C103"],
            "full_name": ["Alice Smith", "Bob Jones", "Charlie Brown"],
            "email": ["alice@example.com", "bob@example.com", "charlie@example.com"],
            "account_balance": [100.0, 250.5, 50.0],
            "latitude": [37.7749, 45.4215, 51.5074],
            "longitude": [-122.4194, -75.6972, -0.1278],
        }
    )


@pytest.fixture
def sample_contracts() -> list[ColumnContract]:
    return [
        ColumnContract(
            name="customer_id",
            logical_type="identifier",
            nullable=False,
            unique=True,
            primary_key=True,
        ),
        ColumnContract(name="full_name", logical_type="string", nullable=False),
        ColumnContract(name="email", logical_type="string", sensitive=True),
        ColumnContract(name="account_balance", logical_type="float", min_value=0.0),
    ]


@pytest.fixture
def default_pipeline_config() -> PipelineConfig:
    return PipelineConfig(pipeline_name="test_pipeline")
