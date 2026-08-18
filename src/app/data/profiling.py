"""Data health scoring and profiling."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from app.data.schema import DATE_FIELDS, DISPLAY_NAMES, NUMERIC_FIELDS


@dataclass
class DataProfile:
    health_score: float
    row_count: int
    column_count: int
    duplicate_rows: int
    missing_by_field: dict[str, int] = field(default_factory=dict)
    invalid_dates: dict[str, int] = field(default_factory=dict)
    invalid_numeric: dict[str, int] = field(default_factory=dict)
    unmapped_columns: list[str] = field(default_factory=list)
    issues: list[str] = field(default_factory=list)
    normalization_notes: list[str] = field(default_factory=list)


def profile_dataset(
    data: pd.DataFrame,
    validation: dict[str, Any] | None = None,
) -> DataProfile:
    validation = validation or {}
    rows = len(data)
    score = 100.0
    issues: list[str] = []
    missing_by_field: dict[str, int] = {}
    invalid_dates: dict[str, int] = {}
    invalid_numeric: dict[str, int] = {}

    duplicate_rows = int(data.duplicated().sum())
    if duplicate_rows:
        penalty = min(25, duplicate_rows / max(rows, 1) * 100 * 0.5)
        score -= penalty
        issues.append(f"{duplicate_rows:,} duplicate rows")

    for col in data.columns:
        missing = int(data[col].isna().sum())
        if missing:
            missing_by_field[col] = missing
            if col in ("candidate_id", "interview_status", "offer_status"):
                score -= min(10, missing / max(rows, 1) * 100 * 0.3)

    for col in DATE_FIELDS:
        if col not in data.columns:
            continue
        invalid = int(
            data[col].notna().sum()
            - pd.to_datetime(data[col], errors="coerce").notna().sum()
        )
        if invalid:
            invalid_dates[col] = invalid
            score -= min(8, invalid / max(rows, 1) * 100 * 0.4)
            issues.append(f"{invalid} invalid {DISPLAY_NAMES.get(col, col)}")

    for col in NUMERIC_FIELDS:
        if col not in data.columns:
            continue
        invalid = int(
            data[col].notna().sum()
            - pd.to_numeric(data[col], errors="coerce").notna().sum()
        )
        if invalid:
            invalid_numeric[col] = invalid
            score -= min(5, invalid / max(rows, 1) * 100 * 0.3)

    unmapped = validation.get("unmapped_columns", [])
    if unmapped:
        score -= min(10, len(unmapped) * 2)
        issues.append(f"{len(unmapped)} unmapped columns")

    low_conf = validation.get("low_confidence_columns", [])
    if low_conf:
        score -= min(5, len(low_conf))

    score = max(0.0, round(score, 1))

    return DataProfile(
        health_score=score,
        row_count=rows,
        column_count=len(data.columns),
        duplicate_rows=duplicate_rows,
        missing_by_field=missing_by_field,
        invalid_dates=invalid_dates,
        invalid_numeric=invalid_numeric,
        unmapped_columns=list(unmapped),
        issues=issues,
        normalization_notes=validation.get("warnings", []),
    )
