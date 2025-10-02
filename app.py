# app.py - Enhanced Chart Reminder & Notes (15 Strategies) - FINAL VERSION
import streamlit as st
import json
import os
from datetime import datetime, date, timedelta
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import uuid

# -------------------------
# Optional Dependencies with Fallbacks
# -------------------------
try:
    import plotly.express as px
    import plotly.graph_objects as go
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False

# -------------------------
# Configuration
# -------------------------
st.set_page_config(
    page_title="Chart Reminder & Notes (15 Strategies)", 
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

SAVE_FILE = "strategy_analyses.json"
BACKUP_DIR = "backups"

# -------------------------
# Enhanced Utility Functions
# -------------------------
def ensure_backup_dir():
    """Ensure backup directory exists"""
    os.makedirs(BACKUP_DIR, exist_ok=True)

def load_data() -> Dict:
    """Load data with robust error handling"""
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return normalize_data_structure(data)
        except (json.JSONDecodeError, Exception) as e:
            st.error(f"⚠️ Error loading data: {e}")
            return load_latest_backup()
    return {}

def normalize_data_structure(data: Dict) -> Dict:
    """Ensure data has proper structure"""
    normalized = {}
    for strat_name, indicators in data.items():
        if isinstance(indicators, dict):
            normalized[strat_name] = {}
            for ind_name, meta in indicators.items():
                if isinstance(meta, dict):
                    normalized[strat_name][ind_name] = {
                        "note": meta.get("note", ""),
                        "status": meta.get("status", "Open"),
                        "strategy_tag": meta.get("strategy_tag", "Neutral"),
                        "momentum": meta.get("momentum", "Not Defined"),
                        "analysis_date": meta.get("analysis_date", ""),
                        "last_modified": meta.get("last_modified", ""),
                        "priority": meta.get("priority", "Medium"),
                        "confidence": meta.get("confidence", 75),
                        "id": meta.get("id", str(uuid.uuid4())[:8])
                    }
    return normalized

def save_data(data: Dict) -> bool:
    """Save data with backup creation"""
    try:
        create_backup(data)
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"❌ Error saving data: {e}")
        return False

def create_backup(data: Dict):
    """Create timestamped backup"""
    ensure_backup_dir()
    backup_file = os.path.join(BACKUP_DIR, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
    try:
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    except Exception as e:
        st.error(f"Backup failed: {e}")

def load_latest_backup() -> Dict:
    """Load most recent backup"""
    ensure_backup_dir()
    try:
        backup_files = [f for f in os.listdir(BACKUP_DIR) if f.endswith('.json')]
        if backup_files:
            latest_backup = sorted(backup_files)[-1]
            with open(os.path.join(BACKUP_DIR, latest_backup), "r", encoding="utf-8") as f:
                return json.load(f)
    except Exception:
        pass
    return {}

def sanitize_key(s: str) -> str:
    """Create safe key names"""
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
         .lower()
    )

def get_daily_strategies(analysis_date: date) -> Tuple[List[str], int]:
    """Get strategies for the given date in 5-day cycle"""
    strategy_list = list(STRATEGIES.keys())
    start_date = date(2025, 8, 9)
    days_since_start = (analysis_date - start_date).days
    cycle_day = days_since_start % 5
    start_index = cycle_day * 3
    end_index = start_index + 3
    daily_strategies = strategy_list[start_index:end_index]
    return daily_strategies, cycle_day + 1

def generate_filtered_csv_bytes(data: Dict, target_date: date, export_type: str = "current") -> bytes:
    """Generate CSV data for export"""
    rows = []
    target_str = target_date.strftime("%Y-%m-%d")
    
    for strat, inds in data.items():
        for ind_name, meta in inds.items():
            if export_type == "current" and meta.get("analysis_date") != target_str:
                continue
            if export_type == "all" or (export_type == "current" and meta.get("analysis_date") == target_str):
                rows.append({
                    "Strategy": strat,
                    "Indicator": ind_name,
                    "Note": meta.get("note", ""),
                    "Status": meta.get("status", ""),
                    "Momentum": meta.get("momentum", "Not Defined"),
                    "Tag": meta.get("strategy_tag", "Neutral"),
                    "Priority": meta.get("priority", "Medium"),
                    "Confidence": meta.get("confidence", 75),
                    "Analysis_Date": meta.get("analysis_date", ""),
                    "Last_Modified": meta.get("last_modified", "")
                })
    
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=[
        "Strategy", "Indicator", "Note", "Status", "Momentum", "Tag", 
        "Priority", "Confidence", "Analysis_Date", "Last_Modified"
    ])
    return df.to_csv(index=False).encode("utf-8")

