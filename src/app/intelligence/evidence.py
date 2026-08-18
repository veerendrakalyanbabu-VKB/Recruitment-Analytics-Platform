"""Evidence objects for AI and deterministic analyst."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any


@dataclass
class Evidence:
    metric: str
    value: Any
    comparison: Any | None = None
    change: float | None = None
    entity: str | None = None
    detail: str = ""


@dataclass
class AnalystResponse:
    question: str
    answer: str
    evidence: list[Evidence] = field(default_factory=list)
    metrics: dict[str, Any] = field(default_factory=dict)
    entities: list[str] = field(default_factory=list)
    recommended_action: str = ""
    source: str = "deterministic"
