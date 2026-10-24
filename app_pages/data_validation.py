import pandas as pd
import plotly.express as px
import streamlit as st

from app_lib import artifacts, ui

sid = st.session_state["scenario_id"]
meta = artifacts.meta(sid)
val = artifacts.validation(sid)
forecast = artifacts.forecast_df(sid)

ui.header(
    "Data & Validation",
    "Every input is checked before a plan is built. Bad data is never silently repaired — "
    "errors name the file, row, column and rule.",
    meta,
)

files = pd.DataFrame(val.get("files", []))
errors = val.get("errors", []) or []
warnings = val.get("warnings", []) or []
checks = val.get("checks", []) or []

row_count = int(files["rows"].sum()) if not files.empty and "rows" in files else 0
ui.cards(
    [
        ("Files checked", len(files), "6 CSVs + config.json"),
        ("Rows read", f"{row_count:,}", "validated before use"),
        ("Errors", len(errors), "blocking" if errors else "none found"),
        ("Warnings", len(warnings), "shown, never hidden"),
    ]
)

if errors:
    st.error(f"{len(errors)} blocking error(s). The engine must not produce a plan.")
    st.dataframe(pd.DataFrame(errors), hide_index=True, width="stretch")

left, right = st.columns([1.25, 1], gap="large")

with left:
    st.subheader("Input files")
    if not files.empty:
        st.dataframe(
            files,
            hide_index=True,
            width="stretch",
            column_config={
                "name": st.column_config.TextColumn("File"),
                "rows": st.column_config.NumberColumn("Rows", format="%d"),
                "status": st.column_config.TextColumn("Status"),
                "errors": st.column_config.NumberColumn("Errors", format="%d"),
                "warnings": st.column_config.NumberColumn("Warnings", format="%d"),
            },
        )
    else:
        st.info("No validation report found.")

with right:
    st.subheader("Checks")
    if checks:
        for check in checks:
            icon = "✅" if check.get("passed") else "❌"
            detail = f" — {check['detail']}" if check.get("detail") else ""
            st.markdown(f"{icon} **{check.get('label', 'Check')}**{detail}")
    else:
        st.info("No checks recorded.")

if warnings:
    with st.expander(f"Warnings ({len(warnings)})", expanded=False):
        st.dataframe(pd.DataFrame(warnings), hide_index=True, width="stretch")

st.divider()
st.subheader("Demand forecast vs. store stock")
st.caption(
    "Quantiles never cross and are never negative. Targets subtract opening store stock, "
    "so a store that already holds stock is asked for less."
)

if forecast.empty:
    st.info("No forecast file found.")
else:
    agg = forecast.groupby("store_id", as_index=False)[["p50", "p90"]].sum()
    fig = px.bar(
        agg,
        x="store_id",
        y=["p50", "p90"],
        barmode="group",
        labels={"value": "Units", "variable": "Planning level", "store_id": "Store"},
        color_discrete_map={"p50": "#0F766E", "p90": "#F59E0B"},
    )
    fig.update_layout(
        height=320,
        margin=dict(l=10, r=10, t=30, b=10),
        legend_title_text="",
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

    show = forecast[
        [
            "store_id",
            "sku_id",
            "opening_units",
            "p50",
            "p60",
            "p70",
            "p80",
            "p90",
            "p95",
            "target_p50",
            "target_p90",
        ]
    ]
    st.dataframe(show, hide_index=True, width="stretch", height=320)
    st.download_button(
        "Download forecast CSV",
        show.to_csv(index=False).encode("utf-8"),
        file_name=f"forecast_{sid}.csv",
        mime="text/csv",
    )
