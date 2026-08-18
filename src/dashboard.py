"""Streamlit entrypoint — Recruitment Intelligence OS."""

import io
import json

import pandas as pd
import streamlit as st

from app.analytics.aging import AgingThresholds
from app.analytics.kpis import build_col_map
from app.components.ui import hero
from app.config import APP_SUBTITLE, APP_TITLE, AGING_AGING_MAX, AGING_HEALTHY_MAX, AGING_WATCH_MAX
from app.context import AppContext
from app.data.loader import mapping_table
from app.data.pipeline import profile_from_cache
from app.pages import clients_sources, executive, interviews, pipeline, recruiters, reports, search
from app.streamlit_cache import (
    cached_demo_bundle,
    cached_filtered_frame,
    cached_filter_options,
    cached_kpis,
    kpis_dict_to_dataclass,
    load_upload_bundle,
    resolve_filters,
)
from app.state import (
    filter_widget_key,
    reset_dataset_filters,
    sync_multiselect_defaults,
)
from app.theme import inject_theme
from app.utils.perf import dev_perf_enabled

st.set_page_config(
    page_title=APP_TITLE,
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded",
)
inject_theme()

# --- Data source ---
with st.sidebar:
    st.markdown("## Data Source")
    source_mode = st.radio("Choose dataset", ["Demo Dataset", "Upload CSV"], index=0)
    uploaded_file = None
    if source_mode == "Upload CSV":
        uploaded_file = st.file_uploader("Upload recruitment CSV", type=["csv"])

    st.divider()
    st.markdown("## Aging Thresholds (days)")
    healthy_max = st.number_input("Healthy max", 1, 60, AGING_HEALTHY_MAX, key="aging_healthy")
    watch_max = st.number_input("Watch max", 2, 90, AGING_WATCH_MAX, key="aging_watch")
    aging_max = st.number_input("Aging max", 3, 180, AGING_AGING_MAX, key="aging_aging")
    aging_thresholds = AgingThresholds(int(healthy_max), int(watch_max), int(aging_max))

try:
    if source_mode == "Upload CSV":
        if uploaded_file is None:
            st.info("Upload a CSV from the sidebar to begin analysis.")
            st.stop()
        sig = f"{uploaded_file.name}:{uploaded_file.size}"
        if st.session_state.get("upload_signature") != sig:
            bundle, df, _ = load_upload_bundle(uploaded_file.getvalue(), uploaded_file.name)
            st.session_state.update({
                "upload_signature": sig,
                "dataset_bundle": bundle,
                "uploaded_recruitment_df": df,
            })
        bundle = st.session_state["dataset_bundle"]
        df = st.session_state["uploaded_recruitment_df"]
    else:
        bundle = cached_demo_bundle()
        df = pd.read_parquet(io.BytesIO(bundle["parquet_bytes"]))
        st.session_state.pop("upload_signature", None)
        st.session_state.pop("dataset_bundle", None)
        st.session_state.pop("uploaded_recruitment_df", None)

    validation = bundle["validation"]
    data_profile = profile_from_cache(bundle)
    fingerprint = bundle["fingerprint"]
    parquet_bytes = bundle["parquet_bytes"]
    ingest_timings = bundle.get("ingest_timings_ms", {})

    if source_mode == "Upload CSV" and not validation["valid"]:
        st.error("The uploaded dataset needs attention before analysis.")
        for err in validation["errors"]:
            st.error(err)
        st.stop()
except Exception as exc:
    st.error(f"Unable to load recruitment data: {exc}")
    st.stop()

df.columns = [str(c).strip() for c in df.columns]
COL = build_col_map(df)

