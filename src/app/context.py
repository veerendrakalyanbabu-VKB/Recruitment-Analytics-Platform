"""Shared application context for page modules."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from app.analytics.aging import AgingThresholds
from app.analytics.kpis import RecruitmentKPIs
from app.data.profiling import DataProfile


@dataclass
class AppContext:
    fingerprint: str
    parquet_bytes: bytes
    filter_key: str
    filters_json: str
    filtered_parquet: bytes
    filtered: pd.DataFrame
    full_df: pd.DataFrame
    col: dict[str, str | None]
    kpis: RecruitmentKPIs
    validation: dict[str, Any]
    data_profile: DataProfile
    bundle: dict[str, Any]
    source_mode: str
    aging_thresholds: AgingThresholds
