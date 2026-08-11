from pathlib import Path
import pandas as pd


# ============================================================
# PROJECT PATHS
# ============================================================

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"

INPUT_FILE = DATA_DIR / "recruitment_data_cleaned.csv"


# ============================================================
# LOAD DATA
# ============================================================

def load_data():
    """Load cleaned recruitment data."""

    df = pd.read_csv(INPUT_FILE)

    print(f"Dataset loaded: {df.shape}")

    return df


# ============================================================
# KPI CALCULATIONS
# ============================================================

def calculate_kpis(df):
    """Calculate recruitment KPIs."""

    # --------------------------------------------------------
    # Total applications
    # --------------------------------------------------------

    total_applications = len(df)

    # --------------------------------------------------------
    # Screening
    # --------------------------------------------------------

    screening_selected = (
        df["screening_status"]
        .eq("Selected")
        .sum()
    )

    # --------------------------------------------------------
    # Interviews
    #
    # Business definition:
    # Selected + Rejected = Completed interviews
    #
    # Not Scheduled and No Show are NOT completed interviews.
    # --------------------------------------------------------

    interviews_completed = (
        df["interview_status"]
        .isin(["Selected", "Rejected"])
        .sum()
    )

    interview_selected = (
        df["interview_status"]
        .eq("Selected")
        .sum()
    )

    # --------------------------------------------------------
    # Offers
    # --------------------------------------------------------

    offers_accepted = (
        df["offer_status"]
        .eq("Accepted")
        .sum()
    )

    offers_rejected = (
        df["offer_status"]
        .eq("Rejected")
        .sum()
    )

    offers_made = offers_accepted + offers_rejected

    # --------------------------------------------------------
    # Joining
    # --------------------------------------------------------

    candidates_joined = (
        df["joining_status"]
        .eq("Joined")
        .sum()
    )

    # --------------------------------------------------------
    # Salary
    # --------------------------------------------------------

    avg_salary = df["salary_lpa"].mean()

    # --------------------------------------------------------
    # Time to hire
    # --------------------------------------------------------

    avg_time_to_hire = df["time_to_hire_days"].mean()

    # --------------------------------------------------------
    # Rates
    # --------------------------------------------------------

    screening_rate = (
        screening_selected / total_applications * 100
        if total_applications > 0
        else 0
    )

    interview_selection_rate = (
        interview_selected / interviews_completed * 100
        if interviews_completed > 0
        else 0
    )

    offer_acceptance_rate = (
        offers_accepted / offers_made * 100
        if offers_made > 0
        else 0
    )

    joining_rate = (
        candidates_joined / offers_accepted * 100
        if offers_accepted > 0
        else 0
    )

    # --------------------------------------------------------
    # KPI dictionary
    # --------------------------------------------------------

    kpis = {
        "Total Applications": total_applications,
        "Screening Selected": screening_selected,
        "Interviews Completed": interviews_completed,
        "Interview Selected": interview_selected,
        "Offers Accepted": offers_accepted,
        "Candidates Joined": candidates_joined,

        "Screening Selection Rate (%)":
            round(screening_rate, 2),

        "Interview Selection Rate (%)":
            round(interview_selection_rate, 2),

        "Offer Acceptance Rate (%)":
            round(offer_acceptance_rate, 2),

        "Joining Rate (%)":
            round(joining_rate, 2),

        "Average Salary (LPA)":
            round(avg_salary, 2),

        "Average Time to Hire (Days)":
            round(avg_time_to_hire, 2),
    }

    return kpis


# ============================================================
# RECRUITER ANALYSIS
# ============================================================

def recruiter_analysis(df):
    """Analyze recruiter performance."""

    result = (
        df.groupby("recruiter")
        .agg(
            applications=("candidate_id", "count"),

            interviews=(
                "interview_status",
                lambda x: x.isin(
                    ["Selected", "Rejected"]
                ).sum()
            ),

            offers=(
                "offer_status",
                lambda x: (x == "Accepted").sum()
            ),

            joined=(
                "joining_status",
                lambda x: (x == "Joined").sum()
            ),

            average_salary=(
                "salary_lpa",
                "mean"
            ),
        )
        .reset_index()
    )

    result["joining_rate_%"] = (
        result["joined"]
        / result["applications"]
        * 100
    ).round(2)

    result["average_salary"] = (
        result["average_salary"]
        .round(2)
    )

    return result.sort_values(
        "joining_rate_%",
        ascending=False
    )


