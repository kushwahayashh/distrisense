from __future__ import annotations

import html

import streamlit as st

from . import artifacts

CSS = """
<style>
.block-container { padding-top: 2.0rem; padding-bottom: 3rem; max-width: 1180px; }
.bw-brand { font-size: 1.15rem; font-weight: 800; color: #0F172A; letter-spacing: -0.01em; }
.bw-hero { margin-bottom: 1.1rem; }
.bw-title { font-size: 2.0rem; font-weight: 800; margin: .15rem 0 .35rem;
            color: #0F172A; letter-spacing: -0.02em; line-height: 1.15; }
.bw-sub { color: #64748B; font-size: .94rem; max-width: 78ch; line-height: 1.5; }
.bw-badge { display: inline-block; padding: .20rem .58rem; border-radius: 999px;
            font-size: .71rem; font-weight: 700; margin: .18rem .35rem 0 0;
            letter-spacing: .01em; }
.bw-ok { background: #DCFCE7; color: #166534; }
.bw-warn { background: #FEF3C7; color: #92400E; }
.bw-bad { background: #FEE2E2; color: #991B1B; }
.bw-neutral { background: #E0F2FE; color: #075985; }
.bw-cards { display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
            gap: .7rem; margin: .35rem 0 1.25rem; }
.bw-card { background: #FFFFFF; border: 1px solid #E2E8F0; border-radius: 14px;
           padding: .85rem 1rem; box-shadow: 0 1px 2px rgba(15, 23, 42, .04); }
.bw-card .l { font-size: .69rem; text-transform: uppercase; letter-spacing: .08em;
              color: #64748B; font-weight: 700; }
.bw-card .v { font-size: 1.42rem; font-weight: 800; color: #0F172A; margin-top: .16rem;
              letter-spacing: -0.01em; }
.bw-card .h { font-size: .74rem; color: #94A3B8; margin-top: .12rem; }
.bw-callout { border-left: 3px solid #0F766E; background: #F0FDFA; padding: .7rem .9rem;
              border-radius: 0 10px 10px 0; color: #134E4A; font-size: .88rem;
              margin: .4rem 0 1rem; }
div[data-testid="stSidebar"] { background: #F8FAFC; border-right: 1px solid #E2E8F0; }
div[data-testid="stMetricValue"] { font-size: 1.35rem; }
h2, h3 { letter-spacing: -0.01em; }
</style>
"""


def inject_css() -> None:
    st.markdown(CSS, unsafe_allow_html=True)


def badge(text: str, kind: str = "neutral") -> str:
    return f'<span class="bw-badge bw-{kind}">{html.escape(str(text))}</span>'


def header(title: str, subtitle: str, meta: dict | None = None) -> None:
    badges = ""
    if meta:
        badges += badge(meta.get("scenario_name", "Scenario"), "neutral")
        badges += badge(f"Week {meta.get('planning_week', '—')}", "neutral")
        forecaster = str(meta.get("forecaster_used", "—"))
        badges += badge(f"Forecaster: {forecaster}", "ok" if forecaster.startswith("ml") else "warn")
        status = str(meta.get("solver_status", "—"))
        badges += badge(f"Solver: {status}", "ok" if status == "optimal" else "warn")
    st.markdown(
        f'<div class="bw-hero">'
        f'<div class="bw-title">{html.escape(title)}</div>'
        f'<div class="bw-sub">{html.escape(subtitle)}</div>'
        f'<div>{badges}</div>'
        f"</div>",
        unsafe_allow_html=True,
    )


def cards(items: list[tuple]) -> None:
    cells = "".join(
        f'<div class="bw-card"><div class="l">{html.escape(str(label))}</div>'
        f'<div class="v">{html.escape(str(value))}</div>'
        f'<div class="h">{html.escape(str(hint))}</div></div>'
        for label, value, hint in items
    )
    st.markdown(f'<div class="bw-cards">{cells}</div>', unsafe_allow_html=True)


def callout(text: str) -> None:
    st.markdown(f'<div class="bw-callout">{html.escape(text)}</div>', unsafe_allow_html=True)


def money(value) -> str:
    try:
        return f"₹{float(value):,.0f}"
    except (TypeError, ValueError):
        return "—"


def pct(value, digits: int = 0) -> str:
    try:
        return f"{float(value) * 100:.{digits}f}%"
    except (TypeError, ValueError):
        return "—"


def sidebar() -> str:
    inject_css()
    st.sidebar.markdown('<div class="bw-brand">📦 DistriSense</div>', unsafe_allow_html=True)
    st.sidebar.caption("Adaptive Distribution Intelligence")

    index = artifacts.load_index()
    if not index or not index.get("scenarios"):
        st.sidebar.error("No artifacts found.")
        st.error(
            "No results in `results/`. Run `python scripts/make_mock_results.py` "
            "for mock data, or point the engine at `results/`."
        )
        st.stop()

    scenarios = index["scenarios"]
    ids = [s["id"] for s in scenarios]
    labels = [s["name"] for s in scenarios]

    if st.session_state.get("scenario_id") not in ids:
        st.session_state["scenario_id"] = ids[0]
    current = ids.index(st.session_state["scenario_id"])

    picked = st.sidebar.selectbox("Scenario", labels, index=current)
    sid = ids[labels.index(picked)]
    st.session_state["scenario_id"] = sid

    meta = artifacts.meta(sid)
    st.sidebar.markdown("---")
    st.sidebar.caption(
        f"Planning week **{meta.get('planning_week', '—')}** · seed **{meta.get('seed', '—')}**"
    )
    st.sidebar.caption(f"Forecaster: `{meta.get('forecaster_used', '—')}`")
    st.sidebar.caption(
        f"Solver: `{meta.get('solver_status', '—')}` · {meta.get('solve_time_seconds', '—')}s"
    )
    if index.get("mock", True):
        st.sidebar.markdown("---")
        st.sidebar.caption("⚠️ Mock artifacts — UI development only. Not engine results.")
    st.sidebar.markdown("---")
    st.sidebar.caption(
        "Every plan is checked by an independent validator before it is shown or exported."
    )
    return sid
