
from pathlib import Path
import pandas as pd
import streamlit as st

# ============================================================
# RECRUITMENT ANALYTICS PLATFORM — ATS / OPERATIONS EDITION
# ============================================================

st.set_page_config(
    page_title="Recruitment Analytics Platform",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

# -----------------------------
# Styling
# -----------------------------
st.markdown("""
<style>
.main { background:#0e1117; }
.block-container { max-width:1500px; padding-top:1.5rem; padding-bottom:3rem; }
.hero {
    padding: 22px 26px;
    border:1px solid #293241;
    border-radius:18px;
    background:linear-gradient(135deg,#151b26,#10151e);
    margin-bottom:20px;
}
.hero h1 { margin:0; color:#f8fafc; font-size:38px; }
.hero p { margin:7px 0 0; color:#94a3b8; font-size:15px; }
.section-title { color:#f8fafc; font-size:25px; font-weight:800; margin:18px 0 12px; }
.kpi-card {
    background:linear-gradient(145deg,#151b26,#10151e);
    border:1px solid #293241;
    border-radius:14px;
    padding:18px;
    min-height:132px;
}
.kpi-title { color:#94a3b8; font-size:14px; font-weight:650; }
.kpi-value { color:#f8fafc; font-size:30px; font-weight:850; margin:9px 0 5px; }
.kpi-desc { color:#64748b; font-size:12px; }
.good { color:#22c55e; }
.info { color:#38bdf8; }
.warn { color:#facc15; }
.bad { color:#fb7185; }
.purple { color:#a78bfa; }
.small-note { color:#64748b; font-size:12px; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Paths / loading
# -----------------------------
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
CLEANED_FILE = DATA_DIR / "recruitment_data_cleaned.csv"
RAW_FILE = DATA_DIR / "recruitment_data.csv"

@st.cache_data
def load_data():
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

try:
    df = load_data()
except Exception as exc:
    st.error(f"Unable to load recruitment data: {exc}")
    st.stop()

# -----------------------------
# Column helpers
# -----------------------------
def find_col(names):
    lookup = {str(c).strip().lower(): c for c in df.columns}
    for name in names:
        if name.lower() in lookup:
            return lookup[name.lower()]
    return None

COL = {
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
    "screening": find_col(["screening_status", "screening_result", "screening"]),
    "interview": find_col(["interview_status", "interview_result", "interview"]),
    "interview_date": find_col(["interview_date", "interview_completed_date"]),
    "offer": find_col(["offer_status", "offer_result", "offer"]),
    "offer_date": find_col(["offer_date"]),
    "joining": find_col(["joining_status", "joining_result", "joining"]),
    "joining_date": find_col(["joining_date"]),
    "salary": find_col(["salary_lpa", "salary", "offered_salary", "annual_salary"]),
    "rejection": find_col(["rejection_reason", "rejection"]),
    "time_to_hire": find_col(["time_to_hire_days", "time_to_hire", "days_to_hire"]),
}

def norm_series(data, col):
    if not col or col not in data.columns:
        return pd.Series("", index=data.index)
    return data[col].fillna("").astype(str).str.strip()

def count_values(data, col, values):
    if not col:
        return 0
    return int(norm_series(data, col).str.lower().isin([v.lower() for v in values]).sum())

def pct(num, den):
    return (num / den * 100) if den else 0.0


def display_value(value):
    """Coerce mixed types to strings for Streamlit/Arrow dataframes."""
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return str(value)

def kpi_card(title, value, description="", tone="info"):
    st.markdown(
        f"""
        <div class="kpi-card">
            <div class="kpi-title">{title}</div>
            <div class="kpi-value">{value}</div>
            <div class="kpi-desc {tone}">{description}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

# -----------------------------
# Sidebar filters
# -----------------------------
with st.sidebar:
    st.markdown("## 🎯 Recruitment Control")
    st.caption("Use these filters across the operational views.")
    st.divider()

    def selector(label, col):
        if not col:
            return []
        vals = sorted(norm_series(df, col).replace("", pd.NA).dropna().unique().tolist())
        return st.multiselect(label, vals, default=vals)

    selected_recruiters = selector("Recruiter", COL["recruiter"])
    selected_clients = selector("Client", COL["client"])
    selected_roles = selector("Role", COL["role"])
    selected_sources = selector("Source", COL["source"])
    selected_technologies = selector("Technology", COL["technology"])

    st.divider()
    st.caption(f"Dataset: {len(df):,} candidates")
    st.caption(f"Fields: {len(df.columns)}")

# -----------------------------
# Apply filters
# -----------------------------
filtered = df.copy()

def apply_filter(data, col, values):
    if col and values:
        return data[norm_series(data, col).isin(values)].copy()
    return data

filtered = apply_filter(filtered, COL["recruiter"], selected_recruiters)
filtered = apply_filter(filtered, COL["client"], selected_clients)
filtered = apply_filter(filtered, COL["role"], selected_roles)
filtered = apply_filter(filtered, COL["source"], selected_sources)
filtered = apply_filter(filtered, COL["technology"], selected_technologies)

# -----------------------------
# Recruitment status model
# -----------------------------
screening_selected = count_values(filtered, COL["screening"],
                                  ["selected", "screened", "passed", "screening selected"])

interview_selected = count_values(filtered, COL["interview"],
                                  ["selected", "interview selected", "passed", "selected for offer"])

interview_rejected = count_values(filtered, COL["interview"],
                                  ["rejected", "declined"])

interview_no_show = count_values(filtered, COL["interview"],
                                 ["no show", "no-show", "noshow"])

interview_not_scheduled = count_values(filtered, COL["interview"],
                                       ["not scheduled", "pending", "scheduled"])

# In this dataset, Selected + Rejected represents completed interview outcomes.
# No Show and Not Scheduled are operational exceptions and are not completed.
interviews_completed = interview_selected + interview_rejected

offers_accepted = count_values(filtered, COL["offer"],
                               ["accepted", "offer accepted"])

offers_declined = count_values(filtered, COL["offer"],
                               ["declined", "rejected", "offer declined"])

joined = count_values(filtered, COL["joining"],
                      ["joined", "joining confirmed"])

total = len(filtered)

screening_rate = pct(screening_selected, total)
interview_selection_rate = pct(interview_selected, interviews_completed)
offer_acceptance_rate = pct(offers_accepted, interview_selected)
joining_rate = pct(joined, offers_accepted)

avg_salary = None
if COL["salary"]:
    avg_salary = pd.to_numeric(filtered[COL["salary"]], errors="coerce").mean()

avg_tth = None
if COL["time_to_hire"]:
    avg_tth = pd.to_numeric(filtered[COL["time_to_hire"]], errors="coerce").mean()

# -----------------------------
# Header
# -----------------------------
st.markdown("""
<div class="hero">
    <h1>📊 Recruitment Analytics Platform</h1>
    <p>Executive intelligence + ATS-style candidate operations for recruitment teams.</p>
</div>
""", unsafe_allow_html=True)

tabs = st.tabs([
    "🏠 Executive",
    "🧭 Candidate Pipeline",
    "🎤 Interview Operations",
    "👥 Recruiter Workbench",
    "🏢 Clients & Sources",
    "🔎 Candidate Search",
    "📋 Reports & Data Quality",
])

# ============================================================
# EXECUTIVE
# ============================================================
with tabs[0]:
    st.markdown('<div class="section-title">Key Recruitment KPIs</div>', unsafe_allow_html=True)

    a,b,c,d = st.columns(4)
    with a: kpi_card("Applications", f"{total:,}", "Total candidates in current scope", "info")
    with b: kpi_card("Screening Selected", f"{screening_selected:,}", f"{screening_rate:.2f}% of applications", "good")
    with c: kpi_card("Interviews Completed", f"{interviews_completed:,}", f"{interview_selected:,} selected after interview", "info")
    with d: kpi_card("Candidates Joined", f"{joined:,}", f"{joining_rate:.2f}% of accepted offers", "good")

    a,b,c,d = st.columns(4)
    with a: kpi_card("Interview Selection", f"{interview_selection_rate:.2f}%", "Completed → Selected", "purple")
    with b: kpi_card("Offer Acceptance", f"{offer_acceptance_rate:.2f}%", "Interview Selected → Accepted", "good")
    with c: kpi_card("Average Salary", f"₹{avg_salary:.2f} LPA" if pd.notna(avg_salary) else "N/A", "Average offered salary", "warn")
    with d: kpi_card("Avg Time to Hire", f"{avg_tth:.1f} days" if pd.notna(avg_tth) else "N/A", "Average hiring cycle", "info")

    st.divider()
    st.markdown('<div class="section-title">Hiring Funnel</div>', unsafe_allow_html=True)

    funnel = pd.DataFrame({
        "Stage": [
            "Applications", "Screening Selected", "Interviews Completed",
            "Interview Selected", "Offers Accepted", "Joined"
        ],
        "Candidates": [
            total, screening_selected, interviews_completed,
            interview_selected, offers_accepted, joined
        ],
    })
    st.bar_chart(funnel.set_index("Stage"), y="Candidates", width="stretch", height=380)
    st.dataframe(funnel, width="stretch", hide_index=True)

    st.divider()
    st.markdown('<div class="section-title">🚦 Action Center</div>', unsafe_allow_html=True)

    actions = pd.DataFrame({
        "Operational Queue": [
            "Interviews not scheduled",
            "Interview no-shows",
            "Interview rejections",
            "Offers declined",
            "Accepted offers not joined",
        ],
        "Count": [
            interview_not_scheduled,
            interview_no_show,
            interview_rejected,
            offers_declined,
            max(offers_accepted - joined, 0),
        ],
        "Priority": ["High", "High", "Monitor", "High", "High"],
    })
    st.dataframe(actions, width="stretch", hide_index=True)

# ============================================================
# PIPELINE
# ============================================================
with tabs[1]:
    st.markdown('<div class="section-title">🧭 Candidate Pipeline</div>', unsafe_allow_html=True)

    pipeline_counts = pd.DataFrame({
        "Stage": [
            "Screening Selected",
            "Interview Not Scheduled",
            "Interview No Show",
            "Interview Rejected",
            "Interview Selected",
            "Offer Accepted",
            "Joined",
        ],
        "Candidates": [
            screening_selected,
            interview_not_scheduled,
            interview_no_show,
            interview_rejected,
            interview_selected,
            offers_accepted,
            joined,
        ],
    })
    st.bar_chart(pipeline_counts.set_index("Stage"), y="Candidates", width="stretch", height=400)

    if COL["interview"]:
        pipeline_status = norm_series(filtered, COL["interview"]).replace("", "Unknown").value_counts().reset_index()
        pipeline_status.columns = ["Interview Status", "Candidates"]
        st.subheader("Interview Status Distribution")
        st.dataframe(pipeline_status, width="stretch", hide_index=True)

    st.subheader("Candidates Requiring Attention")
    attention = filtered.copy()
    if COL["interview"]:
        mask = norm_series(attention, COL["interview"]).str.lower().isin(
            ["not scheduled", "no show", "pending", ""]
        )
        attention = attention[mask].copy()

    cols = [c for c in [
        COL["id"], COL["name"], COL["recruiter"], COL["client"],
        COL["role"], COL["technology"], COL["interview"],
        COL["interview_date"]
    ] if c]
    if len(attention):
        st.dataframe(attention[cols].head(200), width="stretch", hide_index=True)
    else:
        st.success("No interview-action candidates in the current filter scope.")

# ============================================================
# INTERVIEW OPERATIONS
# ============================================================
with tabs[2]:
    st.markdown('<div class="section-title">🎤 Interview Operations</div>', unsafe_allow_html=True)

    a,b,c,d = st.columns(4)
    with a: kpi_card("Completed", f"{interviews_completed:,}", "Selected + Rejected outcomes", "good")
    with b: kpi_card("Selected", f"{interview_selected:,}", f"{interview_selection_rate:.2f}% selection", "purple")
    with c: kpi_card("No Show", f"{interview_no_show:,}", "Attendance issue", "bad")
    with d: kpi_card("Not Scheduled", f"{interview_not_scheduled:,}", "Scheduling queue", "warn")

    if COL["interview"]:
        dist = norm_series(filtered, COL["interview"]).replace("", "Unknown").value_counts().reset_index()
        dist.columns = ["Status", "Candidates"]
        st.subheader("Interview Outcome Mix")
        st.bar_chart(dist.set_index("Status"), y="Candidates", width="stretch", height=350)

    st.subheader("Interview Operations Table")
    cols = [c for c in [
        COL["id"], COL["name"], COL["recruiter"], COL["client"], COL["role"],
        COL["interview"], COL["interview_date"], COL["source"]
    ] if c]
    st.dataframe(filtered[cols].sort_values(cols[0] if cols else filtered.columns[0]).head(300),
                 width="stretch", hide_index=True)

# ============================================================
# RECRUITER
# ============================================================
with tabs[3]:
    st.markdown('<div class="section-title">👥 Recruiter Workbench</div>', unsafe_allow_html=True)

    if COL["recruiter"]:
        rec = filtered.groupby(COL["recruiter"]).size().reset_index(name="Applications")
        rec = rec.sort_values("Applications", ascending=False)
        st.bar_chart(rec.set_index(COL["recruiter"]), y="Applications", width="stretch", height=350)

        # Funnel-derived recruiter KPIs
        recruiter_rows = []
        for recruiter, group in filtered.groupby(COL["recruiter"]):
            apps = len(group)
            scr = count_values(group, COL["screening"], ["selected","screened","passed","screening selected"])
            sel = count_values(group, COL["interview"], ["selected","interview selected","passed","selected for offer"])
            rej = count_values(group, COL["interview"], ["rejected","declined"])
            comp = sel + rej
            acc = count_values(group, COL["offer"], ["accepted","offer accepted"])
            jn = count_values(group, COL["joining"], ["joined","joining confirmed"])
            recruiter_rows.append({
                "Recruiter": recruiter,
                "Applications": apps,
                "Screening Selected": scr,
                "Interviews Completed": comp,
                "Interview Selected": sel,
                "Offers Accepted": acc,
                "Joined": jn,
                "Interview Selection %": round(pct(sel, comp), 2),
                "Joining %": round(pct(jn, acc), 2),
            })
        rec_perf = pd.DataFrame(recruiter_rows).sort_values("Applications", ascending=False)
        st.dataframe(rec_perf, width="stretch", hide_index=True)
    else:
        st.info("Recruiter column not available.")

# ============================================================
# CLIENTS & SOURCES
# ============================================================
with tabs[4]:
    st.markdown('<div class="section-title">🏢 Clients & Recruitment Sources</div>', unsafe_allow_html=True)

    if COL["client"]:
        st.subheader("Client Demand")
        client = filtered.groupby(COL["client"]).size().reset_index(name="Applications").sort_values("Applications", ascending=False)
        st.bar_chart(client.set_index(COL["client"]), y="Applications", width="stretch", height=320)
        st.dataframe(client, width="stretch", hide_index=True)

    if COL["source"]:
        st.subheader("Source Performance")
        source = filtered.groupby(COL["source"]).size().reset_index(name="Applications").sort_values("Applications", ascending=False)
        st.bar_chart(source.set_index(COL["source"]), y="Applications", width="stretch", height=320)
        st.dataframe(source, width="stretch", hide_index=True)

    if COL["role"]:
        st.subheader("Role Demand")
        roles = filtered.groupby(COL["role"]).size().reset_index(name="Applications").sort_values("Applications", ascending=False)
        st.bar_chart(roles.set_index(COL["role"]), y="Applications", width="stretch", height=320)
        st.dataframe(roles, width="stretch", hide_index=True)

# ============================================================
# SEARCH / PROFILE
# ============================================================
with tabs[5]:
    st.markdown('<div class="section-title">🔎 Candidate Search & Profile</div>', unsafe_allow_html=True)

    search = st.text_input(
        "Search candidate",
        placeholder="Candidate ID, name, recruiter, client, role or technology..."
    )

    results = filtered.copy()
    if search.strip():
        q = search.strip().lower()
        searchable = pd.Series(False, index=results.index)
        for key in ["id", "name", "recruiter", "client", "role", "technology", "location", "source"]:
            col = COL[key]
            if col:
                searchable |= norm_series(results, col).str.lower().str.contains(q, na=False)
        results = results[searchable]

    st.write(f"**{len(results):,}** candidate(s) found.")

    display_cols = [c for c in [
        COL["id"], COL["name"], COL["recruiter"], COL["client"], COL["role"],
        COL["technology"], COL["interview"], COL["offer"], COL["joining"]
    ] if c]
    st.dataframe(results[display_cols].head(250), width="stretch", hide_index=True)

    if len(results):
        if COL["id"]:
            options = results[COL["id"]].astype(str).tolist()
            selected_id = st.selectbox("Open candidate profile", options)
            profile = results[results[COL["id"]].astype(str) == selected_id].iloc[0]

            st.subheader("Candidate Profile")
            profile_cols = [c for c in [
                COL["id"], COL["name"], COL["application_date"], COL["recruiter"],
                COL["client"], COL["role"], COL["technology"], COL["experience"],
                COL["location"], COL["source"], COL["screening"], COL["interview"],
                COL["interview_date"], COL["offer"], COL["offer_date"],
                COL["joining"], COL["joining_date"], COL["salary"],
                COL["rejection"], COL["time_to_hire"]
            ] if c]

            profile_df = pd.DataFrame({
                "Field": [str(c) for c in profile_cols],
                "Value": [display_value(profile[c]) for c in profile_cols],
            })
            st.dataframe(profile_df, width="stretch", hide_index=True)

# ============================================================
# REPORTS / DATA QUALITY
# ============================================================
with tabs[6]:
    st.markdown('<div class="section-title">📋 Reports & Data Quality</div>', unsafe_allow_html=True)

    st.subheader("Management Report")
    management = pd.DataFrame({
        "Metric": [
            "Applications", "Screening Selected", "Interviews Completed",
            "Interview Selected", "Offers Accepted", "Joined",
            "Screening Rate %", "Interview Selection %", "Offer Acceptance %",
            "Joining Rate %", "Average Salary LPA", "Average Time to Hire Days"
        ],
        "Value": [
            display_value(total),
            display_value(screening_selected),
            display_value(interviews_completed),
            display_value(interview_selected),
            display_value(offers_accepted),
            display_value(joined),
            display_value(round(screening_rate, 2)),
            display_value(round(interview_selection_rate, 2)),
            display_value(round(offer_acceptance_rate, 2)),
            display_value(round(joining_rate, 2)),
            display_value(round(avg_salary, 2) if pd.notna(avg_salary) else None),
            display_value(round(avg_tth, 2) if pd.notna(avg_tth) else None),
        ],
    })
    st.dataframe(management, width="stretch", hide_index=True)

    csv_report = management.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download KPI Report",
        data=csv_report,
        file_name="recruitment_kpi_report.csv",
        mime="text/csv",
    )

    st.subheader("Data Quality")
    quality_rows = []
    for key, col in COL.items():
        if col:
            missing = int(filtered[col].isna().sum())
            quality_rows.append({
                "Field": col,
                "Missing": missing,
                "Missing %": round(pct(missing, len(filtered)), 2),
            })
    quality = pd.DataFrame(quality_rows).sort_values("Missing %", ascending=False)
    st.dataframe(quality, width="stretch", hide_index=True)

    duplicate_count = int(filtered.duplicated().sum())
    st.metric("Duplicate rows", duplicate_count)

    st.subheader("Filtered Dataset Export")
    export = filtered.to_csv(index=False).encode("utf-8")
    st.download_button(
        "⬇️ Download Filtered Candidate Data",
        data=export,
        file_name="filtered_recruitment_candidates.csv",
        mime="text/csv",
    )

st.divider()
st.caption(
    "Recruitment Analytics Platform • ATS Operations • Python • Pandas • Streamlit"
)
