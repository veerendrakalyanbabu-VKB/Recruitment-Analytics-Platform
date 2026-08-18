"""Dataset validation rules."""

from __future__ import annotations

from typing import Any

import pandas as pd

from app.data.schema import (
    CANONICAL_ALIASES,
    CRITICAL_FIELDS,
    DATE_FIELDS,
    DISPLAY_NAMES,
    NUMERIC_FIELDS,
)


def validate_recruitment_data(
    data: pd.DataFrame,
    mapping: dict[str, str],
    unmapped: list[str] | None = None,
    low_confidence: list[str] | None = None,
) -> dict[str, Any]:
    recognized = [c for c in CANONICAL_ALIASES if c in data.columns]
    status_fields = [
        c for c in ["screening_status", "interview_status", "offer_status", "joining_status"]
        if c in data.columns
    ]

    errors: list[str] = []
    warnings: list[str] = []

    if len(data) < 1:
        errors.append("The dataset contains no candidate records.")

    if not recognized:
        errors.append(
            "No recognizable recruitment columns were found. "
            "Use fields such as Candidate ID, Interview Status, Offer Status, or Joining Status."
        )

    if "candidate_id" not in data.columns:
        warnings.append(
            "Candidate ID was not detected. Candidate search and profile selection will be limited."
        )

    if not status_fields:
        warnings.append(
            "No recruitment status field was detected. Funnel KPIs will be limited."
        )

    duplicate_count = int(data.duplicated().sum())
    if duplicate_count:
        warnings.append(f"{duplicate_count:,} duplicate row(s) detected.")

    if unmapped:
        warnings.append(
            f"{len(unmapped)} column(s) were not mapped automatically: "
            + ", ".join(unmapped[:8])
            + ("..." if len(unmapped) > 8 else "")
        )

    if low_confidence:
        warnings.append(
            f"{len(low_confidence)} column(s) mapped with fuzzy matching — review recommended: "
            + ", ".join(low_confidence[:8])
        )

    if "candidate_id" in data.columns:
        missing_ids = int(data["candidate_id"].isna().sum())
        if missing_ids:
            warnings.append(f"{missing_ids:,} record(s) have a missing Candidate ID.")
        duplicate_ids = int(data["candidate_id"].dropna().astype(str).duplicated().sum())
        if duplicate_ids:
            warnings.append(f"{duplicate_ids:,} duplicate Candidate ID value(s) detected.")

    for col in DATE_FIELDS:
        if col in data.columns:
            invalid = int(
                data[col].notna().sum()
                - pd.to_datetime(data[col], errors="coerce").notna().sum()
            )
            if invalid:
                warnings.append(
                    f"{invalid:,} invalid {DISPLAY_NAMES.get(col, col).lower()} value(s) detected."
                )

    if "salary_lpa" in data.columns:
        invalid_salary = int(
            data["salary_lpa"].notna().sum()
            - pd.to_numeric(data["salary_lpa"], errors="coerce").notna().sum()
        )
        if invalid_salary:
            warnings.append(
                f"{invalid_salary:,} salary value(s) could not be interpreted as numbers."
            )

    missing_critical = [
        f for f in CRITICAL_FIELDS
        if f not in data.columns and f.replace("_status", "") in "".join(mapping.values())
    ]

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "rows": int(len(data)),
        "columns": int(len(data.columns)),
        "recognized_fields": recognized,
        "mapping": mapping,
        "unmapped_columns": unmapped or [],
        "low_confidence_columns": low_confidence or [],
        "duplicate_rows": duplicate_count,
        "mapped_count": len(mapping),
        "unmapped_count": len(unmapped or []),
    }
