"""AI recruitment analyst with deterministic fallback."""

from __future__ import annotations

import os
from typing import Any

import pandas as pd

from app.analytics.aging import aging_summary, AgingThresholds
from app.analytics.clients import client_intelligence
from app.analytics.forecasting import target_hire_gap
from app.analytics.funnel import funnel_conversion_rates
from app.analytics.kpis import build_col_map, compute_kpis, RecruitmentKPIs
from app.analytics.recruiters import recruiter_intelligence
from app.analytics.roles import role_intelligence
from app.analytics.sources import source_intelligence, best_quality_source
from app.analytics.comparisons import period_comparisons
from app.intelligence.evidence import AnalystResponse, Evidence
from app.intelligence.nl_query import parse_intent, QueryIntent


def _get_llm_key() -> str | None:
    try:
        import streamlit as st
        key = st.secrets.get("OPENAI_API_KEY") or os.environ.get("OPENAI_API_KEY")
        return key if key else None
    except Exception:
        return os.environ.get("OPENAI_API_KEY")


def answer_question(
    question: str,
    df: pd.DataFrame,
    kpis: RecruitmentKPIs,
    col_map: dict[str, str | None] | None = None,
    thresholds: AgingThresholds | None = None,
) -> AnalystResponse:
    if col_map is None:
        col_map = build_col_map(df)
    intent = parse_intent(question)
    response = _deterministic_answer(intent, df, kpis, col_map, thresholds)
    llm_key = _get_llm_key()
    if llm_key and response.source == "deterministic":
        try:
            enhanced = _llm_enhance(question, response, llm_key)
            if enhanced:
                return enhanced
        except Exception:
            pass
    return response


