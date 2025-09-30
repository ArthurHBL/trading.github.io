# app.py
import streamlit as st
import json
import os
from datetime import datetime, date
import pandas as pd
import io

st.set_page_config(page_title="Chart Reminder & Notes (15 Strategies)", layout="wide")

SAVE_FILE = "strategy_analyses.json"

def load_data():
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
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

def generate_excel_report(data, analysis_date):
    report_data = []
    for strategy_name, indicators in data.items():
        strategy_tag = "Neutral"
        strategy_type = "Not Defined"
        if indicators:
            first_indicator = next(iter(indicators.values()))
            strategy_tag = first_indicator.get('strategy_tag', 'Neutral')
            strategy_type = first_indicator.get('momentum', 'Not Defined')
        for ind_name, meta in indicators.items():
            report_data.append({
                'Strategy': strategy_name,
                'Strategy_Tag': strategy_tag,
                'Strategy_Type': strategy_type,
                'Indicator': ind_name,
                'Status': meta.get('status', ''),
                'Analysis': meta.get('note', ''),
                'Analysis_Date': meta.get('analysis_date', analysis_date.strftime('%Y-%m-%d')),
                'Last_Modified': meta.get('last_modified', '')
            })
    df = pd.DataFrame(report_data)
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Trading Analysis', index=False)
        summary_data = {
            'Metric': ['Total Strategies', 'Total Indicators', 'Analysis Date'],
            'Value': [len(data), sum(len(indicators) for indicators in data.values()), analysis_date.strftime('%m/%d/%Y')]
        }
        summary_df = pd.DataFrame(summary_data)
        summary_df.to_excel(writer, sheet_name='Summary', index=False)
        for sheet_name in writer.sheets:
            worksheet = writer.sheets[sheet_name]
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
    buffer.seek(0)
    return buffer

# -------------------------
# Estratégias
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
 "Rational Strategy LT": ["Overview","MMBs","GR-Multiple MAs","SAR","Support and Resistance","Coppock Curve","Stoch RSI","BBPower","%R MA","TRIX"]
}

# -------------------------
# Load existing data
# -------------------------
data = load_data()

# Set all strategy tags to Neutral
for strategy_name in data:
    for indicator_name in data[strategy_name]:
        data[strategy_name][indicator_name]['strategy_tag'] = 'Neutral'

save_data(data)

# Sidebar
st.sidebar.title("Controls")
st.sidebar.subheader("📅 Analysis Date")
start_date = date(2025, 8, 9)
analysis_date = st.sidebar.date_input(
    "Select analysis date:",
    value=date.today() if date.today() >= start_date else start_date,
    min_value=start_date,
    help="August 9, 2025 is Day 1 of the 5-day cycle"
)
st.sidebar.markdown("---")

daily_strategies, cycle_day = get_daily_strategies(analysis_date)

st.sidebar.subheader("📋 Today's Focus")
st.sidebar.info(f"**Day {cycle_day} of 5-day cycle**\n\nToday's strategies:\n• {daily_strategies[0]}\n• {daily_strategies[1]}\n• {daily_strategies[2]}")

selected_strategy = st.sidebar.selectbox("Choose a strategy:", daily_strategies)

st.sidebar.subheader("📋 All 15 Strategies")
strategy_list = list(STRATEGIES.keys())
for i, strategy in enumerate(strategy_list, 1):
    if strategy in daily_strategies:
        st.sidebar.markdown(f"**{i}. {strategy}** ⭐")
    else:
        st.sidebar.markdown(f"{i}. {strategy}")

st.sidebar.markdown("---")
st.sidebar.subheader("📄 Export Analyses")
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("📁 JSON"):
        st.download_button(
            label="Download JSON",
            data=json.dumps(data, ensure_ascii=False, indent=2),
            file_name=f"strategy_analyses_{analysis_date.strftime('%Y%m%d')}.json",
            mime="application/json"
        )
