"""Streamlit caching layer — dataset ingestion and analytics."""

from __future__ import annotations

import io
from typing import Any

import pandas as pd
import streamlit as st

from app.analytics.kpis import build_col_map, compute_kpis, RecruitmentKPIs
from app.analytics.store import (
    AnalyticsStore,
    build_filter_dict,
    search_columns,
    store_from_parquet,
)
from app.config import CLEANED_FILE, RAW_FILE
from app.data.fingerprint import fingerprint_from_path
from app.data.pipeline import (
    build_filter_key,
    cache_dict_to_dataframe,
    ingest_bytes,
    prepared_to_cache_dict,
    profile_from_cache,
)
from app.data.profiling import DataProfile
from app.intelligence.insight_engine import generate_insights, recruiter_scorecards
from app.analytics.trends import compute_trends
from app.analytics.aging import AgingThresholds
from app.intelligence.executive import build_executive_package
from app.analytics.recruiters import recruiter_intelligence
from app.analytics.clients import client_intelligence
from app.analytics.sources import source_intelligence
from app.analytics.roles import role_intelligence
from app.analytics.forecasting import forecast_joins, target_hire_gap
from app.intelligence.ai_analyst import answer_question
from app.utils.perf import timed


@st.cache_data(show_spinner=False)
def cached_ingest(fingerprint: str, raw_bytes: bytes, source_name: str) -> dict[str, Any]:
    """Parse, normalize, validate, profile — once per fingerprint."""
    prepared = ingest_bytes(raw_bytes, source_name=source_name)
    return prepared_to_cache_dict(prepared)


@st.cache_data(show_spinner=False)
def cached_demo_bundle() -> dict[str, Any]:
    path = CLEANED_FILE if CLEANED_FILE.exists() else RAW_FILE
    raw_bytes = path.read_bytes()
    fp = fingerprint_from_path(path)
    return cached_ingest(fp, raw_bytes, f"demo:{path.name}")


@st.cache_resource(show_spinner=False)
def cached_analytics_store(fingerprint: str, parquet_bytes: bytes) -> AnalyticsStore:
    return store_from_parquet(fingerprint, parquet_bytes)


@st.cache_data(show_spinner=False)
def cached_filter_options(fingerprint: str, parquet_bytes: bytes, column: str) -> list[str]:
    store = cached_analytics_store(fingerprint, parquet_bytes)
    return store.distinct_values(column)


@st.cache_data(show_spinner=False)
def cached_filtered_frame(
    fingerprint: str,
    filter_key: str,
    parquet_bytes: bytes,
    filters_json: str,
) -> bytes:
    """Return filtered subset as parquet bytes — keyed by filter_key, not re-ingest."""
    import json

    store = cached_analytics_store(fingerprint, parquet_bytes)
    filters = json.loads(filters_json)
    timings: dict[str, float] = {}
    df = store.query_filtered(filters=filters, timings=timings)
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    return buf.getvalue()


@st.cache_data(show_spinner=False)
def cached_search_results(
    fingerprint: str,
    filter_key: str,
    search_text: str,
    parquet_bytes: bytes,
    filters_json: str,
    limit: int = 250,
) -> bytes:
    import json

    store = cached_analytics_store(fingerprint, parquet_bytes)
    filters = json.loads(filters_json)
    col_map = store.col_map
    search_cols = search_columns(col_map)
    timings: dict[str, float] = {}
    df = store.query_filtered(
        filters=filters,
        search_text=search_text,
        search_cols=search_cols,
        limit=limit,
        timings=timings,
    )
    buf = io.BytesIO()
    df.to_parquet(buf, index=False)
    return buf.getvalue()


@st.cache_data(show_spinner=False)
def cached_group_count(
    fingerprint: str,
    filter_key: str,
    parquet_bytes: bytes,
    filters_json: str,
    group_column: str,
) -> pd.DataFrame:
    import json

    store = cached_analytics_store(fingerprint, parquet_bytes)
    filters = json.loads(filters_json)
    return store.group_count(group_column, filters=filters)


