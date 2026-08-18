"""Regression tests for filter/session data-flow bug."""

from pathlib import Path

import pandas as pd

from app.analytics.kpis import compute_kpis
from app.analytics.store import AnalyticsStore, build_filter_dict
from app.data.pipeline import ingest_bytes
from app.state import selection_for_query, sync_multiselect_defaults
from app.streamlit_cache import resolve_filters
from app.analytics.kpis import build_col_map

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_10K = ROOT / "sample_data" / "recruitment_dataset_10000.csv"
DEMO_CLEANED = ROOT / "data" / "recruitment_data_cleaned.csv"


def _load_10k():
    return ingest_bytes(SAMPLE_10K.read_bytes(), "10k.csv")


def test_10k_full_dataset_kpis_no_filters():
    prepared = _load_10k()
    kpis = compute_kpis(prepared.data)
    assert kpis.total == 10_000
    assert kpis.screening_selected == 7_457
    assert kpis.interviews_completed == 6_689
    assert kpis.interview_selected == 4_351
    assert kpis.offers_accepted == 3_602
    assert kpis.joined == 3_262


def test_empty_filter_dict_returns_full_dataset():
    prepared = _load_10k()
    store = AnalyticsStore(prepared.fingerprint, prepared.data)
    full = store.query_filtered(filters={})
    assert len(full) == 10_000


def test_resolve_filters_all_selected_means_no_sql_filter():
    prepared = _load_10k()
    col = build_col_map(prepared.data)
    recruiters = store_distinct(prepared.data, col["recruiter"])
    clients = store_distinct(prepared.data, col["client"])
    roles = store_distinct(prepared.data, col["role"])
    sources = store_distinct(prepared.data, col["source"])
    techs = store_distinct(prepared.data, col["technology"])

    _, filters_json = resolve_filters(
        col,
        recruiters,
        clients,
        roles,
        sources,
        techs,
        all_options={
            "recruiter": recruiters,
            "client": clients,
            "role": roles,
            "source": sources,
            "technology": techs,
        },
    )
    assert filters_json == "{}"


def test_partial_filter_reduces_rows():
    prepared = _load_10k()
    col = build_col_map(prepared.data)
    recruiters = store_distinct(prepared.data, col["recruiter"])
    one = recruiters[0]
    filters = build_filter_dict(col, {"recruiter": [one]})
    store = AnalyticsStore(prepared.fingerprint, prepared.data)
    subset = store.query_filtered(filters=filters)
    assert len(subset) < 10_000
    assert len(subset) > 0


def test_clear_filter_returns_full_scope():
    prepared = _load_10k()
    col = build_col_map(prepared.data)
    recruiters = store_distinct(prepared.data, col["recruiter"])
    # partial then full
    partial = selection_for_query([recruiters[0]], recruiters)
    assert partial == [recruiters[0]]
    full = selection_for_query(recruiters, recruiters)
    assert full == []


def test_stale_partial_selection_simulation():
    """Simulate demo recruiters leaking into 10k filter scope."""
    prepared = _load_10k()
    col = build_col_map(prepared.data)
    all_recruiters = store_distinct(prepared.data, col["recruiter"])
    # Stale: only first recruiter from a pretend demo subset
    stale = [all_recruiters[0]]
    filters = build_filter_dict(col, {"recruiter": stale})
    store = AnalyticsStore(prepared.fingerprint, prepared.data)
    assert len(store.query_filtered(filters=filters)) < 10_000

    # Correct: no filter when all selected
    no_filter = build_filter_dict(
        col, {"recruiter": selection_for_query(all_recruiters, all_recruiters)}
    )
    assert len(store.query_filtered(filters=no_filter)) == 10_000


def test_demo_dataset_row_count():
    if not DEMO_CLEANED.exists():
        return
    prepared = ingest_bytes(DEMO_CLEANED.read_bytes(), "demo.csv")
    kpis = compute_kpis(prepared.data)
    assert kpis.total == 1_000


def store_distinct(df: pd.DataFrame, col: str | None) -> list[str]:
    if not col or col not in df.columns:
        return []
    return sorted(df[col].dropna().astype(str).str.strip().unique().tolist())
