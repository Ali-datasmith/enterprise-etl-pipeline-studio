"""Lineage tracking module for pipeline stage transitions."""

import uuid
from typing import Any

from etl.models import LineageRecord, current_utc_iso


class LineageTracker:
    def __init__(self, run_id: str) -> None:
        self.run_id = run_id
        self.records: list[LineageRecord] = []

    def record_stage(
        self,
        stage: str,
        input_artifact: str,
        output_artifact: str,
        operation: str,
        row_count_in: int | None = None,
        row_count_out: int | None = None,
        status: str = "success",
        duration_seconds: float | None = None,
        details: dict[str, Any] | None = None,
    ) -> LineageRecord:
        lineage_id = f"lin_{uuid.uuid4().hex[:8]}"
        rec = LineageRecord(
            lineage_id=lineage_id,
            run_id=self.run_id,
            stage=stage,
            input_artifact=input_artifact,
            output_artifact=output_artifact,
            operation=operation,
            row_count_in=row_count_in,
            row_count_out=row_count_out,
            status=status,  # type: ignore
            started_at=current_utc_iso(),
            finished_at=current_utc_iso(),
            duration_seconds=duration_seconds,
            details=details,
        )
        self.records.append(rec)
        return rec

    def get_records(self) -> list[LineageRecord]:
        return self.records
