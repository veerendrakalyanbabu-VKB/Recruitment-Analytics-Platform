
from pathlib import Path
import pandas as pd
import streamlit as st

# ============================================================
# CANDIDATE MANAGEMENT — ATS OPERATIONS MODULE
# Designed to run as a Streamlit multipage app.
# ============================================================

st.set_page_config(
    page_title="Candidate Management | Recruitment ATS",
    page_icon="👤",
    layout="wide",
)

BASE_DIR = Path(__file__).resolve().parents[1]
DATA_DIR = BASE_DIR / "data"
CLEANED_FILE = DATA_DIR / "recruitment_data_cleaned.csv"
RAW_FILE = DATA_DIR / "recruitment_data.csv"

st.markdown("""
<style>
.block-container {max-width:1500px;padding-top:1.5rem;padding-bottom:3rem;}
.hero{padding:22px 26px;border:1px solid #293241;border-radius:18px;
background:linear-gradient(135deg,#151b26,#10151e);margin-bottom:20px;}
.hero h1{margin:0;color:#f8fafc;font-size:36px;}
.hero p{margin:7px 0 0;color:#94a3b8;}
.card{background:linear-gradient(145deg,#151b26,#10151e);
border:1px solid #293241;border-radius:14px;padding:18px;min-height:120px;}
.label{color:#94a3b8;font-size:13px;font-weight:650;}
.value{color:#f8fafc;font-size:25px;font-weight:850;margin-top:8px;}
.stage{font-size:15px;font-weight:800;padding:8px 12px;border-radius:10px;
display:inline-block;background:#1e293b;color:#f8fafc;}
.good{color:#22c55e}.warn{color:#facc15}.bad{color:#fb7185}.info{color:#38bdf8}
</style>
""", unsafe_allow_html=True)


@st.cache_data
def load_demo_data():
    path = CLEANED_FILE if CLEANED_FILE.exists() else RAW_FILE
    if not path.exists():
        raise FileNotFoundError(
            f"No recruitment CSV found in {DATA_DIR}. "
            "Expected recruitment_data_cleaned.csv or recruitment_data.csv."
        )
    data = pd.read_csv(path)
    data = data.loc[:, ~data.columns.astype(str).str.startswith("Unnamed")]
    data.columns = [str(c).strip() for c in data.columns]
    return data

def load_data():
    # Reuse the Level-1 uploaded dataset from the main dashboard session.
    uploaded = st.session_state.get("uploaded_recruitment_df")
    if uploaded is not None:
        return uploaded.copy()
    return load_demo_data()


try:
    df = load_data()
except Exception as exc:
    st.error(f"Unable to load recruitment data: {exc}")
    st.stop()


def find_col(names):
    lookup = {str(c).strip().lower(): c for c in df.columns}
    for name in names:
        if name.lower() in lookup:
            return lookup[name.lower()]
    return None


C = {
    "id": find_col(["candidate_id", "candidate id", "id"]),
    "name": find_col(["candidate_name", "candidate name", "name"]),
    "application_date": find_col(["application_date", "applied_date"]),
    "recruiter": find_col(["recruiter"]),
    "client": find_col(["client"]),
    "role": find_col(["role", "job_role"]),
    "technology": find_col(["technology", "tech", "primary_technology"]),
    "experience": find_col(["experience_years", "experience"]),
    "location": find_col(["location", "city"]),
    "source": find_col(["source", "application_source"]),
    "screening": find_col(["screening_status", "screening"]),
    "screening_result": find_col(["screening_result", "screening_outcome"]),
    "interview": find_col(["interview_status", "interview"]),
    "interview_result": find_col(["interview_result", "interview_outcome"]),
    "interview_date": find_col(["interview_date", "interview_completed_date"]),
    "offer": find_col(["offer_status", "offer"]),
    "offer_result": find_col(["offer_result", "offer_outcome"]),
    "offer_date": find_col(["offer_date"]),
    "joining": find_col(["joining_status", "joining"]),
    "joining_result": find_col(["joining_result", "joining_outcome"]),
    "joining_date": find_col(["joining_date"]),
    "salary": find_col(["salary_lpa", "salary", "offered_salary", "annual_salary"]),
    "rejection": find_col(["rejection_reason", "rejection"]),
    "time_to_hire": find_col(["time_to_hire_days", "time_to_hire", "days_to_hire"]),
}


