"""Canonical recruitment schema and column alias definitions."""

from __future__ import annotations

# Single source of truth for column recognition across ingestion and analytics.
CANONICAL_ALIASES: dict[str, list[str]] = {
    "candidate_id": [
        "candidate_id", "candidate id", "candidateid", "applicant_id",
        "applicant id", "id", "candidate_id_number",
    ],
    "candidate_name": [
        "candidate_name", "candidate name", "candidate", "applicant_name",
        "applicant name", "name", "applicant", "full name", "full_name",
    ],
    "application_date": [
        "application_date", "application date", "applied_date", "applied date",
        "applied_on", "applied on", "date_applied", "date applied",
    ],
    "recruiter": [
        "recruiter", "recruiter_name", "recruiter name", "talent_acquisition",
        "ta", "ta owner", "recruiter_owner",
    ],
    "client": [
        "client", "client_name", "client name", "customer", "account",
    ],
    "role": [
        "role", "job_role", "job role", "position", "job_title", "job title",
        "designation",
    ],
    "technology": [
        "technology", "tech", "primary_technology", "primary technology",
        "skill", "skills",
    ],
    "experience_years": [
        "experience_years", "experience years", "experience",
        "years_experience", "years of experience",
    ],
    "location": [
        "location", "city", "candidate_location", "candidate location",
    ],
    "source": [
        "source", "application_source", "application source",
        "candidate_source", "candidate source", "channel",
    ],
    "screening_status": [
        "screening_status", "screening status", "candidate_status",
        "candidate status", "application_status", "application status",
        "recruitment_status", "recruitment status", "current_status",
        "current status", "screening",
    ],
    "screening_result": [
        "screening_result", "screening result", "screening_outcome",
        "screening outcome",
    ],
    "interview_status": [
        "interview_status", "interview status", "interview",
        "interview stage", "interview completion",
    ],
    "interview_result": [
        "interview_result", "interview result", "interview_outcome",
        "interview outcome", "interview decision",
    ],
    "interview_date": [
        "interview_date", "interview date", "interview_completed_date",
        "interview completed date",
    ],
    "offer_status": [
        "offer_status", "offer status", "offer", "offer outcome",
    ],
    "offer_result": [
        "offer_result", "offer result", "offer_outcome", "offer outcome",
    ],
    "offer_date": ["offer_date", "offer date"],
    "joining_status": [
        "joining_status", "joining status", "joining", "joined",
        "onboarding_status", "onboarding status", "joining outcome",
    ],
    "joining_result": [
        "joining_result", "joining result", "joining_outcome",
        "joining outcome",
    ],
    "joining_date": [
        "joining_date", "joining date", "start_date", "start date",
        "date_joined",
    ],
    "salary_lpa": [
        "salary_lpa", "salary lpa", "salary", "offered_salary",
        "offered salary", "offered salary lpa", "annual_salary",
        "annual salary", "ctc", "compensation", "expected_salary_lpa",
    ],
    "rejection_reason": [
        "rejection_reason", "rejection reason", "rejection",
        "reason_for_rejection", "reason for rejection",
    ],
    "time_to_hire_days": [
        "time_to_hire_days", "time to hire days", "time_to_hire",
        "time to hire", "days_to_hire", "days to hire",
    ],
}

DISPLAY_NAMES: dict[str, str] = {
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

# Analytics-layer short keys mapped to canonical column names.
ANALYTICS_KEY_MAP: dict[str, str] = {
    "id": "candidate_id",
    "name": "candidate_name",
    "application_date": "application_date",
    "recruiter": "recruiter",
    "client": "client",
    "role": "role",
    "technology": "technology",
    "experience": "experience_years",
    "location": "location",
    "source": "source",
    "screening": "screening_status",
    "screening_result": "screening_result",
    "interview": "interview_status",
    "interview_result": "interview_result",
    "interview_date": "interview_date",
    "offer": "offer_status",
    "offer_result": "offer_result",
    "offer_date": "offer_date",
    "joining": "joining_status",
    "joining_result": "joining_result",
    "joining_date": "joining_date",
    "salary": "salary_lpa",
    "rejection": "rejection_reason",
    "time_to_hire": "time_to_hire_days",
}

# Recruitment status vocabulary — deterministic analytics source of truth.
SCREENING_SELECTED = frozenset({
    "selected", "screened", "passed", "screening selected", "qualified",
    "shortlisted",
})
INTERVIEW_SELECTED = frozenset({
    "selected", "interview selected", "passed", "selected for offer",
    "pass", "recommended", "shortlisted",
})
INTERVIEW_REJECTED = frozenset({
    "rejected", "declined", "failed", "not selected", "unsuccessful",
    "reject", "fail",
})
INTERVIEW_NO_SHOW = frozenset({
    "no show", "no-show", "noshow", "did not attend",
})
INTERVIEW_NOT_SCHEDULED = frozenset({
    "not scheduled", "pending", "scheduled", "not booked",
})
INTERVIEW_COMPLETED_STATUS = frozenset({
    "completed", "complete", "conducted", "done", "finished",
})
OFFERS_ACCEPTED = frozenset({
    "accepted", "offer accepted", "accept", "accepted offer",
})
OFFERS_DECLINED = frozenset({
    "declined", "rejected", "offer declined", "withdrawn", "cancelled",
})
JOINED = frozenset({
    "joined", "joining confirmed", "onboarded", "onboarded successfully",
    "started", "onboarded/joined",
})

CRITICAL_FIELDS = frozenset({
    "candidate_id", "screening_status", "interview_status", "offer_status",
    "joining_status",
})
DATE_FIELDS = frozenset({
    "application_date", "interview_date", "offer_date", "joining_date",
})
NUMERIC_FIELDS = frozenset({
    "experience_years", "salary_lpa", "time_to_hire_days",
})