def get_analysis_dates(data: Dict) -> List[str]:
    """Get all dates with analysis data"""
    dates = set()
    for strategy in data.values():
        for indicator in strategy.values():
            if indicator.get('analysis_date'):
                dates.add(indicator['analysis_date'])
    return sorted(dates, reverse=True)

# FIX: REMOVED CACHE DECORATOR - dictionaries are not hashable
def calculate_progress(data: Dict, daily_strategies: List[str], analysis_date: date) -> Dict:
    """Calculate progress statistics"""
    target_date_str = analysis_date.strftime("%Y-%m-%d")
    
    total_indicators = sum(len(STRATEGIES.get(s, [])) for s in daily_strategies)
    completed_indicators = 0
    strategy_progress = {}
    
    for strategy in daily_strategies:
        strategy_inds = STRATEGIES.get(strategy, [])
        completed = 0
        for ind in strategy_inds:
            if (data.get(strategy, {}).get(ind, {}).get('analysis_date') == target_date_str and
                data.get(strategy, {}).get(ind, {}).get('status') == 'Done'):
                completed += 1
                completed_indicators += 1
        strategy_progress[strategy] = {
            'completed': completed,
            'total': len(strategy_inds),
            'progress': completed / len(strategy_inds) if strategy_inds else 0
        }
    
    overall_progress = completed_indicators / total_indicators if total_indicators else 0
    
    return {
        'overall': overall_progress,
        'strategies': strategy_progress,
        'completed_indicators': completed_indicators,
        'total_indicators': total_indicators
    }

def create_progress_chart(progress_data: Dict, daily_strategies: List[str]):
    """Create a progress visualization with fallback"""
    if not PLOTLY_AVAILABLE:
        st.subheader("📊 Progress Overview")
        for strategy in daily_strategies:
            progress = progress_data['strategies'][strategy]['progress']
            st.write(f"**{strategy}**: {progress_data['strategies'][strategy]['completed']}/{progress_data['strategies'][strategy]['total']}")
            st.progress(progress)
        return None
    
    strategies = daily_strategies
    completed = [progress_data['strategies'][s]['completed'] for s in strategies]
    total = [progress_data['strategies'][s]['total'] for s in strategies]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        name='Completed',
        x=strategies,
        y=completed,
        marker_color='#2E8B57',
        text=completed,
        textposition='auto',
    ))
    
    fig.add_trace(go.Bar(
        name='Remaining',
        x=strategies,
        y=[t - c for t, c in zip(total, completed)],
        marker_color='#FF6B6B',
        text=total,
        textposition='auto',
    ))
    
    fig.update_layout(
        title="📊 Today's Progress by Strategy",
        barmode='stack',
        showlegend=True,
        height=300,
        xaxis_tickangle=-45
    )
    
    return fig

def create_tag_distribution_chart(data: Dict, analysis_date: date):
    """Create tag distribution visualization with fallback"""
    target_date_str = analysis_date.strftime("%Y-%m-%d")
    tag_counts = {'Buy': 0, 'Sell': 0, 'Neutral': 0}
    
    for strategy in data.values():
        for indicator in strategy.values():
            if indicator.get('analysis_date') == target_date_str:
                tag = indicator.get('strategy_tag', 'Neutral')
                tag_counts[tag] = tag_counts.get(tag, 0) + 1
    
    if not PLOTLY_AVAILABLE:
        st.subheader("🎯 Tag Distribution")
        for tag, count in tag_counts.items():
            color = "🟢" if tag == "Buy" else "🔴" if tag == "Sell" else "⚪"
            st.write(f"{color} {tag}: {count}")
        return None
    
    colors = {'Buy': '#00FF7F', 'Sell': '#FF6B6B', 'Neutral': '#87CEEB'}
    
    fig = px.pie(
        values=list(tag_counts.values()),
        names=list(tag_counts.keys()),
        title="🎯 Strategy Tag Distribution (Today)",
        color=list(tag_counts.keys()),
        color_discrete_map=colors
    )
    
    fig.update_traces(textposition='inside', textinfo='percent+label')
    return fig

