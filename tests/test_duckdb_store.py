"""DuckDB analytics store tests."""

from pathlib import Path

import pandas as pd

from app.analytics.kpis import compute_kpis
from app.analytics.store import AnalyticsStore, build_filter_dict, search_columns
from app.data.pipeline import ingest_bytes

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_10K = ROOT / "sample_data" / "recruitment_dataset_10000.csv"


def _store() -> AnalyticsStore:
    prepared = ingest_bytes(SAMPLE_10K.read_bytes(), source_name="10k.csv")
    return AnalyticsStore(prepared.fingerprint, prepared.data)


def test_duckdb_filter_matches_pandas():
    prepared = ingest_bytes(SAMPLE_10K.read_bytes(), source_name="10k.csv")
    df = prepared.data
    store = AnalyticsStore(prepared.fingerprint, df)
    col_map = store.col_map
    recruiter_col = col_map["recruiter"]
    recruiters = store.distinct_values(recruiter_col)[:2]
    filters = build_filter_dict(col_map, {"recruiter": recruiters})
    filtered = store.query_filtered(filters=filters)
    pandas_mask = df[recruiter_col].isin(recruiters)
    assert len(filtered) == int(pandas_mask.sum())


def test_duckdb_search():
    store = _store()
    col_map = store.col_map
    search_cols = search_columns(col_map)
    results = store.query_filtered(search_text="recruiter", search_cols=search_cols, limit=50)
    assert len(results) <= 50
    assert len(results) > 0


def test_duckdb_group_count():
    store = _store()
    col_map = store.col_map
    client_col = col_map["client"]
    grouped = store.group_count(client_col)
    assert "count" in grouped.columns
    assert grouped["count"].sum() == len(store.query_filtered())


def test_filtered_kpis_match_full_on_10k():
    prepared = ingest_bytes(SAMPLE_10K.read_bytes(), source_name="10k.csv")
    full_kpis = compute_kpis(prepared.data)
    store = AnalyticsStore(prepared.fingerprint, prepared.data)
    filtered = store.query_filtered()
    filtered_kpis = compute_kpis(filtered)
    assert filtered_kpis.total == full_kpis.total
    assert filtered_kpis.interviews_completed == full_kpis.interviews_completed
