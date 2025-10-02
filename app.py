# app.py - Enhanced Chart Reminder & Notes (15 Strategies) - CLEAN VERSION
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

def create_enhanced_progress_chart(progress_data: Dict, daily_strategies: List[str]):
    """More engaging progress visualization"""
    if not PLOTLY_AVAILABLE:
        st.subheader("📊 Progress Overview")
        for strategy in daily_strategies:
            progress = progress_data['strategies'][strategy]['progress']
            st.write(f"**{strategy}**: {progress_data['strategies'][strategy]['completed']}/{progress_data['strategies'][strategy]['total']}")
            st.progress(progress)
        return None
    
    strategies = daily_strategies
    progress_pct = [progress_data['strategies'][s]['progress'] * 100 for s in strategies]
    
    # Color based on completion
    colors = ['#FF6B6B' if p < 30 else '#FFD166' if p < 70 else '#06D6A0' for p in progress_pct]
    
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=strategies,
        y=progress_pct,
        marker_color=colors,
        text=[f"{p:.0f}%" for p in progress_pct],
        textposition='auto',
    ))
    
    fig.update_layout(
        title="📊 Today's Completion Progress",
        yaxis_title="Completion %",
        yaxis_range=[0, 100],
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

def show_recent_activity(data: Dict, strategy: str):
    """Show recent changes for collaborative awareness"""
    recent_changes = []
    for ind, meta in data.get(strategy, {}).items():
        if meta.get('last_modified'):
            recent_changes.append({
                'indicator': ind,
                'time': meta['last_modified'],
                'user': 'You'  # Could be extended for multi-user
            })
    
    if recent_changes:
        st.sidebar.markdown("---")
        st.sidebar.subheader("🕒 Recent Activity")
        for change in sorted(recent_changes, key=lambda x: x['time'], reverse=True)[:3]:
            st.sidebar.caption(f"**{change['indicator']}** - {change['time'][:16]}")

def create_analysis_insights(data: Dict, daily_strategies: List[str], analysis_date: date) -> str:
    """Provide AI-like insights about the analysis"""
    target_date_str = analysis_date.strftime("%Y-%m-%d")
    
    buy_signals = 0
    sell_signals = 0
    high_confidence = 0
    
    for strategy in daily_strategies:
        for ind_name, meta in data.get(strategy, {}).items():
            if meta.get('analysis_date') == target_date_str:
                tag = meta.get('strategy_tag', 'Neutral')
                confidence = meta.get('confidence', 75)
                
                if tag == 'Buy':
                    buy_signals += 1
                elif tag == 'Sell':
                    sell_signals += 1
                
                if confidence >= 80:
                    high_confidence += 1
    
    total_signals = buy_signals + sell_signals
    
    # REMOVED: Annoying "no analysis completed" message
    # Only show insights when there's actual data
    if total_signals == 0:
        return ""  # Return empty string instead of annoying message
    
    if buy_signals > sell_signals * 2:
        insight = "🎯 **Insight:** Strong bullish bias across strategies today"
    elif sell_signals > buy_signals * 2:
        insight = "⚠️ **Insight:** Bearish signals dominating today"
    else:
        insight = "⚖️ **Insight:** Mixed signals - proceed with caution"
    
    if high_confidence >= total_signals * 0.7:
        insight += " | High confidence levels 📈"
    elif high_confidence <= total_signals * 0.3:
        insight += " | Low confidence - verify signals 🔍"
    
    return insight

def create_guided_onboarding(strategy: str, indicators: List[str], has_data: bool):
    """Help users get started with guided analysis"""
    if not has_data:
        st.info(f"""
        **🎯 Getting Started with {strategy}**
        
        1. **Set Strategy Direction**: Choose Buy/Sell/Neutral tag above
        2. **Analyze Indicators**: Expand each indicator to add notes
        3. **Set Confidence**: Adjust based on signal strength
        4. **Mark Complete**: Change status to Done when finished
        5. **Save**: Don't forget to save your analysis!
        """)

def with_loading_spinner(operation_name: str):
    """Decorator for operations that might take time"""
    def decorator(func):
        def wrapper(*args, **kwargs):
            with st.spinner(f"{operation_name}..."):
                return func(*args, **kwargs)
        return wrapper
    return decorator

@with_loading_spinner("Loading analysis data")
def load_enhanced_data():
    return load_data()

def create_mobile_friendly_layout():
    """Adjust layout for better mobile experience"""
    if st.sidebar.checkbox("📱 Mobile Optimized View", key="mobile_view"):
        st.markdown("""
        <style>
        .block-container {
            padding-top: 1rem;
            padding-bottom: 1rem;
        }
        .stExpander {
            margin-bottom: 0.5rem;
        }
        .element-container {
            margin-bottom: 0.5rem;
        }
        </style>
        """, unsafe_allow_html=True)

def create_quick_actions(data: Dict, strategy: str, indicators: List[str], analysis_date: date):
    """Add quick action buttons"""
    st.markdown("### ⚡ Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎯 Mark All as Done", key="mark_all_done", use_container_width=True):
            target_date_str = analysis_date.strftime("%Y-%m-%d")
            
            for ind in indicators:
                if strategy not in data:
                    data[strategy] = {}
                if ind not in data[strategy]:
                    data[strategy][ind] = {}
                
                # Preserve existing notes if any, otherwise leave empty
                existing_note = data[strategy][ind].get("note", "")
                
                data[strategy][ind].update({
                    "status": "Done",
                    "note": existing_note,  # Keep existing notes or leave empty
                    "analysis_date": target_date_str,
                    "last_modified": datetime.utcnow().isoformat() + "Z",
                    # Preserve other existing values or set defaults
                    "strategy_tag": data[strategy][ind].get("strategy_tag", "Neutral"),
                    "momentum": data[strategy][ind].get("momentum", "Not Defined"),
                    "priority": data[strategy][ind].get("priority", "Medium"),
                    "confidence": data[strategy][ind].get("confidence", 75),
                    "id": data[strategy][ind].get("id", str(uuid.uuid4())[:8])
                })
            
            if save_data(data):
                st.session_state.data = data
                st.success("All indicators marked as Done! ✅")
                st.rerun()
                
    with col2:
        if st.button("🔄 Reset Today", key="reset_today", use_container_width=True):
            target_date_str = analysis_date.strftime("%Y-%m-%d")
            for ind in indicators:
                if strategy in data and ind in data[strategy]:
                    if data[strategy][ind].get('analysis_date') == target_date_str:
                        data[strategy][ind] = {
                            "note": "",
                            "status": "Open",
                            "momentum": "Not Defined",
                            "strategy_tag": "Neutral",
                            "priority": "Medium",
                            "confidence": 75,
                            "analysis_date": target_date_str,
                            "last_modified": datetime.utcnow().isoformat() + "Z",
                            "id": str(uuid.uuid4())[:8]
                        }
            
            if save_data(data):
                st.session_state.data = data
                st.success("Today's analysis reset! 🔄")
                st.rerun()

def handle_quick_status_updates(data: Dict, strategy: str, indicators: List[str], analysis_date: date):
    """Handle quick status updates with proper state management"""
    target_date_str = analysis_date.strftime("%Y-%m-%d")
    status_changed = False
    
    # Initialize session state for tracking updates
    if 'quick_status_updates' not in st.session_state:
        st.session_state.quick_status_updates = {}
    
    st.markdown("#### ⚡ Quick Status Update")
    quick_status_cols = st.columns(min(6, len(indicators)))
    
    for i, ind in enumerate(indicators):
        with quick_status_cols[i % len(quick_status_cols)]:
            current_status = data.get(strategy, {}).get(ind, {}).get("status", "Open")
            status_options = ["Open", "In Progress", "Done", "Skipped"]
            
            # Create a unique key for each indicator's status
            status_key = f"quick_status_{sanitize_key(strategy)}_{sanitize_key(ind)}"
            
            new_status = st.selectbox(
                f"{ind[:12]}...",
                status_options,
                index=status_options.index(current_status) if current_status in status_options else 0,
                key=status_key
            )
            
            # Check if status actually changed
            if new_status != current_status:
                st.session_state.quick_status_updates[(strategy, ind)] = new_status
                status_changed = True
    
    # Apply all status updates at once
    if status_changed:
        for (strat, indicator), new_status in st.session_state.quick_status_updates.items():
            if strat not in data:
                data[strat] = {}
            if indicator not in data[strat]:
                data[strat][indicator] = {}
            
            data[strat][indicator].update({
                "status": new_status,
                "analysis_date": target_date_str,
                "last_modified": datetime.utcnow().isoformat() + "Z",
                "strategy_tag": data[strat][indicator].get("strategy_tag", "Neutral"),
                "momentum": data[strat][indicator].get("momentum", "Not Defined"),
                "priority": data[strat][indicator].get("priority", "Medium"),
                "confidence": data[strat][indicator].get("confidence", 75),
                "id": data[strat][indicator].get("id", str(uuid.uuid4())[:8])
            })
        
        if save_data(data):
            st.session_state.data = data
            st.session_state.quick_status_updates = {}  # Clear updates
            st.success("✅ Status updates saved!")
            st.rerun()

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
if 'data' not in st.session_state:
    st.session_state.data = load_enhanced_data()

data = st.session_state.data

# -------------------------
# Enhanced Sidebar
# -------------------------
st.sidebar.title("🎛️ Control Panel")
st.sidebar.markdown("---")

# Date handling
start_date = date(2025, 8, 9)

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

if analysis_date < start_date:
    analysis_date = start_date

# Display current date
st.sidebar.subheader("📅 Analysis Date")
st.sidebar.markdown(f"**Current Date:** {analysis_date.strftime('%m/%d/%Y')}")

# Date navigation
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

# 🚀 Quick Navigation
st.sidebar.subheader("🚀 Quick Navigation")
quick_strategy = st.sidebar.selectbox(
    "Jump to Strategy:", 
    daily_strategies,
    key="quick_nav"
)

# Update selected strategy if quick nav is used
if 'last_quick_nav' not in st.session_state:
    st.session_state.last_quick_nav = quick_strategy

if quick_strategy != st.session_state.last_quick_nav:
    st.session_state.strategy_selector = quick_strategy
    st.session_state.last_quick_nav = quick_strategy
    st.rerun()

# Strategy Selection
selected_strategy = st.sidebar.selectbox(
    "🎯 Choose a strategy:", 
    daily_strategies,
    index=daily_strategies.index(quick_strategy) if quick_strategy in daily_strategies else 0,
    key="strategy_selector"
)

# All Strategies List
with st.sidebar.expander("📚 All 15 Strategies", expanded=False):
    for i, strategy in enumerate(STRATEGIES.keys(), 1):
        star = " ⭐" if strategy in daily_strategies else ""
        status_icon = "✅" if progress_data['strategies'].get(strategy, {}).get('progress', 0) == 1 else "🕓"
        st.write(f"{status_icon} {i}. {strategy}{star}")

# Recent Activity
show_recent_activity(data, selected_strategy)

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
        st.session_state.data = load_enhanced_data()
        st.rerun()
    
    if st.button("💾 Create Backup", key="create_backup"):
        if save_data(data):
            st.success("Backup created!")
    
    st.warning("⚠️ Data is automatically saved on changes")

# 🎨 Display Options
with st.sidebar.expander("🎨 Display Options", expanded=False):
    theme = st.selectbox("Color Theme", ["Default", "Dark", "Professional"], key="theme_select")
    compact_mode = st.checkbox("Compact Mode", False, key="compact_mode")
    create_mobile_friendly_layout()

# Help Section
with st.sidebar.expander("ℹ️ How to Use", expanded=False):
    st.markdown("""
    **Daily Workflow:**
    1. Check today's 3 focus strategies
    2. Use Quick Navigation to jump between strategies
    3. Analyze each indicator systematically  
    4. Set appropriate tags and confidence levels
    5. Mark completed indicators as "Done"
    6. Save your analysis
    
    **5-Day Cycle:** Systematically rotates through all 15 strategies
    """)

# -------------------------
# Main Layout
# -------------------------
st.title("📊 Advanced Chart Reminder & Indicator Notes")
st.markdown(f"**Day {cycle_day}** | Strategy: **{selected_strategy}** | Date: **{analysis_date.strftime('%m/%d/%Y')}**")

# Analysis Insights - Only show when there's actual data
insight_text = create_analysis_insights(data, daily_strategies, analysis_date)
if insight_text:  # Only display if there's an actual insight
    st.info(insight_text)

# Progress Visualization
if PLOTLY_AVAILABLE:
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        progress_chart = create_enhanced_progress_chart(progress_data, daily_strategies)
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
        create_enhanced_progress_chart(progress_data, daily_strategies)
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
# Notes Form - CLEAN VERSION
# -------------------------
st.subheader(f"✏️ Analysis Editor - {selected_strategy}")

strategy_data = data.get(selected_strategy, {})
has_strategy_data = any(strategy_data.values())

# Quick Actions
create_quick_actions(data, selected_strategy, STRATEGIES[selected_strategy], analysis_date)

# Guided Onboarding
create_guided_onboarding(selected_strategy, STRATEGIES[selected_strategy], has_strategy_data)

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

# FIXED: Quick Status Updates - Now works properly!
handle_quick_status_updates(data, selected_strategy, STRATEGIES[selected_strategy], analysis_date)

st.markdown("---")

# Indicator Analysis Section
st.markdown("### 📊 Detailed Indicator Analysis")

indicators = STRATEGIES[selected_strategy]
col_objs = st.columns(2)

# Main form
with st.form("analysis_form", clear_on_submit=False):
    form_data = {}
    
    for i, ind in enumerate(indicators):
        col = col_objs[i % 2]
        key_base = f"{sanitize_key(selected_strategy)}_{sanitize_key(ind)}_{analysis_date.strftime('%Y%m%d')}"
        existing = strategy_data.get(ind, {})
        
        with col.expander(f"**{ind}**", expanded=False):
            # Status - this will reflect the quick status updates
            current_status = existing.get("status", "Open")
            status = st.selectbox(
                "Status", 
                ["Open", "In Progress", "Done", "Skipped"], 
                index=["Open", "In Progress", "Done", "Skipped"].index(current_status) if current_status in ["Open", "In Progress", "Done", "Skipped"] else 0,
                key=f"status_{key_base}"
            )
            
            # Note area
            note = st.text_area(
                f"Analysis notes for {ind}",
                value=existing.get("note", ""),
                height=160,
                key=f"note_{key_base}",
                placeholder=f"Enter your analysis for {ind}..."
            )
            
            # Individual indicator confidence
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
    
    # Single save button
    submitted = st.form_submit_button("💾 Save All Analysis", use_container_width=True)
    
    if submitted:
        # FIXED: More flexible validation - allow Done status without notes but show warnings
        warnings = []
        
        for ind in indicators:
            if form_data[ind]['status'] == 'Done' and not form_data[ind]['note'].strip():
                warnings.append(f"⚠️ {ind} is marked 'Done' but has no notes")
        
        # Show warnings but don't block saving
        if warnings:
            for warning in warnings:
                st.warning(warning)
            # Ask for confirmation to proceed
            if not st.checkbox("✅ I understand and want to save anyway", key="confirm_save_without_notes"):
                st.stop()  # Stop execution if not confirmed
        
        # Check for overwriting different dates - just warn, don't block
        date_warnings = []
        for ind in indicators:
            existing_data = data.get(selected_strategy, {}).get(ind, {})
            existing_date = existing_data.get("analysis_date")
            current_date_str = analysis_date.strftime("%Y-%m-%d")
            
            if existing_date and existing_date != current_date_str:
                date_warnings.append(f"{ind} ({existing_date})")
        
        # Show warning but proceed anyway (cleaner UX)
        if date_warnings:
            st.warning(f"⚠️ Overwriting data from: {', '.join(date_warnings)}")
        
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
            st.session_state.data = data
            st.success("✅ Analysis saved successfully!")
            st.balloons()

# -------------------------
# Analysis Display
# -------------------------
st.markdown("---")
st.subheader("📜 Saved Analyses & Historical View")

# View options
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
    if st.button("🔄 Check Today's Progress", key="check_progress_footer"):
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
st.caption("Advanced Chart Reminder & Notes v3.3 | Clean & Encouraging | Built with Streamlit | 15 Strategy Rotation System")
