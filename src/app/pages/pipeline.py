"""Pipeline and aging views."""

from __future__ import annotations

import streamlit as st

from app.analytics.aging import aging_summary, group_aging
from app.components.ui import kpi_card
from app.context import AppContext
from app.analytics.kpis import norm_series


def render(ctx: AppContext) -> None:
    kpis = ctx.kpis
    filtered = ctx.filtered
    col = ctx.col

    st.markdown('<div class="section-title">Candidate Pipeline</div>', unsafe_allow_html=True)

    pipeline_counts = {
        "Screening Selected": kpis.screening_selected,
        "Interview Not Scheduled": kpis.interview_not_scheduled,
        "Interview No Show": kpis.interview_no_show,
        "Interview Rejected": kpis.interview_rejected,
        "Interview Selected": kpis.interview_selected,
        "Offer Accepted": kpis.offers_accepted,
        "Joined": kpis.joined,
    }
    import pandas as pd
    pc = pd.DataFrame({"Stage": list(pipeline_counts.keys()), "Candidates": list(pipeline_counts.values())})
    st.bar_chart(pc.set_index("Stage"), y="Candidates", width="stretch", height=380)

    date_col = col.get("application_date")
    if date_col:
        st.subheader("Pipeline Aging")
        aged = aging_summary(filtered, date_col, ctx.aging_thresholds)
        if not aged.empty:
            bucket_counts = aged["aging_bucket"].value_counts().reset_index()
            bucket_counts.columns = ["Bucket", "Candidates"]
            st.bar_chart(bucket_counts.set_index("Bucket"), y="Candidates", height=280)
            if col.get("recruiter"):
                st.dataframe(
                    group_aging(filtered, col["recruiter"], date_col, ctx.aging_thresholds).head(15),
                    width="stretch", hide_index=True,
                )

    if col.get("interview"):
        pipeline_status = norm_series(filtered, col["interview"]).replace("", "Unknown").value_counts().reset_index()
        pipeline_status.columns = ["Interview Status", "Candidates"]
        st.subheader("Interview Status Distribution")
        st.dataframe(pipeline_status, width="stretch", hide_index=True)

    st.subheader("Candidates Requiring Attention")
    attention = filtered.copy()
    if col.get("interview"):
        mask = norm_series(attention, col["interview"]).str.lower().isin(
            ["not scheduled", "no show", "pending", ""]
        )
        attention = attention[mask]
    cols = [c for c in [
        col.get("id"), col.get("name"), col.get("recruiter"), col.get("client"),
        col.get("role"), col.get("technology"), col.get("interview"), col.get("interview_date"),
    ] if c]
    if len(attention):
        st.dataframe(attention[cols].head(200), width="stretch", hide_index=True)
    else:
        st.success("No interview-action candidates in the current filter scope.")