def text(row, key):
    col = C.get(key)
    if not col:
        return ""
    value = row.get(col, "")
    if pd.isna(value):
        return ""
    return str(value).strip()


def lower(row, key):
    return text(row, key).lower()


def current_stage(row):
    """
    Derive the candidate's current ATS stage from existing source data.
    This is intentionally read-only: it does not invent or overwrite
    source-system statuses.
    """
    joining_status = lower(row, "joining")
    joining_result = lower(row, "joining_result")
    joining = joining_result or joining_status

    offer_status = lower(row, "offer")
    offer_result = lower(row, "offer_result")
    offer = offer_result or offer_status

    interview_status = lower(row, "interview")
    interview_result = lower(row, "interview_result")
    interview = interview_result or interview_status

    screening_status = lower(row, "screening")
    screening_result = lower(row, "screening_result")
    screening = screening_result or screening_status

    if joining in {"joined", "joining confirmed"}:
        return "Joined"

    if joining and joining not in {"not joined", "pending", "not started"}:
        return "Joining"

    if offer in {"accepted", "offer accepted"}:
        return "Offer Accepted"

    if offer in {"declined", "rejected", "offer declined"}:
        return "Offer Declined"

    if offer:
        return "Offer"

    if interview in {"selected", "interview selected", "passed", "selected for offer"}:
        return "Interview Selected"

    if interview in {"rejected", "declined"}:
        return "Interview Rejected"

    if interview in {"no show", "no-show", "noshow"}:
        return "Interview — No Show"

    if interview in {"not scheduled", "pending"} or not interview:
        if screening in {"selected", "screened", "passed", "screening selected"}:
            return "Interview — Not Scheduled"

    if interview:
        return "Interview"

    if screening in {"selected", "screened", "passed", "screening selected"}:
        return "Screening Selected"

    if screening:
        return "Screening"

    return "Applied"


def stage_priority(stage):
    order = {
        "Joined": 7,
        "Joining": 6,
        "Offer Accepted": 5,
        "Offer Declined": 5,
        "Offer": 4,
        "Interview Selected": 4,
        "Interview Rejected": 4,
        "Interview — No Show": 3,
        "Interview — Not Scheduled": 3,
        "Interview": 3,
        "Screening Selected": 2,
        "Screening": 1,
        "Applied": 0,
    }
    return order.get(stage, 0)


def action_required(row):
    stage = current_stage(row)
    if stage == "Interview — Not Scheduled":
        return "Schedule interview"
    if stage == "Interview — No Show":
        return "Follow up / reschedule"
    if stage == "Interview Selected":
        if not text(row, "offer"):
            return "Initiate offer process"
        return "Complete offer workflow"
    if stage == "Offer Accepted":
        if not text(row, "joining_date"):
            return "Confirm joining date"
        return "Track joining"
    if stage == "Offer":
        return "Await offer decision"
    return "No immediate action"


def stage_tone(stage):
    if stage == "Joined":
        return "good"
    if "Rejected" in stage or "Declined" in stage:
        return "bad"
    if "No Show" in stage or "Not Scheduled" in stage or stage == "Offer":
        return "warn"
    return "info"


# ============================================================
# HEADER
# ============================================================

data_source_label = (
    "Uploaded company CSV"
    if st.session_state.get("uploaded_recruitment_df") is not None
    else "Demo recruitment dataset"
)

st.markdown(f"""
<div class="hero">
    <h1>👤 Candidate Management</h1>
    <p>ATS-style candidate search, pipeline stage, profile intelligence and operational actions.</p>
    <p><strong>Data source:</strong> {data_source_label}</p>
</div>
""", unsafe_allow_html=True)

# ============================================================
# FILTERS
# ============================================================

with st.sidebar:
    st.header("Candidate Filters")

    def multi(label, key):
        col = C.get(key)
        if not col:
            return []
        vals = sorted(df[col].dropna().astype(str).unique().tolist())
        return st.multiselect(label, vals)

    recruiter_filter = multi("Recruiter", "recruiter")
    client_filter = multi("Client", "client")
    role_filter = multi("Role", "role")
    stage_options = [
        "Applied", "Screening", "Screening Selected",
        "Interview — Not Scheduled", "Interview — No Show",
        "Interview", "Interview Selected", "Interview Rejected",
        "Offer", "Offer Accepted", "Offer Declined",
        "Joining", "Joined"
    ]
    stage_filter = st.multiselect("Current Stage", stage_options)

    st.divider()
    st.caption(f"Source records: {len(df):,}")


