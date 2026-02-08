import math
import pandas as pd
import streamlit as st

st.set_page_config(page_title="Services 2.0 Calculator", layout="wide")

# ---------- Helpers ----------
@st.cache_data
def load_data_from_excel(file) -> pd.DataFrame:
    """
    Reads the canonical workbook's 'Data' sheet.
    Expected columns:
      - Service
      - Building
      - Level
      - Capacity
      - CumCost
      - MaxLevel
    """
    df = pd.read_excel(file, sheet_name="Data")
    df.columns = [str(c).strip() for c in df.columns]

    needed = ["Service", "Building", "Level", "Capacity", "CumCost", "MaxLevel"]
    missing = [c for c in needed if c not in df.columns]
    if missing:
        raise ValueError(f"Data sheet missing columns: {missing}")

    df["Service"] = df["Service"].astype(str).str.strip()
    df["Building"] = df["Building"].astype(str).str.strip()

    df["Level"] = pd.to_numeric(df["Level"], errors="coerce").astype("Int64")
    df["MaxLevel"] = pd.to_numeric(df["MaxLevel"], errors="coerce").astype("Int64")
    df["Capacity"] = pd.to_numeric(df["Capacity"], errors="coerce")
    df["CumCost"] = pd.to_numeric(df["CumCost"], errors="coerce")

    df = df.dropna(subset=["Service", "Building", "Level"]).copy()
    df["Level"] = df["Level"].astype(int)
    df["MaxLevel"] = df["MaxLevel"].astype(int)

    return df

def lookup(df: pd.DataFrame, service: str, building: str, level: int):
    row = df[(df["Service"] == service) & (df["Building"] == building) & (df["Level"] == level)]
    if row.empty:
        return None
    r = row.iloc[0]
    return {
        "capacity": float(r["Capacity"]),
        "cumcost": float(r["CumCost"]),
        "maxlevel": int(r["MaxLevel"]),
    }

def ceil_div(a: float, b: float) -> int:
    if b is None or b <= 0:
        return 0
    return int(math.ceil(a / b))

# ---------- UI ----------
st.title("Services 2.0 Calculator")

st.markdown(
    "Upload your canonical Excel workbook (the one with the **Data** sheet). "
    "If you don't upload, the app will try to load `data/Services_2_Calculator.xlsx`."
)

uploaded = st.file_uploader("Upload Services 2.0 Excel", type=["xlsx"])

default_path = "data/Services_2_Calculator.xlsx"
df = None
load_err = None

try:
    if uploaded is not None:
        df = load_data_from_excel(uploaded)
    else:
        # fall back to local file
        import os
        if os.path.exists(default_path):
            df = load_data_from_excel(default_path)
        else:
            st.warning("No file uploaded and no default file found at `data/Services_2_Calculator.xlsx`.")
            st.stop()
except Exception as e:
    load_err = str(e)

if load_err:
    st.error("Couldn't load the workbook. Details:")
    st.code(load_err)
    st.stop()

services = sorted(df["Service"].unique().tolist())
utilities_by_service = {
    s: sorted(df[df["Service"] == s]["Building"].unique().tolist()) for s in services
}

tab1, tab2 = st.tabs(["City Demand & Build Plan", "Scenario Builder"])

