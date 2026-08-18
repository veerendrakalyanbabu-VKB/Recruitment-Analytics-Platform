"""Recruiter workbench page."""

from __future__ import annotations

import json

import streamlit as st

from app.context import AppContext
from app.streamlit_cache import cached_group_count, cached_recruiter_intel


def render(ctx: AppContext) -> None:
    col = ctx.col
    th_json = json.dumps({
        "healthy_max": ctx.aging_thresholds.healthy_max,
        "watch_max": ctx.aging_thresholds.watch_max,
        "aging_max": ctx.aging_thresholds.aging_max,
    })

    st.markdown('<div class="section-title">Recruiter Workbench</div>', unsafe_allow_html=True)

    if col.get("recruiter"):
        rec = cached_group_count(
            ctx.fingerprint, ctx.filter_key, ctx.parquet_bytes, ctx.filters_json, col["recruiter"]
        )
        if not rec.empty:
            rec = rec.rename(columns={"group_key": col["recruiter"], "count": "Applications"})
            st.bar_chart(rec.set_index(col["recruiter"]), y="Applications", width="stretch", height=320)

        intel = cached_recruiter_intel(
            ctx.fingerprint, ctx.filter_key, ctx.filtered_parquet, th_json
        )
        if not intel.empty:
            st.dataframe(intel, width="stretch", hide_index=True)
    else:
        st.info("Recruiter column not available.")