# -------------------------
# STRATEGIES Definition
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
# Initialize Data with Session State
# -------------------------
# FIX: Use session state to persist data across reruns
if 'data' not in st.session_state:
    st.session_state.data = load_data()

data = st.session_state.data

# -------------------------
# Enhanced Sidebar
# -------------------------
st.sidebar.title("🎛️ Control Panel")
st.sidebar.markdown("---")

# FIX: More robust query params handling
start_date = date(2025, 8, 9)

# Get date from URL parameters - more robust approach
try:
    current_date_str = st.query_params["date"]
except (KeyError, IndexError):
    current_date_str = ""

if current_date_str:
    try:
        analysis_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
    except ValueError:
        analysis_date = date.today()
else:
    analysis_date = date.today()

# Ensure analysis_date is not before start_date
if analysis_date < start_date:
    analysis_date = start_date

# Display current date
st.sidebar.subheader("📅 Analysis Date")
st.sidebar.markdown(f"**Current Date:** {analysis_date.strftime('%m/%d/%Y')}")

# FIX: SIMPLIFIED Date navigation with direct button actions
col1, col2 = st.sidebar.columns(2)
with col1:
    if st.button("◀️ Prev Day", use_container_width=True, key="prev_day_unique"):
        new_date = analysis_date - timedelta(days=1)
        if new_date >= start_date:
            st.query_params["date"] = new_date.strftime("%Y-%m-%d")
            st.rerun()
        else:
            st.sidebar.warning("Cannot go before start date")
with col2:
    if st.button("Next Day ▶️", use_container_width=True, key="next_day_unique"):
        new_date = analysis_date + timedelta(days=1)
        st.query_params["date"] = new_date.strftime("%Y-%m-%d")
        st.rerun()

# Quick date reset button
if st.sidebar.button("🔄 Today", use_container_width=True, key="today_btn_unique"):
    st.query_params["date"] = date.today().strftime("%Y-%m-%d")
    st.rerun()

st.sidebar.markdown("---")

# Daily Strategies
daily_strategies, cycle_day = get_daily_strategies(analysis_date)
progress_data = calculate_progress(data, daily_strategies, analysis_date)

st.sidebar.subheader("📋 Today's Focus")
st.sidebar.info(f"**Day {cycle_day} of 5-day cycle**")

st.sidebar.metric(
    "Overall Progress", 
    f"{progress_data['completed_indicators']}/{progress_data['total_indicators']}",
    f"{progress_data['overall']*100:.1f}%"
)

for strategy in daily_strategies:
    strat_progress = progress_data['strategies'][strategy]
    st.sidebar.progress(strat_progress['progress'], text=f"{strategy}: {strat_progress['completed']}/{strat_progress['total']}")

st.sidebar.markdown("---")

# Strategy Selection
selected_strategy = st.sidebar.selectbox(
    "🎯 Choose a strategy:", 
    daily_strategies,
    index=0,
    key="strategy_selector"
)

# All Strategies List
with st.sidebar.expander("📚 All 15 Strategies", expanded=False):
    for i, strategy in enumerate(STRATEGIES.keys(), 1):
        star = " ⭐" if strategy in daily_strategies else ""
        status_icon = "✅" if progress_data['strategies'].get(strategy, {}).get('progress', 0) == 1 else "🕓"
        st.write(f"{status_icon} {i}. {strategy}{star}")

st.sidebar.markdown("---")

# Enhanced Export Options
st.sidebar.subheader("📤 Export Data")
export_type = st.sidebar.radio("Export Type:", ["Current Date", "All Data"], key="export_type")

csv_bytes = generate_filtered_csv_bytes(data, analysis_date, "current" if export_type == "Current Date" else "all")
export_filename = f"strategy_analyses_{analysis_date.strftime('%Y%m%d')}.csv" if export_type == "Current Date" else "strategy_analyses_complete.csv"

st.sidebar.download_button(
    label=f"⬇️ Download {export_type} CSV",
    data=csv_bytes,
    file_name=export_filename,
    mime="text/csv",
    key="download_csv"
)

