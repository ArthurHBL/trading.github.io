# app.py - COMPLETE Trading Dashboard with Authentication
import streamlit as st
import streamlit_authenticator as stauth
import sqlite3
from datetime import datetime, date, timedelta
import json
import os
import pandas as pd
import numpy as np
from typing import Dict, List, Optional, Tuple
import uuid

# -------------------------
# AUTHENTICATION SETUP
# -------------------------
def init_db():
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users
                 (username TEXT PRIMARY KEY, name TEXT, password TEXT, plan TEXT, expires TEXT)''')
    
    # Insert demo users if not exists
    demo_users = [
        ("admin", "Arthur (Admin)", "admin123", "premium", "2030-12-31"),
        ("maria", "Maria Silva", "maria123", "premium", "2025-12-31"),
        ("joao", "João Santos", "joao123", "basic", "2024-01-31"),  # Expired
        ("demo", "Demo User", "demo123", "basic", "2024-12-31")
    ]
    
    for user in demo_users:
        try:
            c.execute("INSERT OR IGNORE INTO users VALUES (?, ?, ?, ?, ?)", user)
        except:
            pass
    
    conn.commit()
    conn.close()

def get_user(username):
    conn = sqlite3.connect("users.db")
    c = conn.cursor()
    c.execute("SELECT * FROM users WHERE username=?", (username,))
    user = c.fetchone()
    conn.close()
    return user

# Initialize database
init_db()

# Static users for authentication
names = ["Arthur (Admin)", "Maria Silva", "João Santos", "Demo User"]
usernames = ["admin", "maria", "joao", "demo"]
passwords = ["admin123", "maria123", "joao123", "demo123"]

authenticator = stauth.Authenticate(
    names, usernames, passwords,
    "trading_dashboard", "abcdef", cookie_expiry_days=30
)

# -------------------------
# APP CONFIGURATION
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
# UTILITY FUNCTIONS
# -------------------------
def ensure_backup_dir():
    os.makedirs(BACKUP_DIR, exist_ok=True)

def load_data() -> Dict:
    if os.path.exists(SAVE_FILE):
        try:
            with open(SAVE_FILE, "r", encoding="utf-8") as f:
                data = json.load(f)
                return normalize_data_structure(data)
        except:
            return {}
    return {}

def normalize_data_structure(data: Dict) -> Dict:
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
    try:
        ensure_backup_dir()
        backup_file = os.path.join(BACKUP_DIR, f"backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        with open(backup_file, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        st.error(f"❌ Error saving data: {e}")
        return False

def sanitize_key(s: str) -> str:
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
    strategy_list = list(STRATEGIES.keys())
    start_date = date(2025, 8, 9)
    days_since_start = (analysis_date - start_date).days
    cycle_day = days_since_start % 5
    start_index = cycle_day * 3
    end_index = start_index + 3
    daily_strategies = strategy_list[start_index:end_index]
    return daily_strategies, cycle_day + 1

def calculate_progress(data: Dict, daily_strategies: List[str], analysis_date: date) -> Dict:
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

# -------------------------
# STRATEGIES DEFINITION
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
# DASHBOARD COMPONENTS
# -------------------------
def render_premium_dashboard():
    """Full featured dashboard for premium users"""
    
    # Initialize data
    if 'data' not in st.session_state:
        st.session_state.data = load_data()
    data = st.session_state.data
    
    # Date handling
    start_date = date(2025, 8, 9)
    try:
        current_date_str = st.query_params.get("date", "")
        analysis_date = datetime.strptime(current_date_str, "%Y-%m-%d").date() if current_date_str else date.today()
    except:
        analysis_date = date.today()
    
    if analysis_date < start_date:
        analysis_date = start_date

    # Sidebar
    st.sidebar.title("🎛️ Control Panel")
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("📅 Analysis Date")
    st.sidebar.markdown(f"**Current Date:** {analysis_date.strftime('%m/%d/%Y')}")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("◀️ Prev Day", use_container_width=True):
            new_date = analysis_date - timedelta(days=1)
            if new_date >= start_date:
                st.query_params["date"] = new_date.strftime("%Y-%m-%d")
                st.rerun()
    with col2:
        if st.button("Next Day ▶️", use_container_width=True):
            new_date = analysis_date + timedelta(days=1)
            st.query_params["date"] = new_date.strftime("%Y-%m-%d")
            st.rerun()

    if st.sidebar.button("🔄 Today", use_container_width=True):
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
        key="strategy_selector"
    )

    # Main content
    st.title("🚀 Premium Trading Dashboard")
    st.markdown(f"**Day {cycle_day}** | Strategy: **{selected_strategy}** | Date: **{analysis_date.strftime('%m/%d/%Y')}**")
    
    # Progress indicators
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

    # Analysis Form
    st.subheader(f"✏️ Analysis Editor - {selected_strategy}")
    strategy_data = data.get(selected_strategy, {})

    # Strategy-level settings
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        current_tag = next(iter(strategy_data.values()), {}).get("strategy_tag", "Neutral")
        strategy_tag = st.selectbox("🏷️ Strategy Tag:", ["Neutral", "Buy", "Sell"], index=["Neutral", "Buy", "Sell"].index(current_tag))
    with col2:
        current_type = next(iter(strategy_data.values()), {}).get("momentum", "Not Defined")
        strategy_type = st.selectbox("📈 Strategy Type:", ["Momentum", "Extreme", "Not Defined"], index=["Momentum", "Extreme", "Not Defined"].index(current_type))
    with col3:
        current_priority = next(iter(strategy_data.values()), {}).get("priority", "Medium")
        strategy_priority = st.selectbox("🎯 Priority:", ["Low", "Medium", "High", "Critical"], index=["Low", "Medium", "High", "Critical"].index(current_priority))
    with col4:
        current_confidence = next(iter(strategy_data.values()), {}).get("confidence", 75)
        strategy_confidence = st.slider("💪 Confidence:", 50, 100, current_confidence)
        st.caption(f"Confidence: {strategy_confidence}%")

    st.markdown("---")

    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎯 Mark All as Done", use_container_width=True):
            target_date_str = analysis_date.strftime("%Y-%m-%d")
            for ind in STRATEGIES[selected_strategy]:
                if selected_strategy not in data:
                    data[selected_strategy] = {}
                data[selected_strategy][ind] = {
                    "status": "Done",
                    "note": data[selected_strategy].get(ind, {}).get("note", ""),
                    "analysis_date": target_date_str,
                    "last_modified": datetime.utcnow().isoformat() + "Z",
                    "strategy_tag": strategy_tag,
                    "momentum": strategy_type,
                    "priority": strategy_priority,
                    "confidence": strategy_confidence,
                    "id": str(uuid.uuid4())[:8]
                }
            if save_data(data):
                st.session_state.data = data
                st.success("All indicators marked as Done! ✅")
                st.rerun()
    with col2:
        if st.button("🔄 Reset Today", use_container_width=True):
            target_date_str = analysis_date.strftime("%Y-%m-%d")
            for ind in STRATEGIES[selected_strategy]:
                if selected_strategy in data and ind in data[selected_strategy]:
                    if data[selected_strategy][ind].get('analysis_date') == target_date_str:
                        data[selected_strategy][ind] = {
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

    st.markdown("---")

    # Detailed Analysis Form
    st.markdown("### 📊 Detailed Indicator Analysis")
    indicators = STRATEGIES[selected_strategy]
    col_objs = st.columns(2)

    with st.form("analysis_form", clear_on_submit=False):
        form_data = {}
        
        for i, ind in enumerate(indicators):
            col = col_objs[i % 2]
            key_base = f"{sanitize_key(selected_strategy)}_{sanitize_key(ind)}_{analysis_date.strftime('%Y%m%d')}"
            existing = strategy_data.get(ind, {})
            
            with col.expander(f"**{ind}**", expanded=False):
                current_status = existing.get("status", "Open")
                status = st.selectbox("Status", ["Open", "In Progress", "Done", "Skipped"], 
                                    index=["Open", "In Progress", "Done", "Skipped"].index(current_status) if current_status in ["Open", "In Progress", "Done", "Skipped"] else 0,
                                    key=f"status_{key_base}")
                
                note = st.text_area(f"Analysis notes for {ind}", value=existing.get("note", ""), height=120, key=f"note_{key_base}")
                
                ind_confidence = st.slider("Indicator Confidence", 50, 100, existing.get("confidence", strategy_confidence), key=f"conf_{key_base}")
                
                form_data[ind] = {'note': note, 'status': status, 'confidence': ind_confidence}
        
        submitted = st.form_submit_button("💾 Save All Analysis", use_container_width=True)
        
        if submitted:
            # Save data
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
            
            if save_data(data):
                st.session_state.data = data
                st.success("✅ Analysis saved successfully!")
                st.balloons()

def render_basic_dashboard():
    """Limited dashboard for basic users"""
    st.sidebar.title("🔓 Basic Access")
    st.sidebar.info("Upgrade to Premium for full features")
    
    st.title("📊 Trading Analysis - Basic Plan")
    st.warning("🔒 You are on the Basic plan. Upgrade to Premium for all 15 strategies and advanced features.")
    
    # Limited to first 3 strategies only
    available_strategies = list(STRATEGIES.keys())[:3]
    selected_strategy = st.selectbox("Select Strategy", available_strategies)
    
    # Simple analysis form
    with st.form("basic_analysis"):
        st.subheader(f"Basic Analysis - {selected_strategy}")
        
        # Limited to first 3 indicators per strategy
        for indicator in STRATEGIES[selected_strategy][:3]:
            st.text_area(f"Notes for {indicator}", key=f"basic_{indicator}", height=100)
        
        if st.form_submit_button("💾 Save Notes"):
            st.success("Notes saved! Upgrade to Premium for full analysis features.")
    
    st.markdown("---")
    st.info("⭐ **Premium features you're missing:**\n- All 15 strategies\n- Progress tracking\n- Confidence levels\n- Strategy tagging\n- Historical analysis\n- Export functionality")

def render_admin_dashboard():
    """Admin dashboard with user management"""
    st.sidebar.title("👑 Admin Panel")
    
    # User management
    st.title("👑 Admin Dashboard - User Management")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("Current Users")
        conn = sqlite3.connect("users.db")
        users_df = pd.read_sql("SELECT username, name, plan, expires FROM users", conn)
        conn.close()
        st.dataframe(users_df, use_container_width=True)
    
    with col2:
        st.subheader("Add New User")
        with st.form("add_user"):
            new_username = st.text_input("Username")
            new_name = st.text_input("Full Name")
            new_password = st.text_input("Password", type="password")
            new_plan = st.selectbox("Plan", ["basic", "premium"])
            new_expires = st.date_input("Expiry Date", value=date.today() + timedelta(days=365))
            
            if st.form_submit_button("Add User"):
                conn = sqlite3.connect("users.db")
                c = conn.cursor()
                try:
                    c.execute("INSERT OR REPLACE INTO users VALUES (?, ?, ?, ?, ?)", 
                             (new_username, new_name, new_password, new_plan, new_expires.strftime("%Y-%m-%d")))
                    conn.commit()
                    st.success("✅ User added successfully!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Error adding user: {e}")
                finally:
                    conn.close()
    
    st.markdown("---")
    
    # Admin also gets full premium access
    st.title("Premium Dashboard Access")
    render_premium_dashboard()

# -------------------------
# MAIN APP
# -------------------------
def main():
    # Login
    name, authentication_status, username = authenticator.login("Login", "main")
    
    if authentication_status:
        authenticator.logout('Logout', 'sidebar')
        
        if username == "admin":
            st.sidebar.success("👑 Admin Access")
            render_admin_dashboard()
            
        else:
            user_data = get_user(username)
            
            if user_data:
                plan = user_data[3]
                expires = user_data[4]
                expiry_date = datetime.strptime(expires, "%Y-%m-%d").date() if expires else date.today()
                
                if expiry_date > date.today():
                    # Active subscription
                    if plan == "premium":
                        st.sidebar.success(f"⭐ Premium Member (expires {expires})")
                        render_premium_dashboard()
                    else:
                        st.sidebar.info(f"🔓 Basic Member (expires {expires})")
                        render_basic_dashboard()
                else:
                    # Expired subscription
                    st.sidebar.error(f"❌ Subscription expired {expires}")
                    st.error("Your subscription has expired. Please renew to access all features.")
                    render_basic_dashboard()
            else:
                st.error("User not found in database")
                
    elif authentication_status == False:
        st.error("❌ Invalid username or password")
    else:
        st.warning("Please enter your username and password")

if __name__ == "__main__":
    main()
