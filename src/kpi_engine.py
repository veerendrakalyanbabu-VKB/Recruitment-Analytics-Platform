"""Shared recruitment KPI engine — handles separate Status + Result columns."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

# Canonical column aliases used when building column maps from arbitrary CSVs.
COL_ALIASES: dict[str, list[str]] = {
    "id": ["candidate_id", "candidate id", "id"],
    "name": ["candidate_name", "candidate name", "name"],
    "application_date": ["application_date", "applied_date"],
    "recruiter": ["recruiter"],
    "client": ["client"],
    "role": ["role", "job_role"],
    "technology": ["technology", "tech", "primary_technology"],
    "experience": ["experience_years", "experience"],
    "location": ["location", "city"],
    "source": ["source", "application_source"],
    "screening": ["screening_status", "screening"],
    "screening_result": ["screening_result", "screening_outcome"],
    "interview": ["interview_status", "interview"],
    "interview_result": ["interview_result", "interview_outcome"],
    "interview_date": ["interview_date", "interview_completed_date"],
    "offer": ["offer_status", "offer"],
    "offer_result": ["offer_result", "offer_outcome"],
    "offer_date": ["offer_date"],
    "joining": ["joining_status", "joining"],
    "joining_result": ["joining_result", "joining_outcome"],
    "joining_date": ["joining_date"],
    "salary": ["salary_lpa", "salary", "offered_salary", "annual_salary"],
    "rejection": ["rejection_reason", "rejection"],
    "time_to_hire": ["time_to_hire_days", "time_to_hire", "days_to_hire"],
}

SCREENING_SELECTED = {
    "selected", "screened", "passed", "screening selected", "qualified",
}
INTERVIEW_SELECTED = {
    "selected", "interview selected", "passed", "selected for offer",
    "pass", "recommended",
}
INTERVIEW_REJECTED = {
    "rejected", "declined", "failed", "not selected", "unsuccessful",
}
INTERVIEW_NO_SHOW = {"no show", "no-show", "noshow", "did not attend"}
INTERVIEW_NOT_SCHEDULED = {"not scheduled", "pending", "scheduled", "not booked"}
INTERVIEW_COMPLETED_STATUS = {"completed", "complete", "conducted", "done"}
OFFERS_ACCEPTED = {"accepted", "offer accepted", "accept", "accepted offer"}
OFFERS_DECLINED = {
    "declined", "rejected", "offer declined", "withdrawn", "cancelled",
}
JOINED = {
    "joined", "joining confirmed", "onboarded", "onboarded successfully",
}


def build_col_map(df: pd.DataFrame) -> dict[str, str | None]:
    lookup = {str(c).strip().lower(): c for c in df.columns}
    result: dict[str, str | None] = {}
    for key, aliases in COL_ALIASES.items():
        col = None
        for name in aliases:
            if name.lower() in lookup:
                col = lookup[name.lower()]
                break
        result[key] = col
    return result


def norm_series(data: pd.DataFrame, col: str | None) -> pd.Series:
    if not col or col not in data.columns:
        return pd.Series("", index=data.index)
    return data[col].fillna("").astype(str).str.strip()


def combined_status(
    data: pd.DataFrame,
    status_col: str | None,
    result_col: str | None,
) -> pd.Series:
    """Prefer result/outcome when present; fall back to status."""
    status = norm_series(data, status_col)
    result = norm_series(data, result_col)
    return result.where(result.ne(""), status).str.lower()


def value_mask(series: pd.Series, values: set[str] | frozenset[str]) -> pd.Series:
    return series.isin(values)


def pct(num: float | int, den: float | int) -> float:
    return (num / den * 100) if den else 0.0


@dataclass
class RecruitmentKPIs:
    total: int
    screening_selected: int
    interviews_completed: int
    interview_selected: int
    interview_rejected: int
    interview_no_show: int
    interview_not_scheduled: int
    offers_accepted: int
    offers_declined: int
    offers_made: int
    joined: int
    screening_rate: float
    interview_selection_rate: float
    offer_acceptance_rate: float
    joining_rate: float
    avg_salary: float | None
    avg_time_to_hire: float | None


def compute_kpis(
    data: pd.DataFrame,
    col: dict[str, str | None] | None = None,
) -> RecruitmentKPIs:
    """Calculate funnel KPIs from a normalized recruitment dataframe."""
    if col is None:
        col = build_col_map(data)

    total = len(data)

    screening_outcome = combined_status(data, col["screening"], col["screening_result"])
    screening_selected = int(value_mask(screening_outcome, SCREENING_SELECTED).sum())

    interview_outcome = combined_status(data, col["interview"], col["interview_result"])
    interview_status = norm_series(data, col["interview"]).str.lower()

    interview_selected = int(value_mask(interview_outcome, INTERVIEW_SELECTED).sum())
    interview_rejected = int(value_mask(interview_outcome, INTERVIEW_REJECTED).sum())
    interview_no_show = int(value_mask(interview_outcome, INTERVIEW_NO_SHOW).sum())
    interview_not_scheduled = int(
        value_mask(interview_status, INTERVIEW_NOT_SCHEDULED).sum()
    )

    completed_status_only = (
        interview_status.isin(INTERVIEW_COMPLETED_STATUS)
        & ~interview_outcome.isin(
            INTERVIEW_SELECTED | INTERVIEW_REJECTED | INTERVIEW_NO_SHOW
        )
    )

    date_completed = pd.Series(False, index=data.index)
    if col["interview_date"]:
        interview_dates = pd.to_datetime(data[col["interview_date"]], errors="coerce")
        date_completed = interview_dates.notna() & ~interview_outcome.isin(
            INTERVIEW_NO_SHOW | {"not scheduled", "pending"}
        )

    interviews_completed = interview_selected + interview_rejected + int(
        completed_status_only.sum()
    )
    if interviews_completed == 0:
        interviews_completed = int(date_completed.sum())

    offer_outcome = combined_status(data, col["offer"], col["offer_result"])
    offers_accepted = int(value_mask(offer_outcome, OFFERS_ACCEPTED).sum())
    offers_declined = int(value_mask(offer_outcome, OFFERS_DECLINED).sum())
    offers_made = offers_accepted + offers_declined

    joining_outcome = combined_status(data, col["joining"], col["joining_result"])
    joined = int(value_mask(joining_outcome, JOINED).sum())

    avg_salary: float | None = None
    if col["salary"]:
        avg_salary = pd.to_numeric(data[col["salary"]], errors="coerce").mean()

    avg_tth: float | None = None
    if col["time_to_hire"]:
        avg_tth = pd.to_numeric(data[col["time_to_hire"]], errors="coerce").mean()

    return RecruitmentKPIs(
        total=total,
        screening_selected=screening_selected,
        interviews_completed=interviews_completed,
        interview_selected=interview_selected,
        interview_rejected=interview_rejected,
        interview_no_show=interview_no_show,
        interview_not_scheduled=interview_not_scheduled,
        offers_accepted=offers_accepted,
        offers_declined=offers_declined,
        offers_made=offers_made,
        joined=joined,
        screening_rate=round(pct(screening_selected, total), 2),
        interview_selection_rate=round(
            pct(interview_selected, interviews_completed), 2
        ),
        offer_acceptance_rate=round(pct(offers_accepted, offers_made), 2),
        joining_rate=round(pct(joined, offers_accepted), 2),
        avg_salary=round(avg_salary, 2) if pd.notna(avg_salary) else None,
        avg_time_to_hire=round(avg_tth, 2) if pd.notna(avg_tth) else None,
    )


def kpis_to_dict(kpis: RecruitmentKPIs) -> dict[str, Any]:
    return {
        "Total Applications": kpis.total,
        "Screening Selected": kpis.screening_selected,
        "Interviews Completed": kpis.interviews_completed,
        "Interview Selected": kpis.interview_selected,
        "Offers Accepted": kpis.offers_accepted,
        "Candidates Joined": kpis.joined,
        "Screening Selection Rate (%)": kpis.screening_rate,
        "Interview Selection Rate (%)": kpis.interview_selection_rate,
        "Offer Acceptance Rate (%)": kpis.offer_acceptance_rate,
        "Joining Rate (%)": kpis.joining_rate,
        "Average Salary (LPA)": kpis.avg_salary,
        "Average Time to Hire (Days)": kpis.avg_time_to_hire,
    }


def group_interviews_completed(data: pd.DataFrame, col: dict[str, str | None]) -> int:
    int_outcome = combined_status(data, col["interview"], col["interview_result"])
    sel = int(value_mask(int_outcome, INTERVIEW_SELECTED).sum())
    rej = int(value_mask(int_outcome, INTERVIEW_REJECTED).sum())
    completed_only = (
        norm_series(data, col["interview"]).str.lower().isin(INTERVIEW_COMPLETED_STATUS)
        & ~int_outcome.isin(INTERVIEW_SELECTED | INTERVIEW_REJECTED | INTERVIEW_NO_SHOW)
    )
    comp = sel + rej + int(completed_only.sum())
    if comp == 0 and col["interview_date"]:
        dates = pd.to_datetime(data[col["interview_date"]], errors="coerce")
        comp = int(dates.notna().sum())
    return comp


def generate_executive_insights(
    data: pd.DataFrame,
    kpis: RecruitmentKPIs,
    col: dict[str, str | None],
) -> list[dict[str, str]]:
    """Return ranked executive intelligence cards for the dashboard."""
    insights: list[dict[str, str]] = []

    if kpis.interview_not_scheduled > 0:
        insights.append({
            "type": "action",
            "title": "Interview scheduling backlog",
            "body": (
                f"{kpis.interview_not_scheduled:,} candidates are not scheduled for interview. "
                "Prioritize recruiter follow-up to protect funnel velocity."
            ),
        })

    if kpis.interview_no_show > 0:
        rate = pct(kpis.interview_no_show, kpis.interviews_completed + kpis.interview_no_show)
        insights.append({
            "type": "risk",
            "title": "Interview no-show risk",
            "body": (
                f"{kpis.interview_no_show:,} no-shows detected ({rate:.1f}% of interview activity). "
                "Consider reminder workflows and slot confirmation."
            ),
        })

    if kpis.offers_accepted > kpis.joined:
        gap = kpis.offers_accepted - kpis.joined
        insights.append({
            "type": "action",
            "title": "Offer-to-join gap",
            "body": (
                f"{gap:,} accepted offers have not converted to joining yet. "
                "Track offer release, documentation and onboarding readiness."
            ),
        })

    if col["recruiter"] and col["recruiter"] in data.columns:
        rows = []
        for recruiter, group in data.groupby(col["recruiter"]):
            g_kpis = compute_kpis(group, col)
            rows.append((recruiter, g_kpis.joined, g_kpis.total))
        if rows:
            top = max(rows, key=lambda r: r[1])
            if top[1] > 0:
                insights.append({
                    "type": "highlight",
                    "title": "Top hiring contributor",
                    "body": (
                        f"{top[0]} leads with {top[1]:,} joined candidates "
                        f"from {top[2]:,} applications in the current scope."
                    ),
                })

    if col["source"] and col["source"] in data.columns:
        source_rows = []
        for source, group in data.groupby(col["source"]):
            g_kpis = compute_kpis(group, col)
            source_rows.append((source, g_kpis.joined, g_kpis.total))
        if source_rows:
            best = max(source_rows, key=lambda r: pct(r[1], r[2]))
            conv = pct(best[1], best[2])
            insights.append({
                "type": "highlight",
                "title": "Best conversion source",
                "body": (
                    f"{best[0]} delivers the highest application-to-join rate "
                    f"at {conv:.1f}% ({best[1]:,}/{best[2]:,})."
                ),
            })

    if kpis.interview_selection_rate < 50 and kpis.interviews_completed > 10:
        insights.append({
            "type": "risk",
            "title": "Low interview selection rate",
            "body": (
                f"Interview selection is {kpis.interview_selection_rate:.1f}%. "
                "Review screening quality, role calibration and interviewer feedback loops."
            ),
        })

    if kpis.joining_rate >= 85 and kpis.offers_accepted > 0:
        insights.append({
            "type": "highlight",
            "title": "Strong offer conversion",
            "body": (
                f"Joining rate of {kpis.joining_rate:.1f}% indicates healthy "
                "offer acceptance and onboarding execution."
            ),
        })

    if not insights:
        insights.append({
            "type": "info",
            "title": "Pipeline snapshot",
            "body": (
                f"{kpis.total:,} applications → {kpis.joined:,} joined. "
                "Upload or filter data to surface deeper operational signals."
            ),
        })

    return insights
