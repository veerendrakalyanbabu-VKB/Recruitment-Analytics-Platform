"""Premium dark enterprise theme."""

ENTERPRISE_CSS = """
<style>
:root {
  --bg-primary: #0a0d12;
  --bg-surface: #11161f;
  --bg-elevated: #151b26;
  --border: #1e293b;
  --border-subtle: #293241;
  --text-primary: #f1f5f9;
  --text-secondary: #94a3b8;
  --text-muted: #64748b;
  --accent: #38bdf8;
  --success: #22c55e;
  --warning: #facc15;
  --danger: #fb7185;
  --purple: #a78bfa;
}
.main, .stApp { background: var(--bg-primary); }
.block-container {
  max-width: 1480px;
  padding-top: 1.25rem;
  padding-bottom: 2.5rem;
}
.hero {
  padding: 20px 24px;
  border: 1px solid var(--border-subtle);
  border-radius: 16px;
  background: linear-gradient(135deg, var(--bg-elevated), var(--bg-surface));
  margin-bottom: 18px;
}
.hero h1 {
  margin: 0;
  color: var(--text-primary);
  font-size: 32px;
  font-weight: 700;
  letter-spacing: -0.02em;
}
.hero p {
  margin: 6px 0 0;
  color: var(--text-secondary);
  font-size: 14px;
}
.section-title {
  color: var(--text-primary);
  font-size: 20px;
  font-weight: 700;
  margin: 16px 0 10px;
  letter-spacing: -0.01em;
}
.kpi-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 16px 18px;
  min-height: 118px;
}
.kpi-title {
  color: var(--text-secondary);
  font-size: 12px;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 0.04em;
}
.kpi-value {
  color: var(--text-primary);
  font-size: 28px;
  font-weight: 750;
  margin: 8px 0 4px;
  letter-spacing: -0.02em;
}
.kpi-desc { color: var(--text-muted); font-size: 12px; line-height: 1.4; }
.insight-card {
  background: var(--bg-elevated);
  border: 1px solid var(--border-subtle);
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 8px;
}
.insight-sev-critical { border-left: 3px solid var(--danger); }
.insight-sev-high { border-left: 3px solid var(--warning); }
.insight-sev-medium { border-left: 3px solid var(--accent); }
.insight-sev-low { border-left: 3px solid var(--success); }
.good { color: var(--success); }
.info { color: var(--accent); }
.warn { color: var(--warning); }
.bad { color: var(--danger); }
.purple { color: var(--purple); }
.health-badge {
  display: inline-block;
  padding: 4px 10px;
  border-radius: 999px;
  font-size: 12px;
  font-weight: 600;
  background: var(--bg-surface);
  border: 1px solid var(--border-subtle);
}
</style>
"""


def inject_theme() -> None:
    import streamlit as st
    st.markdown(ENTERPRISE_CSS, unsafe_allow_html=True)
