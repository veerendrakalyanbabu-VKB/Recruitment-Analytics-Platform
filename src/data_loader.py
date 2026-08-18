from __future__ import annotations

import re
from typing import Any

import pandas as pd


CANONICAL_ALIASES: dict[str, list[str]] = {
    "candidate_id": ["candidate_id", "candidate id", "candidateid", "applicant_id", "applicant id", "id"],
    "candidate_name": ["candidate_name", "candidate name", "candidate", "applicant_name", "applicant name", "name"],
    "application_date": ["application_date", "application date", "applied_date", "applied date", "applied_on", "applied on", "date_applied", "date applied"],
    "recruiter": ["recruiter", "recruiter_name", "recruiter name", "talent_acquisition"],
    "client": ["client", "client_name", "client name", "customer", "account"],
    "role": ["role", "job_role", "job role", "position", "job_title", "job title", "designation"],
    "technology": ["technology", "tech", "primary_technology", "primary technology", "skill", "skills"],
    "experience_years": ["experience_years", "experience years", "experience", "years_experience", "years of experience"],
    "location": ["location", "city", "candidate_location", "candidate location"],
    "source": ["source", "application_source", "application source", "candidate_source", "candidate source", "channel"],
    "screening_status": ["screening_status", "screening status", "candidate_status", "candidate status", "application_status", "application status", "recruitment_status", "recruitment status", "current_status", "current status", "screening"],
    "screening_result": ["screening_result", "screening result", "screening_outcome", "screening outcome"],
    "interview_status": ["interview_status", "interview status", "interview"],
    "interview_result": ["interview_result", "interview result", "interview_outcome", "interview outcome"],
    "interview_date": ["interview_date", "interview date", "interview_completed_date", "interview completed date"],
    "offer_status": ["offer_status", "offer status", "offer"],
    "offer_result": ["offer_result", "offer result", "offer_outcome", "offer outcome"],
    "offer_date": ["offer_date", "offer date"],
    "joining_status": ["joining_status", "joining status", "joining", "onboarding_status", "onboarding status"],
    "joining_result": ["joining_result", "joining result", "joining_outcome", "joining outcome"],
    "joining_date": ["joining_date", "joining date", "start_date", "start date", "date_joined"],
    "salary_lpa": ["salary_lpa", "salary lpa", "salary", "offered_salary", "offered salary", "annual_salary", "annual salary"],
    "rejection_reason": ["rejection_reason", "rejection reason", "rejection", "reason_for_rejection", "reason for rejection"],
    "time_to_hire_days": ["time_to_hire_days", "time to hire days", "time_to_hire", "time to hire", "days_to_hire", "days to hire"],
}

DISPLAY_NAMES = {
    "candidate_id": "Candidate ID",
    "candidate_name": "Candidate Name",
    "application_date": "Application Date",
    "recruiter": "Recruiter",
    "client": "Client",
    "role": "Role",
    "technology": "Technology",
    "experience_years": "Experience",
    "location": "Location",
    "source": "Source",
    "screening_status": "Screening Status",
    "screening_result": "Screening Result",
    "interview_status": "Interview Status",
    "interview_result": "Interview Result",
    "interview_date": "Interview Date",
    "offer_status": "Offer Status",
    "offer_result": "Offer Result",
    "offer_date": "Offer Date",
    "joining_status": "Joining Status",
    "joining_result": "Joining Result",
    "joining_date": "Joining Date",
    "salary_lpa": "Salary",
    "rejection_reason": "Rejection Reason",
    "time_to_hire_days": "Time to Hire",
}


def _normalize_name(value: Any) -> str:
    text = str(value).strip().lower()
    text = re.sub(r"[^a-z0-9]+", "_", text)
    return re.sub(r"_+", "_", text).strip("_")


def _alias_map() -> dict[str, str]:
    result: dict[str, str] = {}
    for canonical, aliases in CANONICAL_ALIASES.items():
        for alias in aliases:
            result[_normalize_name(alias)] = canonical
    return result


