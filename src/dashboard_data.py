from pathlib import Path

import pandas as pd
import streamlit as st


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
REPORTS_DIR = BASE_DIR / "reports"


# ============================================================
# PAGE CONFIGURATION
# ============================================================

st.set_page_config(
    page_title="Recruitment Analytics Platform",
    page_icon="📊",
    layout="wide",
)


# ============================================================
# CUSTOM STYLING
# ============================================================

st.markdown(
    """
    <style>

    .main-title {
        font-size: 42px;
        font-weight: 700;
        margin-bottom: 5px;
    }

    .subtitle {
        font-size: 20px;
        color: #9ca3af;
        margin-bottom: 30px;
    }

    .section-title {
        font-size: 28px;
        font-weight: 650;
        margin-top: 25px;
        margin-bottom: 15px;
    }

    </style>
    """,
    unsafe_allow_html=True,
)


# ============================================================
# TITLE
# ============================================================

st.markdown(
    '<div class="main-title">📊 Recruitment Analytics Platform</div>',
    unsafe_allow_html=True,
)

st.markdown(
    '<div class="subtitle">'
    "Recruitment funnel, recruiter, client, role and technology analytics"
    "</div>",
    unsafe_allow_html=True,
)


# ============================================================
# REFRESH CONTROL
# ============================================================

col_refresh, col_info = st.columns([1, 5])

with col_refresh:
    if st.button("🔄 Refresh Data"):
        st.rerun()

with col_info:
    st.caption(
        "Dashboard reads the latest CSV reports from the reports/ folder."
    )


# ============================================================
# LOAD DATA
# ============================================================

def load_csv(filename):
    """Load a CSV report from the reports directory."""

    file_path = REPORTS_DIR / filename

    if not file_path.exists():
        st.error(f"Missing report file: {file_path}")
        st.stop()

    return pd.read_csv(file_path)


# IMPORTANT:
# No @st.cache_data here.
# This prevents the dashboard from showing old KPI values.

kpis = load_csv("kpi_summary.csv")
recruiters = load_csv("recruiter_performance.csv")
clients = load_csv("client_performance.csv")
roles = load_csv("role_performance.csv")
technologies = load_csv("technology_performance.csv")
sources = load_csv("source_performance.csv")
rejections = load_csv("rejection_analysis.csv")


# ============================================================
# KPI DICTIONARY
# ============================================================

kpi_values = dict(
    zip(
        kpis["metric"],
        kpis["value"],
    )
)


# ============================================================
# SAFE KPI FUNCTION
# ============================================================

def get_kpi(metric_name, default=0):
    """Safely retrieve a KPI value."""

    value = kpi_values.get(metric_name, default)

    try:
        value = float(value)

        if pd.isna(value):
            return default

        return value

    except (TypeError, ValueError):
        return default


# ============================================================
# KPI VALUES
# ============================================================

total_applications = get_kpi("Total Applications")

screening_selected = get_kpi("Screening Selected")

interviews_completed = get_kpi("Interviews Completed")

interview_selected = get_kpi("Interview Selected")

offers_accepted = get_kpi("Offers Accepted")

candidates_joined = get_kpi("Candidates Joined")

screening_rate = get_kpi("Screening Selection Rate (%)")

interview_rate = get_kpi("Interview Selection Rate (%)")

offer_acceptance_rate = get_kpi("Offer Acceptance Rate (%)")

joining_rate = get_kpi("Joining Rate (%)")

average_salary = get_kpi("Average Salary (LPA)")

average_time_to_hire = get_kpi("Average Time to Hire (Days)")


# ============================================================
# KEY RECRUITMENT KPIs
# ============================================================

st.markdown(
    '<div class="section-title">Key Recruitment KPIs</div>',
    unsafe_allow_html=True,
)


row1 = st.columns(4)

with row1[0]:
    st.metric(
        "Applications",
        f"{int(total_applications):,}",
    )

with row1[1]:
    st.metric(
        "Screening Selected",
        f"{int(screening_selected):,}",
    )

with row1[2]:
    st.metric(
        "Interviews",
        f"{int(interviews_completed):,}",
    )

with row1[3]:
    st.metric(
        "Candidates Joined",
        f"{int(candidates_joined):,}",
    )


row2 = st.columns(4)

with row2[0]:
    st.metric(
        "Screening Rate",
        f"{screening_rate:.2f}%",
    )

with row2[1]:
    st.metric(
        "Interview Rate",
        f"{interview_rate:.2f}%",
    )

with row2[2]:
    st.metric(
        "Offer Acceptance",
        f"{offer_acceptance_rate:.2f}%",
    )

with row2[3]:
    st.metric(
        "Avg Salary",
        f"₹{average_salary:.2f} LPA",
    )


st.divider()


# ============================================================
# HIRING FUNNEL
# ============================================================

st.markdown(
    '<div class="section-title">Hiring Funnel</div>',
    unsafe_allow_html=True,
)


funnel_data = pd.DataFrame(
    {
        "Stage": [
            "Applications",
            "Screening Selected",
            "Interviews",
            "Offers Accepted",
            "Candidates Joined",
        ],
        "Candidates": [
            total_applications,
            screening_selected,
            interviews_completed,
            offers_accepted,
            candidates_joined,
        ],
    }
)


st.bar_chart(
    funnel_data.set_index("Stage"),
    use_container_width=True,
)


# ============================================================
# FUNNEL SUMMARY
# ============================================================