@st.cache_data(show_spinner=False)
def cached_kpis(
    fingerprint: str,
    filter_key: str,
    filtered_parquet_bytes: bytes,
) -> dict[str, Any]:
    df = pd.read_parquet(io.BytesIO(filtered_parquet_bytes))
    col = build_col_map(df)
    kpis = compute_kpis(df, col)
    return {
        "total": kpis.total,
        "screening_selected": kpis.screening_selected,
        "interviews_completed": kpis.interviews_completed,
        "interview_selected": kpis.interview_selected,
        "interview_rejected": kpis.interview_rejected,
        "interview_no_show": kpis.interview_no_show,
        "interview_not_scheduled": kpis.interview_not_scheduled,
        "offers_accepted": kpis.offers_accepted,
        "offers_declined": kpis.offers_declined,
        "offers_made": kpis.offers_made,
        "joined": kpis.joined,
        "screening_rate": kpis.screening_rate,
        "interview_selection_rate": kpis.interview_selection_rate,
        "offer_acceptance_rate": kpis.offer_acceptance_rate,
        "joining_rate": kpis.joining_rate,
        "avg_salary": kpis.avg_salary,
        "avg_time_to_hire": kpis.avg_time_to_hire,
    }


def kpis_dict_to_dataclass(d: dict[str, Any]) -> RecruitmentKPIs:
    return RecruitmentKPIs(
        total=d["total"],
        screening_selected=d["screening_selected"],
        interviews_completed=d["interviews_completed"],
        interview_selected=d["interview_selected"],
        interview_rejected=d["interview_rejected"],
        interview_no_show=d["interview_no_show"],
        interview_not_scheduled=d["interview_not_scheduled"],
        offers_accepted=d["offers_accepted"],
        offers_declined=d["offers_declined"],
        offers_made=d["offers_made"],
        joined=d["joined"],
        screening_rate=d["screening_rate"],
        interview_selection_rate=d["interview_selection_rate"],
        offer_acceptance_rate=d["offer_acceptance_rate"],
        joining_rate=d["joining_rate"],
        avg_salary=d["avg_salary"],
        avg_time_to_hire=d["avg_time_to_hire"],
    )


@st.cache_data(show_spinner=False)
def cached_insights(
    fingerprint: str,
    filter_key: str,
    filtered_parquet_bytes: bytes,
) -> list[dict[str, Any]]:
    df = pd.read_parquet(io.BytesIO(filtered_parquet_bytes))
    col = build_col_map(df)
    kpis = compute_kpis(df, col)
    insights = generate_insights(df, kpis, col)
    return [
        {
            "title": i.title,
            "insight_type": i.insight_type.value,
            "severity": i.severity.value,
            "metric": i.metric,
            "reason": i.reason,
            "recommended_action": i.recommended_action,
            "evidence": i.evidence,
        }
        for i in insights
    ]


@st.cache_data(show_spinner=False)
def cached_recruiter_scorecards(
    fingerprint: str,
    filter_key: str,
    filtered_parquet_bytes: bytes,
) -> pd.DataFrame:
    df = pd.read_parquet(io.BytesIO(filtered_parquet_bytes))
    col = build_col_map(df)
    return recruiter_scorecards(df, col)


@st.cache_data(show_spinner=False)
def cached_executive_package(
    fingerprint: str,
    filter_key: str,
    filtered_parquet_bytes: bytes,
    health_score: float,
    thresholds_json: str,
) -> dict[str, Any]:
    import json
    from app.data.profiling import DataProfile

    df = pd.read_parquet(io.BytesIO(filtered_parquet_bytes))
    col = build_col_map(df)
    kpis = compute_kpis(df, col)
    th = AgingThresholds(**json.loads(thresholds_json))
    profile = DataProfile(
        health_score=health_score, row_count=len(df), column_count=len(df.columns),
        duplicate_rows=0,
    )
    pkg = build_executive_package(df, kpis, col, profile, th)
    health = pkg["health"]
    return {
        "health_score": health.score,
        "health_components": health.components,
        "comparisons": [
            {
                "metric": c.metric, "current": c.current, "previous": c.previous,
                "absolute_change": c.absolute_change, "percent_change": c.percent_change,
                "note": c.note,
            }
            for c in pkg["comparisons"]
        ],
        "findings": [
            {"category": f.category, "title": f.title, "detail": f.detail, "severity": f.severity}
            for f in pkg["findings"]
        ],
        "funnel_rates": pkg["funnel_rates"].to_dict(orient="records"),
    }


