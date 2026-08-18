"""Pipeline aging engine."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

import pandas as pd

from app.config import AGING_AGING_MAX, AGING_HEALTHY_MAX, AGING_WATCH_MAX


@dataclass
class AgingThresholds:
    healthy_max: int = AGING_HEALTHY_MAX
    watch_max: int = AGING_WATCH_MAX
    aging_max: int = AGING_AGING_MAX


def aging_bucket(days: int, thresholds: AgingThresholds) -> str:
    if days <= thresholds.healthy_max:
        return "HEALTHY"
    if days <= thresholds.watch_max:
        return "WATCH"
    if days <= thresholds.aging_max:
        return "AGING"
    return "CRITICAL"


def compute_aging_days(
    df: pd.DataFrame,
    reference_date_col: str | None,
    as_of: datetime | None = None,
) -> pd.Series:
    if not reference_date_col or reference_date_col not in df.columns:
        return pd.Series(dtype=float)
    ref = pd.to_datetime(df[reference_date_col], errors="coerce")
    today = pd.Timestamp(as_of or datetime.now()).normalize()
    if hasattr(today, "tz") and today.tz is not None:
        today = today.tz_localize(None)
    return (today - ref).dt.days


def aging_summary(
    df: pd.DataFrame,
    reference_date_col: str | None,
    thresholds: AgingThresholds | None = None,
) -> pd.DataFrame:
    thresholds = thresholds or AgingThresholds()
    days = compute_aging_days(df, reference_date_col)
    if days.empty:
        return pd.DataFrame()
    out = df.copy()
    out["aging_days"] = days
    out = out[out["aging_days"].notna()]
    out["aging_bucket"] = out["aging_days"].apply(
        lambda d: aging_bucket(int(d), thresholds)
    )
    return out


def aging_risk_score(aging_df: pd.DataFrame) -> float:
    if aging_df.empty or "aging_bucket" not in aging_df.columns:
        return 100.0
    weights = {"HEALTHY": 0, "WATCH": 1, "AGING": 2, "CRITICAL": 3}
    scores = aging_df["aging_bucket"].map(weights).fillna(0)
    avg = scores.mean()
    return round(max(0, 100 - avg * 25), 1)


def group_aging(
    df: pd.DataFrame,
    group_col: str,
    reference_date_col: str | None,
    thresholds: AgingThresholds | None = None,
) -> pd.DataFrame:
    if group_col not in df.columns:
        return pd.DataFrame()
    aged = aging_summary(df, reference_date_col, thresholds)
    if aged.empty:
        return pd.DataFrame()
    summary = (
        aged.groupby(group_col)
        .agg(
            candidates=("aging_days", "count"),
            avg_aging_days=("aging_days", "mean"),
            critical=("aging_bucket", lambda s: int((s == "CRITICAL").sum())),
            aging=("aging_bucket", lambda s: int((s == "AGING").sum())),
        )
        .reset_index()
    )
    summary["avg_aging_days"] = summary["avg_aging_days"].round(1)
    return summary.sort_values("avg_aging_days", ascending=False)
