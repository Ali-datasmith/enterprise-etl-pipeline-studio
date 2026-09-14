"""Data contract inference and contract editing module."""

from typing import Any

from etl.models import ColumnContract


def infer_contract_from_profile(profile: dict[str, Any]) -> list[ColumnContract]:
    contracts: list[ColumnContract] = []

    for col in profile.get("columns", []):
        col_name = col["name"]
        logical_type = col["logical_type"]
        null_count = col["null_count"]
        unique_pct = col.get("unique_percentage", 0.0)
        is_sensitive = col.get("is_sensitive", False)
        min_val = col.get("min_val")
        max_val = col.get("max_val")

        is_nullable = null_count > 0
        is_unique = unique_pct == 100.0
        is_pk = col_name.lower() in ("id", "user_id", "customer_id", "transaction_id") or (
            is_unique and not is_nullable
        )

        contract = ColumnContract(
            name=col_name,
            logical_type=logical_type,
            nullable=is_nullable,
            unique=is_unique,
            primary_key=is_pk,
            sensitive=is_sensitive,
            min_value=min_val,
            max_value=max_val,
            description=f"Inferred contract for column '{col_name}'.",
        )
        contracts.append(contract)

    return contracts


def update_contract(
    contracts: list[ColumnContract],
    col_name: str,
    **updates: Any,
) -> list[ColumnContract]:
    updated_contracts: list[ColumnContract] = []
    for c in contracts:
        if c.name == col_name:
            data = c.model_dump()
            data.update(updates)
            updated_contracts.append(ColumnContract(**data))
        else:
            updated_contracts.append(c)
    return updated_contracts
