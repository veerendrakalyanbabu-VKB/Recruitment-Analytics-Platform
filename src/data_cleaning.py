from pathlib import Path
import pandas as pd


# Project paths
BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

INPUT_FILE = DATA_DIR / "recruitment_data.csv"


def clean_recruitment_data():
    """
    Load and clean the recruitment dataset.
    """

    # Load raw data
    df = pd.read_csv(INPUT_FILE)

    print("\n--- Original Dataset ---")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    # Standardize column names
    df.columns = (
        df.columns
        .str.strip()
        .str.lower()
        .str.replace(" ", "_")
    )

    # Remove duplicate records
    df = df.drop_duplicates()

    # Remove leading/trailing spaces from text fields
    text_columns = df.select_dtypes(include="object").columns

    for column in text_columns:
        df[column] = df[column].astype(str).str.strip()

    # Standardize date columns
    date_columns = [
        "application_date",
        "interview_date",
        "offer_date",
        "joining_date"
    ]

    for column in date_columns:
        if column in df.columns:
            df[column] = pd.to_datetime(
                df[column],
                errors="coerce"
            )

    # Standardize salary
    if "salary_lpa" in df.columns:
        df["salary_lpa"] = pd.to_numeric(
            df["salary_lpa"],
            errors="coerce"
        )

    # Create useful recruitment metric
    if "application_date" in df.columns and "joining_date" in df.columns:
        df["time_to_hire_days"] = (
            df["joining_date"] - df["application_date"]
        ).dt.days

    # Save cleaned dataset
    cleaned_file = DATA_DIR / "recruitment_data_cleaned.csv"

    df.to_csv(cleaned_file, index=False)

    print("\n--- Cleaning Completed ---")
    print(f"Rows after cleaning: {len(df)}")
    print(f"Cleaned file: {cleaned_file}")

    return df


if __name__ == "__main__":
    clean_recruitment_data()