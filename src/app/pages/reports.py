"""Reports, forecasting, and data quality."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from app.analytics.forecasting import forecast_joins, target_hire_gap
from app.analytics.kpis import pct
from app.components.ui import kpi_card
from app.context import AppContext
from app.utils.formatting import display_value


def render(ctx: AppContext) -> None:
    kpis = ctx.kpis
    filtered = ctx.filtered
    col = ctx.col
    data_profile = ctx.data_profile

    st.markdown('<div class="section-title">Reports & Data Quality</div>', unsafe_allow_html=True)

    management = pd.DataFrame({
        "Metric": [
            "Applications", "Screening Selected", "Interviews Completed",
            "Interview Selected", "Offers Accepted", "Joined",
            "Screening Rate %", "Interview Selection %", "Offer Acceptance %",
            "Joining Rate %", "Average Salary LPA", "Average Time to Hire Days",
        ],
        "Value": [
            display_value(kpis.total), display_value(kpis.screening_selected),
            display_value(kpis.interviews_completed), display_value(kpis.interview_selected),
            display_value(kpis.offers_accepted), display_value(kpis.joined),
            display_value(kpis.screening_rate), display_value(kpis.interview_selection_rate),
            display_value(kpis.offer_acceptance_rate), display_value(kpis.joining_rate),
            display_value(kpis.avg_salary), display_value(kpis.avg_time_to_hire),
        ],
    })
    st.dataframe(management, width="stretch", hide_index=True)
    st.download_button(
        "Download KPI Report (CSV)",
        data=management.to_csv(index=False).encode("utf-8"),
        file_name="recruitment_kpi_report.csv",
        mime="text/csv",
    )

    st.subheader("Data Quality")
    st.metric("Data Health Score", f"{data_profile.health_score:.0f} / 100")
    if data_profile.issues:
        for issue in data_profile.issues:
            st.warning(issue)

    quality_rows = []
    for key, c in col.items():
        if c and c in filtered.columns:
            missing = int(filtered[c].isna().sum())
            quality_rows.append({
                "Field": c, "Missing": missing,
                "Missing %": round(pct(missing, len(filtered)), 2),
            })
    if quality_rows:
        st.dataframe(pd.DataFrame(quality_rows).sort_values("Missing %", ascending=False),
                     width="stretch", hide_index=True)

    st.download_button(
        "Download Filtered Data (CSV)",
        data=filtered.to_csv(index=False).encode("utf-8"),
        file_name="filtered_recruitment_candidates.csv",
        mime="text/csv",
    )

    st.divider()
    st.markdown('<div class="section-title">Forecast</div>', unsafe_allow_html=True)
    st.caption("ESTIMATE — not a guarantee.")

    date_col = col.get("application_date")
    fc = forecast_joins(filtered, date_col, col)
    if fc.sufficient_data:
        kpi_card(
            "Expected Joins (next period)",
            f"{fc.estimate_low:.0f} – {fc.estimate_high:.0f}",
            fc.message, "info",
        )
    else:
        st.warning(fc.message)

    target = st.number_input("Target hires", min_value=1, value=100, step=10)
    gap = target_hire_gap(filtered, int(target), date_col, col)
    if gap.sufficient_data:
        st.write(
            f"**ESTIMATE:** Expected {gap.expected_low:.0f}–{gap.expected_high:.0f} joins. "
            f"Gap {gap.gap_low:.0f}–{gap.gap_high:.0f}. "
            f"Pipeline needed ~{gap.pipeline_required_low:,.0f}–{gap.pipeline_required_high:,.0f} applications."
        )
    else:
        st.warning(gap.message)
