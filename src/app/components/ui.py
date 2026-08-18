"""Reusable UI components."""

from __future__ import annotations

import streamlit as st

from app.intelligence.insight_engine import Insight


def kpi_card(title: str, value: str, description: str = "", tone: str = "info") -> None:
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-desc {tone}">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def hero(title: str, subtitle: str) -> None:
    st.markdown(
        f"""
        <div class="hero">
            <h1>{title}</h1>
            <p>{subtitle}</p>
        </div>
        """,
        unsafe_allow_html=True,
    )


def insight_card(insight: Insight) -> None:
    sev_class = f"insight-sev-{insight.severity.value.lower()}"
    st.markdown(
        f"""
        <div class="insight-card {sev_class}">
            <div style="font-size:11px;color:#94a3b8;font-weight:600;
            text-transform:uppercase;">{insight.severity.value} · {insight.insight_type.value}</div>
            <div style="font-size:15px;font-weight:700;color:#f8fafc;margin:6px 0;">
            {insight.title}</div>
            <div style="font-size:13px;color:#94a3b8;margin-bottom:6px;">{insight.reason}</div>
            <div style="font-size:12px;color:#64748b;">
            <strong>Action:</strong> {insight.recommended_action}</div>
            <div style="font-size:11px;color:#64748b;margin-top:6px;">
            Evidence: {"; ".join(insight.evidence)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def empty_state(message: str) -> None:
    st.info(message)
