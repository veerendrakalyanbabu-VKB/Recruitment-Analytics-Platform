"""KPI engine regression tests."""

from pathlib import Path

import pandas as pd

from app.analytics.kpis import compute_kpis
from app.config import CLEANED_FILE, RAW_FILE, SAMPLE_10K
from app.data.loader import load_demo_dataframe
from app.data.normalization import normalize_dataframe

ROOT = Path(__file__).resolve().parents[1]


def _load_demo_normalized():
    raw = load_demo_dataframe()
    data, mapping, unmapped, low_conf = normalize_dataframe(raw)
    return data


def _load_10k_normalized():
    raw = pd.read_csv(SAMPLE_10K)
    data, _, _, _ = normalize_dataframe(raw)
    return data


def test_demo_dataset_kpis():
    data = _load_demo_normalized()
    k = compute_kpis(data)
    assert k.total == 1000
    assert k.screening_selected == 734
    assert k.interviews_completed == 655
    assert k.interview_selected == 423
    assert k.joined == 293
    assert k.interview_selection_rate == 64.58
    assert k.offer_acceptance_rate == 82.74


def test_10k_dataset_kpis():
    data = _load_10k_normalized()
    k = compute_kpis(data)
    assert k.total == 10_000
    assert k.screening_selected == 7_457
    assert k.interviews_completed == 6_689
    assert k.interview_selected == 4_351
    assert k.offers_accepted == 3_602
    assert k.joined == 3_262
    assert k.interview_selection_rate == 65.05
    assert k.offer_acceptance_rate == 82.79
    assert round(k.joining_rate, 2) == 90.56


def test_interview_status_result_regression():
    """Completed status + Selected result must count as completed interview."""
    raw = pd.DataFrame({
        "candidate_id": ["C1", "C2"],
        "interview_status": ["Completed", "Completed"],
        "interview_result": ["Selected", "Rejected"],
    })
    data, _, _, _ = normalize_dataframe(raw)
    k = compute_kpis(data)
    assert k.interviews_completed == 2
    assert k.interview_selected == 1
    assert k.interview_rejected == 1
