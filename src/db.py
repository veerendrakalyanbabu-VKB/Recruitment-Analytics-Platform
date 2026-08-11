from __future__ import annotations

import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Any, Iterable

import pandas as pd


# ============================================================
# DATABASE CONFIGURATION
# ============================================================

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"
DB_PATH = DATA_DIR / "recruitment.db"
RAW_CSV = DATA_DIR / "recruitment_data_cleaned.csv"


SCHEMA = """
CREATE TABLE IF NOT EXISTS candidates (
    candidate_id TEXT PRIMARY KEY,
    candidate_name TEXT,
    application_date TEXT,
    recruiter TEXT,
    client TEXT,
    role TEXT,
    technology TEXT,
    experience_years REAL,
    location TEXT,
    source TEXT,

    screening_status TEXT,
    interview_status TEXT,
    interview_date TEXT,

    offer_status TEXT,
    offer_date TEXT,

    joining_status TEXT,
    joining_date TEXT,

    salary_lpa REAL,
    rejection_reason TEXT,
    time_to_hire_days REAL,

    created_at TEXT DEFAULT CURRENT_TIMESTAMP,
    updated_at TEXT DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_candidates_recruiter
ON candidates(recruiter);

CREATE INDEX IF NOT EXISTS idx_candidates_client
ON candidates(client);

CREATE INDEX IF NOT EXISTS idx_candidates_role
ON candidates(role);

CREATE INDEX IF NOT EXISTS idx_candidates_screening
ON candidates(screening_status);

CREATE INDEX IF NOT EXISTS idx_candidates_interview
ON candidates(interview_status);

CREATE INDEX IF NOT EXISTS idx_candidates_offer
ON candidates(offer_status);

CREATE INDEX IF NOT EXISTS idx_candidates_joining
ON candidates(joining_status);


CREATE TABLE IF NOT EXISTS audit_log (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    candidate_id TEXT,
    action TEXT NOT NULL,
    old_value TEXT,
    new_value TEXT,
    changed_by TEXT DEFAULT 'system',
    changed_at TEXT DEFAULT CURRENT_TIMESTAMP
);
"""


@contextmanager
def get_connection():
    """Open a SQLite connection with safe defaults."""
    DATA_DIR.mkdir(parents=True, exist_ok=True)

    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row

    try:
        conn.execute("PRAGMA foreign_keys = ON")
        conn.execute("PRAGMA journal_mode = WAL")
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def init_db() -> None:
    """Create tables and indexes if they do not already exist."""
    with get_connection() as conn:
        conn.executescript(SCHEMA)


def _clean_value(value: Any) -> Any:
    if pd.isna(value):
        return None
    return value


