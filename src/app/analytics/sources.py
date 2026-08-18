"""Source intelligence analytics."""

from __future__ import annotations

import pandas as pd

from app.analytics.kpis import build_col_map, group_kpis_by


def source_intelligence(
    df: pd.DataFrame,
    col_map: dict[str, str | None] = None,
) -> pd.DataFrame:
    if col_map is None:
        col_map = build_col_map(df)
    source_col = col_map.get("source")
    if not source_col or source_col not in df.columns:
        return pd.DataFrame()

    base = group_kpis_by(df, source_col, col_map)
    base["application_to_join_%"] = base["joining_rate_%"]
    base["quality_score"] = (
        base["application_to_join_%"] * 0.5
        + base["interview_selection_%"] * 0.3
        + base["offer_acceptance_%"] * 0.2
    ).round(2)
    return base.sort_values("quality_score", ascending=False)


def best_quality_source(intel: pd.DataFrame) -> tuple[str, float] | None:
    if intel.empty:
        return None
    col = intel.columns[0]
    best = intel.sort_values("quality_score", ascending=False).iloc[0]
    return str(best[col]), float(best["quality_score"])
