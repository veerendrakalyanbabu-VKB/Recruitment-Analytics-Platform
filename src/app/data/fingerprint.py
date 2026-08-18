"""Deterministic dataset fingerprinting."""

from __future__ import annotations

import hashlib
from pathlib import Path
from typing import Any


def compute_fingerprint(
    content: bytes,
    source_name: str = "",
    extra_metadata: str = "",
) -> str:
    """
    Build a stable fingerprint for cache keys.
    Incorporates content hash, size, and source metadata so different uploads never collide.
    """
    size = len(content)
    meta = f"{source_name}|{size}|{extra_metadata}"
    digest = hashlib.sha256()
    digest.update(content)
    digest.update(meta.encode("utf-8"))
    return digest.hexdigest()


def fingerprint_from_path(path: Path) -> str:
    raw = path.read_bytes()
    return compute_fingerprint(raw, source_name=path.name, extra_metadata=str(path.resolve()))