# Historical view functionality
available_dates = get_analysis_dates(data)
if available_dates:
    with st.sidebar.expander("🕓 Historical Analyses", expanded=False):
        selected_historical_date = st.selectbox("View past analyses:", available_dates)
        if st.button("📅 Load Historical View", key="load_historical"):
            st.query_params["date"] = selected_historical_date
            st.rerun()

# Data Management
with st.sidebar.expander("⚙️ Data Management", expanded=False):
    if st.button("🔄 Refresh Data", key="refresh_data"):
        st.session_state.data = load_data()
        st.rerun()
    
    if st.button("💾 Create Backup", key="create_backup"):
        if save_data(data):
            st.success("Backup created!")
    
    st.warning("⚠️ Data is automatically saved on changes")

# Help Section
with st.sidebar.expander("ℹ️ How to Use", expanded=False):
    st.markdown("""
    **Daily Workflow:**
    1. Check today's 3 focus strategies
    2. Analyze each indicator systematically  
    3. Set appropriate tags and confidence levels
    4. Mark completed indicators as "Done"
    5. Save your analysis
    
    **5-Day Cycle:** Systematically rotates through all 15 strategies
    """)

# -------------------------
# Main Layout
# -------------------------
st.title("📊 Advanced Chart Reminder & Indicator Notes")
st.markdown(f"**Day {cycle_day}** | Strategy: **{selected_strategy}** | Date: **{analysis_date.strftime('%m/%d/%Y')}**")

# Progress Visualization
if PLOTLY_AVAILABLE:
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        progress_chart = create_progress_chart(progress_data, daily_strategies)
        if progress_chart:
            st.plotly_chart(progress_chart, use_container_width=True)
    with col2:
        tag_chart = create_tag_distribution_chart(data, analysis_date)
        if tag_chart:
            st.plotly_chart(tag_chart, use_container_width=True)
    with col3:
        total_analyses = sum(len(inds) for inds in data.values())
        today_analyses = sum(1 for strat in data.values() for ind in strat.values() 
                            if ind.get('analysis_date') == analysis_date.strftime('%Y-%m-%d'))
        
        st.metric("Total Analyses", total_analyses)
        st.metric("Today's Analyses", today_analyses)
        st.metric("Completion Rate", f"{progress_data['overall']*100:.1f}%")
else:
    col1, col2 = st.columns(2)
    with col1:
        create_progress_chart(progress_data, daily_strategies)
    with col2:
        create_tag_distribution_chart(data, analysis_date)
    
    col3, col4 = st.columns(2)
    with col3:
        total_analyses = sum(len(inds) for inds in data.values())
        st.metric("Total Analyses", total_analyses)
    with col4:
        today_analyses = sum(1 for strat in data.values() for ind in strat.values() 
                            if ind.get('analysis_date') == analysis_date.strftime('%Y-%m-%d'))
        st.metric("Today's Analyses", today_analyses)

# Strategy Progress Indicators
st.subheader("🎯 Today's Strategy Progress")
progress_cols = st.columns(3)
for i, strat in enumerate(daily_strategies):
    with progress_cols[i]:
        strat_data = progress_data['strategies'][strat]
        progress_pct = strat_data['progress']
        
        if progress_pct == 1:
            st.success(f"✅ **{strat}** (Complete)")
        elif progress_pct > 0:
            st.info(f"🔄 **{strat}** ({strat_data['completed']}/{strat_data['total']})")
        else:
            st.warning(f"🕓 **{strat}** (Not Started)")
        
        st.progress(progress_pct)

st.markdown("---")

# -------------------------
# Notes Form - FINAL POLISHED VERSION
# -------------------------
st.subheader(f"✏️ Analysis Editor - {selected_strategy}")

strategy_data = data.get(selected_strategy, {})

# Strategy-level settings
col1, col2, col3, col4 = st.columns(4)

with col1:
    current_tag = next(iter(strategy_data.values()), {}).get("strategy_tag", "Neutral")
    strategy_tag = st.selectbox(
        "🏷️ Strategy Tag:", 
        ["Neutral", "Buy", "Sell"], 
        index=["Neutral", "Buy", "Sell"].index(current_tag),
        key="strategy_tag_global"
    )

