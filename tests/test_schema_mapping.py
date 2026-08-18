"""Schema mapping tests."""

import pandas as pd

from app.data.normalization import map_columns, normalize_dataframe


def test_expanded_aliases_map():
    cols = ["Full Name", "TA Owner", "Interview Stage", "CTC", "Job_Role"]
    mapping, unmapped, low_conf = map_columns(cols)
    assert mapping.get("Full Name") == "candidate_name"
    assert mapping.get("TA Owner") == "recruiter"
    assert mapping.get("Interview Stage") == "interview_status"
    assert mapping.get("CTC") == "salary_lpa"
    assert mapping.get("Job_Role") == "role"


def test_status_result_preserved():
    raw = pd.DataFrame({
        "Interview_Status": ["Completed"],
        "Interview_Result": ["Selected"],
    })
    data, mapping, _, _ = normalize_dataframe(raw)
    assert "interview_status" in data.columns
    assert "interview_result" in data.columns
    assert data.loc[0, "interview_status"] == "Completed"
    assert data.loc[0, "interview_result"] == "Selected"


def test_missing_optional_columns():
    raw = pd.DataFrame({
        "Candidate_ID": ["1"],
        "Interview_Status": ["Completed"],
        "Interview_Result": ["Selected"],
    })
    data, mapping, unmapped, _ = normalize_dataframe(raw)
    assert len(data) == 1
    assert "candidate_id" in data.columns
