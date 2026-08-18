"""Backward-compatible re-exports — use app.analytics.kpis in new code."""

from app.analytics.kpis import *  # noqa: F403
from app.analytics.kpis import group_kpis_by
from app.intelligence.insight_engine import generate_executive_insights
