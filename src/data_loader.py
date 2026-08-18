"""Backward-compatible re-exports — use app.data in new code."""

from app.data.loader import mapping_table
from app.data.schema import CANONICAL_ALIASES, DISPLAY_NAMES
from app.data.validation import validate_recruitment_data


def normalize_dataframe(df, manual_overrides=None):
    """Legacy 3-tuple return for existing callers."""
    from app.data.normalization import normalize_dataframe as _normalize
    data, mapping, unmapped, _low = _normalize(df, manual_overrides)
    return data, mapping, unmapped