# ============================================================
# CLIENT ANALYSIS
# ============================================================

def client_analysis(df):
    """Analyze client performance."""

    result = (
        df.groupby("client")
        .agg(
            applications=("candidate_id", "count"),

            interviews=(
                "interview_status",
                lambda x: x.isin(
                    ["Selected", "Rejected"]
                ).sum()
            ),

            offers=(
                "offer_status",
                lambda x: (x == "Accepted").sum()
            ),

            joined=(
                "joining_status",
                lambda x: (x == "Joined").sum()
            ),

            average_salary=(
                "salary_lpa",
                "mean"
            ),
        )
        .reset_index()
    )

    result["joining_rate_%"] = (
        result["joined"]
        / result["applications"]
        * 100
    ).round(2)

    result["average_salary"] = (
        result["average_salary"]
        .round(2)
    )

    return result.sort_values(
        "joining_rate_%",
        ascending=False
    )


# ============================================================
# ROLE ANALYSIS
# ============================================================

def role_analysis(df):
    """Analyze recruitment performance by role."""

    result = (
        df.groupby("role")
        .agg(
            applications=("candidate_id", "count"),

            interviews=(
                "interview_status",
                lambda x: x.isin(
                    ["Selected", "Rejected"]
                ).sum()
            ),

            offers=(
                "offer_status",
                lambda x: (x == "Accepted").sum()
            ),

            joined=(
                "joining_status",
                lambda x: (x == "Joined").sum()
            ),

            average_salary=(
                "salary_lpa",
                "mean"
            ),
        )
        .reset_index()
    )

    result["joining_rate_%"] = (
        result["joined"]
        / result["applications"]
        * 100
    ).round(2)

    result["average_salary"] = (
        result["average_salary"]
        .round(2)
    )

    return result.sort_values(
        "joining_rate_%",
        ascending=False
    )


# ============================================================
# SOURCE ANALYSIS
# ============================================================

def source_analysis(df):
    """Analyze candidate source performance."""

    result = (
        df.groupby("source")
        .agg(
            applications=("candidate_id", "count"),

            interviews=(
                "interview_status",
                lambda x: x.isin(
                    ["Selected", "Rejected"]
                ).sum()
            ),

            offers=(
                "offer_status",
                lambda x: (x == "Accepted").sum()
            ),

            joined=(
                "joining_status",
                lambda x: (x == "Joined").sum()
            ),
        )
        .reset_index()
    )

    result["conversion_rate_%"] = (
        result["joined"]
        / result["applications"]
        * 100
    ).round(2)

    return result.sort_values(
        "conversion_rate_%",
        ascending=False
    )


# ============================================================
# TECHNOLOGY ANALYSIS
# ============================================================

def technology_analysis(df):
    """Analyze recruitment performance by technology."""

    result = (
        df.groupby("technology")
        .agg(
            applications=("candidate_id", "count"),

            interviews=(
                "interview_status",
                lambda x: x.isin(
                    ["Selected", "Rejected"]
                ).sum()
            ),

            offers=(
                "offer_status",
                lambda x: (x == "Accepted").sum()
            ),

            joined=(
                "joining_status",
                lambda x: (x == "Joined").sum()
            ),

            average_salary=(
                "salary_lpa",
                "mean"
            ),
        )
        .reset_index()
    )

    result["average_salary"] = (
        result["average_salary"]
        .round(2)
    )

    result["joining_rate_%"] = (
        result["joined"]
        / result["applications"]
        * 100
    ).round(2)

    return result.sort_values(
        "average_salary",
        ascending=False
    )


# ============================================================
# REJECTION ANALYSIS
# ============================================================

def rejection_analysis(df):
    """Analyze reasons candidates were rejected."""

    result = (
        df["rejection_reason"]
        .dropna()
        .value_counts()
        .reset_index()
    )

    result.columns = [
        "rejection_reason",
        "count"
    ]

    return result


