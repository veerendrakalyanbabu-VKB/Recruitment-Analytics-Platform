"""Role / hiring difficulty intelligence."""

from __future__ import annotations

import pandas as pd

from app.analytics.aging import aging_summary, AgingThresholds
from app.analytics.kpis import build_col_map, group_kpis_by


def _difficulty_score(row: pd.Series) -> float:
    """Higher = harder to hire (deterministic internal score)."""
    factors = []
    if row.get("interview_selection_%", 100) < 50:
        factors.append(25)
    if row.get("offer_acceptance_%", 100) < 70:
        factors.append(20)
    if row.get("joining_rate_%", 100) < 80:
        factors.append(20)
    if pd.notna(row.get("avg_time_to_hire")) and row["avg_time_to_hire"] > 40:
        factors.append(15)
    if pd.notna(row.get("avg_aging_days")) and row["avg_aging_days"] > 21:
        factors.append(20)
    if row.get("applications", 0) < 5:
        factors.append(10)
    return round(min(100, sum(factors)), 1)


def _difficulty_reasons(row: pd.Series) -> str:
    reasons = []
    if row.get("interview_selection_%", 100) < 50:
        reasons.append("low interview selection")
    if row.get("offer_acceptance_%", 100) < 70:
        reasons.append("low offer acceptance")
    if row.get("joining_rate_%", 100) < 80:
        reasons.append("low joining rate")
    if pd.notna(row.get("avg_time_to_hire")) and row["avg_time_to_hire"] > 40:
        reasons.append("long time-to-hire")
    if pd.notna(row.get("avg_aging_days")) and row["avg_aging_days"] > 21:
        reasons.append("pipeline aging")
    return "; ".join(reasons) if reasons else "within normal range"


def role_intelligence(
    df: pd.DataFrame,
    col_map: dict[str, str | None] = None,
    aging_date_col: str | None = None,
    thresholds: AgingThresholds | None = None,
) -> pd.DataFrame:
    if col_map is None:
        col_map = build_col_map(df)
    role_col = col_map.get("role")
    if not role_col or role_col not in df.columns:
        return pd.DataFrame()

    base = group_kpis_by(df, role_col, col_map)
    if aging_date_col and aging_date_col in df.columns:
        aged = aging_summary(df, aging_date_col, thresholds)
        if not aged.empty:
            avg_age = aged.groupby(role_col)["aging_days"].mean().reset_index()
            avg_age.columns = [role_col, "avg_aging_days"]
            base = base.merge(avg_age, on=role_col, how="left")

    base["hiring_difficulty_score"] = base.apply(_difficulty_score, axis=1)
    base["difficulty_reasons"] = base.apply(_difficulty_reasons, axis=1)
    return base.sort_values("hiring_difficulty_score", ascending=False)
