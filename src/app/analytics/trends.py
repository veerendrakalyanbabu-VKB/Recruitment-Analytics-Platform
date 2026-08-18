"""Trend analysis over time."""

from __future__ import annotations

import pandas as pd

from app.analytics.kpis import build_col_map, compute_kpis


def _period_label(series: pd.Series, freq: str) -> pd.Series:
    dt = pd.to_datetime(series, errors="coerce")
    if freq == "D":
        return dt.dt.strftime("%Y-%m-%d")
    if freq == "W":
        return dt.dt.to_period("W").astype(str)
    return dt.dt.to_period("M").astype(str)


def compute_trends(
    df: pd.DataFrame,
    date_col: str | None,
    freq: str = "M",
    col_map: dict[str, str | None] | None = None,
) -> pd.DataFrame:
    """Aggregate funnel metrics by time period."""
    if not date_col or date_col not in df.columns:
        return pd.DataFrame()
    if col_map is None:
        col_map = build_col_map(df)

    working = df.copy()
    working["_period"] = _period_label(working[date_col], freq)
    working = working[working["_period"].notna() & (working["_period"] != "NaT")]
    if working.empty:
        return pd.DataFrame()

    rows = []
    for period, group in working.groupby("_period", sort=True):
        k = compute_kpis(group, col_map)
        rows.append({
            "Period": period,
            "Applications": k.total,
            "Screening Selected": k.screening_selected,
            "Interviews Completed": k.interviews_completed,
            "Interview Selected": k.interview_selected,
            "Interview Selection %": k.interview_selection_rate,
            "Offers Accepted": k.offers_accepted,
            "Offer Acceptance %": k.offer_acceptance_rate,
            "Joined": k.joined,
            "Joining Rate %": k.joining_rate,
            "Avg Time to Hire": k.avg_time_to_hire,
        })
    return pd.DataFrame(rows)
