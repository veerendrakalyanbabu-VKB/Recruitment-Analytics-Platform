"""Lightweight performance instrumentation (development only)."""

from __future__ import annotations

import os
import time
from contextlib import contextmanager
from typing import Generator

DEV_PERF_ENABLED = os.environ.get("RIOS_DEV_PERF", "").lower() in ("1", "true", "yes")


@contextmanager
def timed(label: str, timings: dict[str, float] | None = None) -> Generator[None, None, None]:
    start = time.perf_counter()
    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start) * 1000
        if timings is not None:
            timings[label] = round(elapsed_ms, 2)
        if DEV_PERF_ENABLED:
            print(f"[rios-perf] {label}: {elapsed_ms:.1f}ms")


def dev_perf_enabled() -> bool:
    return DEV_PERF_ENABLED
