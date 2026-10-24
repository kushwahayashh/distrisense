import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

from app_lib import artifacts, ui

sid = st.session_state["scenario_id"]
meta = artifacts.meta(sid)
risk = artifacts.risk_df(sid)
baselines = artifacts.baselines_df(sid)
evaluation = artifacts.evaluation(sid)

ui.header(
    "Risk Dial & Baselines",
    "The same optimizer runs at six planning levels. A level is a setting, not a "
    "fulfillment guarantee — the measured cost and P10 service are shown beside it.",
    meta,
)

if risk.empty:
    st.info("Risk Dial not available yet. Waiting for the 200-draw engine evaluation.")
    st.stop()

if not artifacts.planner_ready(sid):
    st.info("Risk Dial not available yet. Waiting for a complete, jointly validated A/B/D run.")
    st.stop()

threshold_pct = st.slider(
    "Minimum acceptable P10 fulfillment",
    min_value=50,
    max_value=100,
    value=90,
    step=1,
    format="%d%%",
    help="P10 fulfillment is the bad-case service level across 200 demand draws.",
)
threshold = threshold_pct / 100

qualifying = risk[risk["fulfillment_p10"] >= threshold].sort_values("realized_cost_mean")
best = qualifying.iloc[0] if not qualifying.empty else None

ui.cards(
    [
        (
            "Cheapest qualifying plan",
            best["level"] if best is not None else "None",
            f"at P10 ≥ {threshold_pct}%",
        ),
        ("Its realized cost", ui.money(best["realized_cost_mean"]) if best is not None else "—", "mean over 200 draws"),
        ("Its P10 fulfillment", ui.pct(best["fulfillment_p10"]) if best is not None else "—", "bad-case service"),
        ("Demand draws", int(artifacts.load_json(sid, "risk_dial.json", {}).get("draws", 200)), "seeded, identical for every level"),
    ]
)

if best is None:
    st.warning(
        f"No planning level reaches a P10 fulfillment of {threshold_pct}%. "
        "The threshold is not met — we report that rather than hide it."
    )
else:
    st.success(
        f"**{best['level']}** is the cheapest plan that reaches P10 ≥ {threshold_pct}%, "
        f"at {ui.money(best['realized_cost_mean'])} mean realized cost."
    )

left, right = st.columns([1.35, 1], gap="large")

with left:
    st.subheader("Cost vs. reliability")
    ordered = risk.sort_values("fulfillment_p10")
    fig = px.line(
        ordered,
        x="fulfillment_p10",
        y="realized_cost_mean",
        markers=True,
        text="level",
        labels={"fulfillment_p10": "P10 fulfillment", "realized_cost_mean": "Mean realized cost (₹)"},
    )
    fig.update_traces(
        line_color="#0F766E",
        marker=dict(size=9, color="#0F766E"),
        textposition="top center",
        textfont=dict(size=11, color="#0F172A"),
    )
    fig.add_vline(
        x=threshold,
        line_dash="dash",
        line_color="#DC2626",
        annotation_text=f"{threshold_pct}% threshold",
        annotation_position="top right",
    )
    if best is not None:
        fig.add_trace(
            go.Scatter(
                x=[best["fulfillment_p10"]],
                y=[best["realized_cost_mean"]],
                mode="markers",
                marker=dict(size=17, color="#F59E0B", symbol="star"),
                name="Cheapest qualifying",
                hoverinfo="skip",
            )
        )
    fig.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=30, b=10),
        showlegend=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig.update_xaxes(tickformat=".0%", gridcolor="#F1F5F9")
    fig.update_yaxes(tickprefix="₹", gridcolor="#F1F5F9")
    st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})

with right:
    st.subheader("Freight by level")
    fig2 = px.bar(
        risk,
        x="level",
        y="freight",
        color="freight",
        color_continuous_scale=["#CCFBF1", "#0F766E"],
        labels={"level": "Planning level", "freight": "Freight (₹)"},
    )
    fig2.update_layout(
        height=360,
        margin=dict(l=10, r=10, t=30, b=10),
        coloraxis_showscale=False,
        plot_bgcolor="rgba(0,0,0,0)",
        paper_bgcolor="rgba(0,0,0,0)",
    )
    fig2.update_yaxes(tickprefix="₹", gridcolor="#F1F5F9")
    st.plotly_chart(fig2, width="stretch", config={"displayModeBar": False})

st.subheader("The six planning levels")
risk_show = risk.copy()
risk_show["status"] = [
    "★ cheapest qualifying"
    if best is not None and row["level"] == best["level"]
    else ("meets" if row["fulfillment_p10"] >= threshold else "—")
    for _, row in risk_show.iterrows()
]
# Artifacts store fulfillment as a fraction; convert for display formatting.
risk_show["fulfillment_mean"] = risk_show["fulfillment_mean"] * 100
risk_show["fulfillment_p10"] = risk_show["fulfillment_p10"] * 100
st.dataframe(
    risk_show[
        [
            "level",
            "freight",
            "realized_cost_mean",
            "realized_cost_p90",
            "fulfillment_mean",
            "fulfillment_p10",
            "unmet_units",
            "status",
        ]
    ],
    hide_index=True,
    width="stretch",
    column_config={
        "level": "Level",
        "freight": st.column_config.NumberColumn("Freight (₹)", format="%d"),
        "realized_cost_mean": st.column_config.NumberColumn("Realized cost, mean (₹)", format="%d"),
        "realized_cost_p90": st.column_config.NumberColumn("Realized cost, P90 (₹)", format="%d"),
        "fulfillment_mean": st.column_config.NumberColumn("Fulfillment, mean", format="%.1f%%"),
        "fulfillment_p10": st.column_config.NumberColumn("Fulfillment, P10", format="%.1f%%"),
        "unmet_units": st.column_config.NumberColumn("Unmet units", format="%d"),
        "status": "Status",
    },
)
st.caption(
    "Higher planning levels buy more cover with more freight. "
    "The starred row is the cheapest plan that meets the threshold."
)