funnel_col1, funnel_col2, funnel_col3, funnel_col4, funnel_col5 = st.columns(5)

with funnel_col1:
    st.metric(
        "Applications",
        f"{int(total_applications):,}",
    )

with funnel_col2:
    st.metric(
        "Screened",
        f"{int(screening_selected):,}",
    )

with funnel_col3:
    st.metric(
        "Interviews",
        f"{int(interviews_completed):,}",
    )

with funnel_col4:
    st.metric(
        "Offers",
        f"{int(offers_accepted):,}",
    )

with funnel_col5:
    st.metric(
        "Joined",
        f"{int(candidates_joined):,}",
    )


st.divider()


# ============================================================
# RECRUITER PERFORMANCE
# ============================================================

st.markdown(
    '<div class="section-title">Recruiter Performance</div>',
    unsafe_allow_html=True,
)

st.dataframe(
    recruiters,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# CLIENT PERFORMANCE
# ============================================================

st.markdown(
    '<div class="section-title">Client Performance</div>',
    unsafe_allow_html=True,
)

st.dataframe(
    clients,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# ROLE PERFORMANCE
# ============================================================

st.markdown(
    '<div class="section-title">Role Performance</div>',
    unsafe_allow_html=True,
)


role_chart_data = (
    roles
    .set_index("role")["joined"]
    .sort_values(ascending=False)
)

st.bar_chart(
    role_chart_data,
    use_container_width=True,
)

st.dataframe(
    roles,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# TECHNOLOGY ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">Technology Hiring Analysis</div>',
    unsafe_allow_html=True,
)


tech_col1, tech_col2 = st.columns(2)


with tech_col1:

    st.markdown("#### Applications by Technology")

    technology_applications = (
        technologies
        .set_index("technology")["applications"]
        .sort_values(ascending=False)
    )

    st.bar_chart(
        technology_applications,
        use_container_width=True,
    )


with tech_col2:

    st.markdown("#### Average Salary by Technology")

    technology_salary = (
        technologies
        .set_index("technology")["average_salary"]
        .sort_values(ascending=False)
    )

    st.bar_chart(
        technology_salary,
        use_container_width=True,
    )


st.dataframe(
    technologies,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# SOURCE ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">Recruitment Source Effectiveness</div>',
    unsafe_allow_html=True,
)


source_chart = (
    sources
    .set_index("source")["conversion_rate_%"]
    .sort_values(ascending=False)
)

st.bar_chart(
    source_chart,
    use_container_width=True,
)

st.dataframe(
    sources,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# REJECTION ANALYSIS
# ============================================================

st.markdown(
    '<div class="section-title">Candidate Rejection Analysis</div>',
    unsafe_allow_html=True,
)


rejection_chart = (
    rejections
    .set_index("rejection_reason")["count"]
    .sort_values(ascending=False)
)

st.bar_chart(
    rejection_chart,
    use_container_width=True,
)

st.dataframe(
    rejections,
    use_container_width=True,
    hide_index=True,
)


# ============================================================
# ADDITIONAL BUSINESS INSIGHTS
# ============================================================

st.markdown(
    '<div class="section-title">Business Insights</div>',
    unsafe_allow_html=True,
)


insight_col1, insight_col2, insight_col3 = st.columns(3)


# ------------------------------------------------------------
# TOP RECRUITER
# ------------------------------------------------------------

with insight_col1:

    if not recruiters.empty:

        top_recruiter = recruiters.iloc[0]

        st.info(
            f"""
            **🏆 Top Recruiter**

            **{top_recruiter['recruiter']}**

            Joining Rate:
            **{top_recruiter['joining_rate_%']:.2f}%**

            Candidates Joined:
            **{int(top_recruiter['joined'])}**
            """
        )


# ------------------------------------------------------------
# TOP CLIENT
# ------------------------------------------------------------

with insight_col2:

    if not clients.empty:

        top_client = (
            clients
            .sort_values(
                "joining_rate_%",
                ascending=False,
            )
            .iloc[0]
        )

        st.success(
            f"""
            **🏢 Best Client**

            **{top_client['client']}**

            Joining Rate:
            **{top_client['joining_rate_%']:.2f}%**

            Candidates Joined:
            **{int(top_client['joined'])}**
            """
        )


# ------------------------------------------------------------
# TOP TECHNOLOGY
# ------------------------------------------------------------

with insight_col3:

    if not technologies.empty:

        top_technology = (
            technologies
            .sort_values(
                "average_salary",
                ascending=False,
            )
            .iloc[0]
        )

        st.warning(
            f"""
            **💻 Highest Paying Technology**

            **{top_technology['technology']}**

            Average Salary:
            **₹{top_technology['average_salary']:.2f} LPA**

            Candidates Joined:
            **{int(top_technology['joined'])}**
            """
        )


# ============================================================
# RECRUITMENT SUMMARY
# ============================================================

st.markdown(
    '<div class="section-title">Recruitment Summary</div>',
    unsafe_allow_html=True,
)


summary_col1, summary_col2 = st.columns(2)


with summary_col1:

    st.metric(
        "Average Time to Hire",
        f"{average_time_to_hire:.2f} Days",
    )


with summary_col2:

    st.metric(
        "Joining Rate",
        f"{joining_rate:.2f}%",
    )


# ============================================================
# FOOTER
# ============================================================

st.divider()

st.caption(
    "Recruitment Analytics Platform | "
    "Python • Pandas • SQL • Streamlit • Data Analytics"
)