with col2:
    current_type = next(iter(strategy_data.values()), {}).get("momentum", "Not Defined")
    strategy_type = st.selectbox(
        "📈 Strategy Type:", 
        ["Momentum", "Extreme", "Not Defined"], 
        index=["Momentum", "Extreme", "Not Defined"].index(current_type),
        key="strategy_type_global"
    )

with col3:
    current_priority = next(iter(strategy_data.values()), {}).get("priority", "Medium")
    strategy_priority = st.selectbox(
        "🎯 Priority:", 
        ["Low", "Medium", "High", "Critical"], 
        index=["Low", "Medium", "High", "Critical"].index(current_priority),
        key="strategy_priority_global"
    )

with col4:
    current_confidence = next(iter(strategy_data.values()), {}).get("confidence", 75)
    strategy_confidence = st.slider(
        "💪 Confidence:", 
        min_value=50,
        max_value=100, 
        value=current_confidence,
        key="strategy_confidence_global"
    )
    st.caption(f"Confidence: {strategy_confidence}%")

st.markdown("---")

# Indicator Analysis Section
st.markdown("### 📊 Indicator Analysis")

indicators = STRATEGIES[selected_strategy]
col_objs = st.columns(2)

# Main form
with st.form("analysis_form", clear_on_submit=False):
    form_data = {}
    
    for i, ind in enumerate(indicators):
        col = col_objs[i % 2]
        # FIX: Make keys more unique by including date
        key_base = f"{sanitize_key(selected_strategy)}_{sanitize_key(ind)}_{analysis_date.strftime('%Y%m%d')}"
        existing = strategy_data.get(ind, {})
        
        with col.expander(f"**{ind}**", expanded=False):
            # Status
            current_status = existing.get("status", "Open")
            status = st.selectbox(
                "Status", 
                ["Open", "In Progress", "Done", "Skipped"], 
                index=["Open", "In Progress", "Done", "Skipped"].index(current_status) if current_status in ["Open", "In Progress", "Done", "Skipped"] else 0,
                key=f"status_{key_base}"
            )
            
            # Note area
            default_note = existing.get("note", "")
            note = st.text_area(
                f"Analysis notes for {ind}",
                value=default_note,
                height=160,
                key=f"note_{key_base}",
                placeholder=f"Enter your analysis for {ind}..."
            )
            
            # Individual indicator confidence - using a different approach
            ind_confidence = st.slider(
                "Indicator Confidence",
                min_value=50,
                max_value=100,
                value=existing.get("confidence", strategy_confidence),
                key=f"conf_{key_base}"
            )
            
            form_data[ind] = {
                'note': note,
                'status': status,
                'confidence': ind_confidence
            }
            
            if existing.get("last_modified"):
                st.caption(f"Last updated: {existing['last_modified'][:16]}")
    
    # Single save button - clean and simple
    submitted = st.form_submit_button("💾 Save All Analysis", use_container_width=True)
    
    # FIX: SIMPLIFIED Overwrite Logic - Just warn and proceed
    if submitted:
        # Validate form data
        errors = []
        for ind in indicators:
            if form_data[ind]['status'] == 'Done' and not form_data[ind]['note'].strip():
                errors.append(f"❌ {ind} is marked 'Done' but has no notes")
        
        if errors:
            for error in errors:
                st.error(error)
        else:
            # Check for overwriting different dates - just warn, don't block
            warnings = []
            for ind in indicators:
                existing_data = data.get(selected_strategy, {}).get(ind, {})
                existing_date = existing_data.get("analysis_date")
                current_date_str = analysis_date.strftime("%Y-%m-%d")
                
                if existing_date and existing_date != current_date_str:
                    warnings.append(f"{ind} ({existing_date})")
            
            # Show warning but proceed anyway (cleaner UX)
            if warnings:
                st.warning(f"⚠️ Overwriting data from: {', '.join(warnings)}")
            
            # Save the data
            if selected_strategy not in data:
                data[selected_strategy] = {}
            
            for ind in indicators:
                data[selected_strategy][ind] = {
                    "note": form_data[ind]['note'],
                    "status": form_data[ind]['status'],
                    "momentum": strategy_type,
                    "strategy_tag": strategy_tag,
                    "priority": strategy_priority,
                    "confidence": form_data[ind]['confidence'],
                    "analysis_date": analysis_date.strftime("%Y-%m-%d"),
                    "last_modified": datetime.utcnow().isoformat() + "Z",
                    "id": str(uuid.uuid4())[:8]
                }
            
            # Update session state when saving data
            if save_data(data):
                st.session_state.data = data  # Update session state
                st.success("✅ Analysis saved successfully!")
                st.balloons()

