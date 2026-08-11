from pathlib import Path
import random
from datetime import datetime, timedelta

import pandas as pd


# ---------------------------------------------------------
# PROJECT PATHS
# ---------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

OUTPUT_FILE = DATA_DIR / "recruitment_data.csv"


# ---------------------------------------------------------
# SAMPLE BUSINESS DATA
# ---------------------------------------------------------

FIRST_NAMES = [
    "Rahul", "Amit", "Priya", "Sneha", "Arjun",
    "Kiran", "Neha", "Vikram", "Ananya", "Rohit",
    "Pooja", "Sanjay", "Meera", "Nikhil", "Swathi"
]

LAST_NAMES = [
    "Kumar", "Sharma", "Reddy", "Patel", "Verma",
    "Singh", "Rao", "Gupta", "Das", "Naidu"
]

RECRUITERS = [
    "Recruiter A",
    "Recruiter B",
    "Recruiter C",
    "Recruiter D",
    "Recruiter E"
]

CLIENTS = [
    "TechCorp",
    "Global Systems",
    "FinServe",
    "HealthTech",
    "CloudWorks",
    "Enterprise Solutions",
    "DataSystems",
    "DigitalWorks"
]

ROLES = [
    "Python Developer",
    "Data Analyst",
    "Cloud Support Engineer",
    "Technical Support Engineer",
    "AI Engineer",
    "GCP Engineer",
    "Software Engineer",
    "IT Support Engineer"
]

TECHNOLOGIES = [
    "Python",
    "SQL",
    "GCP",
    "Java",
    "AWS",
    "Power BI",
    "Linux",
    "C#"
]

LOCATIONS = [
    "Hyderabad",
    "Bangalore",
    "Chennai",
    "Pune",
    "Mumbai",
    "Delhi NCR"
]

SOURCES = [
    "LinkedIn",
    "Naukri",
    "Indeed",
    "Employee Referral",
    "Company Website",
    "Recruiter Sourcing"
]

REJECTION_REASONS = [
    "Skills mismatch",
    "Experience mismatch",
    "Client rejected",
    "Candidate withdrew",
    "Salary expectations",
    "Position closed",
    "Interview failed"
]


# ---------------------------------------------------------
# DATA GENERATION
# ---------------------------------------------------------

def generate_recruitment_data(number_of_records=1000):

    random.seed(42)

    records = []

    start_date = datetime(2026, 1, 1)

    for i in range(1, number_of_records + 1):

        candidate_id = f"CAND{i:05d}"

        first_name = random.choice(FIRST_NAMES)
        last_name = random.choice(LAST_NAMES)

        candidate_name = f"{first_name} {last_name}"

        application_date = start_date + timedelta(
            days=random.randint(0, 220)
        )

        recruiter = random.choice(RECRUITERS)
        client = random.choice(CLIENTS)
        role = random.choice(ROLES)
        technology = random.choice(TECHNOLOGIES)
        location = random.choice(LOCATIONS)
        source = random.choice(SOURCES)

        experience = random.randint(0, 8)

        # ---------------------------------------------
        # SCREENING
        # ---------------------------------------------

        screening_status = random.choices(
            ["Selected", "Rejected"],
            weights=[72, 28]
        )[0]

        # ---------------------------------------------
        # INTERVIEW
        # ---------------------------------------------

        if screening_status == "Selected":

            interview_status = random.choices(
                ["Selected", "Rejected", "No Show"],
                weights=[58, 32, 10]
            )[0]

            interview_date = application_date + timedelta(
                days=random.randint(2, 12)
            )

        else:

            interview_status = "Not Scheduled"
            interview_date = None

        # ---------------------------------------------
        # OFFER
        # ---------------------------------------------

        if interview_status == "Selected":

            offer_status = random.choices(
                ["Accepted", "Rejected"],
                weights=[78, 22]
            )[0]

            offer_date = interview_date + timedelta(
                days=random.randint(1, 7)
            )

        else:

            offer_status = "Not Applicable"
            offer_date = None

        # ---------------------------------------------
        # JOINING
        # ---------------------------------------------

        if offer_status == "Accepted":

            joining_status = random.choices(
                ["Joined", "Candidate Dropped"],
                weights=[85, 15]
            )[0]

            joining_date = offer_date + timedelta(
                days=random.randint(7, 45)
            )

        else:

            joining_status = "Not Applicable"
            joining_date = None

        # ---------------------------------------------
        # SALARY
        # ---------------------------------------------

        if offer_status == "Accepted":

            salary_lpa = round(
                random.uniform(4.0, 18.0),
                2
            )

        else:

            salary_lpa = None

        # ---------------------------------------------
        # REJECTION REASON
        # ---------------------------------------------

        if screening_status == "Rejected":

            rejection_reason = random.choice(
                REJECTION_REASONS
            )

        elif interview_status in ["Rejected", "No Show"]:

            rejection_reason = random.choice(
                REJECTION_REASONS
            )

        elif offer_status == "Rejected":

            rejection_reason = random.choice(
                REJECTION_REASONS
            )

        elif joining_status == "Candidate Dropped":

            rejection_reason = "Candidate withdrew"

        else:

            rejection_reason = None

        # ---------------------------------------------
        # RECORD
        # ---------------------------------------------

        records.append({

            "candidate_id": candidate_id,

            "candidate_name": candidate_name,

            "application_date": application_date.date(),

            "recruiter": recruiter,

            "client": client,

            "role": role,

            "technology": technology,

            "experience_years": experience,

            "location": location,

            "source": source,

            "screening_status": screening_status,

            "interview_status": interview_status,

            "interview_date": (
                interview_date.date()
                if interview_date
                else None
            ),

            "offer_status": offer_status,

            "offer_date": (
                offer_date.date()
                if offer_date
                else None
            ),

            "joining_status": joining_status,

            "joining_date": (
                joining_date.date()
                if joining_date
                else None
            ),

            "salary_lpa": salary_lpa,

            "rejection_reason": rejection_reason
        })

    df = pd.DataFrame(records)

    DATA_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    df.to_csv(
        OUTPUT_FILE,
        index=False
    )

    print("\n========================================")
    print("RECRUITMENT DATASET CREATED")
    print("========================================")
    print(f"Records created : {len(df)}")
    print(f"Columns         : {len(df.columns)}")
    print(f"Output file     : {OUTPUT_FILE}")
    print("========================================")

    print("\nFirst 5 records:")
    print(df.head())

    print("\nDataset shape:")
    print(df.shape)


# ---------------------------------------------------------
# RUN PROGRAM
# ---------------------------------------------------------

if __name__ == "__main__":
    generate_recruitment_data(1000)