"""Application configuration and paths."""

from pathlib import Path

# src/app/config.py -> project root is two levels up from app/
APP_DIR = Path(__file__).resolve().parent
SRC_DIR = APP_DIR.parent
BASE_DIR = SRC_DIR.parent

DATA_DIR = BASE_DIR / "data"
REPORTS_DIR = BASE_DIR / "reports"
SAMPLE_DATA_DIR = BASE_DIR / "sample_data"

CLEANED_FILE = DATA_DIR / "recruitment_data_cleaned.csv"
RAW_FILE = DATA_DIR / "recruitment_data.csv"
SAMPLE_10K = SAMPLE_DATA_DIR / "recruitment_dataset_10000.csv"

APP_TITLE = "Recruitment Intelligence OS"
APP_SUBTITLE = "Enterprise recruitment analytics · ATS intelligence · Executive command center"

# Default pipeline aging thresholds (days)
AGING_HEALTHY_MAX = 7
AGING_WATCH_MAX = 14
AGING_AGING_MAX = 30
