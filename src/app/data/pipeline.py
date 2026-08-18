"""Pure ingestion pipeline (no Streamlit)."""

from __future__ import annotations

import io
import json
from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from app.data.fingerprint import compute_fingerprint
from app.data.loader import read_csv_flexible
from app.data.normalization import normalize_dataframe
from app.data.profiling import DataProfile, profile_dataset
from app.data.validation import validate_recruitment_data
from app.utils.perf import timed


@dataclass
class PreparedDataset:
    fingerprint: str
    source_name: str
    data: pd.DataFrame
    parquet_bytes: bytes
    mapping: dict[str, str]
    unmapped: list[str]
    low_confidence: list[str]
    validation: dict[str, Any]
    profile: DataProfile
    ingest_timings_ms: dict[str, float] = field(default_factory=dict)


def _to_parquet_bytes(df: pd.DataFrame) -> bytes:
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    return buf.getvalue()


def ingest_bytes(
    raw_bytes: bytes,
    source_name: str = "",
    manual_overrides: dict[str, str] | None = None,
) -> PreparedDataset:
    """Parse, normalize, validate, and profile once per unique fingerprint."""
    timings: dict[str, float] = {}

    with timed("fingerprint", timings):
        fingerprint = compute_fingerprint(raw_bytes, source_name=source_name)

    with timed("parse_csv", timings):
        raw_df = read_csv_flexible(io.BytesIO(raw_bytes))

    with timed("normalize", timings):
        normalized, mapping, unmapped, low_conf = normalize_dataframe(
            raw_df, manual_overrides
        )

    with timed("validate", timings):
        validation = validate_recruitment_data(
            normalized, mapping, unmapped, low_conf
        )

    with timed("profile", timings):
        profile = profile_dataset(normalized, validation)

    with timed("parquet", timings):
        parquet_bytes = _to_parquet_bytes(normalized)

    return PreparedDataset(
        fingerprint=fingerprint,
        source_name=source_name,
        data=normalized,
        parquet_bytes=parquet_bytes,
        mapping=mapping,
        unmapped=unmapped,
        low_confidence=low_conf,
        validation=validation,
        profile=profile,
        ingest_timings_ms=timings,
    )


def prepared_to_cache_dict(prepared: PreparedDataset) -> dict[str, Any]:
    """Serialize for Streamlit cache_data (validation/profile as JSON-safe dicts)."""
    return {
        "fingerprint": prepared.fingerprint,
        "source_name": prepared.source_name,
        "parquet_bytes": prepared.parquet_bytes,
        "mapping": prepared.mapping,
        "unmapped": prepared.unmapped,
        "low_confidence": prepared.low_confidence,
        "validation": prepared.validation,
        "profile": {
            "health_score": prepared.profile.health_score,
            "row_count": prepared.profile.row_count,
            "column_count": prepared.profile.column_count,
            "duplicate_rows": prepared.profile.duplicate_rows,
            "issues": prepared.profile.issues,
            "missing_by_field": prepared.profile.missing_by_field,
            "invalid_dates": prepared.profile.invalid_dates,
            "invalid_numeric": prepared.profile.invalid_numeric,
            "unmapped_columns": prepared.profile.unmapped_columns,
            "normalization_notes": prepared.profile.normalization_notes,
        },
        "ingest_timings_ms": prepared.ingest_timings_ms,
    }


def cache_dict_to_dataframe(cache: dict[str, Any]) -> pd.DataFrame:
    return pd.read_parquet(io.BytesIO(cache["parquet_bytes"]))


def profile_from_cache(cache: dict[str, Any]) -> DataProfile:
    p = cache["profile"]
    return DataProfile(
        health_score=p["health_score"],
        row_count=p["row_count"],
        column_count=p["column_count"],
        duplicate_rows=p["duplicate_rows"],
        missing_by_field=p.get("missing_by_field", {}),
        invalid_dates=p.get("invalid_dates", {}),
        invalid_numeric=p.get("invalid_numeric", {}),
        unmapped_columns=p.get("unmapped_columns", []),
        issues=p.get("issues", []),
        normalization_notes=p.get("normalization_notes", []),
    )


def build_filter_key(filters: dict[str, list[str]]) -> str:
    """Stable hash for sidebar filter selections."""
    import hashlib
    payload = json.dumps(filters, sort_keys=True, default=str)
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()[:24]
