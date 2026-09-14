"""Data quality validation module using Pandera and deterministic checks."""

import re

import pandas as pd
import polars as pl
from loguru import logger

from etl.models import ColumnContract, QualityCheckResult, QualityReport


def run_quality_gates(
    df: pl.DataFrame,
    contracts: list[ColumnContract],
    policy: str = "block_on_failure",
    run_id: str = "run_0",
) -> tuple[QualityReport, pl.DataFrame]:
    results: list[QualityCheckResult] = []
    quarantine_mask: list[bool] = [False] * df.height

    total_rows = df.height
    total_checks = 0
    passed_count = 0
    warning_count = 0
    failed_count = 0

    total_checks += 1
    if total_rows > 0:
        passed_count += 1
        results.append(
            QualityCheckResult(
                check_id="check_row_count",
                check_name="Row Count Non-Empty",
                severity="critical",
                status="passed",
                passed_count=total_rows,
                failed_count=0,
                message=f"Dataset contains {total_rows} rows.",
            )
        )
    else:
        failed_count += 1
        results.append(
            QualityCheckResult(
                check_id="check_row_count",
                check_name="Row Count Non-Empty",
                severity="critical",
                status="failed",
                passed_count=0,
                failed_count=0,
                message="Dataset is empty.",
            )
        )

    pdf = df.to_pandas()

    for contract in contracts:
        col = contract.name
        if col not in pdf.columns:
            total_checks += 1
            failed_count += 1
            results.append(
                QualityCheckResult(
                    check_id=f"check_col_exists_{col}",
                    check_name=f"Column Presence: {col}",
                    column=col,
                    severity="critical",
                    status="failed",
                    message=f"Required column '{col}' is missing from dataset.",
                )
            )
            continue

        series = pdf[col]

        if not contract.nullable:
            total_checks += 1
            null_mask = series.isna()
            null_cnt = int(null_mask.sum())
            if null_cnt == 0:
                passed_count += 1
                results.append(
                    QualityCheckResult(
                        check_id=f"check_null_{col}",
                        check_name=f"Not Null: {col}",
                        column=col,
                        severity="critical",
                        status="passed",
                        passed_count=total_rows,
                        failed_count=0,
                        message=f"Column '{col}' has no null values.",
                    )
                )
            else:
                failed_count += 1
                failed_vals = series[null_mask].head(10).tolist()
                results.append(
                    QualityCheckResult(
                        check_id=f"check_null_{col}",
                        check_name=f"Not Null: {col}",
                        column=col,
                        severity="critical",
                        status="failed",
                        passed_count=total_rows - null_cnt,
                        failed_count=null_cnt,
                        message=f"Column '{col}' failed not-null check with {null_cnt} nulls.",
                        failed_samples=failed_vals,
                    )
                )
                for idx in series[null_mask].index:
                    quarantine_mask[idx] = True

        if contract.unique or contract.primary_key:
            total_checks += 1
            dup_mask = series.duplicated(keep=False) & series.notna()
            dup_cnt = int(dup_mask.sum())
            if dup_cnt == 0:
                passed_count += 1
                results.append(
                    QualityCheckResult(
                        check_id=f"check_unique_{col}",
                        check_name=f"Unique Values: {col}",
                        column=col,
                        severity="critical" if contract.primary_key else "warning",
                        status="passed",
                        passed_count=total_rows,
                        failed_count=0,
                        message=f"Column '{col}' has unique values.",
                    )
                )
            else:
                if contract.primary_key:
                    failed_count += 1
                    status = "failed"
                else:
                    warning_count += 1
                    status = "warning"

                failed_vals = series[dup_mask].head(10).tolist()
                results.append(
                    QualityCheckResult(
                        check_id=f"check_unique_{col}",
                        check_name=f"Unique Values: {col}",
                        column=col,
                        severity="critical" if contract.primary_key else "warning",
                        status=status,
                        passed_count=total_rows - dup_cnt,
                        failed_count=dup_cnt,
                        message=f"Column '{col}' has {dup_cnt} duplicate values.",
                        failed_samples=failed_vals,
                    )
                )
                if contract.primary_key:
                    for idx in series[dup_mask].index:
                        quarantine_mask[idx] = True

        if contract.min_value is not None or contract.max_value is not None:
            total_checks += 1
            num_series = pd.to_numeric(series, errors="coerce")
            range_fail = pd.Series([False] * len(series))
            if contract.min_value is not None:
                range_fail |= num_series < contract.min_value
            if contract.max_value is not None:
                range_fail |= num_series > contract.max_value

            range_fail_cnt = int(range_fail.sum())
            if range_fail_cnt == 0:
                passed_count += 1
                results.append(
                    QualityCheckResult(
                        check_id=f"check_range_{col}",
                        check_name=f"Range Check: {col}",
                        column=col,
                        severity="warning",
                        status="passed",
                        passed_count=total_rows,
                        failed_count=0,
                        message=f"Column '{col}' values are within range bounds.",
                    )
                )
            else:
                warning_count += 1
                results.append(
                    QualityCheckResult(
                        check_id=f"check_range_{col}",
                        check_name=f"Range Check: {col}",
                        column=col,
                        severity="warning",
                        status="warning",
                        passed_count=total_rows - range_fail_cnt,
                        failed_count=range_fail_cnt,
                        message=f"Column '{col}' has {range_fail_cnt} values out of range.",
                        failed_samples=series[range_fail].head(10).tolist(),
                    )
                )

        if contract.allowed_values:
            total_checks += 1
            invalid_mask = ~series.isin(contract.allowed_values) & series.notna()
            invalid_cnt = int(invalid_mask.sum())
            if invalid_cnt == 0:
                passed_count += 1
                results.append(
                    QualityCheckResult(
                        check_id=f"check_allowed_{col}",
                        check_name=f"Allowed Values: {col}",
                        column=col,
                        severity="warning",
                        status="passed",
                        passed_count=total_rows,
                        failed_count=0,
                        message=f"Column '{col}' values match allowed set.",
                    )
                )
            else:
                warning_count += 1
                results.append(
                    QualityCheckResult(
                        check_id=f"check_allowed_{col}",
                        check_name=f"Allowed Values: {col}",
                        column=col,
                        severity="warning",
                        status="warning",
                        passed_count=total_rows - invalid_cnt,
                        failed_count=invalid_cnt,
                        message=f"Column '{col}' has {invalid_cnt} values not in allowed set.",
                        failed_samples=series[invalid_mask].head(10).tolist(),
                    )
                )

        if contract.regex_pattern:
            total_checks += 1
            compiled_pat = re.compile(contract.regex_pattern)
            str_series = series.astype(str)
            regex_fail = (
                ~str_series.apply(lambda x, p=compiled_pat: bool(p.match(x))) & series.notna()
            )
            regex_cnt = int(regex_fail.sum())
            if regex_cnt == 0:
                passed_count += 1
                results.append(
                    QualityCheckResult(
                        check_id=f"check_regex_{col}",
                        check_name=f"Regex Pattern: {col}",
                        column=col,
                        severity="warning",
                        status="passed",
                        passed_count=total_rows,
                        failed_count=0,
                        message=f"Column '{col}' values match regex pattern.",
                    )
                )
            else:
                warning_count += 1
                results.append(
                    QualityCheckResult(
                        check_id=f"check_regex_{col}",
                        check_name=f"Regex Pattern: {col}",
                        column=col,
                        severity="warning",
                        status="warning",
                        passed_count=total_rows - regex_cnt,
                        failed_count=regex_cnt,
                        message=f"Column '{col}' has {regex_cnt} values failing regex match.",
                        failed_samples=series[regex_fail].head(10).tolist(),
                    )
                )

    penalty = (failed_count * 25.0) + (warning_count * 10.0)
    score = max(0.0, min(100.0, 100.0 - penalty))

    if failed_count > 0:
        decision = "blocked" if policy == "block_on_failure" else "passed_with_warnings"
    elif warning_count > 0:
        decision = "manual_review" if policy == "manual_review" else "passed_with_warnings"
    else:
        decision = "passed"

    report = QualityReport(
        run_id=run_id,
        total_checks=total_checks,
        passed_count=passed_count,
        warning_count=warning_count,
        failed_count=failed_count,
        skipped_count=0,
        quality_score=round(score, 1),
        gate_decision=decision,  # type: ignore
        results=results,
    )

    quarantine_df = pl.from_pandas(pdf[quarantine_mask]) if any(quarantine_mask) else pl.DataFrame()

    logger.info(f"Quality run complete. Score: {score}, Decision: {decision}.")
    return report, quarantine_df
