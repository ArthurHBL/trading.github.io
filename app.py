# app.py
import streamlit as st
import json
import os
from datetime import datetime, date
import pandas as pd

st.set_page_config(page_title="Chart Reminder & Notes (15 Strategies)", layout="wide")

SAVE_FILE = "strategy_analyses.json"

# -------------------------
# Utility functions
# -------------------------
def load_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except Exception:
                return {}
    return {}

def save_data(data):
    with open(SAVE_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def sanitize_key(s: str):
    return (
        s.replace(" ", "_")
         .replace("/", "_")
         .replace("&", "and")
         .replace("%", "pct")
         .replace(".", "")
         .replace("-", "_")
         .replace("[", "")
         .replace("]", "")
         .replace("(", "")
         .replace(")", "")
         .replace(",", "_")
    )

def get_daily_strategies(analysis_date):
    strategy_list = list(STRATEGIES.keys())
    start_date = date(2025, 8, 9)
    days_since_start = (analysis_date - start_date).days
    cycle_day = days_since_start % 5
    start_index = cycle_day * 3
    end_index = start_index + 3
    daily_strategies = strategy_list[start_index:end_index]
    return daily_strategies, cycle_day + 1

def generate_filtered_csv_bytes(data, target_date):
    """
    Build CSV bytes containing only rows whose analysis_date == target_date (YYYY-MM-DD).
    Returns bytes.
    """
    rows = []
    target_str = target_date.strftime("%Y-%m-%d")
    for strat, inds in data.items():
        for ind_name, meta in inds.items():
            if meta.get("analysis_date") == target_str:
                rows.append({
                    "Strategy": strat,
                    "Indicator": ind_name,
                    "Note": meta.get("note", ""),
                    "Status": meta.get("status", ""),
                    "Momentum": meta.get("momentum", "Not Defined"),
                    "Tag": meta.get("strategy_tag", "Neutral"),
                    "Analysis_Date": meta.get("analysis_date", ""),
                    "Last_Modified": meta.get("last_modified", "")
                })
    if not rows:
        # create an empty dataframe with headers to keep CSV valid
        df = pd.DataFrame(columns=["Strategy","Indicator","Note","Status","Momentum","Tag","Analysis_Date","Last_Modified"])
    else:
        df = pd.DataFrame(rows)
    return df.to_csv(index=False).encode("utf-8")

# -------------------------
# STRATEGIES (your list)
# -------------------------
STRATEGIES = {
 "Premium Stoch": ["Overview","VWAP AA","VWAP","Volume Delta","Stoch RSI","SMI","RSI(SMI)","RAINBOW_RSI"],
 "LS Copy": ["Overview","NVT","RoC Bands","RoC","BBWP","PSO","RSI","RAINBOW_RSI"],
 "PositionFlow": ["Overview","VWAP","Chart VWAP","MACZ VWAP","MFI","Fisher Transform","RAINBOW_RSI"],
 "RenkoVol": ["Overview","GR-MMAs","Pi Cycle","Keltner & Bollinger","RSI Ichimoku","RWI","BBWP","Trend Master","VWAP-RSI","ASO"],
 "10h WWV Chart": ["Overview","BTC Log Regression","GR-MMAs","PiCycle","%R MA","RSI","Chaikin Oscillator","Ultimate HODL Wave","PVT","BBWP"],
 "Premium Osc Volatility": ["Overview","AO v2","ATR","RSI(ATR)","RSI","Stoch RSI"],
 "RSI Strategy": ["Overview","Supertrend","CM_Ultimate","FibZia","EVWMA_LB","RSI(63)","%R MA","WT_X","RAR [LuxAlgo]","RAINBOW_RSI","Coppock Curve","OBV","Global Liquidity Index"],
 "WeisWaveVol": ["Overview","Bitcoin Rainbow Wave","CVD Candles","Volume Delta","RSI(Volume Delta)","CMF","RAINBOW_RSI"],
 "PremiumACC": ["Overview","GC","PiCycle Top Indicator","EMA Ribbon","RCI3 Lines","TDIGM","CVD Ichimoku","RSI(OSC)","RSI","Crypto Fear & Greed Index","BBWP"],
 "VolPress": ["Overview","Alligator","GR-MMAs","CVO","WWV","RWI","MACD","TSI","Wick Delta Buy/Sell Pressure","Elasticity","WT_LB"],
 "Volatility": ["Overview","Symmetrical STD Channel","4 SMA","Golden Ratio Fib","RECON ATR","BBWP","SMI","Stoch RSI","CA_Fisher","RSI","RSI line"],
 "ACC/DIST": ["Overview","5 SMMA","Demand Index","BTC Transaction Fees","Ratings","BBWP","MVRV Z-Score"],
 "LuxAlgo": ["Overview","Symmetrical STD Channel","Ultimate RSI","RWI"],
 "Point and Figure": ["Overview","RW Monte Carlo","CM SuperGuppy","AOv2","BBWP","SNAB_RSI_EMA","CM_Williams_Vix_Fix","ASO","RAINBOW_RSI"],
 "Rational Strategy LT": ["Overview","MMBs","GR-Multiple MAs","SAR","Support and Resistance","Coppock Curve","Stoch RSI","BBPower","%R MA","TRIX"],
}

# -------------------------
# Load data and ensure defaults
# -------------------------
data = load_data()

# Ensure existing entries have required keys
for strat_name, inds in data.items():
    for ind_name, meta in inds.items():
        meta.setdefault("strategy_tag", "Neutral")
        meta.setdefault("momentum", "Not Defined")
        meta.setdefault("status", "Open")
        meta.setdefault("analysis_date", "")  # might be empty if saved earlier
        meta.setdefault("last_modified", "")

# Save back normalized structure (safe)
save_data(data)

# -------------------------
# Sidebar controls
# -------------------------
st.sidebar.title("Controls")
st.sidebar.subheader("📅 Analysis Date")
start_date = date(2025, 8, 9)
analysis_date = st.sidebar.date_input(
    "Select analysis date:",
    value=date.today() if date.today() >= start_date else start_date,
    min_value=start_date,
    help="Aug 9, 2025 is Day 1"
)
st.sidebar.markdown("---")

daily_strategies, cycle_day = get_daily_strategies(analysis_date)

st.sidebar.subheader("📋 Today's Focus")
st.sidebar.info(f"**Day {cycle_day} of 5-day cycle**\n• {daily_strategies[0]}\n• {daily_strategies[1]}\n• {daily_strategies[2]}")

selected_strategy = st.sidebar.selectbox("Choose a strategy:", daily_strategies)

with st.sidebar.expander("📋 All 15 Strategies", expanded=False):
    strategy_list = list(STRATEGIES.keys())
    for i, strategy in enumerate(strategy_list, 1):
        star = " ⭐" if strategy in daily_strategies else ""
        st.markdown(f"{i}. {strategy}{star}")
st.sidebar.markdown("---")

# CSV export (filtered by selected analysis_date)
csv_bytes = generate_filtered_csv_bytes(data, analysis_date)
st.sidebar.subheader("📄 Export (CSV filtered by date)")
st.sidebar.download_button(
    label="⬇️ Download CSV (filtered by selected date)",
    data=csv_bytes,
    file_name=f"strategy_analyses_{analysis_date.strftime('%Y%m%d')}.csv",
    mime="text/csv"
)

# -------------------------
# Main layout
# -------------------------
st.title("📊 Chart Reminder & Indicator Notes")
st.markdown(f"**Day {cycle_day} of 5-day cycle** | Selected: **{selected_strategy}** | Analysis date: **{analysis_date.strftime('%m/%d/%Y')}**")

# Progress indicator cards
cols = st.columns(3)
for i, strat in enumerate(daily_strategies):
    with cols[i]:
        if strat in data and any(ind.get('analysis_date') == analysis_date.strftime('%Y-%m-%d') for ind in data[strat].values()):
            st.success(f"✓ {strat}")
        elif strat == selected_strategy:
            st.info(f"📝 {strat} (current)")
        else:
            st.warning(f"⏳ {strat}")
st.markdown("---")

# -------------------------
# Notes Form (3-column grid)
# -------------------------
with st.form("notes_form"):
    st.subheader(f"Edit notes — {selected_strategy}")

    strategy_data = data.get(selected_strategy, {})
    # determine current tag / type defaults from existing entries (if any)
    current_strategy_tag = "Neutral"
    current_strategy_type = "Not Defined"
    for meta in strategy_data.values():
        if meta.get("strategy_tag"):
            current_strategy_tag = meta.get("strategy_tag")
        if meta.get("momentum"):
            current_strategy_type = meta.get("momentum")
        break

    # display with simple labels (no CSS)
    strategy_tag = st.selectbox(
        f"Strategy '{selected_strategy}' tag:",
        options=["Neutral", "Buy", "Sell"],
        index=["Neutral", "Buy", "Sell"].index(current_strategy_tag if current_strategy_tag in ["Neutral","Buy","Sell"] else "Neutral"),
        key=f"tag_{sanitize_key(selected_strategy)}"
    )

    strategy_type = st.selectbox(
        f"Strategy '{selected_strategy}' type:",
        options=["Momentum", "Extreme", "Not Defined"],
        index=["Momentum", "Extreme", "Not Defined"].index(current_strategy_type if current_strategy_type in ["Momentum","Extreme","Not Defined"] else "Not Defined"),
        key=f"type_{sanitize_key(selected_strategy)}"
    )

    st.markdown("---")

    indicators = STRATEGIES[selected_strategy]
    n_cols = 3
    col_objs = st.columns(n_cols)

    # Create grid: put each indicator in one of the n_cols columns (i % n_cols)
    for i, ind in enumerate(indicators):
        col = col_objs[i % n_cols]

        key_note = f"note__{sanitize_key(selected_strategy)}__{sanitize_key(ind)}"
        key_status = f"status__{sanitize_key(selected_strategy)}__{sanitize_key(ind)}"

        existing = strategy_data.get(ind, {})
        default_note = existing.get("note", "")
        default_status = existing.get("status", "Open")

        with col.expander(ind, expanded=False):
            st.text_area(f"Analysis — {ind}", value=default_note, key=key_note, height=140)
            st.selectbox("Status", options=["Open", "Done"], index=0 if default_status=="Open" else 1, key=key_status)

    submitted = st.form_submit_button("💾 Save all notes for this strategy")
    if submitted:
        if selected_strategy not in data:
            data[selected_strategy] = {}

        for ind in indicators:
            key_note = f"note__{sanitize_key(selected_strategy)}__{sanitize_key(ind)}"
            key_status = f"status__{sanitize_key(selected_strategy)}__{sanitize_key(ind)}"
            note_val = st.session_state.get(key_note, "")
            status_val = st.session_state.get(key_status, "Open")

            data[selected_strategy][ind] = {
                "note": note_val,
                "status": status_val,
                "momentum": strategy_type,
                "strategy_tag": strategy_tag,
                "analysis_date": analysis_date.strftime("%Y-%m-%d"),
                "last_modified": datetime.utcnow().isoformat() + "Z"
            }
        save_data(data)
        st.success("✅ Notes saved successfully.")

# -------------------------
# Display saved analyses
# -------------------------
st.markdown("---")
st.subheader("📜 View saved analyses")

view_options = ["Today's Focus", "All Strategies"] + daily_strategies
filter_strategy = st.selectbox("Filter by strategy:", view_options, index=0)

if filter_strategy == "Today's Focus":
    strategies_to_show = daily_strategies
elif filter_strategy == "All Strategies":
    strategies_to_show = list(data.keys())
elif filter_strategy in daily_strategies:
    strategies_to_show = [filter_strategy]
else:
    strategies_to_show = list(data.keys())

color_map = {"Buy": "🟢 Buy", "Sell": "🔴 Sell", "Neutral": "⚪ Neutral"}

for strat in strategies_to_show:
    st.markdown(f"### {strat}")
    inds = data.get(strat, {})
    if not inds:
        st.info("No saved notes for this strategy.")
        continue

    # show strategy tag (from first indicator)
    strategy_tag = next(iter(inds.values())).get("strategy_tag", "Neutral") if inds else "Neutral"
    st.markdown(f"**Strategy Tag:** {color_map.get(strategy_tag, strategy_tag)}")
    st.markdown("---")

    for ind_name, meta in inds.items():
        momentum_type = meta.get("momentum", "Not Defined")
        status = meta.get("status", "Open")
        status_icon = "✅ Done" if status == "Done" else "🕓 Open"
        with st.expander(f"📌 {ind_name} ({momentum_type}) — {status_icon}", expanded=False):
            note = meta.get("note", "")
            st.write(note if note else "_No notes yet_")
            st.caption(f"Last updated: {meta.get('last_modified', 'N/A')}")
    st.markdown("---")

st.info("**5-Day Cycle System**: Each day focuses on 3 strategies. Change the analysis date to see different strategy assignments. Use the CSV Export in the sidebar to download the filtered report for the selected date.")
