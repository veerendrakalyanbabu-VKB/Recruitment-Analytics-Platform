"""Period-over-period comparison utilities."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.analytics.kpis import compute_kpis, pct


@dataclass
class PeriodComparison:
    metric: str
    current: float | int
    previous: float | int
    absolute_change: float
    percent_change: float | None
    sufficient_data: bool
    note: str = ""


def safe_pct_change(current: float, previous: float, min_denominator: float = 1.0) -> float | None:
    if previous < min_denominator:
        return None
    return round((current - previous) / previous * 100, 2)


def compare_values(metric: str, current: float | int, previous: float | int) -> PeriodComparison:
    abs_chg = round(float(current) - float(previous), 2)
    pct_chg = safe_pct_change(float(current), float(previous))
    sufficient = previous > 0 or current > 0
    note = ""
    if previous == 0 and current > 0:
        note = "No prior-period baseline"
    return PeriodComparison(
        metric=metric,
        current=current,
        previous=previous,
        absolute_change=abs_chg,
        percent_change=pct_chg,
        sufficient_data=sufficient,
        note=note,
    )


def split_by_period(
    df: pd.DataFrame,
    date_col: str,
    freq: str = "M",
) -> tuple[pd.DataFrame, pd.DataFrame] | None:
    """Split into current and previous period buckets."""
    if date_col not in df.columns:
        return None
    dates = pd.to_datetime(df[date_col], errors="coerce")
    valid = df.loc[dates.notna()].copy()
    if len(valid) < 2:
        return None
    valid["_dt"] = pd.to_datetime(valid[date_col], errors="coerce")
    valid = valid.sort_values("_dt")
    if freq == "W":
        periods = valid["_dt"].dt.to_period("W")
    elif freq == "M":
        periods = valid["_dt"].dt.to_period("M")
    else:
        periods = valid["_dt"].dt.to_period("Q")
    unique_periods = sorted(periods.unique())
    if len(unique_periods) < 2:
        return None
    current_p = unique_periods[-1]
    previous_p = unique_periods[-2]
    current = valid.loc[periods == current_p].drop(columns=["_dt"])
    previous = valid.loc[periods == previous_p].drop(columns=["_dt"])
    return current, previous


def period_comparisons(
    df: pd.DataFrame,
    date_col: str | None,
    col_map: dict[str, str | None] | None = None,
) -> list[PeriodComparison]:
    if not date_col or date_col not in df.columns:
        return []
    split = split_by_period(df, date_col, freq="M")
    if not split:
        return []
    current_df, previous_df = split
    cur = compute_kpis(current_df, col_map)
    prev = compute_kpis(previous_df, col_map)
    metrics = [
        ("Applications", cur.total, prev.total),
        ("Screening Selected", cur.screening_selected, prev.screening_selected),
        ("Interviews Completed", cur.interviews_completed, prev.interviews_completed),
        ("Interview Selection %", cur.interview_selection_rate, prev.interview_selection_rate),
        ("Offers Accepted", cur.offers_accepted, prev.offers_accepted),
        ("Offer Acceptance %", cur.offer_acceptance_rate, prev.offer_acceptance_rate),
        ("Joined", cur.joined, prev.joined),
        ("Joining Rate %", cur.joining_rate, prev.joining_rate),
    ]
    if cur.avg_time_to_hire is not None and prev.avg_time_to_hire is not None:
        metrics.append(("Avg Time to Hire", cur.avg_time_to_hire, prev.avg_time_to_hire))
    return [compare_values(name, c, p) for name, c, p in metrics]
