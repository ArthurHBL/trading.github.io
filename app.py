import streamlit as st
import pandas as pd
import io
from datetime import date

st.set_page_config(page_title="Trading System", layout="wide")

# --- Storage ---
if "strategies" not in st.session_state:
    st.session_state.strategies = {}

# --- Sidebar ---
st.sidebar.title("Trading Dashboard")
analysis_date = st.sidebar.date_input("Select Analysis Date", value=date.today())

# --- Strategy Form ---
st.title("Trading Strategy Notes")

with st.form("notes_form"):
    strategy_name = st.text_input("Strategy Name", "")
    strategy_type = st.selectbox(
        "Strategy Type",
        ["Not Defined", "Scalping", "Swing", "Position", "Algorithmic"],
        index=0  # default = Not Defined
    )
    indicators = st.multiselect(
        "Indicators Used",
        ["RSI", "EMA", "Stoch RSI", "Pure ROC", "ROC Bands", "Volume Delta", "Cumulative Delta"],
    )
    notes = st.text_area("Notes")
    submitted = st.form_submit_button("Save Strategy")

if submitted:
    if analysis_date not in st.session_state.strategies:
        st.session_state.strategies[analysis_date] = []
    st.session_state.strategies[analysis_date].append({
        "Strategy": strategy_name if strategy_name else "Unnamed",
        "Type": strategy_type,
        "Indicators": ", ".join(indicators) if indicators else "None",
        "Notes": notes
    })
    st.success(f"Saved strategy '{strategy_name}' for {analysis_date}")

# --- Display Saved Strategies ---
st.subheader(f"Strategies for {analysis_date}")

strategies_today = st.session_state.strategies.get(analysis_date, [])

if strategies_today:
    n_cols = 2  # number of columns in the grid
    cols = st.columns(n_cols)

    for i, strat in enumerate(strategies_today):
        with cols[i % n_cols].expander(f"{strat['Strategy']} ({strat['Type']})"):
            st.write(f"**Indicators:** {strat['Indicators']}")
            st.write(f"**Notes:** {strat['Notes']}")

    # --- Export CSV filtered by date ---
    df = pd.DataFrame(strategies_today)
    csv_buffer = io.StringIO()
    df.to_csv(csv_buffer, index=False)

    st.download_button(
        label="📥 Download CSV (Excel-ready, filtered by date)",
        data=csv_buffer.getvalue(),
        file_name=f"strategies_{analysis_date}.csv",
        mime="text/csv"
    )
else:
    st.info("No strategies saved for this date yet.")
