import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from data_loader import normalize_dataframe


def _norm(series):
    return series.fillna("").astype(str).str.strip().str.lower()


def test_status_and_result_columns_are_preserved_separately():
    raw = pd.DataFrame(
        {
            "Candidate_ID": ["C1", "C2", "C3"],
            "Interview_Status": ["Completed", "Completed", "Not Scheduled"],
            "Interview_Result": ["Selected", "Rejected", ""],
            "Offer_Status": ["Accepted", "Rejected", "No Offer"],
            "Joining_Status": ["Joined", "Not Joined", "Not Applicable"],
        }
    )

    normalized, mapping, _ = normalize_dataframe(raw)

    assert "interview_status" in normalized.columns
    assert "interview_result" in normalized.columns
    assert normalized.loc[0, "interview_status"] == "Completed"
    assert normalized.loc[0, "interview_result"] == "Selected"
    assert mapping["Interview_Result"] == "interview_result"


def test_uploaded_dataset_produces_non_zero_interview_funnel():
    raw = pd.read_csv(ROOT / "sample_data" / "recruitment_dataset_10000.csv")
    normalized, _, _ = normalize_dataframe(raw)

    outcome = _norm(normalized["interview_result"])
    selected = outcome.isin(
        {"selected", "interview selected", "passed", "selected for offer", "pass", "recommended"}
    ).sum()
    rejected = outcome.isin(
        {"rejected", "declined", "failed", "not selected", "unsuccessful"}
    ).sum()

    assert len(normalized) == 10_000
    assert selected > 0
    assert rejected > 0
    assert selected + rejected > 0


def test_10k_sample_has_consistent_funnel_math():
    raw = pd.read_csv(ROOT / "sample_data" / "recruitment_dataset_10000.csv")
    interview_result = _norm(raw["Interview_Result"])
    offer_status = _norm(raw["Offer_Status"])
    joining_status = _norm(raw["Joining_Status"])

    interview_selected = interview_result.isin(
        {"selected", "interview selected", "passed", "selected for offer", "pass", "recommended"}
    ).sum()
    interview_rejected = interview_result.isin(
        {"rejected", "declined", "failed", "not selected", "unsuccessful"}
    ).sum()
    interviews_completed = interview_selected + interview_rejected

    offers_accepted = offer_status.isin(
        {"accepted", "offer accepted", "accept", "accepted offer"}
    ).sum()
    offers_declined = offer_status.isin(
        {"declined", "rejected", "offer declined", "withdrawn", "cancelled"}
    ).sum()

    candidates_joined = joining_status.isin(
        {"joined", "joining confirmed", "onboarded", "onboarded successfully"}
    ).sum()

    assert len(raw) == 10_000
    assert interviews_completed == 6_689
    assert interview_selected == 4_351
    assert offers_accepted == 3_602
    assert candidates_joined == 3_262
    assert round(interview_selected / interviews_completed * 100, 2) == 65.05
    assert round(offers_accepted / (offers_accepted + offers_declined) * 100, 2) == 82.79