# Upload wizard
if source_mode == "Upload CSV":
    st.markdown("### Dataset Ingestion")
    steps = st.columns(5)
    with steps[0]:
        st.success("Dataset loaded")
    with steps[1]:
        st.success(f"{len(df):,} rows")
    with steps[2]:
        st.success(f"{len(df.columns)} columns")
    with steps[3]:
        st.success("Schema mapped")
    with steps[4]:
        st.success("READY FOR ANALYSIS")
    if validation.get("low_confidence_columns"):
        st.warning(
            "Review fuzzy-mapped columns: "
            + ", ".join(validation["low_confidence_columns"][:6])
        )
    with st.expander("Column mapping", expanded=False):
        st.dataframe(mapping_table(validation["mapping"]), width="stretch", hide_index=True)
    st.metric("Data Health", f"{data_profile.health_score:.0f}/100")

# Reset filter widgets when dataset fingerprint changes (prevents demo→upload leak)
reset_dataset_filters(fingerprint)

# Sidebar filters
with st.sidebar:
    st.markdown("## Filters")
    all_filter_options: dict[str, list[str]] = {}

    def selector(label: str, col_key: str) -> list[str]:
        col_name = COL[col_key]
        if not col_name:
            all_filter_options[col_key] = []
            return []
        opts = cached_filter_options(fingerprint, parquet_bytes, col_name)
        all_filter_options[col_key] = opts
        sync_multiselect_defaults(fingerprint, col_key, opts)
        return st.multiselect(
            label,
            opts,
            key=filter_widget_key(fingerprint, col_key),
        )

    sel_rec = selector("Recruiter", "recruiter")
    sel_cli = selector("Client", "client")
    sel_role = selector("Role", "role")
    sel_src = selector("Source", "source")
    sel_tech = selector("Technology", "technology")

    if dev_perf_enabled():
        with st.expander("Dev diagnostics"):
            st.caption(f"FP: {fingerprint[:16]}…")
            st.caption(f"Canonical rows: {len(df):,}")
            if ingest_timings:
                st.json(ingest_timings)

    st.caption(f"{len(df):,} candidates · {len(df.columns)} fields")

filter_key, filters_json = resolve_filters(
    COL,
    sel_rec,
    sel_cli,
    sel_role,
    sel_src,
    sel_tech,
    all_options=all_filter_options,
)
filtered_parquet = cached_filtered_frame(
    fingerprint, filter_key, parquet_bytes, filters_json
)
filtered = pd.read_parquet(io.BytesIO(filtered_parquet))

if dev_perf_enabled():
    st.sidebar.caption(
        f"Filter key: {filter_key[:12]}… · Filtered rows: {len(filtered):,}"
    )
    with st.sidebar.expander("KPI input diagnostics"):
        st.caption(f"Dataset FP: {fingerprint[:16]}…")
        st.caption(f"Raw / canonical rows: {len(df):,}")
        st.caption(f"Normalized rows: {len(df):,}")
        st.caption(f"Filter key: {filter_key}")
        st.caption(f"Filtered rows: {len(filtered):,}")
        st.caption(f"KPI input rows: {len(filtered):,}")
kpis = kpis_dict_to_dataclass(cached_kpis(fingerprint, filter_key, filtered_parquet))

ctx = AppContext(
    fingerprint=fingerprint,
    parquet_bytes=parquet_bytes,
    filter_key=filter_key,
    filters_json=filters_json,
    filtered_parquet=filtered_parquet,
    filtered=filtered,
    full_df=df,
    col=COL,
    kpis=kpis,
    validation=validation,
    data_profile=data_profile,
    bundle=bundle,
    source_mode=source_mode,
    aging_thresholds=aging_thresholds,
)

hero(APP_TITLE, APP_SUBTITLE)

tabs = st.tabs([
    "Executive",
    "Pipeline",
    "Interviews",
    "Recruiters",
    "Clients & Sources",
    "Search & AI",
    "Reports & Forecast",
])

with tabs[0]:
    executive.render(ctx)
with tabs[1]:
    pipeline.render(ctx)
with tabs[2]:
    interviews.render(ctx)
with tabs[3]:
    recruiters.render(ctx)
with tabs[4]:
    clients_sources.render(ctx)
with tabs[5]:
    search.render(ctx)
with tabs[6]:
    reports.render(ctx)

st.divider()
st.caption(f"{APP_TITLE} · Python · Pandas · DuckDB · Streamlit")