with col2:
    if st.button("📊 Excel"):
        if data:
            excel_buffer = generate_excel_report(data, analysis_date)
            st.download_button(
                label="Download Excel",
                data=excel_buffer.getvalue(),
                file_name=f"trading_report_{analysis_date.strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )
        else:
            st.warning("No saved analyses to export.")

# Main layout
st.title("📊 Chart Reminder & Indicator Notes")
st.markdown("**Day {} of 5-day cycle** | Selected strategy: **{}** | Analysis date: **{}**".format(
    cycle_day, selected_strategy, analysis_date.strftime('%m/%d/%Y')))

col1, col2, col3 = st.columns(3)
for i, strategy in enumerate(daily_strategies):
    with [col1, col2, col3][i]:
        if strategy in data and any(ind.get('analysis_date') == analysis_date.strftime('%Y-%m-%d') for ind in data[strategy].values()):
            st.success(f"✓ {strategy}")
        elif strategy == selected_strategy:
            st.info(f"📝 {strategy} (current)")
        else:
            st.warning(f"⏳ {strategy}")

st.markdown("---")

# Form to edit notes
with st.form("notes_form"):
    strategy_data = data.get(selected_strategy, {})

    # Strategy tag
    current_strategy_tag = "Neutral"
    if strategy_data:
        for ind_data in strategy_data.values():
            if "strategy_tag" in ind_data:
                current_strategy_tag = ind_data["strategy_tag"]
                break

    strategy_tag = st.selectbox(
        f"Strategy '{selected_strategy}' tag:",
        options=["Neutral", "Buy", "Sell"],
        index=["Neutral","Buy","Sell"].index(current_strategy_tag if current_strategy_tag in ["Neutral","Buy","Sell"] else "Neutral"),
        key="strategy_tag"
    )

    # Strategy type
    current_strategy_type = "Not Defined"
    if strategy_data:
        for ind_data in strategy_data.values():
            if "momentum" in ind_data:
                current_strategy_type = ind_data["momentum"]
                break

    strategy_type = st.selectbox(
        f"Strategy '{selected_strategy}' type:",
        options=["Momentum", "Extreme", "Not Defined"],
        index=["Momentum","Extreme","Not Defined"].index(current_strategy_type if current_strategy_type in ["Momentum","Extreme","Not Defined"] else 2),
        key="strategy_type"
    )

    st.markdown("---")
    indicators = STRATEGIES[selected_strategy]
    for ind in indicators:
        key_note = f"note__{sanitize_key(selected_strategy)}__{sanitize_key(ind)}"
        key_status = f"status__{sanitize_key(selected_strategy)}__{sanitize_key(ind)}"
        existing = data.get(selected_strategy, {}).get(ind, {})
        default_note = existing.get("note", "")
        default_status = existing.get("status", "Open")
        with st.expander(ind, expanded=False):
            st.text_area(f"Analysis — {ind}", value=default_note, key=key_note, height=140)
            st.selectbox("Status", options=["Open","Done"], index=0 if default_status=="Open" else 1, key=key_status)

    submitted = st.form_submit_button("💾 Save all notes for this strategy")
    if submitted:
        if selected_strategy not in data:
            data[selected_strategy] = {}
        strategy_tag_val = st.session_state.get("strategy_tag", "Neutral")
        strategy_type_val = st.session_state.get("strategy_type", "Not Defined")
        for ind in indicators:
            key_note = f"note__{sanitize_key(selected_strategy)}__{sanitize_key(ind)}"
            key_status = f"status__{sanitize_key(selected_strategy)}__{sanitize_key(ind)}"
            note_val = st.session_state.get(key_note, "")
            status_val = st.session_state.get(key_status, "Open")
            data[selected_strategy][ind] = {
                "note": note_val,
                "status": status_val,
                "momentum": strategy_type_val,
                "strategy_tag": strategy_tag_val,
                "analysis_date": analysis_date.strftime('%Y-%m-%d'),
                "last_modified": datetime.utcnow().isoformat() + "Z"
            }
        save_data(data)
        st.success("Analyses saved for strategy '{}' with tag '{}'.".format(selected_strategy, strategy_tag_val))

st.markdown("---")

# Display saved analyses
st.subheader("📜 View saved analyses")
view_options = ["Today's Focus", "All Strategies"] + daily_strategies
filter_strategy = st.selectbox("Filter by strategy:", view_options)
if filter_strategy == "Today's Focus":
    strategies_to_show = daily_strategies
elif filter_strategy == "All Strategies":
    strategies_to_show = list(data.keys())
elif filter_strategy in daily_strategies:
    strategies_to_show = [filter_strategy]
else:
    strategies_to_show = list(data.keys())

for strat in strategies_to_show:
    st.markdown(f"### {strat}")
    inds = data.get(strat, {})
    if not inds:
        st.info("No saved notes for this strategy.")
        continue
    strategy_tag = next(iter(inds.values())).get('strategy_tag','Neutral') if inds else 'Neutral'
    st.markdown(f"**Strategy Tag: {strategy_tag}**")
    st.markdown("---")
    for ind_name, meta in inds.items():
        momentum_type = meta.get("momentum","Not Defined")
        st.markdown(f"**{ind_name}** ({momentum_type})")
        note = meta.get("note","")
        st.write(note if note else "_No notes_")
        st.markdown("---")

st.info("**5-Day Cycle System**: Each day focuses on 3 strategies. Change the analysis date to see different strategy assignments. Tip: use the 'Export Analyses' buttons in the sidebar to download a backup.")
