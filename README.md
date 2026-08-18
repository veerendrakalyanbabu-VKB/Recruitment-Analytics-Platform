# 📊 Recruitment Analytics Platform

An end-to-end Recruitment Analytics Platform designed to help recruitment teams monitor hiring pipelines, analyze recruiter performance, track candidate progress, and make data-driven hiring decisions.

Built using **Python, Pandas, Streamlit, SQLite and Data Analytics**.

**🌐 Live Demo:** [recruitment-analytics-platform-vkb.streamlit.app](https://recruitment-analytics-platform-vkb.streamlit.app/)

---

## 🚀 Project Overview

The Recruitment Analytics Platform provides a centralized view of the recruitment lifecycle, from candidate application through screening, interviews, offers and joining.

The platform transforms recruitment data into actionable insights through interactive dashboards, KPIs, analytics and candidate management features.

### Recruitment Lifecycle

Application
↓
Screening
↓
Interview
↓
Selection
↓
Offer
↓
Joining

---

## ⚡ Quick Start

```powershell
git clone https://github.com/veerendrakalyanbabu-VKB/Recruitment-Analytics-Platform.git
cd Recruitment-Analytics-Platform
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python -m streamlit run src\dashboard.py
```

Open the URL shown in the terminal (usually `http://localhost:8501`). Use the sidebar to open **Candidate Management** from the `pages/` module.

### Upload your company CSV

1. Run the dashboard locally.
2. In the sidebar, choose **Upload CSV**.
3. Upload a recruitment export (e.g. `sample_data/recruitment_dataset_10000.csv`).
4. The platform auto-detects columns such as `Interview_Status` + `Interview_Result` and calculates KPIs in-session.

Or view the deployed app: [recruitment-analytics-platform-vkb.streamlit.app](https://recruitment-analytics-platform-vkb.streamlit.app/)

### Run tests

```powershell
python -m pytest tests/ -v
```

---

## 🎯 Key Features

### 📈 Recruitment Dashboard

The main dashboard provides real-time recruitment insights including:

- CSV upload with automatic column mapping
- Separate handling of Status + Result fields (e.g. Interview Status vs Interview Result)
- Executive intelligence insights and action center
- Total Applications
- Screening Selected
- Interviews Completed
- Interview Selection Rate
- Offers Accepted
- Candidates Joined
- Screening Rate
- Interview Rate
- Offer Acceptance Rate
- Joining Rate
- Average Offered Salary
- Hiring Funnel

---

### 👥 Candidate Management

Candidate Management functionality allows recruitment teams to:

- View candidate records
- Search candidates
- Filter candidates
- Track candidate status
- Monitor recruitment progress
- Review candidate information
- Manage recruitment pipeline data

---

### 👨‍💼 Recruiter Analytics

Recruitment teams can analyze:

- Recruiter workload
- Applications handled
- Candidate pipeline
- Recruiter performance
- Hiring contribution

---

### 🏢 Client Analytics

Track recruitment activity across clients:

- Applications by client
- Candidate pipeline
- Hiring volume
- Client recruitment performance

---

### 💼 Role Analytics

Analyze recruitment demand by:

- Job role
- Position
- Technology
- Experience
- Candidate volume

---

### 💻 Technology Analytics

Identify recruitment trends across technologies and technical skill areas.

---

### 📌 Recruitment Source Analytics

Analyze candidate acquisition channels such as:

- Job portals
- Referrals
- LinkedIn
- Direct applications
- Recruitment sources

This helps organizations understand which sourcing channels generate the strongest candidate pipeline.

---

## 📊 Key Recruitment KPIs

| KPI | Description |
|---|---|
| Applications | Total candidates entering the recruitment pipeline |
| Screening Rate | Percentage of applications selected during screening |
| Interviews Completed | Candidates who completed an interview |
| Interview Selection Rate | Percentage of completed interviews resulting in selection |
| Offer Acceptance Rate | Percentage of selected candidates accepting offers |
| Joining Rate | Percentage of accepted offers resulting in joining |
| Average Salary | Average offered salary in LPA |
| Time to Hire | Average number of days required to hire a candidate |

---

## 🛠️ Technology Stack

### Programming & Data

- Python
- Pandas
- NumPy

### Dashboard & Visualization

- Streamlit
- Streamlit Charts

### Database

- SQLite
- SQL

### Development

- VS Code
- Git
- GitHub
- Python Virtual Environment

### Data Processing

- CSV
- Data Cleaning
- Data Transformation
- KPI Calculation
- Recruitment Funnel Analysis

---

## 📁 Project Structure

```text
Recruitment-Analytics-Platform/
│
├── data/
│   ├── recruitment_data.csv
│   ├── recruitment_data_cleaned.csv
│   └── recruitment.db
│
├── docs/
│
├── notebooks/
│
├── pages/
│   └── candidate_management.py
│
├── reports/
│   ├── client_performance.csv
│   ├── kpi_summary.csv
│   ├── kpis.csv
│   ├── recruiter_performance.csv
│   ├── rejection_analysis.csv
│   ├── role_analysis.csv
│   ├── role_performance.csv
│   ├── source_analysis.csv
│   ├── source_performance.csv
│   ├── technology_analysis.csv
│   └── technology_performance.csv
│
├── sql/
│
├── src/
│   ├── analysis.py
│   ├── dashboard.py
│   ├── dashboard_data.py
│   ├── data_cleaning.py
│   ├── data_loader.py
│   ├── db.py
│   ├── generate_data.py
│   └── kpi_engine.py
│
├── sample_data/
│   └── recruitment_dataset_10000.csv
│
├── tests/
│   └── test_upload_pipeline.py
├── .gitignore
├── README.md
└── requirements.txt