"""Data quality and normalization edge cases."""

import pandas as pd

from app.data.normalization import clean_currency_numeric, normalize_dataframe
from app.data.profiling import profile_dataset
from app.data.validation import validate_recruitment_data


def test_currency_salary_normalization():
    series = pd.Series(["₹12.5 LPA", "$15,000", "18"])
    cleaned = clean_currency_numeric(series)
    assert cleaned.iloc[0] == 12.5
    assert cleaned.iloc[2] == 18.0


def test_duplicate_rows_detected():
    raw = pd.DataFrame({
        "candidate_id": ["1", "1"],
        "interview_status": ["Completed", "Completed"],
        "interview_result": ["Selected", "Selected"],
    })
    data, mapping, _, _ = normalize_dataframe(raw)
    validation = validate_recruitment_data(data, mapping)
    assert validation["duplicate_rows"] == 1


def test_empty_dataset_raises():
    try:
        normalize_dataframe(pd.DataFrame())
        assert False, "expected ValueError"
    except ValueError:
        pass


def test_health_score_range():
    raw = pd.DataFrame({
        "candidate_id": ["1", "2"],
        "interview_status": ["Completed", "Completed"],
        "interview_result": ["Selected", "Rejected"],
    })
    data, mapping, _, _ = normalize_dataframe(raw)
    validation = validate_recruitment_data(data, mapping)
    profile = profile_dataset(data, validation)
    assert 0 <= profile.health_score <= 100
