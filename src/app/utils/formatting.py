"""Formatting helpers."""

from __future__ import annotations

import pandas as pd


def display_value(value) -> str:
    if value is None or (isinstance(value, float) and pd.isna(value)):
        return "—"
    return str(value)


def format_int(n: int | float) -> str:
    return f"{int(n):,}"


def format_pct(n: float | None) -> str:
    if n is None:
        return "N/A"
    return f"{n:.2f}%"