st.divider()
st.subheader("Baselines on identical inputs")

if baselines.empty:
    st.info("No baseline comparison found.")
else:
    base_show = baselines.copy()
    base_show["fulfillment_mean"] = base_show["fulfillment_mean"] * 100
    base_show["fulfillment_p10"] = base_show["fulfillment_p10"] * 100

    base_left, base_right = st.columns([1, 1.3], gap="large")

    with base_left:
        st.dataframe(
            base_show[
                [
                    "name",
                    "planned_objective",
                    "realized_cost_mean",
                    "fulfillment_mean",
                    "fulfillment_p10",
                    "unmet_units",
                    "checker_passed",
                ]
            ],
            hide_index=True,
            width="stretch",
            column_config={
                "name": "Method",
                "planned_objective": st.column_config.NumberColumn("Planned objective (₹)", format="%d"),
                "realized_cost_mean": st.column_config.NumberColumn("Realized cost (₹)", format="%d"),
                "fulfillment_mean": st.column_config.NumberColumn("Fulfillment, mean", format="%.1f%%"),
                "fulfillment_p10": st.column_config.NumberColumn("Fulfillment, P10", format="%.1f%%"),
                "unmet_units": st.column_config.NumberColumn("Unmet units", format="%d"),
                "checker_passed": st.column_config.CheckboxColumn("Checker"),
            },
        )

    with base_right:
        base_sorted = baselines.sort_values("realized_cost_mean")
        fig3 = px.bar(
            base_sorted,
            x="realized_cost_mean",
            y="name",
            orientation="h",
            text="realized_cost_mean",
            color="id",
            color_discrete_map={"lp": "#0F766E", "pro_rata": "#94A3B8", "greedy": "#CBD5E1"},
            labels={"realized_cost_mean": "Mean realized cost (₹)", "name": ""},
        )
        fig3.update_traces(texttemplate="₹%{text:,.0f}", textposition="outside")
        fig3.update_layout(
            height=280,
            margin=dict(l=10, r=60, t=20, b=10),
            showlegend=False,
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        fig3.update_xaxes(tickprefix="₹", gridcolor="#F1F5F9")
        st.plotly_chart(fig3, width="stretch", config={"displayModeBar": False})

    st.caption(
        "The LP minimizes the planning objective, not realized cost. It can tie or lose "
        "to a baseline under uncertain demand — ties and losses are reported, not hidden."
    )

st.divider()
st.subheader("Forecast quality")

pinball = evaluation.get("pinball", {})
if pinball:
    selected = pinball.get("selected", "—")
    ui.cards(
        [
            ("Baseline pinball", f"{pinball.get('baseline_ma4', '—')}", "MA4 + residual quantiles"),
            ("ML pinball", f"{pinball.get('ml_gbm', '—')}", "gradient boosting"),
            ("Selected", selected, f"weeks {pinball.get('scored_weeks', '—')}"),
            ("Expiry-risk units", f"{evaluation.get('expiry_risk_units', '—')}", "unshipped, expiring ≤ 7 days"),
        ]
    )
    if selected == "ml_gbm":
        st.caption("The ML model had the lower pinball loss on held-out weeks and is used.")
    else:
        st.caption(
            "The baseline had the lower pinball loss (or the ML model was not ready), so the "
            "baseline is used and no ML-superiority claim is made."
        )

calibration = pd.DataFrame(evaluation.get("calibration", []))
if not calibration.empty:
    cal_left, cal_right = st.columns([1.2, 1], gap="large")
    with cal_left:
        fig4 = px.bar(
            calibration,
            x="level",
            y=["nominal", "observed"],
            barmode="group",
            labels={"value": "Share of actuals ≤ level", "variable": "", "level": "Planning level"},
            color_discrete_map={"nominal": "#CBD5E1", "observed": "#0F766E"},
        )
        fig4.update_layout(
            height=300,
            margin=dict(l=10, r=10, t=30, b=10),
            legend_title_text="",
            plot_bgcolor="rgba(0,0,0,0)",
            paper_bgcolor="rgba(0,0,0,0)",
        )
        fig4.update_yaxes(tickformat=".0%", gridcolor="#F1F5F9")
        st.plotly_chart(fig4, width="stretch", config={"displayModeBar": False})
    with cal_right:
        cal_show = calibration.copy()
        cal_show["nominal"] = cal_show["nominal"] * 100
        cal_show["observed"] = cal_show["observed"] * 100
        st.dataframe(
            cal_show,
            hide_index=True,
            width="stretch",
            column_config={
                "level": "Level",
                "nominal": st.column_config.NumberColumn("Nominal", format="%.0f%%"),
                "observed": st.column_config.NumberColumn("Observed", format="%.0f%%"),
                "within_tolerance": st.column_config.CheckboxColumn("Within ±10 pts"),
            },
        )
        st.caption("Observed coverage is checked against nominal on weeks 41–52.")

with st.expander("Limitations and claims", expanded=False):
    st.markdown(
        """
- Synthetic data, one-week single-period model; results show how the method behaves, not real-world performance.
- Freight is linear per unit; no truck fixed costs.
- Lead times are certain in the model.
- Whole-unit plans are floored after the LP, so they are feasible but **not proven optimal in whole units**.
- A planning level is a **setting**, not a fulfillment guarantee. P90 does not mean 90% service.
- The Risk Dial numbers are measured on this scenario's 200 seeded draws; they do not generalize.
- We do **not** claim actual waste reduction, percentage savings for real businesses, or forecast accuracy on real data.
        """
    )
