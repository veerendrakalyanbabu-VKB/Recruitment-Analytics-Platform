"""Interview operations page."""

from __future__ import annotations

import streamlit as st

from app.components.ui import kpi_card
from app.context import AppContext
from app.analytics.kpis import norm_series


def render(ctx: AppContext) -> None:
    kpis = ctx.kpis
    filtered = ctx.filtered
    col = ctx.col

    st.markdown('<div class="section-title">Interview Operations</div>', unsafe_allow_html=True)

    a, b, c, d = st.columns(4)
    with a:
        kpi_card("Completed", f"{kpis.interviews_completed:,}", "Selected + Rejected", "good")
    with b:
        kpi_card("Selected", f"{kpis.interview_selected:,}", f"{kpis.interview_selection_rate:.2f}%", "purple")
    with c:
        kpi_card("No Show", f"{kpis.interview_no_show:,}", "Attendance", "bad")
    with d:
        kpi_card("Not Scheduled", f"{kpis.interview_not_scheduled:,}", "Queue", "warn")

    if col.get("interview"):
        dist = norm_series(filtered, col["interview"]).replace("", "Unknown").value_counts().reset_index()
        dist.columns = ["Status", "Candidates"]
        st.subheader("Interview Outcome Mix")
        st.bar_chart(dist.set_index("Status"), y="Candidates", width="stretch", height=350)

    cols = [c for c in [
        col.get("id"), col.get("name"), col.get("recruiter"), col.get("client"),
        col.get("role"), col.get("interview"), col.get("interview_date"), col.get("source"),
    ] if c]
    st.subheader("Operations Table")
    st.dataframe(
        filtered[cols].sort_values(cols[0] if cols else filtered.columns[0]).head(300),
        width="stretch", hide_index=True,
    )
