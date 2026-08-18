"""DuckDB-backed analytical store for filtering, search, and aggregations."""

from __future__ import annotations

import io
from typing import Any

import duckdb
import pandas as pd

from app.analytics.kpis import build_col_map
from app.utils.perf import timed


class AnalyticsStore:
    """In-memory DuckDB view over a normalized recruitment dataset."""

    TABLE = "recruitment"

    def __init__(self, fingerprint: str, df: pd.DataFrame) -> None:
        self.fingerprint = fingerprint
        self._conn = duckdb.connect(database=":memory:")
        self._conn.register(self.TABLE, df)
        self._columns = list(df.columns)
        self._col_map = build_col_map(df)

    @property
    def col_map(self) -> dict[str, str | None]:
        return self._col_map

    def _quote(self, col: str) -> str:
        return '"' + col.replace('"', '""') + '"'

    def _build_where(
        self,
        filters: dict[str, list[str]] | None,
        search_text: str | None = None,
        search_cols: list[str] | None = None,
    ) -> tuple[str, list[Any]]:
        clauses: list[str] = []
        params: list[Any] = []

        if filters:
            for col, values in filters.items():
                if not col or not values or col not in self._columns:
                    continue
                placeholders = ", ".join(["?"] * len(values))
                clauses.append(f"{self._quote(col)} IN ({placeholders})")
                params.extend(values)

        if search_text and search_cols:
            q = f"%{search_text.strip().lower()}%"
            search_clauses = []
            for col in search_cols:
                if col in self._columns:
                    search_clauses.append(
                        f"LOWER(CAST({self._quote(col)} AS VARCHAR)) LIKE ?"
                    )
                    params.append(q)
            if search_clauses:
                clauses.append("(" + " OR ".join(search_clauses) + ")")

        if not clauses:
            return "", []
        return " WHERE " + " AND ".join(clauses), params

    def query_filtered(
        self,
        filters: dict[str, list[str]] | None = None,
        search_text: str | None = None,
        search_cols: list[str] | None = None,
        columns: list[str] | None = None,
        limit: int | None = None,
        order_by: str | None = None,
        timings: dict[str, float] | None = None,
    ) -> pd.DataFrame:
        where_sql, params = self._build_where(filters, search_text, search_cols)
        if columns:
            valid = [c for c in columns if c in self._columns]
            col_sql = ", ".join(self._quote(c) for c in valid) if valid else "*"
        else:
            col_sql = "*"

        sql = f"SELECT {col_sql} FROM {self.TABLE}{where_sql}"
        if order_by and order_by in self._columns:
            sql += f" ORDER BY {self._quote(order_by)}"
        if limit:
            sql += f" LIMIT {int(limit)}"

        with timed("duckdb_query", timings):
            return self._conn.execute(sql, params).df()

    def distinct_values(self, column: str, limit: int = 500) -> list[str]:
        if column not in self._columns:
            return []
        sql = (
            f"SELECT DISTINCT {self._quote(column)} AS v FROM {self.TABLE} "
            f"WHERE {self._quote(column)} IS NOT NULL "
            f"ORDER BY v LIMIT {limit}"
        )
        rows = self._conn.execute(sql).fetchall()
        return sorted(str(r[0]).strip() for r in rows if r[0] is not None and str(r[0]).strip())

    def group_count(
        self,
        group_column: str,
        filters: dict[str, list[str]] | None = None,
        timings: dict[str, float] | None = None,
    ) -> pd.DataFrame:
        if group_column not in self._columns:
            return pd.DataFrame()
        where_sql, params = self._build_where(filters)
        sql = (
            f"SELECT {self._quote(group_column)} AS group_key, COUNT(*) AS count "
            f"FROM {self.TABLE}{where_sql} "
            f"GROUP BY {self._quote(group_column)} ORDER BY count DESC"
        )
        with timed("duckdb_group", timings):
            return self._conn.execute(sql, params).df()

    def count_rows(
        self,
        filters: dict[str, list[str]] | None = None,
        search_text: str | None = None,
        search_cols: list[str] | None = None,
    ) -> int:
        where_sql, params = self._build_where(filters, search_text, search_cols)
        sql = f"SELECT COUNT(*) FROM {self.TABLE}{where_sql}"
        return int(self._conn.execute(sql, params).fetchone()[0])


def store_from_parquet(fingerprint: str, parquet_bytes: bytes) -> AnalyticsStore:
    df = pd.read_parquet(io.BytesIO(parquet_bytes))
    return AnalyticsStore(fingerprint, df)


def build_filter_dict(col_map: dict[str, str | None], selections: dict[str, list[str]]) -> dict[str, list[str]]:
    """Map analytics short keys to actual dataframe column names for SQL filters."""
    key_to_short = {
        "recruiter": "recruiter",
        "client": "client",
        "role": "role",
        "source": "source",
        "technology": "technology",
    }
    result: dict[str, list[str]] = {}
    for short_key, values in selections.items():
        col = col_map.get(short_key)
        if col and values:
            result[col] = values
    return result


def search_columns(col_map: dict[str, str | None]) -> list[str]:
    keys = ["id", "name", "recruiter", "client", "role", "technology", "location", "source"]
    return [col_map[k] for k in keys if col_map.get(k)]
