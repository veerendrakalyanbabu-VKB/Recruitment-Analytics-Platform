"""CSV ingestion with delimiter detection and dataset fingerprinting."""

from __future__ import annotations

import io
from pathlib import Path
from typing import Any

import pandas as pd

from app.config import CLEANED_FILE, RAW_FILE
from app.data.normalization import normalize_dataframe
from app.data.validation import validate_recruitment_data


from app.data.fingerprint import compute_fingerprint as fingerprint_bytes
from app.data.fingerprint import fingerprint_from_path as fingerprint_file


def read_csv_flexible(source: Any) -> pd.DataFrame:
    """Read CSV with automatic delimiter detection."""
    if isinstance(source, (str, Path)):
        path = Path(source)
        raw_bytes = path.read_bytes()
        text = raw_bytes.decode("utf-8-sig", errors="replace")
    elif hasattr(source, "read"):
        raw_bytes = source.read()
        if isinstance(raw_bytes, str):
            raw_bytes = raw_bytes.encode("utf-8")
        text = raw_bytes.decode("utf-8-sig", errors="replace")
    else:
        raise TypeError(f"Unsupported CSV source type: {type(source)}")

    # Sniff delimiter from first non-empty lines.
    sample = "\n".join(text.splitlines()[:5])
    delimiter = ","
    try:
        import csv
        dialect = csv.Sniffer().sniff(sample, delimiters=",;\t|")
        delimiter = dialect.delimiter
    except Exception:
        pass

    return pd.read_csv(io.StringIO(text), sep=delimiter)


def load_and_prepare(
    source: Any,
    manual_overrides: dict[str, str] | None = None,
) -> dict[str, Any]:
    """Load, normalize, validate — returns bundle for session state."""
    raw_df = read_csv_flexible(source)
    normalized, mapping, unmapped, low_confidence = normalize_dataframe(
        raw_df, manual_overrides
    )
    validation = validate_recruitment_data(normalized, mapping, unmapped, low_confidence)
    return {
        "raw": raw_df,
        "data": normalized,
        "mapping": mapping,
        "unmapped": unmapped,
        "low_confidence": low_confidence,
        "validation": validation,
    }


def load_demo_dataframe() -> pd.DataFrame:
    path = CLEANED_FILE if CLEANED_FILE.exists() else RAW_FILE
    if not path.exists():
        raise FileNotFoundError(f"No demo recruitment CSV found at {path}")
    return read_csv_flexible(path)


def mapping_table(mapping: dict[str, str]) -> pd.DataFrame:
    from app.data.schema import DISPLAY_NAMES

    return pd.DataFrame(
        [
            {
                "Uploaded Column": original,
                "Recognized As": DISPLAY_NAMES.get(canonical, canonical),
            }
            for original, canonical in mapping.items()
        ]
    )
