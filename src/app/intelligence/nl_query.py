"""Controlled natural-language analytical intent parsing."""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Literal

IntentType = Literal[
    "recruiter_ranking",
    "client_ranking",
    "source_ranking",
    "role_ranking",
    "aging_query",
    "bottleneck",
    "declining_hires",
    "forecast_target",
    "unknown",
]


@dataclass
class QueryIntent:
    intent: IntentType
    ranking: str | None = None  # best, worst, high_volume, low_selection
    aging_days: int | None = None
    target_hires: int | None = None
    raw_query: str = ""


def parse_intent(query: str) -> QueryIntent:
    q = query.strip().lower()
    if not q:
        return QueryIntent(intent="unknown", raw_query=query)

    if re.search(r"stuck|aging|days", q) and re.search(r"\d+", q):
        days = int(re.search(r"(\d+)", q).group(1))
        return QueryIntent(intent="aging_query", aging_days=days, raw_query=query)

    if "stuck" in q or "aging" in q:
        return QueryIntent(intent="aging_query", aging_days=14, raw_query=query)

    if "declin" in q and ("hire" in q or "join" in q):
        return QueryIntent(intent="declining_hires", raw_query=query)

    if "bottleneck" in q or "funnel" in q:
        return QueryIntent(intent="bottleneck", raw_query=query)

    if "recruiter" in q:
        if "underperform" in q or "worst" in q or "low" in q:
            return QueryIntent(intent="recruiter_ranking", ranking="worst", raw_query=query)
        if "efficiency" in q or "best" in q or "top" in q:
            return QueryIntent(intent="recruiter_ranking", ranking="best", raw_query=query)
        if "high interview" in q and "low selection" in q:
            return QueryIntent(intent="recruiter_ranking", ranking="high_vol_low_sel", raw_query=query)
        return QueryIntent(intent="recruiter_ranking", ranking="best", raw_query=query)

    if "client" in q:
        ranking = "worst" if "worst" in q or "hard" in q else "best"
        return QueryIntent(intent="client_ranking", ranking=ranking, raw_query=query)

    if "source" in q:
        ranking = "best" if "best" in q or "quality" in q else "volume"
        return QueryIntent(intent="source_ranking", ranking=ranking, raw_query=query)

    if "role" in q or "hard to hire" in q:
        return QueryIntent(intent="role_ranking", ranking="hard", raw_query=query)

    if re.search(r"\d+\s*hire", q) or "target" in q:
        m = re.search(r"(\d+)", q)
        target = int(m.group(1)) if m else 100
        return QueryIntent(intent="forecast_target", target_hires=target, raw_query=query)

    return QueryIntent(intent="unknown", raw_query=query)