# ============================================================
# KPI REPORT
# ============================================================

def save_kpi_report(kpis):
    """Save KPI summary for Streamlit dashboard."""

    kpi_df = pd.DataFrame(
        list(kpis.items()),
        columns=["metric", "value"]
    )

    kpi_df.to_csv(
        REPORTS_DIR / "kpi_summary.csv",
        index=False
    )


# ============================================================
# SAVE ALL REPORTS
# ============================================================

def save_reports(df):
    """Generate CSV reports for dashboarding."""

    REPORTS_DIR.mkdir(
        exist_ok=True
    )

    # --------------------------------------------------------
    # KPI report
    # --------------------------------------------------------

    kpis = calculate_kpis(df)

    save_kpi_report(kpis)

    # --------------------------------------------------------
    # Recruiter report
    # --------------------------------------------------------

    recruiter_df = recruiter_analysis(df)

    recruiter_df.to_csv(
        REPORTS_DIR / "recruiter_performance.csv",
        index=False
    )

    # --------------------------------------------------------
    # Client report
    # --------------------------------------------------------

    client_df = client_analysis(df)

    client_df.to_csv(
        REPORTS_DIR / "client_performance.csv",
        index=False
    )

    # --------------------------------------------------------
    # Role report
    # --------------------------------------------------------

    role_df = role_analysis(df)

    role_df.to_csv(
        REPORTS_DIR / "role_performance.csv",
        index=False
    )

    # Keep the original filename too
    role_df.to_csv(
        REPORTS_DIR / "role_analysis.csv",
        index=False
    )

    # --------------------------------------------------------
    # Source report
    # --------------------------------------------------------

    source_df = source_analysis(df)

    source_df.to_csv(
        REPORTS_DIR / "source_performance.csv",
        index=False
    )

    # Keep original filename too
    source_df.to_csv(
        REPORTS_DIR / "source_analysis.csv",
        index=False
    )

    # --------------------------------------------------------
    # Technology report
    # --------------------------------------------------------

    technology_df = technology_analysis(df)

    technology_df.to_csv(
        REPORTS_DIR / "technology_performance.csv",
        index=False
    )

    # Keep original filename too
    technology_df.to_csv(
        REPORTS_DIR / "technology_analysis.csv",
        index=False
    )

    # --------------------------------------------------------
    # Rejection report
    # --------------------------------------------------------

    rejection_df = rejection_analysis(df)

    rejection_df.to_csv(
        REPORTS_DIR / "rejection_analysis.csv",
        index=False
    )

    print("\nReports generated successfully.")

    print(f"Reports directory: {REPORTS_DIR}")


# ============================================================
# MAIN
# ============================================================

def main():

    # --------------------------------------------------------
    # Load data
    # --------------------------------------------------------

    df = load_data()

    # --------------------------------------------------------
    # Calculate KPIs
    # --------------------------------------------------------

    kpis = calculate_kpis(df)

    print("\n========== KEY KPIs ==========")

    for name, value in kpis.items():
        print(f"{name}: {value}")

    # --------------------------------------------------------
    # Recruiter analysis
    # --------------------------------------------------------

    print("\n========== RECRUITER ANALYSIS ==========")

    print(
        recruiter_analysis(df)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Client analysis
    # --------------------------------------------------------

    print("\n========== CLIENT ANALYSIS ==========")

    print(
        client_analysis(df)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Role analysis
    # --------------------------------------------------------

    print("\n========== ROLE ANALYSIS ==========")

    print(
        role_analysis(df)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Source analysis
    # --------------------------------------------------------

    print("\n========== SOURCE ANALYSIS ==========")

    print(
        source_analysis(df)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Technology analysis
    # --------------------------------------------------------

    print("\n========== TECHNOLOGY ANALYSIS ==========")

    print(
        technology_analysis(df)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Rejection analysis
    # --------------------------------------------------------

    print("\n========== REJECTION ANALYSIS ==========")

    print(
        rejection_analysis(df)
        .to_string(index=False)
    )

    # --------------------------------------------------------
    # Save reports
    # --------------------------------------------------------

    save_reports(df)


# ============================================================
# ENTRY POINT
# ============================================================

if __name__ == "__main__":
    main()