# ---------- TAB 1 ----------
with tab1:
    st.subheader("Inputs")

    demand_map = {
        "Regular RZ": 35,
        "4-tier Homes": 30,
        "Airport-Related": 40,
        "Old Town": 2,
        "Epic": 45,
        "Regional Buildings": 45,
        "Omega Buildings": 50,
    }

    left, right = st.columns([1, 1])

    with left:
        counts = {}
        for k in demand_map.keys():
            counts[k] = st.number_input(k, min_value=0, value=0, step=1, key=f"cnt_{k}")

    total_homes = int(sum(counts.values()))
    total_demand = int(sum(counts[k] * demand_map[k] for k in demand_map))

    with right:
        st.metric("Total Homes", total_homes)
        st.metric("TOTAL DEMAND (per service)", total_demand)

    st.divider()
    st.subheader("Quick plan (choose 1 utility per service)")

    plan_rows = []
    for s in services:
        util_options = utilities_by_service.get(s, [])
        if not util_options:
            continue

        c1, c2, c3 = st.columns([2, 1, 1])
        with c1:
            util = st.selectbox(f"{s} Utility", util_options, key=f"plan_util_{s}")
        maxlvl = int(df[(df["Service"] == s) & (df["Building"] == util)]["MaxLevel"].max())
        with c2:
            lvl = st.number_input(f"{s} Level", min_value=1, max_value=maxlvl, value=maxlvl, step=1, key=f"plan_lvl_{s}")

        info = lookup(df, s, util, int(lvl))
        cap = info["capacity"] if info else 0
        cost = info["cumcost"] if info else 0

        needed = ceil_div(total_demand, cap)
        spare = needed * cap - total_demand

        plan_rows.append({
            "Service": s,
            "Utility": util,
            "Level": int(lvl),
            "Capacity @ Level": cap,
            "Buildings Needed": needed,
            "Spare Capacity": spare,
            "Cost per Building (CumCost)": cost,
            "Total Cost": needed * cost,
        })

    plan_df = pd.DataFrame(plan_rows)
    st.dataframe(plan_df, use_container_width=True, hide_index=True)

    st.metric("Total Buildings (plan)", int(plan_df["Buildings Needed"].sum()) if not plan_df.empty else 0)
    st.metric("Total Cost (plan)", float(plan_df["Total Cost"].sum()) if not plan_df.empty else 0.0)

# ---------- TAB 2 ----------
with tab2:
    st.subheader("Scenario Builder (compare mixes by Quantity + Level)")
    st.caption("Pick Service + Utility + Level + Quantity. The app calculates row capacity and row cost.")

    # Start with a few blank-ish rows
    default_service = services[0] if services else ""
    default_utility = utilities_by_service[default_service][0] if default_service and utilities_by_service.get(default_service) else ""

    base = pd.DataFrame(
        [{"Service": default_service, "Utility": default_utility, "Level": 1, "Quantity": 0} for _ in range(8)]
    )

    edited = st.data_editor(
        base,
        num_rows="dynamic",
        use_container_width=True,
        column_config={
            "Service": st.column_config.SelectboxColumn("Service", options=services),
            "Utility": st.column_config.SelectboxColumn("Utility", options=sorted(df["Building"].unique().tolist())),
            "Level": st.column_config.NumberColumn("Level", min_value=1, max_value=10, step=1),
            "Quantity": st.column_config.NumberColumn("Quantity", min_value=0, step=1),
        },
        key="scenario_editor"
    )

    out_rows = []
    for _, r in edited.iterrows():
        s = str(r.get("Service", "")).strip()
        u = str(r.get("Utility", "")).strip()
        lvl = int(r.get("Level", 1) or 1)
        qty = int(r.get("Quantity", 0) or 0)

        info = lookup(df, s, u, lvl)
        if info is None:
            out_rows.append({
                "Service": s, "Utility": u, "Level": lvl, "Quantity": qty,
                "Capacity@Level": None, "Cost@Level": None,
                "Row Capacity": None, "Row Cost": None,
                "Status": "Not found"
            })
            continue

        cap = info["capacity"]
        cost = info["cumcost"]

        out_rows.append({
            "Service": s, "Utility": u, "Level": lvl, "Quantity": qty,
            "Capacity@Level": cap, "Cost@Level": cost,
            "Row Capacity": cap * qty, "Row Cost": cost * qty,
            "Status": "OK"
        })

    out_df = pd.DataFrame(out_rows)
    st.dataframe(out_df, use_container_width=True, hide_index=True)

    st.metric("Scenario Total Capacity", float(out_df["Row Capacity"].fillna(0).sum()) if not out_df.empty else 0.0)
    st.metric("Scenario Total Cost", float(out_df["Row Cost"].fillna(0).sum()) if not out_df.empty else 0.0)
