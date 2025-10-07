# app.py - Streamlit Cloud Compatible Version (Fixed Admin)
import streamlit as st
import json
from datetime import datetime, date, timedelta
import pandas as pd
import uuid
from typing import Dict, List, Tuple

# -------------------------
# SIMPLIFIED AUTHENTICATION (No Database)
# -------------------------
def check_login(username, password):
    """Simple login without database"""
    users = {
        "admin": {"password": "admin123", "name": "Arthur (Admin)", "plan": "premium", "expires": "2030-12-31"},
        "maria": {"password": "maria123", "name": "Maria Silva", "plan": "premium", "expires": "2025-12-31"},
        "demo": {"password": "demo123", "name": "Demo User", "plan": "basic", "expires": "2024-12-31"},
        "joao": {"password": "joao123", "name": "João Santos", "plan": "expired", "expires": "2024-01-31"}
    }
    
    if username in users and users[username]["password"] == password:
        return users[username]
    return None

# -------------------------
# APP CONFIGURATION
# -------------------------
st.set_page_config(
    page_title="Trading Analysis Dashboard", 
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# -------------------------
# STRATEGIES DEFINITION
# -------------------------
STRATEGIES = {
    "Premium Stoch": ["Overview","VWAP AA","VWAP","Volume Delta","Stoch RSI","SMI","RSI(SMI)","RAINBOW_RSI"],
    "LS Copy": ["Overview","NVT","RoC Bands","RoC","BBWP","PSO","RSI","RAINBOW_RSI"],
    "PositionFlow": ["Overview","VWAP","Chart VWAP","MACZ VWAP","MFI","Fisher Transform","RAINBOW_RSI"],
    "RenkoVol": ["Overview","GR-MMAs","Pi Cycle","Keltner & Bollinger","RSI Ichimoku","RWI","BBWP","Trend Master","VWAP-RSI","ASO"],
    "10h WWV Chart": ["Overview","BTC Log Regression","GR-MMAs","PiCycle","%R MA","RSI","Chaikin Oscillator","Ultimate HODL Wave","PVT","BBWP"],
}

# -------------------------
# DATA MANAGEMENT (Using Session State)
# -------------------------
def init_session_data():
    """Initialize session state data"""
    if 'trading_data' not in st.session_state:
        st.session_state.trading_data = {}
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

def save_to_session(strategy, indicator, data):
    """Save data to session state"""
    if strategy not in st.session_state.trading_data:
        st.session_state.trading_data[strategy] = {}
    st.session_state.trading_data[strategy][indicator] = data

def get_daily_strategies(analysis_date: date) -> Tuple[List[str], int]:
    strategy_list = list(STRATEGIES.keys())
    start_date = date(2025, 8, 9)
    days_since_start = (analysis_date - start_date).days
    cycle_day = days_since_start % 5
    start_index = cycle_day * 3
    end_index = start_index + 3
    daily_strategies = strategy_list[start_index:end_index]
    return daily_strategies, cycle_day + 1

def calculate_progress(daily_strategies: List[str], analysis_date: date) -> Dict:
    target_date_str = analysis_date.strftime("%Y-%m-%d")
    
    total_indicators = sum(len(STRATEGIES.get(s, [])) for s in daily_strategies)
    completed_indicators = 0
    strategy_progress = {}
    
    for strategy in daily_strategies:
        strategy_inds = STRATEGIES.get(strategy, [])
        completed = 0
        for ind in strategy_inds:
            indicator_data = st.session_state.trading_data.get(strategy, {}).get(ind, {})
            if (indicator_data.get('analysis_date') == target_date_str and
                indicator_data.get('status') == 'Done'):
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
# DASHBOARD COMPONENTS
# -------------------------
def render_login():
    """Render login form"""
    st.title("🔐 Trading Analysis Dashboard")
    st.markdown("---")
    
    with st.form("login_form"):
        username = st.text_input("Username")
        password = st.text_input("Password", type="password")
        submitted = st.form_submit_button("Login")
        
        if submitted:
            user_data = check_login(username, password)
            if user_data:
                st.session_state.user = user_data
                st.session_state.logged_in = True
                st.session_state.trading_data = {}  # Reset data on login
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
    
    # Demo accounts info
    with st.expander("Demo Accounts"):
        st.write("**Admin:** admin / admin123 (User management only)")
        st.write("**Premium:** maria / maria123 (All trading features)")
        st.write("**Basic:** demo / demo123 (Limited features)")
        st.write("**Expired:** joao / joao123 (Demo mode)")

def render_premium_dashboard():
    """Full featured dashboard for premium users"""
    
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
    st.sidebar.write(f"Welcome, **{st.session_state.user['name']}**")
    st.sidebar.success(f"⭐ {st.session_state.user['plan'].title()} Plan")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()
    
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("📅 Analysis Date")
    st.sidebar.write(f"**{analysis_date.strftime('%m/%d/%Y')}**")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("◀️ Prev Day"):
            new_date = analysis_date - timedelta(days=1)
            if new_date >= start_date:
                st.query_params["date"] = new_date.strftime("%Y-%m-%d")
                st.rerun()
    with col2:
        if st.button("Next Day ▶️"):
            new_date = analysis_date + timedelta(days=1)
            st.query_params["date"] = new_date.strftime("%Y-%m-%d")
            st.rerun()

    if st.sidebar.button("🔄 Today"):
        st.query_params["date"] = date.today().strftime("%Y-%m-%d")
        st.rerun()

    st.sidebar.markdown("---")

    # Daily Strategies
    daily_strategies, cycle_day = get_daily_strategies(analysis_date)
    progress_data = calculate_progress(daily_strategies, analysis_date)

    st.sidebar.subheader("📋 Today's Focus")
    st.sidebar.info(f"**Day {cycle_day} of 5-day cycle**")

    st.sidebar.metric(
        "Overall Progress", 
        f"{progress_data['completed_indicators']}/{progress_data['total_indicators']}",
        f"{progress_data['overall']*100:.1f}%"
    )

    for strategy in daily_strategies:
        strat_progress = progress_data['strategies'][strategy]
        st.sidebar.progress(strat_progress['progress'], text=f"{strategy}")

    st.sidebar.markdown("---")

    # Strategy Selection
    selected_strategy = st.sidebar.selectbox("🎯 Choose Strategy", daily_strategies)

    # Main content
    st.title("🚀 Premium Trading Dashboard")
    st.write(f"**Day {cycle_day}** | **{selected_strategy}** | {analysis_date.strftime('%m/%d/%Y')}")
    
    # Progress indicators
    st.subheader("🎯 Today's Progress")
    progress_cols = st.columns(3)
    for i, strat in enumerate(daily_strategies):
        with progress_cols[i]:
            strat_data = progress_data['strategies'][strat]
            progress_pct = strat_data['progress']
            
            if progress_pct == 1:
                st.success(f"✅ **{strat}**")
            elif progress_pct > 0:
                st.info(f"🔄 **{strat}**")
            else:
                st.warning(f"🕓 **{strat}**")
            
            st.progress(progress_pct)
            st.caption(f"{strat_data['completed']}/{strat_data['total']} indicators")

    st.markdown("---")

    # Analysis Form
    st.subheader(f"✏️ Analyze {selected_strategy}")
    
    # Strategy-level settings
    col1, col2, col3 = st.columns(3)
    with col1:
        strategy_tag = st.selectbox("🏷️ Overall Tag", ["Neutral", "Buy", "Sell"])
    with col2:
        strategy_priority = st.selectbox("🎯 Priority", ["Low", "Medium", "High"])
    with col3:
        strategy_confidence = st.slider("💪 Confidence", 50, 100, 75)

    st.markdown("---")

    # Quick Actions
    st.subheader("⚡ Quick Actions")
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🎯 Mark All as Done", use_container_width=True):
            target_date_str = analysis_date.strftime("%Y-%m-%d")
            for ind in STRATEGIES[selected_strategy]:
                save_to_session(selected_strategy, ind, {
                    "status": "Done",
                    "note": st.session_state.trading_data.get(selected_strategy, {}).get(ind, {}).get("note", ""),
                    "analysis_date": target_date_str,
                    "strategy_tag": strategy_tag,
                    "priority": strategy_priority,
                    "confidence": strategy_confidence,
                    "last_modified": datetime.now().isoformat()
                })
            st.success("All indicators marked as Done! ✅")
            st.rerun()
    
    with col2:
        if st.button("🔄 Reset Strategy", use_container_width=True):
            for ind in STRATEGIES[selected_strategy]:
                if selected_strategy in st.session_state.trading_data and ind in st.session_state.trading_data[selected_strategy]:
                    del st.session_state.trading_data[selected_strategy][ind]
            st.success("Strategy analysis reset! 🔄")
            st.rerun()

    st.markdown("---")

    # Detailed Analysis Form
    st.subheader("📊 Indicator Analysis")
    indicators = STRATEGIES[selected_strategy]
    
    with st.form("analysis_form"):
        for i, ind in enumerate(indicators):
            existing_data = st.session_state.trading_data.get(selected_strategy, {}).get(ind, {})
            
            with st.expander(f"**{ind}**", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    status = st.selectbox("Status", ["Open", "In Progress", "Done", "Skipped"], 
                                        index=["Open", "In Progress", "Done", "Skipped"].index(existing_data.get("status", "Open")),
                                        key=f"status_{ind}")
                    confidence = st.slider("Confidence", 50, 100, existing_data.get("confidence", strategy_confidence), key=f"conf_{ind}")
                
                with col2:
                    note = st.text_area("Analysis Notes", value=existing_data.get("note", ""), height=100, key=f"note_{ind}")
                
                # Save immediately or show last modified
                if existing_data.get("last_modified"):
                    st.caption(f"Last updated: {existing_data['last_modified'][:16]}")
        
        if st.form_submit_button("💾 Save All Analysis", use_container_width=True):
            target_date_str = analysis_date.strftime("%Y-%m-%d")
            for ind in indicators:
                save_to_session(selected_strategy, ind, {
                    "note": st.session_state[f"note_{ind}"],
                    "status": st.session_state[f"status_{ind}"],
                    "confidence": st.session_state[f"conf_{ind}"],
                    "strategy_tag": strategy_tag,
                    "priority": strategy_priority,
                    "analysis_date": target_date_str,
                    "last_modified": datetime.now().isoformat()
                })
            st.success("✅ Analysis saved successfully!")
            st.balloons()

def render_basic_dashboard():
    """Limited dashboard for basic users"""
    st.sidebar.title("🔓 Basic Access")
    st.sidebar.write(f"Welcome, **{st.session_state.user['name']}**")
    st.sidebar.warning("Basic Plan - Limited Features")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    st.title("📊 Trading Analysis - Basic Plan")
    st.warning("🔒 You are on the Basic plan. Upgrade to Premium for all strategies and advanced features.")
    
    # Limited to first 2 strategies only
    available_strategies = list(STRATEGIES.keys())[:2]
    selected_strategy = st.selectbox("Select Strategy", available_strategies)
    
    # Simple analysis form
    with st.form("basic_analysis"):
        st.subheader(f"Basic Analysis - {selected_strategy}")
        
        # Limited to first 3 indicators per strategy
        for indicator in STRATEGIES[selected_strategy][:3]:
            st.text_area(f"Notes for {indicator}", key=f"basic_{indicator}", height=80,
                        placeholder="Enter your analysis notes...")
        
        if st.form_submit_button("💾 Save Notes"):
            st.success("Notes saved! Upgrade to Premium for full analysis features.")
    
    st.markdown("---")
    st.info("""
    **⭐ Premium features you're missing:**
    - All 15 trading strategies
    - Progress tracking & analytics
    - Confidence levels & priority settings
    - Strategy tagging (Buy/Sell/Neutral)
    - Historical analysis
    - Export functionality
    - Advanced charting
    """)

def render_admin_dashboard():
    """Admin dashboard - ONLY user management"""
    st.sidebar.title("👑 Admin Panel")
    st.sidebar.write(f"Welcome, **{st.session_state.user['name']}**")
    st.sidebar.success("Full Administrative Access")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()

    st.title("👑 Admin Dashboard")
    st.info("User Management System - Administrative Purposes Only")
    
    # User management section
    st.subheader("📋 User Accounts")
    
    # Current users table
    users = [
        {"username": "admin", "name": "Arthur (Admin)", "plan": "premium", "status": "active", "expires": "2030-12-31"},
        {"username": "maria", "name": "Maria Silva", "plan": "premium", "status": "active", "expires": "2025-12-31"},
        {"username": "demo", "name": "Demo User", "plan": "basic", "status": "active", "expires": "2024-12-31"},
        {"username": "joao", "name": "João Santos", "plan": "expired", "status": "inactive", "expires": "2024-01-31"}
    ]
    
    users_df = pd.DataFrame(users)
    st.dataframe(users_df, use_container_width=True)
    
    # Statistics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", len(users))
    with col2:
        st.metric("Premium Users", len([u for u in users if u['plan'] == 'premium']))
    with col3:
        st.metric("Basic Users", len([u for u in users if u['plan'] == 'basic']))
    with col4:
        st.metric("Inactive Users", len([u for u in users if u['status'] == 'inactive']))
    
    st.markdown("---")
    
    # Add New User Section
    st.subheader("➕ Add New User")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("Username", placeholder="Enter unique username")
            new_name = st.text_input("Full Name", placeholder="Enter user's full name")
            new_plan = st.selectbox("Subscription Plan", ["basic", "premium", "trial"])
            
        with col2:
            new_password = st.text_input("Password", type="password", placeholder="Set user password")
            new_status = st.selectbox("Account Status", ["active", "inactive", "suspended"])
            new_expires = st.date_input("Subscription Expiry", value=date.today() + timedelta(days=365))
        
        st.markdown("---")
        col1, col2 = st.columns([3, 1])
        with col2:
            submitted = st.form_submit_button("🚀 Create User", use_container_width=True)
        
        if submitted:
            if new_username and new_name and new_password:
                # In a real app, you'd save to database here
                st.success(f"✅ User '{new_username}' created successfully!")
                st.info(f"**Username:** {new_username} | **Plan:** {new_plan} | **Status:** {new_status} | **Expires:** {new_expires}")
            else:
                st.error("❌ Please fill in all required fields")
    
    st.markdown("---")
    
    # User Actions Section
    st.subheader("⚡ User Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh User Data", use_container_width=True):
            st.rerun()
    
    with col2:
        if st.button("📊 Export User Report", use_container_width=True):
            st.success("User report exported successfully! (Simulated)")
    
    with col3:
        if st.button("🛑 Bulk Deactivate", use_container_width=True):
            st.warning("Bulk deactivation feature would be implemented here")

# -------------------------
# MAIN APP
# -------------------------
def main():
    init_session_data()
    
    if not st.session_state.logged_in:
        render_login()
    else:
        user_plan = st.session_state.user['plan']
        
        if st.session_state.user['name'] == "Arthur (Admin)":
            render_admin_dashboard()
        elif user_plan == "premium":
            render_premium_dashboard()
        else:
            # Check if subscription is expired
            expires = st.session_state.user['expires']
            expiry_date = datetime.strptime(expires, "%Y-%m-%d").date()
            if expiry_date < date.today():
                st.sidebar.error("❌ Subscription Expired")
                st.error("Your subscription has expired. Please renew to access premium features.")
                render_basic_dashboard()
            else:
                render_basic_dashboard()

if __name__ == "__main__":
    main()
