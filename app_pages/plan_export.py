import pandas as pd
import streamlit as st

from app_lib import artifacts, ui

sid = st.session_state["scenario_id"]
meta = artifacts.meta(sid)
plan_data = artifacts.plan(sid)
levels = list(plan_data.get("levels", {}).keys())

ui.header(
    "Plan & Export",
    "Which batch leaves which warehouse, how many units, and when it arrives. "
    "Only eligible options are used; the independent checker must pass before export.",
    meta,
)

if not levels:
    st.error("No plan file found in this scenario.")
    st.stop()

level = st.radio("Planning level", levels, horizontal=True, key=f"level_{sid}")
node = plan_data["levels"][level]

shipments = pd.DataFrame(node.get("shipments", []))
unmet = pd.DataFrame(node.get("unmet", []))
totals = node.get("totals", {})
blocked = node.get("blocked", {})
checker = node.get("checker", {})

ui.cards(
    [
        ("Freight", ui.money(totals.get("freight", 0)), "linear, per unit"),
        ("Shipped units", f"{int(totals.get('shipped_units', 0)):,}", f"{int(totals.get('shipments', 0)):,} shipments"),
        ("Unmet units", f"{int(totals.get('unmet_units', 0)):,}", "reported, never hidden"),
        ("Target units", f"{int(totals.get('target_units', 0)):,}", f"planning level {level}"),
    ]
)

if checker.get("passed"):
    st.success(
        f"Independent checker passed — 0 violations on {len(shipments)} shipments. "
        "The plan respects stock, route capacity, arrival day and shelf life."
    )
else:
    violations = checker.get("violations", [])
    st.error(f"Checker failed — {len(violations)} violation(s). This plan must not be exported.")
    if violations:
        st.dataframe(pd.DataFrame(violations), hide_index=True, width="stretch")

st.subheader("Options blocked by eligibility rules")
ui.cards(
    [
        ("Route inactive", int(blocked.get("route", 0)), "excluded"),
        ("Arrives too late", int(blocked.get("lead_time", 0)), f"after day {meta.get('latest_arrival_day', 2)}"),
        ("Shelf life too short", int(blocked.get("shelf_life", 0)), f"under {meta.get('min_shelf_life_days', 3)} days"),
    ]
)
st.caption(
    "Each count is a batch–store option rejected before the optimizer ran. "
    "Blocked stock is never silently shipped."
)

st.divider()
st.subheader("Shipments")

if shipments.empty:
    st.info("No shipments at this level.")
else:
    f1, f2, f3 = st.columns(3)
    wh = f1.multiselect("Warehouse", sorted(shipments["warehouse_id"].unique()))
    store = f2.multiselect("Store", sorted(shipments["store_id"].unique()))
    sku = f3.multiselect("SKU", sorted(shipments["sku_id"].unique()))

    filtered = shipments.copy()
    if wh:
        filtered = filtered[filtered["warehouse_id"].isin(wh)]
    if store:
        filtered = filtered[filtered["store_id"].isin(store)]
    if sku:
        filtered = filtered[filtered["sku_id"].isin(sku)]

    st.dataframe(
        filtered,
        hide_index=True,
        width="stretch",
        height=360,
        column_config={
            "warehouse_id": "Warehouse",
            "store_id": "Store",
            "sku_id": "SKU",
            "batch_id": "Batch",
            "units": st.column_config.NumberColumn("Units", format="%d"),
            "unit_cost": st.column_config.NumberColumn("Freight / unit (₹)", format="%d"),
            "freight": st.column_config.NumberColumn("Freight (₹)", format="%d"),
            "arrival_day": st.column_config.NumberColumn("Arrival day", format="%d"),
            "shelf_life_on_arrival": st.column_config.NumberColumn("Shelf life on arrival (d)", format="%d"),
            "expiry_date": "Expiry",
        },
    )

    st.caption(f"Showing {len(filtered):,} of {len(shipments):,} shipments.")
    st.download_button(
        "Download plan CSV",
        filtered.to_csv(index=False).encode("utf-8"),
        file_name=f"plan_{sid}_{level}.csv",
        mime="text/csv",
        type="primary",
        disabled=not checker.get("passed", False),
    )
    if not checker.get("passed", False):
        st.caption("Export is disabled until the checker passes.")

st.divider()
st.subheader("Unmet demand")
if unmet.empty:
    st.success("No unmet units at this planning level — every target was covered by eligible stock.")
else:
    st.dataframe(
        unmet,
        hide_index=True,
        width="stretch",
        column_config={
            "store_id": "Store",
            "sku_id": "SKU",
            "target_units": st.column_config.NumberColumn("Target", format="%d"),
            "shipped_units": st.column_config.NumberColumn("Shipped", format="%d"),
            "unmet_units": st.column_config.NumberColumn("Unmet", format="%d"),
        },
    )
    st.caption(
        f"{int(unmet['unmet_units'].sum()):,} units could not be covered from eligible stock. "
        "This is a constraint result, not a hidden failure."
    )