def _deterministic_answer(
    intent: QueryIntent,
    df: pd.DataFrame,
    kpis: RecruitmentKPIs,
    col_map: dict[str, str | None],
    thresholds: AgingThresholds | None,
) -> AnalystResponse:
    date_col = col_map.get("application_date")

    if intent.intent == "declining_hires":
        comps = period_comparisons(df, date_col, col_map)
        joined_comp = next((c for c in comps if c.metric == "Joined"), None)
        ev: list[Evidence] = []
        if joined_comp:
            ev.append(Evidence("Joined (current)", joined_comp.current, joined_comp.previous,
                                joined_comp.percent_change))
        answer = (
            f"Current joined count is {kpis.joined:,}."
            + (f" Prior period comparison: {joined_comp.percent_change:.1f}% change."
               if joined_comp and joined_comp.percent_change is not None else "")
        )
        return AnalystResponse(
            question=intent.raw_query,
            answer=answer,
            evidence=ev,
            metrics={"joined": kpis.joined},
            recommended_action="Review funnel stages with largest conversion drops.",
        )

    if intent.intent == "bottleneck":
        rates = funnel_conversion_rates(kpis)
        weakest = rates.loc[rates["Rate %"].idxmin()]
        return AnalystResponse(
            question=intent.raw_query,
            answer=f"The biggest funnel bottleneck is {weakest['Conversion']} at {weakest['Rate %']:.1f}%.",
            evidence=[Evidence("bottleneck", weakest["Conversion"], detail=f"{weakest['Rate %']:.1f}%")],
            recommended_action="Focus operational effort on the weakest conversion stage.",
        )

    if intent.intent == "recruiter_ranking":
        intel = recruiter_intelligence(df, col_map, date_col, thresholds)
        if intel.empty:
            return AnalystResponse(intent.raw_query, "No recruiter data available.", source="deterministic")
        rcol = intel.columns[0]
        if intent.ranking == "worst":
            row = intel.iloc[-1]
            answer = f"{row[rcol]} has the lowest efficiency score ({row['efficiency_score']:.1f})."
        elif intent.ranking == "high_vol_low_sel":
            intel["gap"] = intel["applications"] - intel["interview_selection_%"]
            row = intel.sort_values("gap", ascending=False).iloc[0]
            answer = f"{row[rcol]} has high volume ({int(row['applications'])}) with selection {row['interview_selection_%']:.1f}%."
        else:
            row = intel.iloc[0]
            answer = f"{row[rcol]} leads with efficiency score {row['efficiency_score']:.1f}."
        return AnalystResponse(
            question=intent.raw_query,
            answer=answer,
            evidence=[Evidence("recruiter", str(row[rcol]), detail=f"score {row['efficiency_score']:.1f}")],
            entities=[str(row[rcol])],
            recommended_action="Review recruiter pipeline aging and stage conversion.",
        )

    if intent.intent == "client_ranking":
        intel = client_intelligence(df, col_map, date_col, thresholds)
        if intel.empty:
            return AnalystResponse(intent.raw_query, "No client data available.", source="deterministic")
        ccol = intel.columns[0]
        row = intel.iloc[-1] if intent.ranking == "worst" else intel.iloc[0]
        label = "hardest" if intent.ranking == "worst" else "strongest"
        return AnalystResponse(
            question=intent.raw_query,
            answer=f"{row[ccol]} is the {label} client (health score {row['client_health_score']:.1f}).",
            evidence=[Evidence("client_health", row["client_health_score"], entity=str(row[ccol]))],
            entities=[str(row[ccol])],
            recommended_action="Align client expectations and screening calibration.",
        )

    if intent.intent == "source_ranking":
        intel = source_intelligence(df, col_map)
        if intel.empty:
            return AnalystResponse(intent.raw_query, "No source data available.", source="deterministic")
        scol = intel.columns[0]
        if intent.ranking == "volume":
            row = intel.sort_values("applications", ascending=False).iloc[0]
            answer = f"{row[scol]} has highest volume ({int(row['applications'])} applications)."
        else:
            row = intel.sort_values("quality_score", ascending=False).iloc[0]
            answer = f"{row[scol]} has the best quality score ({row['quality_score']:.1f})."
        return AnalystResponse(
            question=intent.raw_query,
            answer=answer,
            evidence=[Evidence("source", str(row[scol]))],
            entities=[str(row[scol])],
            recommended_action="Balance volume and quality when allocating sourcing spend.",
        )

    if intent.intent == "role_ranking":
        intel = role_intelligence(df, col_map, date_col, thresholds)
        if intel.empty:
            return AnalystResponse(intent.raw_query, "No role data available.", source="deterministic")
        rcol = intel.columns[0]
        row = intel.iloc[0]
        return AnalystResponse(
            question=intent.raw_query,
            answer=f"{row[rcol]} is hardest to hire (difficulty {row['hiring_difficulty_score']:.1f}): {row['difficulty_reasons']}.",
            evidence=[Evidence("difficulty", row["hiring_difficulty_score"], entity=str(row[rcol]))],
            entities=[str(row[rcol])],
            recommended_action="Review role requirements, compensation, and pipeline aging.",
        )

    if intent.intent == "aging_query":
        aged = aging_summary(df, date_col, thresholds)
        if aged.empty:
            return AnalystResponse(intent.raw_query, "No date data for aging analysis.", source="deterministic")
        days = intent.aging_days or 14
        stuck = aged[aged["aging_days"] > days]
        return AnalystResponse(
            question=intent.raw_query,
            answer=f"{len(stuck):,} candidates are aging beyond {days} days.",
            evidence=[Evidence("stuck_candidates", len(stuck))],
            metrics={"threshold_days": days, "stuck_count": len(stuck)},
            recommended_action="Prioritize recruiter follow-up on aging candidates.",
        )

    if intent.intent == "forecast_target":
        target = intent.target_hires or 100
        gap = target_hire_gap(df, target, date_col, col_map)
        if not gap.sufficient_data:
            return AnalystResponse(intent.raw_query, gap.message, source="deterministic")
        return AnalystResponse(
            question=intent.raw_query,
            answer=(
                f"ESTIMATE: expected joins {gap.expected_low:.0f}–{gap.expected_high:.0f} "
                f"vs target {target}. Gap {gap.gap_low:.0f}–{gap.gap_high:.0f}. "
                f"Additional pipeline ~{gap.pipeline_required_low:,.0f}–{gap.pipeline_required_high:,.0f} applications."
            ),
            evidence=[
                Evidence("expected_joins_mid", gap.expected_mid),
                Evidence("gap_high", gap.gap_high),
            ],
            metrics={"target": target, "expected_mid": gap.expected_mid},
            recommended_action="Increase sourcing or improve conversion at bottleneck stage.",
        )

    return AnalystResponse(
        question=intent.raw_query,
        answer="I could not interpret that question. Try: 'Which recruiter is underperforming?' or 'Where is the biggest funnel bottleneck?'",
        source="deterministic",
    )


def _llm_enhance(question: str, base: AnalystResponse, api_key: str) -> AnalystResponse | None:
    """Optional LLM polish — never replaces metrics."""
    # Minimal implementation: skip external call in tests; structure ready for OpenAI
    return None
