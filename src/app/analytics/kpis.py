"""Recruitment KPI calculations — deterministic analytics core."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import pandas as pd

from app.data.schema import (
    ANALYTICS_KEY_MAP,
    INTERVIEW_COMPLETED_STATUS,
    INTERVIEW_NOT_SCHEDULED,
    INTERVIEW_NO_SHOW,
    INTERVIEW_REJECTED,
    INTERVIEW_SELECTED,
    JOINED,
    OFFERS_ACCEPTED,
    OFFERS_DECLINED,
    SCREENING_SELECTED,
)


def build_col_map(df: pd.DataFrame) -> dict[str, str | None]:
    lookup = {str(c).strip().lower(): c for c in df.columns}
    result: dict[str, str | None] = {}
    for short_key, canonical in ANALYTICS_KEY_MAP.items():
        col = None
        if canonical.lower() in lookup:
            col = lookup[canonical.lower()]
        elif short_key.lower() in lookup:
            col = lookup[short_key.lower()]
        result[short_key] = col
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


def value_mask(series: pd.Series, values: frozenset[str]) -> pd.Series:
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

    # Completed = selected + rejected outcomes OR explicit completed status.
    # Do NOT infer completion from result alone when status is missing.
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


def group_kpis_by(
    data: pd.DataFrame,
    group_col: str,
    col: dict[str, str | None] | None = None,
) -> pd.DataFrame:
    if col is None:
        col = build_col_map(data)
    rows = []
    for name, group in data.groupby(group_col, dropna=False):
        k = compute_kpis(group, col)
        salary_col = col.get("salary")
        avg_salary = None
        if salary_col and salary_col in group.columns:
            avg_salary = pd.to_numeric(group[salary_col], errors="coerce").mean()
        rows.append({
            group_col: name,
            "applications": k.total,
            "screening_selected": k.screening_selected,
            "interviews": k.interviews_completed,
            "interview_selected": k.interview_selected,
            "offers": k.offers_accepted,
            "joined": k.joined,
            "screening_rate_%": k.screening_rate,
            "interview_selection_%": k.interview_selection_rate,
            "offer_acceptance_%": k.offer_acceptance_rate,
            "joining_rate_%": k.joining_rate,
            "average_salary": round(avg_salary, 2) if pd.notna(avg_salary) else None,
            "avg_time_to_hire": k.avg_time_to_hire,
        })
    return pd.DataFrame(rows)
