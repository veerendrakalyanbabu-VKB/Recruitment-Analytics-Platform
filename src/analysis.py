from pathlib import Path
import pandas as pd

from kpi_engine import build_col_map, compute_kpis, kpis_to_dict, group_kpis_by


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
    """Calculate recruitment KPIs using the shared status+result engine."""
    col = build_col_map(df)
    return kpis_to_dict(compute_kpis(df, col))


# ============================================================
# RECRUITER ANALYSIS
# ============================================================

def _group_performance(df, group_col: str):
    """Aggregate funnel metrics by a dimension using the shared KPI engine."""
    return group_kpis_by(df, group_col)


def recruiter_analysis(df):
    """Analyze recruiter performance."""
    return _group_performance(df, "recruiter")


# ============================================================
# CLIENT ANALYSIS
# ============================================================

def client_analysis(df):
    """Analyze client performance."""
    return _group_performance(df, "client")


# ============================================================
# ROLE ANALYSIS
# ============================================================

def role_analysis(df):
    """Analyze recruitment performance by role."""
    return _group_performance(df, "role")


# ============================================================
# SOURCE ANALYSIS
# ============================================================

def source_analysis(df):
    """Analyze candidate source performance."""
    result = _group_performance(df, "source")
    result = result.rename(columns={"joining_rate_%": "conversion_rate_%"})
    return result.sort_values("conversion_rate_%", ascending=False)


# ============================================================
# TECHNOLOGY ANALYSIS
# ============================================================

def technology_analysis(df):
    """Analyze recruitment performance by technology."""
    result = _group_performance(df, "technology")
    return result.sort_values("average_salary", ascending=False)


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