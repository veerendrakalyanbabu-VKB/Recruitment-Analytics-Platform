"""Lightweight transparent forecasting."""

from __future__ import annotations

from dataclasses import dataclass

import pandas as pd

from app.analytics.kpis import compute_kpis, pct
from app.analytics.trends import compute_trends


@dataclass
class ForecastResult:
    metric: str
    estimate_low: float
    estimate_high: float
    estimate_mid: float
    sufficient_data: bool
    message: str
    historical_periods: int = 0


@dataclass
class TargetGapResult:
    target_hires: int
    period_label: str
    expected_low: float
    expected_high: float
    expected_mid: float
    gap_low: float
    gap_high: float
    pipeline_required_low: float
    pipeline_required_high: float
    sufficient_data: bool
    message: str
    label: str = "ESTIMATE"


def _period_join_rates(trends: pd.DataFrame) -> list[float]:
    rates = []
    for _, row in trends.iterrows():
        apps = row.get("Applications", 0)
        joined = row.get("Joined", 0)
        if apps and apps >= 5:
            rates.append(joined / apps)
    return rates


def forecast_joins(
    df: pd.DataFrame,
    date_col: str | None,
    col_map: dict[str, str | None] | None = None,
    min_periods: int = 3,
) -> ForecastResult:
    trends = compute_trends(df, date_col, freq="M", col_map=col_map)
    if trends.empty or len(trends) < min_periods:
        return ForecastResult(
            metric="joins",
            estimate_low=0,
            estimate_high=0,
            estimate_mid=0,
            sufficient_data=False,
            message="Insufficient historical data for reliable forecasting.",
            historical_periods=len(trends),
        )
    recent = trends.tail(3)
    avg_joins = recent["Joined"].mean()
    std = recent["Joined"].std() if len(recent) > 1 else avg_joins * 0.1
    low = max(0, avg_joins - std)
    high = avg_joins + std
    return ForecastResult(
        metric="joins",
        estimate_low=round(low, 1),
        estimate_high=round(high, 1),
        estimate_mid=round(avg_joins, 1),
        sufficient_data=True,
        message="Based on recent monthly join average (ESTIMATE).",
        historical_periods=len(trends),
    )


def target_hire_gap(
    df: pd.DataFrame,
    target_hires: int,
    date_col: str | None,
    col_map: dict[str, str | None] = None,
) -> TargetGapResult:
    fc = forecast_joins(df, date_col, col_map)
    kpis = compute_kpis(df, col_map)
    join_rate = kpis.joined / kpis.total if kpis.total else 0

    if not fc.sufficient_data or join_rate <= 0:
        return TargetGapResult(
            target_hires=target_hires,
            period_label="next period",
            expected_low=0,
            expected_high=0,
            expected_mid=0,
            gap_low=target_hires,
            gap_high=target_hires,
            pipeline_required_low=0,
            pipeline_required_high=0,
            sufficient_data=False,
            message=fc.message,
        )

    expected_mid = fc.estimate_mid
    expected_low = fc.estimate_low
    expected_high = fc.estimate_high
    gap_low = max(0, target_hires - expected_high)
    gap_high = max(0, target_hires - expected_low)

    # Pipeline required: gap / application-to-join rate
    conv = max(join_rate, 0.001)
    pipe_low = gap_low / conv
    pipe_high = gap_high / conv

    return TargetGapResult(
        target_hires=target_hires,
        period_label="next period",
        expected_low=expected_low,
        expected_high=expected_high,
        expected_mid=expected_mid,
        gap_low=round(gap_low, 1),
        gap_high=round(gap_high, 1),
        pipeline_required_low=round(pipe_low, 0),
        pipeline_required_high=round(pipe_high, 0),
        sufficient_data=True,
        message="ESTIMATE based on recent join velocity and historical conversion.",
    )