# -------------------------
# Analysis Display
# -------------------------
st.markdown("---")
st.subheader("📜 Saved Analyses & Historical View")

# View options - SIMPLIFIED
view_options = ["Today's Focus", "All Strategies"] + daily_strategies
filter_type = st.selectbox("View:", view_options, key="view_filter")

# Determine strategies to show
if filter_type == "Today's Focus":
    strategies_to_show = daily_strategies
elif filter_type == "All Strategies":
    strategies_to_show = list(STRATEGIES.keys())
else:
    strategies_to_show = [filter_type]

# Color and icon mappings
color_map = {"Buy": "🟢", "Sell": "🔴", "Neutral": "⚪"}
status_icons = {"Open": "🕓", "In Progress": "🔄", "Done": "✅", "Skipped": "⏭️"}

# Display analyses
for strat in strategies_to_show:
    if strat not in data or not data[strat]:
        continue
        
    st.markdown(f"### {strat}")
    inds = data[strat]
    
    # Strategy summary
    strategy_tags = [meta.get("strategy_tag", "Neutral") for meta in inds.values()]
    tag_counts = {tag: strategy_tags.count(tag) for tag in set(strategy_tags)}
    tag_summary = " | ".join([f"{color_map.get(tag, '⚪')} {tag}: {count}" for tag, count in tag_counts.items()])
    
    st.markdown(f"**Strategy Summary:** {tag_summary}")
    
    # Create analysis cards
    for ind_name, meta in inds.items():
        tag = meta.get("strategy_tag", "Neutral")
        status = meta.get("status", "Open")
        confidence = meta.get("confidence", 75)
        priority = meta.get("priority", "Medium")
        
        with st.expander(
            f"{color_map.get(tag, '⚪')} {ind_name} | "
            f"{status_icons.get(status, '🕓')} {status} | "
            f"💪 {confidence}% | "
            f"🎯 {priority}", 
            expanded=False
        ):
            col_left, col_right = st.columns([3, 1])
            
            with col_left:
                st.write(meta.get("note", "") or "_No analysis notes yet_")
                
            with col_right:
                st.metric("Confidence", f"{confidence}%")
                st.write(f"**Priority:** {priority}")
                st.write(f"**Type:** {meta.get('momentum', 'Not Defined')}")
                st.write(f"**Last Updated:** {meta.get('last_modified', 'N/A')[:16]}")
                
                if st.button("📋 Copy Notes", key=f"copy_{meta.get('id', ind_name)}"):
                    st.code(meta.get("note", ""))

    st.markdown("---")

# Empty state handling
if not any(strat in data and data[strat] for strat in strategies_to_show):
    st.info("📝 No analyses found for the selected filters.")

# -------------------------
# Footer
# -------------------------
st.markdown("---")
footer_col1, footer_col2, footer_col3 = st.columns(3)

with footer_col1:
    st.markdown("📈 Analysis Statistics")
    total_notes = sum(len(inds) for inds in data.values())
    completed_notes = sum(1 for strat in data.values() for ind in strat.values() if ind.get('status') == 'Done')
    st.write(f"Total Analyses: {total_notes}")
    st.write(f"Completed: {completed_notes}")
    st.write(f"Completion Rate: {completed_notes/total_notes*100:.1f}%" if total_notes else "0%")

with footer_col2:
    st.markdown("🎯 Quick Actions")
    if st.button("🔄 Check Today's Progress", key="check_progress"):
        progress_data = calculate_progress(data, daily_strategies, analysis_date)
        st.rerun()

with footer_col3:
    st.markdown("🔮 Insights")
    if progress_data['overall'] > 0.8:
        st.success("Excellent progress today! 🎉")
    elif progress_data['overall'] > 0.5:
        st.info("Good progress! Keep going! 💪")
    else:
        st.warning("Time to focus on today's strategies! ⏰")

st.markdown("---")
st.caption("Advanced Chart Reminder & Notes v2.0 | Built with Streamlit | 15 Strategy Rotation System")