def import_csv_if_empty(csv_path: Path | None = None) -> int:
    """
    Import the cleaned CSV only when the candidates table is empty.

    Existing database records are never overwritten by this function.
    Returns the number of imported candidates.
    """
    init_db()

    csv_path = csv_path or RAW_CSV

    with get_connection() as conn:
        existing = conn.execute(
            "SELECT COUNT(*) AS count FROM candidates"
        ).fetchone()["count"]

    if existing:
        return 0

    if not csv_path.exists():
        return 0

    df = pd.read_csv(csv_path)
    df = df.loc[:, ~df.columns.astype(str).str.startswith("Unnamed")]

    expected = [
        "candidate_id",
        "candidate_name",
        "application_date",
        "recruiter",
        "client",
        "role",
        "technology",
        "experience_years",
        "location",
        "source",
        "screening_status",
        "interview_status",
        "interview_date",
        "offer_status",
        "offer_date",
        "joining_status",
        "joining_date",
        "salary_lpa",
        "rejection_reason",
        "time_to_hire_days",
    ]

    for column in expected:
        if column not in df.columns:
            df[column] = None

    df = df[expected]

    records = [
        tuple(_clean_value(value) for value in row)
        for row in df.itertuples(index=False, name=None)
    ]

    with get_connection() as conn:
        conn.executemany(
            """
            INSERT OR IGNORE INTO candidates (
                candidate_id, candidate_name, application_date,
                recruiter, client, role, technology, experience_years,
                location, source, screening_status, interview_status,
                interview_date, offer_status, offer_date,
                joining_status, joining_date, salary_lpa,
                rejection_reason, time_to_hire_days
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            records,
        )

    return len(records)


def get_candidate(candidate_id: str) -> dict[str, Any] | None:
    init_db()

    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM candidates WHERE candidate_id = ?",
            (candidate_id,),
        ).fetchone()

    return dict(row) if row else None


def list_candidates(
    search: str = "",
    recruiter: str = "",
    client: str = "",
    role: str = "",
    limit: int = 500,
) -> pd.DataFrame:
    """Return candidates matching operational filters."""
    init_db()

    query = """
        SELECT *
        FROM candidates
        WHERE 1 = 1
    """
    params: list[Any] = []

    if search.strip():
        query += """
            AND (
                candidate_id LIKE ?
                OR candidate_name LIKE ?
                OR role LIKE ?
                OR technology LIKE ?
            )
        """
        term = f"%{search.strip()}%"
        params.extend([term, term, term, term])

    if recruiter:
        query += " AND recruiter = ?"
        params.append(recruiter)

    if client:
        query += " AND client = ?"
        params.append(client)

    if role:
        query += " AND role = ?"
        params.append(role)

    query += " ORDER BY updated_at DESC LIMIT ?"
    params.append(max(1, min(int(limit), 5000)))

    with get_connection() as conn:
        return pd.read_sql_query(query, conn, params=params)


def create_candidate(data: dict[str, Any], changed_by: str = "recruiter") -> str:
    """Create a new candidate and record the creation in audit_log."""
    init_db()

    required = ["candidate_id", "candidate_name", "role"]
    missing = [field for field in required if not str(data.get(field, "")).strip()]

    if missing:
        raise ValueError(
            "Missing required fields: " + ", ".join(missing)
        )

    candidate_id = str(data["candidate_id"]).strip()

    columns = [
        "candidate_id", "candidate_name", "application_date",
        "recruiter", "client", "role", "technology",
        "experience_years", "location", "source",
        "screening_status", "interview_status", "interview_date",
        "offer_status", "offer_date", "joining_status",
        "joining_date", "salary_lpa", "rejection_reason",
        "time_to_hire_days",
    ]

    values = [_clean_value(data.get(column)) for column in columns]

    with get_connection() as conn:
        exists = conn.execute(
            "SELECT 1 FROM candidates WHERE candidate_id = ?",
            (candidate_id,),
        ).fetchone()

        if exists:
            raise ValueError(
                f"Candidate ID '{candidate_id}' already exists."
            )

        placeholders = ", ".join(["?"] * len(columns))
        column_sql = ", ".join(columns)

        conn.execute(
            f"""
            INSERT INTO candidates ({column_sql})
            VALUES ({placeholders})
            """,
            values,
        )

        conn.execute(
            """
            INSERT INTO audit_log
            (candidate_id, action, old_value, new_value, changed_by)
            VALUES (?, ?, ?, ?, ?)
            """,
            (
                candidate_id,
                "CREATE",
                None,
                "Candidate created",
                changed_by,
            ),
        )

    return candidate_id


def update_candidate(
    candidate_id: str,
    updates: dict[str, Any],
    changed_by: str = "recruiter",
) -> bool:
    """
    Update candidate fields and create one audit entry per changed field.
    """
    init_db()

    allowed = {
        "candidate_name",
        "application_date",
        "recruiter",
        "client",
        "role",
        "technology",
        "experience_years",
        "location",
        "source",
        "screening_status",
        "interview_status",
        "interview_date",
        "offer_status",
        "offer_date",
        "joining_status",
        "joining_date",
        "salary_lpa",
        "rejection_reason",
        "time_to_hire_days",
    }

    updates = {
        key: value
        for key, value in updates.items()
        if key in allowed
    }

    if not updates:
        return False

    with get_connection() as conn:
        old = conn.execute(
            "SELECT * FROM candidates WHERE candidate_id = ?",
            (candidate_id,),
        ).fetchone()

        if not old:
            raise ValueError(
                f"Candidate '{candidate_id}' was not found."
            )

        for field, new_value in updates.items():
            old_value = old[field]
            new_value = _clean_value(new_value)

            old_text = "" if old_value is None else str(old_value)
            new_text = "" if new_value is None else str(new_value)

            if old_text == new_text:
                continue

            conn.execute(
                f"""
                UPDATE candidates
                SET {field} = ?, updated_at = CURRENT_TIMESTAMP
                WHERE candidate_id = ?
                """,
                (new_value, candidate_id),
            )

            conn.execute(
                """
                INSERT INTO audit_log
                (candidate_id, action, old_value, new_value, changed_by)
                VALUES (?, ?, ?, ?, ?)
                """,
                (
                    candidate_id,
                    f"UPDATE {field}",
                    old_text,
                    new_text,
                    changed_by,
                ),
            )

    return True


def get_audit_log(candidate_id: str) -> pd.DataFrame:
    init_db()

    with get_connection() as conn:
        return pd.read_sql_query(
            """
            SELECT
                action,
                old_value,
                new_value,
                changed_by,
                changed_at
            FROM audit_log
            WHERE candidate_id = ?
            ORDER BY id DESC
            """,
            conn,
            params=(candidate_id,),
        )


def get_pipeline_counts() -> pd.DataFrame:
    """Return operational pipeline counts."""
    init_db()

    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT
                COUNT(*) AS applications,
                SUM(
                    CASE
                        WHEN LOWER(COALESCE(screening_status, ''))
                        IN ('selected', 'screened', 'passed',
                            'screening selected')
                        THEN 1 ELSE 0
                    END
                ) AS screening_selected,

                SUM(
                    CASE
                        WHEN LOWER(COALESCE(interview_status, ''))
                        IN ('selected')
                        THEN 1 ELSE 0
                    END
                ) AS interview_selected,

                SUM(
                    CASE
                        WHEN LOWER(COALESCE(offer_status, ''))
                        IN ('accepted', 'offer accepted')
                        THEN 1 ELSE 0
                    END
                ) AS offers_accepted,

                SUM(
                    CASE
                        WHEN LOWER(COALESCE(joining_status, ''))
                        IN ('joined', 'joining confirmed')
                        THEN 1 ELSE 0
                    END
                ) AS joined
            FROM candidates
            """
        ).fetchone()

    return pd.DataFrame([dict(row)])


def database_summary() -> dict[str, Any]:
    init_db()

    with get_connection() as conn:
        candidates = conn.execute(
            "SELECT COUNT(*) AS count FROM candidates"
        ).fetchone()["count"]

        audits = conn.execute(
            "SELECT COUNT(*) AS count FROM audit_log"
        ).fetchone()["count"]

    return {
        "database": str(DB_PATH),
        "candidates": candidates,
        "audit_events": audits,
    }


if __name__ == "__main__":
    init_db()
    imported = import_csv_if_empty()

    print("Recruitment database ready.")
    print(f"Database: {DB_PATH}")
    print(f"Imported candidates: {imported}")
    print(database_summary())
