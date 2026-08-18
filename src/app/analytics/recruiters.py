"""Recruiter intelligence analytics."""

from __future__ import annotations

import pandas as pd

from app.analytics.aging import aging_summary, AgingThresholds
from app.analytics.kpis import build_col_map, compute_kpis, group_kpis_by, pct
from app.intelligence.insight_engine import _recruiter_efficiency_score


def recruiter_intelligence(
    df: pd.DataFrame,
    col_map: dict[str, str | None] | None = None,
    aging_date_col: str | None = None,
    thresholds: AgingThresholds | None = None,
) -> pd.DataFrame:
    if col_map is None:
        col_map = build_col_map(df)
    recruiter_col = col_map.get("recruiter")
    if not recruiter_col or recruiter_col not in df.columns:
        return pd.DataFrame()

    base = group_kpis_by(df, recruiter_col, col_map)
    base["efficiency_score"] = [
        _recruiter_efficiency_score(compute_kpis(df[df[recruiter_col] == r], col_map))
        for r in base[recruiter_col]
    ]
    median = base["efficiency_score"].median()
    base["vs_team_median"] = (base["efficiency_score"] - median).round(1)
    base["interview_completion_rate"] = (
        base["interviews"] / base["applications"].replace(0, pd.NA) * 100
    ).round(2)

    if aging_date_col and aging_date_col in df.columns:
        aged = aging_summary(df, aging_date_col, thresholds)
        if not aged.empty and "aging_days" in aged.columns:
            avg_age = aged.groupby(recruiter_col)["aging_days"].mean().reset_index()
            avg_age.columns = [recruiter_col, "avg_aging_days"]
            base = base.merge(avg_age, on=recruiter_col, how="left")

    return base.sort_values("efficiency_score", ascending=False)


def recruiter_highlights(df: pd.DataFrame) -> dict[str, list[str]]:
    intel = recruiter_intelligence(df)
    if intel.empty:
        return {}
    rcol = intel.columns[0]
    top = intel.iloc[0]
    bottom = intel.iloc[-1]
    high_vol = intel.sort_values("applications", ascending=False).iloc[0]
    best_conv = intel.sort_values("joining_rate_%", ascending=False).iloc[0]
    return {
        "top_performer": [str(top[rcol]), f"Efficiency {top['efficiency_score']:.1f}"],
        "underperformer": [str(bottom[rcol]), f"Efficiency {bottom['efficiency_score']:.1f}"],
        "high_volume": [str(high_vol[rcol]), f"{int(high_vol['applications'])} applications"],
        "best_conversion": [str(best_conv[rcol]), f"Join rate {best_conv['joining_rate_%']:.1f}%"],
    }
