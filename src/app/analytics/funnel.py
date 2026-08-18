"""Hiring funnel construction."""

from __future__ import annotations

import pandas as pd

from app.analytics.kpis import RecruitmentKPIs


def build_funnel_dataframe(kpis: RecruitmentKPIs) -> pd.DataFrame:
    return pd.DataFrame({
        "Stage": [
            "Applications",
            "Screening Selected",
            "Interviews Completed",
            "Interview Selected",
            "Offers Accepted",
            "Joined",
        ],
        "Candidates": [
            kpis.total,
            kpis.screening_selected,
            kpis.interviews_completed,
            kpis.interview_selected,
            kpis.offers_accepted,
            kpis.joined,
        ],
    })


def funnel_conversion_rates(kpis: RecruitmentKPIs) -> pd.DataFrame:
    stages = [
        ("Applications → Screening", kpis.screening_selected, kpis.total),
        ("Screening → Interviews", kpis.interviews_completed, kpis.screening_selected),
        ("Interviews → Selected", kpis.interview_selected, kpis.interviews_completed),
        ("Selected → Offers", kpis.offers_accepted, kpis.interview_selected),
        ("Offers → Joined", kpis.joined, kpis.offers_accepted),
    ]
    rows = []
    for label, num, den in stages:
        rate = (num / den * 100) if den else 0.0
        rows.append({
            "Conversion": label,
            "Rate %": round(rate, 2),
            "From": den,
            "To": num,
        })
    return pd.DataFrame(rows)
