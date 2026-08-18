"""Executive intelligence — health score, summary, findings."""

from __future__ import annotations

from dataclasses import dataclass, field

import pandas as pd

from app.analytics.aging import aging_risk_score, aging_summary, AgingThresholds
from app.analytics.comparisons import period_comparisons
from app.analytics.funnel import funnel_conversion_rates
from app.analytics.kpis import RecruitmentKPIs, build_col_map, compute_kpis, pct
from app.data.profiling import DataProfile


@dataclass
class RecruitmentHealthScore:
    score: float
    funnel_efficiency: float
    hiring_velocity: float
    offer_acceptance: float
    joining: float
    aging: float
    data_quality: float
    label: str = "Internal Recruitment Health Score"
    components: dict[str, float] = field(default_factory=dict)


@dataclass
class ExecutiveFinding:
    category: str
    title: str
    detail: str
    severity: str = "MEDIUM"


def compute_health_score(
    kpis: RecruitmentKPIs,
    data_profile: DataProfile | None,
    aging_df: pd.DataFrame | None,
    thresholds: AgingThresholds | None = None,
) -> RecruitmentHealthScore:
    funnel_eff = (
        min(kpis.screening_rate / 100, 1) * 0.25
        + min(kpis.interview_selection_rate / 100, 1) * 0.25
        + min(kpis.offer_acceptance_rate / 100, 1) * 0.25
        + min(kpis.joining_rate / 100, 1) * 0.25
    ) * 100

    velocity = 70.0
    if kpis.avg_time_to_hire is not None and kpis.avg_time_to_hire > 0:
        velocity = max(20, min(100, 45 / kpis.avg_time_to_hire * 100))

    offer = min(kpis.offer_acceptance_rate, 100)
    joining = min(kpis.joining_rate, 100)

    aging_score = 85.0
    if aging_df is not None and not aging_df.empty:
        aging_score = aging_risk_score(aging_df)

    dq = data_profile.health_score if data_profile else 80.0

    total = (
        funnel_eff * 0.3 + velocity * 0.15 + offer * 0.15
        + joining * 0.2 + aging_score * 0.15 + dq * 0.1
    )
    return RecruitmentHealthScore(
        score=round(total, 1),
        funnel_efficiency=round(funnel_eff, 1),
        hiring_velocity=round(velocity, 1),
        offer_acceptance=round(offer, 1),
        joining=round(joining, 1),
        aging=round(aging_score, 1),
        data_quality=round(dq, 1),
        components={
            "funnel_efficiency": round(funnel_eff, 1),
            "hiring_velocity": round(velocity, 1),
            "offer_acceptance": round(offer, 1),
            "joining": round(joining, 1),
            "aging": round(aging_score, 1),
            "data_quality": round(dq, 1),
        },
    )


def executive_findings(
    kpis: RecruitmentKPIs,
    comparisons: list,
    funnel_df: pd.DataFrame,
) -> list[ExecutiveFinding]:
    findings: list[ExecutiveFinding] = []

    for comp in comparisons:
        if comp.metric == "Joined" and comp.percent_change is not None:
            if comp.percent_change < -10:
                findings.append(ExecutiveFinding(
                    "DECLINE", "Hiring volume declining",
                    f"Joined candidates down {comp.percent_change:.1f}% vs prior period.",
                    "HIGH",
                ))
            elif comp.percent_change > 10:
                findings.append(ExecutiveFinding(
                    "OPPORTUNITY", "Hiring volume increasing",
                    f"Joined candidates up {comp.percent_change:.1f}% vs prior period.",
                    "LOW",
                ))

    if funnel_df is not None and not funnel_df.empty:
        weakest = funnel_df.loc[funnel_df["Rate %"].idxmin()]
        findings.append(ExecutiveFinding(
            "BOTTLENECK",
            "Biggest funnel bottleneck",
            f"{weakest['Conversion']} at {weakest['Rate %']:.1f}%.",
            "HIGH",
        ))

    if kpis.offer_acceptance_rate < 75 and kpis.offers_made > 5:
        findings.append(ExecutiveFinding(
            "RISK", "Offer acceptance below target",
            f"Offer acceptance at {kpis.offer_acceptance_rate:.1f}%.",
            "MEDIUM",
        ))

    if kpis.joining_rate >= 85:
        findings.append(ExecutiveFinding(
            "STRENGTH", "Strong joining execution",
            f"Joining rate {kpis.joining_rate:.1f}%.",
            "LOW",
        ))

    return findings


def build_executive_package(
    df: pd.DataFrame,
    kpis: RecruitmentKPIs,
    col_map: dict[str, str | None] | None = None,
    data_profile: DataProfile | None = None,
    thresholds: AgingThresholds | None = None,
) -> dict:
    if col_map is None:
        col_map = build_col_map(df)
    date_col = col_map.get("application_date")
    aging_col = date_col
    aged = aging_summary(df, aging_col, thresholds) if aging_col else pd.DataFrame()
    health = compute_health_score(kpis, data_profile, aged, thresholds)
    comps = period_comparisons(df, date_col, col_map)
    funnel_rates = funnel_conversion_rates(kpis)
    findings = executive_findings(kpis, comps, funnel_rates)
    return {
        "health": health,
        "comparisons": comps,
        "findings": findings,
        "funnel_rates": funnel_rates,
    }