filtered = df.copy()


def apply_multi(data, col, values):
    if col and values:
        return data[data[col].fillna("").astype(str).isin(values)].copy()
    return data


filtered = apply_multi(filtered, C["recruiter"], recruiter_filter)
filtered = apply_multi(filtered, C["client"], client_filter)
filtered = apply_multi(filtered, C["role"], role_filter)

if stage_filter:
    filtered = filtered[
        filtered.apply(lambda r: current_stage(r) in stage_filter, axis=1)
    ].copy()

filtered["_current_stage"] = filtered.apply(current_stage, axis=1)
filtered["_action"] = filtered.apply(action_required, axis=1)

# ============================================================
# SEARCH
# ============================================================

search = st.text_input(
    "🔎 Search candidates",
    placeholder="Candidate ID, name, recruiter, client, role, technology, location..."
)

if search.strip():
    q = search.strip().lower()
    mask = pd.Series(False, index=filtered.index)
    for key in ["id", "name", "recruiter", "client", "role", "technology", "location"]:
        col = C.get(key)
        if col:
            mask |= filtered[col].fillna("").astype(str).str.lower().str.contains(q, na=False)
    filtered = filtered[mask].copy()

# ============================================================
# KPI SUMMARY
# ============================================================

st.subheader("Candidate Operations")

stage_counts = filtered["_current_stage"].value_counts()

a, b, c, d = st.columns(4)
with a:
    st.markdown(f'<div class="card"><div class="label">Candidates in View</div><div class="value">{len(filtered):,}</div></div>', unsafe_allow_html=True)
with b:
    urgent = int(filtered["_action"].isin([
        "Schedule interview",
        "Follow up / reschedule",
        "Initiate offer process",
        "Confirm joining date"
    ]).sum())
    st.markdown(f'<div class="card"><div class="label">Action Required</div><div class="value warn">{urgent:,}</div></div>', unsafe_allow_html=True)
with c:
    joined = int((filtered["_current_stage"] == "Joined").sum())
    st.markdown(f'<div class="card"><div class="label">Joined</div><div class="value good">{joined:,}</div></div>', unsafe_allow_html=True)
with d:
    rejected = int(filtered["_current_stage"].isin(["Interview Rejected", "Offer Declined"]).sum())
    st.markdown(f'<div class="card"><div class="label">Rejected / Declined</div><div class="value bad">{rejected:,}</div></div>', unsafe_allow_html=True)

# ============================================================
# PIPELINE
# ============================================================

st.subheader("Recruitment Pipeline")

pipeline_order = [
    "Applied", "Screening", "Screening Selected",
    "Interview — Not Scheduled", "Interview — No Show",
    "Interview", "Interview Selected",
    "Offer", "Offer Accepted", "Joining", "Joined"
]

pipeline = pd.DataFrame({
    "Stage": pipeline_order,
    "Candidates": [int(stage_counts.get(s, 0)) for s in pipeline_order]
})

st.bar_chart(
    pipeline.set_index("Stage"),
    y="Candidates",
    width="stretch",
    height=360,
)

# ============================================================
# CANDIDATE TABLE
# ============================================================

st.subheader("Candidate Queue")

display_cols = [
    C[k] for k in [
        "id", "name", "recruiter", "client", "role",
        "technology", "location", "interview", "offer", "joining"
    ] if C[k]
]
display_cols += ["_current_stage", "_action"]

if display_cols:
    queue = filtered[display_cols].copy()
    rename = {
        "_current_stage": "Current Stage",
        "_action": "Next Action",
    }
    queue = queue.rename(columns=rename)
    st.dataframe(queue.head(500), width="stretch", hide_index=True)
else:
    st.warning("No usable candidate fields were detected.")

# ============================================================
# PROFILE
# ============================================================

st.divider()
st.subheader("Candidate Profile")

if len(filtered) == 0:
    st.info("No candidates match the current filters.")