def normalize_dataframe(df: pd.DataFrame) -> tuple[pd.DataFrame, dict[str, str], list[str]]:
    """Clean a recruitment CSV and map recognized columns to canonical names."""
    if df is None:
        raise ValueError("No dataset was supplied.")

    data = df.copy()
    data = data.loc[:, ~data.columns.astype(str).str.startswith("Unnamed")]
    data.columns = [str(c).strip() for c in data.columns]

    if data.empty:
        raise ValueError("The uploaded CSV contains no rows.")

    if len(data.columns) == 0:
        raise ValueError("The uploaded CSV contains no columns.")

    aliases = _alias_map()
    mapping: dict[str, str] = {}
    used_canonicals: set[str] = set()

    for original in data.columns:
        normalized = _normalize_name(original)
        canonical = aliases.get(normalized)
        if canonical and canonical not in used_canonicals:
            mapping[original] = canonical
            used_canonicals.add(canonical)

    # Fuzzy fallback for common headers such as "Candidate ID Number".
    for original in data.columns:
        if original in mapping:
            continue
        n = _normalize_name(original)
        candidates = []
        for canonical, aliases_list in CANONICAL_ALIASES.items():
            if canonical in used_canonicals:
                continue
            for alias in aliases_list:
                a = _normalize_name(alias)
                if len(a) >= 5 and (n.startswith(a) or n.endswith(a) or a in n):
                    candidates.append(canonical)
                    break
        if len(candidates) == 1:
            mapping[original] = candidates[0]
            used_canonicals.add(candidates[0])

    rename = {original: canonical for original, canonical in mapping.items()}
    data = data.rename(columns=rename)

    # If a canonical column already existed alongside an alias, preserve the
    # first canonical column and avoid duplicate dataframe column names.
    data = data.loc[:, ~data.columns.duplicated(keep="first")]

    # Normalize dates/numbers without being overly destructive.
    for col in ["application_date", "interview_date", "offer_date", "joining_date"]:
        if col in data.columns:
            parsed = pd.to_datetime(data[col], errors="coerce")
            data[col] = parsed.dt.strftime("%Y-%m-%d").where(parsed.notna(), data[col])

    for col in ["experience_years", "salary_lpa", "time_to_hire_days"]:
        if col in data.columns:
            data[col] = pd.to_numeric(data[col], errors="coerce")

    # Standardize missing values while retaining original text values.
    for col in data.columns:
        if data[col].dtype == "object":
            data[col] = data[col].replace(r"^\s*$", pd.NA, regex=True)

    return data, mapping, []


def validate_recruitment_data(
    data: pd.DataFrame,
    mapping: dict[str, str],
) -> dict[str, Any]:
    """Return actionable validation findings for an uploaded recruitment dataset."""
    recognized = [c for c in CANONICAL_ALIASES if c in data.columns]
    status_fields = [c for c in ["screening_status", "interview_status", "offer_status", "joining_status"] if c in data.columns]

    errors: list[str] = []
    warnings: list[str] = []

    if len(data) < 1:
        errors.append("The dataset contains no candidate records.")

    if not recognized:
        errors.append(
            "No recognizable recruitment columns were found. "
            "Use fields such as Candidate ID, Status, Interview Status, Offer Status, or Joining Status."
        )

    if "candidate_id" not in data.columns:
        warnings.append("Candidate ID was not detected. Candidate search/profile selection will be limited.")

    if not status_fields:
        warnings.append(
            "No recruitment status field was detected. Funnel and hiring-status KPIs will be limited."
        )

    duplicate_count = int(data.duplicated().sum())
    if duplicate_count:
        warnings.append(f"{duplicate_count:,} duplicate row(s) detected.")

    if "candidate_id" in data.columns:
        missing_ids = int(data["candidate_id"].isna().sum())
        if missing_ids:
            warnings.append(f"{missing_ids:,} record(s) have a missing Candidate ID.")

        duplicate_ids = int(data["candidate_id"].dropna().astype(str).duplicated().sum())
        if duplicate_ids:
            warnings.append(f"{duplicate_ids:,} duplicate Candidate ID value(s) detected.")

    for col in ["application_date", "interview_date", "offer_date", "joining_date"]:
        if col in data.columns:
            invalid = int(
                data[col].notna().sum()
                - pd.to_datetime(data[col], errors="coerce").notna().sum()
            )
            if invalid:
                warnings.append(f"{invalid:,} invalid {DISPLAY_NAMES[col].lower()} value(s) detected.")

    if "salary_lpa" in data.columns:
        invalid_salary = int(
            data["salary_lpa"].notna().sum()
            - pd.to_numeric(data["salary_lpa"], errors="coerce").notna().sum()
        )
        if invalid_salary:
            warnings.append(f"{invalid_salary:,} salary value(s) could not be interpreted as numbers.")

    return {
        "valid": not errors,
        "errors": errors,
        "warnings": warnings,
        "rows": int(len(data)),
        "columns": int(len(data.columns)),
        "recognized_fields": recognized,
        "mapping": mapping,
        "duplicate_rows": duplicate_count,
    }


def mapping_table(mapping: dict[str, str]) -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "Uploaded Column": original,
                "Recognized As": DISPLAY_NAMES.get(canonical, canonical),
            }
            for original, canonical in mapping.items()
        ]
    )
