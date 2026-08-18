
from pathlib import Path
import pandas as pd
import streamlit as st

from app.analytics.funnel import build_funnel_dataframe
from app.analytics.kpis import build_col_map, compute_kpis, norm_series, pct
from app.components.ui import hero, insight_card, kpi_card
from app.config import APP_SUBTITLE, APP_TITLE
from app.data.loader import load_and_prepare, load_demo_dataframe, mapping_table
from app.data.normalization import normalize_dataframe as normalize_full
from app.data.profiling import profile_dataset
from app.data.validation import validate_recruitment_data
from app.intelligence.insight_engine import generate_insights, recruiter_scorecards
from app.theme import inject_theme
from app.utils.formatting import display_value

# ============================================================
# RECRUITMENT INTELLIGENCE OS — Entry Point
# ============================================================

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_theme()


@st.cache_data(show_spinner=False)
def load_demo_data():
    return load_demo_dataframe()


def load_uploaded_csv(uploaded_file, manual_overrides=None):
    bundle = load_and_prepare(uploaded_file, manual_overrides)
    return bundle["data"], bundle["validation"]


# ------------------------------------------------------------
# DATA SOURCE
# ------------------------------------------------------------
with st.sidebar:
    st.markdown("## 📥 Data Source")
    source_mode = st.radio(
        "Choose dataset",
        ["Demo Dataset", "Upload CSV"],
        index=0,
        help="Upload a company recruitment CSV to analyze it immediately. "
             "Uploaded data is used only for the current Streamlit session.",
    )

    uploaded_file = None
    if source_mode == "Upload CSV":
        uploaded_file = st.file_uploader(
            "Upload recruitment CSV",
            type=["csv"],
            help="CSV only. The platform automatically recognizes common recruitment column names.",
        )

try:
    if source_mode == "Upload CSV":
        if uploaded_file is None:
            st.info("Upload a CSV from the sidebar to begin analysis.")
            st.stop()

        file_signature = f"{uploaded_file.name}:{uploaded_file.size}"
        if st.session_state.get("upload_signature") != file_signature:
            uploaded_df, upload_validation = load_uploaded_csv(uploaded_file)
            st.session_state["upload_signature"] = file_signature
            st.session_state["uploaded_recruitment_df"] = uploaded_df
            st.session_state["upload_validation"] = upload_validation

        df = st.session_state["uploaded_recruitment_df"]
        validation = st.session_state["upload_validation"]

        if not validation["valid"]:
            st.error("The uploaded dataset needs attention before analysis.")
            for error in validation["errors"]:
                st.error(error)
            st.stop()

    else:
        df = load_demo_data()
        df, demo_mapping, unmapped, low_conf = normalize_full(df)
        validation = validate_recruitment_data(df, demo_mapping, unmapped, low_conf)
        st.session_state.pop("upload_signature", None)
        st.session_state.pop("uploaded_recruitment_df", None)
        st.session_state.pop("upload_validation", None)

except Exception as exc:
    st.error(f"Unable to load recruitment data: {exc}")
    st.stop()

df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]
df.columns = [str(c).strip() for c in df.columns]

