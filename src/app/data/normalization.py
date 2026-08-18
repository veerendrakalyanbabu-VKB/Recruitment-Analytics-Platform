"""Column and value normalization utilities."""

from __future__ import annotations

import re
from typing import Any

import pandas as pd

from app.data.schema import CANONICAL_ALIASES, DATE_FIELDS, NUMERIC_FIELDS


def normalize_header_name(value: Any) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def build_alias_lookup() -> dict[str, str]:
    lookup: dict[str, str] = {}
    for canonical, aliases in CANONICAL_ALIASES.items():
        for alias in aliases:
            lookup[normalize_header_name(alias)] = canonical
    return lookup


def clean_currency_numeric(series: pd.Series) -> pd.Series:
    """Parse salary strings with currency symbols, commas, and LPA suffixes."""
    as_str = series.fillna("").astype(str)
    cleaned = (
        as_str
        .str.replace(r"lpa", "", case=False, regex=True)
        .str.replace(r"[^\d.\-]", "", regex=True)
        .str.strip()
    )
    return pd.to_numeric(cleaned, errors="coerce")


def clean_percent_numeric(series: pd.Series) -> pd.Series:
    if series.dtype != "object":
        return pd.to_numeric(series, errors="coerce")
    cleaned = series.fillna("").astype(str).str.replace("%", "", regex=False).str.strip()
    return pd.to_numeric(cleaned, errors="coerce")


def map_columns(
    columns: list[str],
    manual_overrides: dict[str, str] | None = None,
) -> tuple[dict[str, str], list[str], list[str]]:
    """
    Map uploaded headers to canonical names.
    Returns (mapping, unmapped_columns, low_confidence_columns).
    """
    aliases = build_alias_lookup()
    mapping: dict[str, str] = {}
    used: set[str] = set()
    low_confidence: list[str] = []
    overrides = manual_overrides or {}

    for original in columns:
        if original in overrides:
            canonical = overrides[original]
            if canonical not in used:
                mapping[original] = canonical
                used.add(canonical)
            continue

        normalized = normalize_header_name(original)
        canonical = aliases.get(normalized)
        if canonical and canonical not in used:
            mapping[original] = canonical
            used.add(canonical)

    for original in columns:
        if original in mapping:
            continue
        n = normalize_header_name(original)
        candidates: list[str] = []
        for canonical, alias_list in CANONICAL_ALIASES.items():
            if canonical in used:
                continue
            for alias in alias_list:
                a = normalize_header_name(alias)
                if len(a) >= 5 and (n.startswith(a) or n.endswith(a) or a in n):
                    candidates.append(canonical)
                    break
        if len(candidates) == 1:
            mapping[original] = candidates[0]
            used.add(candidates[0])
            low_confidence.append(original)

    unmapped = [c for c in columns if c not in mapping]
    return mapping, unmapped, low_confidence


def normalize_dataframe_values(data: pd.DataFrame) -> pd.DataFrame:
    """Apply safe value normalization without dropping rows."""
    result = data.copy()

    for col in DATE_FIELDS:
        if col in result.columns:
            parsed = pd.to_datetime(result[col], errors="coerce")
            result[col] = parsed.dt.strftime("%Y-%m-%d").where(parsed.notna(), result[col])

    for col in NUMERIC_FIELDS:
        if col not in result.columns:
            continue
        if col == "salary_lpa":
            result[col] = clean_currency_numeric(result[col])
        else:
            result[col] = pd.to_numeric(result[col], errors="coerce")

    for col in result.columns:
        if result[col].dtype == "object":
            result[col] = result[col].replace(r"^\s*$", pd.NA, regex=True)

    return result


def normalize_dataframe(
    df: pd.DataFrame,
    manual_overrides: dict[str, str] | None = None,
) -> tuple[pd.DataFrame, dict[str, str], list[str], list[str]]:
    """Clean headers, map columns, normalize values. Never drops original data silently."""
    if df is None:
        raise ValueError("No dataset was supplied.")

    data = df.copy()
    data = data.loc[:, ~data.columns.astype(str).str.startswith("Unnamed")]
    data.columns = [str(c).strip() for c in data.columns]

    if data.empty:
        raise ValueError("The uploaded CSV contains no rows.")
    if len(data.columns) == 0:
        raise ValueError("The uploaded CSV contains no columns.")

    # Remove fully blank rows but preserve partial records.
    blank_mask = data.isna().all(axis=1)
    if blank_mask.any():
        data = data.loc[~blank_mask].copy()

    mapping, unmapped, low_confidence = map_columns(list(data.columns), manual_overrides)
    rename = {orig: canon for orig, canon in mapping.items()}
    data = data.rename(columns=rename)
    data = data.loc[:, ~data.columns.duplicated(keep="first")]
    data = normalize_dataframe_values(data)

    return data, mapping, unmapped, low_confidence
