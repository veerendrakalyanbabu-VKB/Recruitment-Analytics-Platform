"""Deterministic recruitment intelligence and insight rules."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

import pandas as pd

from app.analytics.kpis import (
    build_col_map,
    compute_kpis,
    group_kpis_by,
    pct,
    RecruitmentKPIs,
)


class InsightType(str, Enum):
    BOTTLENECK = "BOTTLENECK"
    DECLINE = "DECLINE"
    OPPORTUNITY = "OPPORTUNITY"
    RISK = "RISK"
    ANOMALY = "ANOMALY"
    BENCHMARK = "BENCHMARK"
    FORECAST = "FORECAST"


class Severity(str, Enum):
    CRITICAL = "CRITICAL"
    HIGH = "HIGH"
    MEDIUM = "MEDIUM"
    LOW = "LOW"


@dataclass
class Insight:
    title: str
    insight_type: InsightType
    severity: Severity
    metric: str
    current_value: float | int | str
    comparison_value: float | int | str | None = None
    change: float | None = None
    entity: str | None = None
    reason: str = ""
    recommended_action: str = ""
    evidence: list[str] = field(default_factory=list)

    def to_display_dict(self) -> dict[str, str]:
        return {
            "type": self.insight_type.value,
            "severity": self.severity.value,
            "title": self.title,
            "metric": self.metric,
            "current": str(self.current_value),
            "comparison": str(self.comparison_value) if self.comparison_value is not None else "—",
            "change": f"{self.change:.1f}%" if self.change is not None else "—",
            "entity": self.entity or "—",
            "reason": self.reason,
            "action": self.recommended_action,
            "evidence": "; ".join(self.evidence),
        }


def _recruiter_efficiency_score(k: RecruitmentKPIs) -> float:
    """Normalized 0–100 score — not volume-only."""
    if k.total == 0:
        return 0.0
    screening = min(k.screening_rate / 100, 1.0)
    interview_sel = min(k.interview_selection_rate / 100, 1.0) if k.interviews_completed else 0.5
    offer_acc = min(k.offer_acceptance_rate / 100, 1.0) if k.offers_made else 0.5
    joining = min(k.joining_rate / 100, 1.0) if k.offers_accepted else 0.5
    velocity = 1.0
    if k.avg_time_to_hire is not None and k.avg_time_to_hire > 0:
        velocity = max(0.2, min(1.0, 45 / k.avg_time_to_hire))
    score = (
        screening * 0.2 + interview_sel * 0.25 + offer_acc * 0.2
        + joining * 0.25 + velocity * 0.1
    ) * 100
    return round(score, 1)


def recruiter_scorecards(
    data: pd.DataFrame,
    col: dict[str, str | None] | None = None,
) -> pd.DataFrame:
    if col is None:
        col = build_col_map(data)
    recruiter_col = col.get("recruiter")
    if not recruiter_col:
        return pd.DataFrame()
    base = group_kpis_by(data, recruiter_col, col)
    base["efficiency_score"] = [
        _recruiter_efficiency_score(
            compute_kpis(data[data[recruiter_col] == r], col)
        )
        for r in base[recruiter_col]
    ]
    median = base["efficiency_score"].median()
    base["vs_team_median"] = (base["efficiency_score"] - median).round(1)
    return base.sort_values("efficiency_score", ascending=False)


def generate_insights(
    data: pd.DataFrame,
    kpis: RecruitmentKPIs,
    col: dict[str, str | None] | None = None,
) -> list[Insight]:
    if col is None:
        col = build_col_map(data)
    insights: list[Insight] = []

    if kpis.interview_not_scheduled > 0:
        insights.append(Insight(
            title="Interview scheduling backlog",
            insight_type=InsightType.BOTTLENECK,
            severity=Severity.HIGH if kpis.interview_not_scheduled > 50 else Severity.MEDIUM,
            metric="interview_not_scheduled",
            current_value=kpis.interview_not_scheduled,
            reason="Candidates awaiting interview scheduling block funnel velocity.",
            recommended_action="Assign scheduling owners and clear the interview queue within 48 hours.",
            evidence=[f"{kpis.interview_not_scheduled:,} candidates not scheduled"],
        ))

    if kpis.interview_no_show > 0:
        rate = pct(kpis.interview_no_show, kpis.interviews_completed + kpis.interview_no_show)
        insights.append(Insight(
            title="Interview no-show risk",
            insight_type=InsightType.RISK,
            severity=Severity.HIGH if rate > 10 else Severity.MEDIUM,
            metric="interview_no_show_rate",
            current_value=round(rate, 1),
            comparison_value=10.0,
            change=rate - 10.0,
            reason="No-shows waste recruiter and interviewer capacity.",
            recommended_action="Enable reminder workflows and confirmation before interview slots.",
            evidence=[f"{kpis.interview_no_show:,} no-shows ({rate:.1f}% of interview activity)"],
        ))

    if kpis.offers_accepted > kpis.joined:
        gap = kpis.offers_accepted - kpis.joined
        insights.append(Insight(
            title="Offer-to-join gap",
            insight_type=InsightType.RISK,
            severity=Severity.HIGH,
            metric="offer_join_gap",
            current_value=gap,
            reason="Accepted offers not yet converted to joining.",
            recommended_action="Track documentation, release letters, and onboarding readiness.",
            evidence=[f"{gap:,} accepted offers pending join"],
        ))

    if kpis.interview_selection_rate < 50 and kpis.interviews_completed > 10:
        insights.append(Insight(
            title="Low interview selection rate",
            insight_type=InsightType.DECLINE,
            severity=Severity.MEDIUM,
            metric="interview_selection_rate",
            current_value=kpis.interview_selection_rate,
            comparison_value=50.0,
            change=kpis.interview_selection_rate - 50.0,
            reason="Screening quality or role calibration may be misaligned.",
            recommended_action="Review screening criteria and interviewer feedback loops.",
            evidence=[
                f"Selection rate {kpis.interview_selection_rate:.1f}%",
                f"{kpis.interview_selected:,}/{kpis.interviews_completed:,} interviews selected",
            ],
        ))

    if col.get("recruiter") and col["recruiter"] in data.columns:
        cards = recruiter_scorecards(data, col)
        if len(cards) >= 2:
            bottom = cards.iloc[-1]
            median = cards["efficiency_score"].median()
            if bottom["efficiency_score"] < median - 15:
                insights.append(Insight(
                    title="Recruiter underperformance signal",
                    insight_type=InsightType.BENCHMARK,
                    severity=Severity.MEDIUM,
                    metric="recruiter_efficiency_score",
                    current_value=bottom["efficiency_score"],
                    comparison_value=round(median, 1),
                    change=bottom["efficiency_score"] - median,
                    entity=str(bottom[col["recruiter"]]),
                    reason="Efficiency score materially below team median.",
                    recommended_action="Review pipeline aging and conversion stages for this recruiter.",
                    evidence=[
                        f"Score {bottom['efficiency_score']:.1f} vs median {median:.1f}",
                        f"Joined {int(bottom['joined'])}/{int(bottom['applications'])} applications",
                    ],
                ))
            top = cards.iloc[0]
            if top["efficiency_score"] >= median + 10:
                insights.append(Insight(
                    title="Top recruiter efficiency",
                    insight_type=InsightType.OPPORTUNITY,
                    severity=Severity.LOW,
                    metric="recruiter_efficiency_score",
                    current_value=top["efficiency_score"],
                    comparison_value=round(median, 1),
                    entity=str(top[col["recruiter"]]),
                    reason="Strong normalized efficiency across funnel stages.",
                    recommended_action="Document best practices from this recruiter for team enablement.",
                    evidence=[f"Efficiency score {top['efficiency_score']:.1f}"],
                ))

    if col.get("source") and col["source"] in data.columns:
        source_df = group_kpis_by(data, col["source"], col)
        if len(source_df):
            source_df["join_conversion_%"] = source_df["joining_rate_%"]
            best = source_df.sort_values("join_conversion_%", ascending=False).iloc[0]
            worst_vol = source_df.sort_values("applications", ascending=False).iloc[0]
            if best["join_conversion_%"] > 0:
                insights.append(Insight(
                    title="Highest-quality source",
                    insight_type=InsightType.OPPORTUNITY,
                    severity=Severity.LOW,
                    metric="source_join_rate",
                    current_value=best["join_conversion_%"],
                    entity=str(best[col["source"]]),
                    reason="Best application-to-join conversion among sources.",
                    recommended_action="Increase investment in this channel if capacity allows.",
                    evidence=[
                        f"{best['join_conversion_%']:.1f}% join rate",
                        f"{int(best['joined'])}/{int(best['applications'])} applications",
                    ],
                ))
            if worst_vol["applications"] > kpis.total * 0.3 and worst_vol["join_conversion_%"] < 5:
                insights.append(Insight(
                    title="High-volume low-conversion source",
                    insight_type=InsightType.RISK,
                    severity=Severity.MEDIUM,
                    metric="source_volume_vs_conversion",
                    current_value=int(worst_vol["applications"]),
                    entity=str(worst_vol[col["source"]]),
                    reason="Large volume source with weak join conversion.",
                    recommended_action="Re-evaluate sourcing spend and screening for this channel.",
                    evidence=[
                        f"{int(worst_vol['applications']):,} applications",
                        f"Join rate {worst_vol['join_conversion_%']:.1f}%",
                    ],
                ))

    if kpis.joining_rate >= 85 and kpis.offers_accepted > 0:
        insights.append(Insight(
            title="Strong offer conversion",
            insight_type=InsightType.BENCHMARK,
            severity=Severity.LOW,
            metric="joining_rate",
            current_value=kpis.joining_rate,
            comparison_value=85.0,
            reason="Healthy offer acceptance and onboarding execution.",
            recommended_action="Maintain onboarding SLA and candidate communication.",
            evidence=[f"Joining rate {kpis.joining_rate:.1f}%"],
        ))

    if not insights:
        insights.append(Insight(
            title="Pipeline snapshot",
            insight_type=InsightType.BENCHMARK,
            severity=Severity.LOW,
            metric="applications",
            current_value=kpis.total,
            reason="Baseline funnel metrics for current filter scope.",
            recommended_action="Apply filters or upload data to surface operational signals.",
            evidence=[f"{kpis.total:,} applications → {kpis.joined:,} joined"],
        ))

    severity_order = {Severity.CRITICAL: 0, Severity.HIGH: 1, Severity.MEDIUM: 2, Severity.LOW: 3}
    insights.sort(key=lambda i: severity_order[i.severity])
    return insights


def generate_executive_insights(
    data: pd.DataFrame,
    kpis: RecruitmentKPIs,
    col: dict[str, str | None] | None = None,
) -> list[dict[str, str]]:
    """Backward-compatible card format for existing UI components."""
    tone_map = {
        InsightType.RISK: "risk",
        InsightType.BOTTLENECK: "action",
        InsightType.DECLINE: "risk",
        InsightType.OPPORTUNITY: "highlight",
        InsightType.BENCHMARK: "info",
        InsightType.ANOMALY: "risk",
        InsightType.FORECAST: "info",
    }
    cards = []
    for insight in generate_insights(data, kpis, col):
        body = insight.reason
        if insight.recommended_action:
            body = f"{insight.reason} {insight.recommended_action}"
        cards.append({
            "type": tone_map.get(insight.insight_type, "info"),
            "title": insight.title,
            "body": body,
            "severity": insight.severity.value,
            "metric": insight.metric,
            "evidence": insight.evidence,
        })
    return cards


def insight_from_record(record: dict) -> Insight:
    """Rebuild Insight for UI from cached serializable record."""
    return Insight(
        title=record["title"],
        insight_type=InsightType(record["insight_type"]),
        severity=Severity(record["severity"]),
        metric=record["metric"],
        current_value=record.get("current_value", "—"),
        reason=record.get("reason", ""),
        recommended_action=record.get("recommended_action", ""),
        evidence=record.get("evidence", []),
    )
