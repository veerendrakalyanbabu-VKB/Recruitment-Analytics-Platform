"""Session-state helpers for dataset-scoped filters."""

from __future__ import annotations

import streamlit as st

FILTER_DIMENSIONS = ("recruiter", "client", "role", "source", "technology")
_ACTIVE_FP_KEY = "_rios_active_dataset_fingerprint"


def filter_widget_key(fingerprint: str, col_key: str) -> str:
    """Session key scoped to dataset fingerprint — prevents cross-dataset filter leak."""
    return f"ms_{fingerprint[:16]}_{col_key}"


def reset_dataset_filters(fingerprint: str) -> bool:
    """
    Clear filter widget state when the active dataset fingerprint changes.
    Returns True if a reset occurred.
    """
    previous = st.session_state.get(_ACTIVE_FP_KEY)
    if previous == fingerprint:
        return False

    # Remove legacy unscoped keys from Phase 3–8 bug.
    for col_key in FILTER_DIMENSIONS:
        st.session_state.pop(f"ms_{col_key}", None)
        if previous:
            st.session_state.pop(filter_widget_key(previous, col_key), None)

    st.session_state[_ACTIVE_FP_KEY] = fingerprint
    return True


def sync_multiselect_defaults(
    fingerprint: str,
    col_key: str,
    options: list[str],
) -> list[str]:
    """
    Ensure multiselect session value is valid for current options.
    If missing or stale (values not in options), default to full scope (all options).
    """
    key = filter_widget_key(fingerprint, col_key)
    if not options:
        st.session_state[key] = []
        return []

    current = st.session_state.get(key)
    if current is None:
        st.session_state[key] = list(options)
        return list(options)

    valid = [v for v in current if v in options]
    if set(valid) != set(current) or not valid:
        st.session_state[key] = list(options)
        return list(options)

    # Full scope = all options selected → treat as no filter downstream
    if len(valid) == len(options):
        return list(options)
    return valid


def selection_for_query(selected: list[str], all_options: list[str]) -> list[str]:
    """Return values to apply as a filter. Empty list means no filter (full scope)."""
    if not all_options:
        return []
    if not selected:
        return []
    if set(selected) == set(all_options):
        return []
    return list(selected)
