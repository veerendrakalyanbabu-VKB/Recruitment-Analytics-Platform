"""Insight engine tests."""

import pandas as pd

from app.analytics.kpis import compute_kpis
from app.data.normalization import normalize_dataframe
from app.intelligence.insight_engine import generate_insights, Severity


def test_insights_have_evidence():
    raw = pd.read_csv(
        __import__("pathlib").Path(__file__).resolve().parents[1]
        / "sample_data" / "recruitment_dataset_10000.csv"
    )
    data, _, _, _ = normalize_dataframe(raw)
    kpis = compute_kpis(data)
    insights = generate_insights(data, kpis)
    assert len(insights) > 0
    for insight in insights:
        assert insight.title
        assert insight.metric
        assert insight.recommended_action or insight.reason
        assert isinstance(insight.severity, Severity)