else:
    if C["id"]:
        ids = filtered[C["id"]].fillna("").astype(str).tolist()
        selected = st.selectbox("Select Candidate ID", ids)
        row = filtered[filtered[C["id"]].fillna("").astype(str) == selected].iloc[0]
    else:
        selected_index = st.selectbox("Select Candidate", filtered.index.tolist())
        row = filtered.loc[selected_index]

    stage = current_stage(row)
    tone = stage_tone(stage)
    action = action_required(row)

    left, right = st.columns([2, 1])

    with left:
        candidate_name = text(row, "name") or "Unnamed Candidate"
        candidate_id = text(row, "id") or "N/A"
        st.markdown(f"### {candidate_name}")
        st.caption(f"Candidate ID: {candidate_id}")

        p1, p2, p3 = st.columns(3)
        with p1:
            st.markdown(f'<div class="card"><div class="label">Current Stage</div><div class="value {tone}">{stage}</div></div>', unsafe_allow_html=True)
        with p2:
            st.markdown(f'<div class="card"><div class="label">Next Action</div><div class="value" style="font-size:18px">{action}</div></div>', unsafe_allow_html=True)
        with p3:
            st.markdown(f'<div class="card"><div class="label">Recruiter</div><div class="value" style="font-size:20px">{text(row, "recruiter") or "N/A"}</div></div>', unsafe_allow_html=True)

    with right:
        st.markdown("#### Operational Status")
        st.write(f"**Client:** {text(row, 'client') or 'N/A'}")
        st.write(f"**Role:** {text(row, 'role') or 'N/A'}")
        st.write(f"**Technology:** {text(row, 'technology') or 'N/A'}")
        st.write(f"**Location:** {text(row, 'location') or 'N/A'}")

    st.markdown("#### Candidate Details")

    details = [
        ("Application Date", text(row, "application_date")),
        ("Experience", text(row, "experience")),
        ("Source", text(row, "source")),
        ("Screening Status", text(row, "screening")),
        ("Interview Status", text(row, "interview")),
        ("Interview Result", text(row, "interview_result")),
        ("Interview Date", text(row, "interview_date")),
        ("Offer Status", text(row, "offer")),
        ("Offer Result", text(row, "offer_result")),
        ("Offer Date", text(row, "offer_date")),
        ("Joining Status", text(row, "joining")),
        ("Joining Result", text(row, "joining_result")),
        ("Joining Date", text(row, "joining_date")),
        ("Salary (LPA)", text(row, "salary")),
        ("Time to Hire (Days)", text(row, "time_to_hire")),
        ("Rejection Reason", text(row, "rejection")),
    ]

    detail_df = pd.DataFrame(
        [{"Field": k, "Value": v if v else "—"} for k, v in details],
        dtype=str,
    )
    st.dataframe(detail_df, width="stretch", hide_index=True)

    st.markdown("#### Recruitment Journey")

    journey = pd.DataFrame({
        "Stage": [
            "Applied",
            "Screening",
            "Interview",
            "Interview Selected",
            "Offer",
            "Joined",
        ],
        "Status": [
            "Recorded" if text(row, "application_date") else "Not recorded",
            text(row, "screening") or "Not recorded",
            text(row, "interview") or "Not recorded",
            "Selected" if lower(row, "interview") in {
                "selected", "interview selected", "passed", "selected for offer"
            } else "—",
            text(row, "offer") or "Not recorded",
            text(row, "joining") or "Not recorded",
        ],
    })
    st.dataframe(journey, width="stretch", hide_index=True)

    # Deliberately read-only until a database/write-back layer exists.
    if action != "No immediate action":
        st.warning(
            f"Action required: **{action}**. "
            "This module is currently read-only; no source-system status is modified."
        )

# ============================================================
# EXPORT
# ============================================================

st.divider()
export_cols = [c for c in filtered.columns if not c.startswith("_")]
export_data = filtered[export_cols].to_csv(index=False).encode("utf-8")

st.download_button(
    "⬇️ Export Current Candidate View",
    data=export_data,
    file_name="candidate_management_export.csv",
    mime="text/csv",
)

st.caption(
    "Candidate Management • Read-only ATS operations layer • "
    "Source data is never modified by this module."
)
