"""Candidate search, AI analyst, and NL queries."""

from __future__ import annotations

import io
import json

import pandas as pd
import streamlit as st

from app.context import AppContext
from app.utils.formatting import display_value
from app.streamlit_cache import cached_analyst_answer, cached_search_results


def render(ctx: AppContext) -> None:
    col = ctx.col
    filtered = ctx.filtered
    th_json = json.dumps({
        "healthy_max": ctx.aging_thresholds.healthy_max,
        "watch_max": ctx.aging_thresholds.watch_max,
        "aging_max": ctx.aging_thresholds.aging_max,
    })

    st.markdown('<div class="section-title">Candidate Search</div>', unsafe_allow_html=True)

    search = st.text_input(
        "Search candidate",
        placeholder="ID, name, recruiter, client, role, technology...",
        key="candidate_search_input",
    )

    if search.strip():
        search_parquet = cached_search_results(
            ctx.fingerprint, ctx.filter_key, search.strip(),
            ctx.parquet_bytes, ctx.filters_json, limit=250,
        )
        results = pd.read_parquet(io.BytesIO(search_parquet))
    else:
        results = filtered

    st.write(f"**{len(results):,}** candidate(s) found.")
    display_cols = [c for c in [
        col.get("id"), col.get("name"), col.get("recruiter"), col.get("client"),
        col.get("role"), col.get("technology"), col.get("interview"), col.get("offer"), col.get("joining"),
    ] if c]
    st.dataframe(results[display_cols].head(250), width="stretch", hide_index=True)

    if len(results) and col.get("id"):
        options = results[col["id"]].astype(str).tolist()
        selected_id = st.selectbox("Open candidate profile", options)
        profile = results[results[col["id"]].astype(str) == selected_id].iloc[0]
        profile_cols = [c for c in [
            col.get("id"), col.get("name"), col.get("application_date"), col.get("recruiter"),
            col.get("client"), col.get("role"), col.get("technology"), col.get("experience"),
            col.get("location"), col.get("source"), col.get("screening"), col.get("interview"),
            col.get("interview_date"), col.get("offer"), col.get("joining"), col.get("salary"),
        ] if c]
        profile_df = pd.DataFrame({
            "Field": [str(c) for c in profile_cols],
            "Value": [display_value(profile[c]) for c in profile_cols],
        })
        st.dataframe(profile_df, width="stretch", hide_index=True)

    st.divider()
    st.markdown('<div class="section-title">Recruitment AI Analyst</div>', unsafe_allow_html=True)
    st.caption("Deterministic analytics with optional LLM enhancement when configured.")

    question = st.text_input(
        "Ask a recruitment question",
        placeholder="Why are hires declining? Which source has the best joining rate?",
        key="ai_analyst_question",
    )
    if question.strip():
        resp = cached_analyst_answer(
            ctx.fingerprint, ctx.filter_key, ctx.filtered_parquet, question.strip(), th_json
        )
        st.markdown(f"**Answer:** {resp['answer']}")
        if resp.get("recommended_action"):
            st.info(f"Recommended action: {resp['recommended_action']}")
        if resp.get("evidence"):
            st.dataframe(pd.DataFrame(resp["evidence"]), width="stretch", hide_index=True)
        st.caption(f"Source: {resp.get('source', 'deterministic')}")
