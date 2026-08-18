"""Client intelligence analytics."""

from __future__ import annotations

import pandas as pd

from app.analytics.aging import aging_summary, AgingThresholds
from app.analytics.kpis import build_col_map, compute_kpis, group_kpis_by


def _client_health_score(row: pd.Series) -> float:
    join = min(row.get("joining_rate_%", 0) / 100, 1.0)
    offer = min(row.get("offer_acceptance_%", 0) / 100, 1.0)
    interview = min(row.get("interview_selection_%", 0) / 100, 1.0)
    velocity = 1.0
    if pd.notna(row.get("avg_time_to_hire")) and row["avg_time_to_hire"] > 0:
        velocity = max(0.2, min(1.0, 45 / row["avg_time_to_hire"]))
    aging_penalty = 0.0
    if pd.notna(row.get("avg_aging_days")):
        aging_penalty = min(0.3, row["avg_aging_days"] / 100)
    score = (join * 0.35 + offer * 0.25 + interview * 0.2 + velocity * 0.2 - aging_penalty) * 100
    return round(max(0, min(100, score)), 1)


def client_intelligence(
    df: pd.DataFrame,
    col_map: dict[str, str | None] = None,
    aging_date_col: str | None = None,
    thresholds: AgingThresholds | None = None,
) -> pd.DataFrame:
    if col_map is None:
        col_map = build_col_map(df)
    client_col = col_map.get("client")
    if not client_col or client_col not in df.columns:
        return pd.DataFrame()

    base = group_kpis_by(df, client_col, col_map)
    if aging_date_col and aging_date_col in df.columns:
        aged = aging_summary(df, aging_date_col, thresholds)
        if not aged.empty:
            avg_age = aged.groupby(client_col)["aging_days"].mean().reset_index()
            avg_age.columns = [client_col, "avg_aging_days"]
            base = base.merge(avg_age, on=client_col, how="left")

    base["client_health_score"] = base.apply(_client_health_score, axis=1)
    return base.sort_values("client_health_score", ascending=False)
