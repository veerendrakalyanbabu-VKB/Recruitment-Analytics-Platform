"""Ingestion pipeline and cache-safety tests."""

from pathlib import Path

import pandas as pd

from app.data.fingerprint import compute_fingerprint
from app.data.pipeline import ingest_bytes

ROOT = Path(__file__).resolve().parents[1]
SAMPLE_10K = ROOT / "sample_data" / "recruitment_dataset_10000.csv"


def test_ingest_twice_same_fingerprint():
    raw = SAMPLE_10K.read_bytes()
    p1 = ingest_bytes(raw, source_name="10k.csv")
    p2 = ingest_bytes(raw, source_name="10k.csv")
    assert p1.fingerprint == p2.fingerprint
    assert p1.fingerprint == compute_fingerprint(raw, source_name="10k.csv")
    assert len(p1.data) == 10_000


def test_ingest_produces_parquet_roundtrip():
    raw = SAMPLE_10K.read_bytes()
    prepared = ingest_bytes(raw, source_name="10k.csv")
    restored = pd.read_parquet(__import__("io").BytesIO(prepared.parquet_bytes))
    assert len(restored) == len(prepared.data)
    assert list(restored.columns) == list(prepared.data.columns)


def test_ingest_timings_recorded():
    raw = SAMPLE_10K.read_bytes()
    prepared = ingest_bytes(raw, source_name="10k.csv")
    assert "parse_csv" in prepared.ingest_timings_ms
    assert prepared.ingest_timings_ms["parse_csv"] >= 0