@st.cache_data(show_spinner=False)
def cached_trends(
    fingerprint: str,
    filter_key: str,
    filtered_parquet_bytes: bytes,
    date_col: str,
    freq: str = "M",
) -> pd.DataFrame:
    df = pd.read_parquet(io.BytesIO(filtered_parquet_bytes))
    if not date_col or date_col not in df.columns:
        return pd.DataFrame()
    return compute_trends(df, date_col, freq=freq)


@st.cache_data(show_spinner=False)
def cached_recruiter_intel(
    fingerprint: str,
    filter_key: str,
    filtered_parquet_bytes: bytes,
    thresholds_json: str,
) -> pd.DataFrame:
    import json
    df = pd.read_parquet(io.BytesIO(filtered_parquet_bytes))
    col = build_col_map(df)
    th = AgingThresholds(**json.loads(thresholds_json))
    return recruiter_intelligence(df, col, col.get("application_date"), th)


@st.cache_data(show_spinner=False)
def cached_client_intel(
    fingerprint: str,
    filter_key: str,
    filtered_parquet_bytes: bytes,
    thresholds_json: str,
) -> pd.DataFrame:
    import json
    df = pd.read_parquet(io.BytesIO(filtered_parquet_bytes))
    col = build_col_map(df)
    th = AgingThresholds(**json.loads(thresholds_json))
    return client_intelligence(df, col, col.get("application_date"), th)


@st.cache_data(show_spinner=False)
def cached_source_intel(
    fingerprint: str,
    filter_key: str,
    filtered_parquet_bytes: bytes,
) -> pd.DataFrame:
    df = pd.read_parquet(io.BytesIO(filtered_parquet_bytes))
    return source_intelligence(df, build_col_map(df))


@st.cache_data(show_spinner=False)
def cached_role_intel(
    fingerprint: str,
    filter_key: str,
    filtered_parquet_bytes: bytes,
    thresholds_json: str,
) -> pd.DataFrame:
    import json
    df = pd.read_parquet(io.BytesIO(filtered_parquet_bytes))
    col = build_col_map(df)
    th = AgingThresholds(**json.loads(thresholds_json))
    return role_intelligence(df, col, col.get("application_date"), th)


@st.cache_data(show_spinner=False)
def cached_analyst_answer(
    fingerprint: str,
    filter_key: str,
    filtered_parquet_bytes: bytes,
    question: str,
    thresholds_json: str,
) -> dict[str, Any]:
    import json
    df = pd.read_parquet(io.BytesIO(filtered_parquet_bytes))
    col = build_col_map(df)
    kpis = compute_kpis(df, col)
    th = AgingThresholds(**json.loads(thresholds_json))
    resp = answer_question(question, df, kpis, col, th)
    return {
        "question": resp.question,
        "answer": resp.answer,
        "recommended_action": resp.recommended_action,
        "entities": resp.entities,
        "metrics": resp.metrics,
        "evidence": [
            {"metric": e.metric, "value": e.value, "detail": e.detail, "entity": e.entity}
            for e in resp.evidence
        ],
        "source": resp.source,
    }


def load_upload_bundle(uploaded_bytes: bytes, source_name: str) -> tuple[dict[str, Any], pd.DataFrame, DataProfile]:
    from app.data.fingerprint import compute_fingerprint

    fp = compute_fingerprint(uploaded_bytes, source_name=source_name)
    bundle = cached_ingest(fp, uploaded_bytes, source_name)
    df = cache_dict_to_dataframe(bundle)
    profile = profile_from_cache(bundle)
    return bundle, df, profile


def resolve_filters(
    col_map: dict[str, str | None],
    recruiters: list[str],
    clients: list[str],
    roles: list[str],
    sources: list[str],
    technologies: list[str],
    all_options: dict[str, list[str]] | None = None,
) -> tuple[str, str]:
    import json
    from app.state import selection_for_query

    all_options = all_options or {}
    selections = {
        "recruiter": selection_for_query(recruiters, all_options.get("recruiter", recruiters)),
        "client": selection_for_query(clients, all_options.get("client", clients)),
        "role": selection_for_query(roles, all_options.get("role", roles)),
        "source": selection_for_query(sources, all_options.get("source", sources)),
        "technology": selection_for_query(
            technologies, all_options.get("technology", technologies)
        ),
    }
    filter_dict = build_filter_dict(col_map, selections)
    filter_key = build_filter_key(selections)
    filters_json = json.dumps(filter_dict, sort_keys=True)
    return filter_key, filters_json
