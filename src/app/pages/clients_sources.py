"""Clients, sources, and roles intelligence."""

from __future__ import annotations

import json

import streamlit as st

from app.context import AppContext
from app.streamlit_cache import (
    cached_client_intel,
    cached_group_count,
    cached_role_intel,
    cached_source_intel,
)


def render(ctx: AppContext) -> None:
    col = ctx.col
    th_json = json.dumps({
        "healthy_max": ctx.aging_thresholds.healthy_max,
        "watch_max": ctx.aging_thresholds.watch_max,
        "aging_max": ctx.aging_thresholds.aging_max,
    })

    st.markdown('<div class="section-title">Clients & Sources</div>', unsafe_allow_html=True)

    if col.get("client"):
        st.subheader("Client Intelligence")
        intel = cached_client_intel(ctx.fingerprint, ctx.filter_key, ctx.filtered_parquet, th_json)
        if not intel.empty:
            st.dataframe(intel, width="stretch", hide_index=True)
        client = cached_group_count(
            ctx.fingerprint, ctx.filter_key, ctx.parquet_bytes, ctx.filters_json, col["client"]
        )
        if not client.empty:
            client = client.rename(columns={"group_key": col["client"], "count": "Applications"})
            st.bar_chart(client.set_index(col["client"]), y="Applications", height=280)

    if col.get("source"):
        st.subheader("Source Intelligence")
        sint = cached_source_intel(ctx.fingerprint, ctx.filter_key, ctx.filtered_parquet)
        if not sint.empty:
            st.dataframe(sint, width="stretch", hide_index=True)

    if col.get("role"):
        st.subheader("Role Intelligence")
        rint = cached_role_intel(ctx.fingerprint, ctx.filter_key, ctx.filtered_parquet, th_json)
        if not rint.empty:
            st.dataframe(rint, width="stretch", hide_index=True)
