"""Phases 3-8 comprehensive tests."""

from pathlib import Path

import pandas as pd
import pytest

from app.analytics.aging import AgingThresholds, aging_bucket, aging_summary
from app.analytics.clients import client_intelligence
from app.analytics.comparisons import compare_values, safe_pct_change
from app.analytics.forecasting import forecast_joins, target_hire_gap
from app.analytics.kpis import compute_kpis
from app.analytics.recruiters import recruiter_intelligence
from app.analytics.roles import role_intelligence
from app.analytics.sources import source_intelligence
from app.analytics.trends import compute_trends
from app.data.fingerprint import compute_fingerprint
from app.data.normalization import normalize_dataframe
from app.data.pipeline import ingest_bytes
from app.intelligence.ai_analyst import answer_question
from app.intelligence.executive import compute_health_score
from app.intelligence.nl_query import parse_intent
from app.data.profiling import DataProfile

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_10K = ROOT / "sample_data" / "recruitment_dataset_10000.csv"


def _load_10k():
    raw = SAMPLE_10K.read_bytes()
    return ingest_bytes(raw, "10k.csv").data


def test_safe_pct_change_zero_denominator():
    assert safe_pct_change(10, 0) is None


def test_period_comparison():
    c = compare_values("Joined", 100, 80)
    assert c.percent_change == 25.0


def test_trend_calculation():
    df = _load_10k()
    trends = compute_trends(df, "application_date", freq="M")
    assert not trends.empty
    assert "Joined" in trends.columns


def test_recruiter_efficiency_score_range():
    df = _load_10k()
    intel = recruiter_intelligence(df)
    assert not intel.empty
    assert intel["efficiency_score"].between(0, 100).all()


def test_client_health_score():
    df = _load_10k()
    intel = client_intelligence(df)
    assert "client_health_score" in intel.columns


def test_source_quality_ranking():
    df = _load_10k()
    intel = source_intelligence(df)
    assert "quality_score" in intel.columns


def test_role_difficulty():
    df = _load_10k()
    intel = role_intelligence(df)
    assert "hiring_difficulty_score" in intel.columns
    assert intel.iloc[0]["hiring_difficulty_score"] >= 0


def test_aging_thresholds():
    assert aging_bucket(5, AgingThresholds()) == "HEALTHY"
    assert aging_bucket(20, AgingThresholds()) == "AGING"
    assert aging_bucket(45, AgingThresholds()) == "CRITICAL"


def test_configurable_aging():
    th = AgingThresholds(healthy_max=3, watch_max=7, aging_max=14)
    assert aging_bucket(5, th) == "WATCH"


def test_forecast_sufficient_data():
    df = _load_10k()
    fc = forecast_joins(df, "application_date")
    assert fc.sufficient_data
    assert fc.estimate_mid > 0


def test_forecast_insufficient_data():
    tiny = pd.DataFrame({
        "application_date": ["2024-01-01"],
        "interview_result": ["Selected"],
        "interview_status": ["Completed"],
    })
    tiny, _, _, _ = normalize_dataframe(tiny)
    fc = forecast_joins(tiny, "application_date")
    assert not fc.sufficient_data


def test_forecast_target_gap():
    df = _load_10k()
    gap = target_hire_gap(df, 500, "application_date")
    assert gap.label == "ESTIMATE"


def test_nl_intent_recruiter():
    intent = parse_intent("Which recruiter is underperforming?")
    assert intent.intent == "recruiter_ranking"


def test_nl_intent_invalid():
    intent = parse_intent("hello random question xyz")
    assert intent.intent == "unknown"


def test_ai_analyst_fallback_no_api():
    df = _load_10k()
    kpis = compute_kpis(df)
    resp = answer_question("Where is the biggest funnel bottleneck?", df, kpis)
    assert resp.answer
    assert resp.source == "deterministic"


def test_fingerprint_stability():
    raw = b"test,data\n1,a"
    assert compute_fingerprint(raw, "a") == compute_fingerprint(raw, "a")
    assert compute_fingerprint(raw, "b") != compute_fingerprint(raw, "a")


def test_executive_health_score():
    df = _load_10k()
    kpis = compute_kpis(df)
    profile = DataProfile(health_score=90, row_count=len(df), column_count=len(df.columns), duplicate_rows=0)
    aged = aging_summary(df, "application_date")
    health = compute_health_score(kpis, profile, aged)
    assert 0 <= health.score <= 100


def test_status_result_regression_engine():
    raw = pd.DataFrame({
        "candidate_id": ["C1"],
        "interview_status": ["Completed"],
        "interview_result": ["Selected"],
    })
    data, _, _, _ = normalize_dataframe(raw)
    k = compute_kpis(data)
    assert k.interviews_completed == 1
    assert k.interview_selected == 1
