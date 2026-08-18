"""Executive Command Center page."""

from __future__ import annotations

import json

import pandas as pd
import streamlit as st

from app.analytics.funnel import build_funnel_dataframe
from app.components.ui import insight_card, kpi_card
from app.context import AppContext
from app.intelligence.insight_engine import insight_from_record
from app.streamlit_cache import (
    cached_client_intel,
    cached_executive_package,
    cached_insights,
    cached_recruiter_intel,
    cached_trends,
)


def render(ctx: AppContext) -> None:
    kpis = ctx.kpis
    th_json = json.dumps({
        "healthy_max": ctx.aging_thresholds.healthy_max,
        "watch_max": ctx.aging_thresholds.watch_max,
        "aging_max": ctx.aging_thresholds.aging_max,
    })

    exec_pkg = cached_executive_package(
        ctx.fingerprint,
        ctx.filter_key,
        ctx.filtered_parquet,
        ctx.data_profile.health_score,
        th_json,
    )

    st.markdown('<div class="section-title">RECRUITMENT COMMAND CENTER</div>', unsafe_allow_html=True)

    hc = st.columns(6)
    with hc[0]:
        st.metric("Recruitment Health", f"{exec_pkg['health_score']:.0f}/100")
    with hc[1]:
        st.metric("Applications", f"{kpis.total:,}")
    with hc[2]:
        st.metric("Interviews", f"{kpis.interviews_completed:,}")
    with hc[3]:
        st.metric("Interview Selection", f"{kpis.interview_selection_rate:.2f}%")
    with hc[4]:
        st.metric("Joined", f"{kpis.joined:,}")
    with hc[5]:
        st.metric("Joining Rate", f"{kpis.joining_rate:.2f}%")

    st.caption("Internal analytical score — not an industry certification.")

    row = st.columns(4)
    with row[0]:
        kpi_card("Screening Selected", f"{kpis.screening_selected:,}", f"{kpis.screening_rate:.2f}%", "good")
    with row[1]:
        kpi_card("Offers Accepted", f"{kpis.offers_accepted:,}", f"{kpis.offer_acceptance_rate:.2f}%", "good")
    with row[2]:
        avg_s = kpis.avg_salary
        kpi_card("Avg Salary", f"₹{avg_s:.2f} LPA" if avg_s else "N/A", "Offered salary", "warn")
    with row[3]:
        avg_t = kpis.avg_time_to_hire
        kpi_card("Time to Hire", f"{avg_t:.1f} days" if avg_t else "N/A", "Hiring velocity", "info")

    st.divider()
    st.markdown('<div class="section-title">Attention Required</div>', unsafe_allow_html=True)
    insights = [
        insight_from_record(r)
        for r in cached_insights(ctx.fingerprint, ctx.filter_key, ctx.filtered_parquet)
    ]
    risks = [i for i in insights if i.severity.value in ("CRITICAL", "HIGH")]
    for insight in (risks or insights)[:6]:
        insight_card(insight)

    st.divider()
    st.markdown('<div class="section-title">Opportunities</div>', unsafe_allow_html=True)
    for finding in exec_pkg.get("findings", []):
        if finding["category"] in ("OPPORTUNITY", "STRENGTH"):
            st.success(f"{finding['title']}: {finding['detail']}")

    st.divider()
    st.markdown('<div class="section-title">Recruitment Trends</div>', unsafe_allow_html=True)
    date_col = ctx.col.get("application_date")
    if date_col:
        trends = cached_trends(ctx.fingerprint, ctx.filter_key, ctx.filtered_parquet, date_col, "M")
        if not trends.empty:
            st.line_chart(trends.set_index("Period")[["Applications", "Joined"]], height=320)
            st.dataframe(trends, width="stretch", hide_index=True)
        else:
            st.info("Insufficient dated records for monthly trends.")
    else:
        st.info("Application date not available — trends skipped.")

    st.divider()
    st.markdown('<div class="section-title">Funnel Performance</div>', unsafe_allow_html=True)
    funnel = build_funnel_dataframe(kpis)
    st.bar_chart(funnel.set_index("Stage"), y="Candidates", width="stretch", height=300)
    if exec_pkg.get("funnel_rates"):
        st.dataframe(pd.DataFrame(exec_pkg["funnel_rates"]), width="stretch", hide_index=True)

    if exec_pkg.get("comparisons"):
        st.markdown('<div class="section-title">Period Comparison</div>', unsafe_allow_html=True)
        st.dataframe(pd.DataFrame(exec_pkg["comparisons"]), width="stretch", hide_index=True)

    st.divider()
    rec_intel = cached_recruiter_intel(ctx.fingerprint, ctx.filter_key, ctx.filtered_parquet, th_json)
    if not rec_intel.empty:
        st.markdown('<div class="section-title">Recruiter Performance</div>', unsafe_allow_html=True)
        st.dataframe(rec_intel.head(10), width="stretch", hide_index=True)

    client_intel = cached_client_intel(ctx.fingerprint, ctx.filter_key, ctx.filtered_parquet, th_json)
    if not client_intel.empty:
        st.markdown('<div class="section-title">Client Performance</div>', unsafe_allow_html=True)
        st.dataframe(client_intel.head(10), width="stretch", hide_index=True)