# Show a compact validation/status panel before the dashboard controls.
if source_mode == "Upload CSV":
    st.markdown(
        f"""
        <div class="hero">
            <h1>📥 {uploaded_file.name}</h1>
            <p>Uploaded dataset • {len(df):,} candidates • {len(df.columns)} fields • Ready for analysis</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if validation["warnings"]:
        with st.expander(
            f"⚠️ Data Quality Warnings ({len(validation['warnings'])})",
            expanded=False,
        ):
            for warning in validation["warnings"]:
                st.warning(warning)

    with st.expander("🔎 Detected Column Mapping", expanded=False):
        st.dataframe(
            mapping_table(validation["mapping"]),
            width="stretch",
            hide_index=True,
        )

    status_cols = st.columns(4)
    with status_cols[0]:
        st.metric("Records", f"{len(df):,}")
    with status_cols[1]:
        st.metric("Fields", f"{len(df.columns):,}")
    with status_cols[2]:
        st.metric("Mapped", f"{validation.get('mapped_count', len(validation['recognized_fields'])):,}")
    with status_cols[3]:
        st.metric("Duplicates", f"{validation['duplicate_rows']:,}")

    profile = profile_dataset(df, validation)
    st.metric("Data Health Score", f"{profile.health_score:.0f} / 100")

    st.success(
        "✅ Dataset validated. The analysis engine is using the uploaded CSV directly "
        "for all KPIs, funnels, recruiter metrics and operational views."
    )

# -----------------------------
# Column helpers
# -----------------------------
COL = build_col_map(df)

def count_values(data, col, values):
    if not col:
        return 0
    return int(norm_series(data, col).str.lower().isin([v.lower() for v in values]).sum())

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
    if source_mode == "Upload CSV":
        st.success("● LIVE UPLOAD")
    else:
        st.info("● DEMO DATASET")

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
# Recruitment status model (shared KPI engine)
# -----------------------------
kpis = compute_kpis(filtered, COL)

total = kpis.total
screening_selected = kpis.screening_selected
interviews_completed = kpis.interviews_completed
interview_selected = kpis.interview_selected
interview_rejected = kpis.interview_rejected
interview_no_show = kpis.interview_no_show
interview_not_scheduled = kpis.interview_not_scheduled
offers_accepted = kpis.offers_accepted
offers_declined = kpis.offers_declined
offers_made = kpis.offers_made
joined = kpis.joined
screening_rate = kpis.screening_rate
interview_selection_rate = kpis.interview_selection_rate
offer_acceptance_rate = kpis.offer_acceptance_rate
joining_rate = kpis.joining_rate
avg_salary = kpis.avg_salary
avg_tth = kpis.avg_time_to_hire
structured_insights = generate_insights(filtered, kpis, COL)
data_profile = profile_dataset(filtered, validation if source_mode == "Upload CSV" else None)

# -----------------------------
# Header
# -----------------------------
hero(APP_TITLE, APP_SUBTITLE)

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
    st.markdown('<div class="section-title">RECRUITMENT COMMAND CENTER</div>', unsafe_allow_html=True)

    hc = st.columns(5)
    with hc[0]:
        st.metric("Data Health", f"{data_profile.health_score:.0f}/100")
    with hc[1]:
        st.metric("Records", f"{total:,}")
    with hc[2]:
        st.metric("Interviews Completed", f"{interviews_completed:,}")
    with hc[3]:
        st.metric("Interview Selection", f"{interview_selection_rate:.2f}%")
    with hc[4]:
        st.metric("Joining Rate", f"{joining_rate:.2f}%")

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

    funnel = build_funnel_dataframe(kpis)
    st.bar_chart(funnel.set_index("Stage"), y="Candidates", width="stretch", height=380)
    st.dataframe(funnel, width="stretch", hide_index=True)

    st.divider()
    st.markdown('<div class="section-title">Attention Required</div>', unsafe_allow_html=True)

    for insight in structured_insights[:8]:
        insight_card(insight)

    st.divider()
    st.markdown('<div class="section-title">Action Center</div>', unsafe_allow_html=True)

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

        rec_perf = recruiter_scorecards(filtered, COL)
        if not rec_perf.empty:
            display_cols = [
                COL["recruiter"], "applications", "screening_selected",
                "interviews", "interview_selected", "offers", "joined",
                "interview_selection_%", "joining_rate_%", "efficiency_score",
                "vs_team_median", "avg_time_to_hire",
            ]
            display_cols = [c for c in display_cols if c in rec_perf.columns]
            st.dataframe(
                rec_perf[display_cols].sort_values("efficiency_score", ascending=False),
                width="stretch",
                hide_index=True,
            )
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
    st.metric("Data Health Score", f"{data_profile.health_score:.0f} / 100")
    if data_profile.issues:
        for issue in data_profile.issues:
            st.warning(issue)

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
st.caption(f"{APP_TITLE} · Recruitment Intelligence OS · Python · Pandas · Streamlit")
