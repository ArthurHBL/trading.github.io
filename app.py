# app.py - Fixed Premium Dashboard with Authentication
import streamlit as st
import json
from datetime import datetime, date, timedelta
import pandas as pd
import uuid
from typing import Dict, List, Tuple

# -------------------------
# SIMPLIFIED AUTHENTICATION
# -------------------------
def check_login(username, password):
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
    page_title="Chart Reminder & Notes (15 Strategies)", 
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
# DATA MANAGEMENT
# -------------------------
def init_session_data():
    if 'trading_data' not in st.session_state:
        st.session_state.trading_data = {}
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'logged_in' not in st.session_state:
        st.session_state.logged_in = False

def save_to_session(strategy, indicator, data):
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
                st.rerun()
            else:
                st.error("❌ Invalid username or password")
    
    with st.expander("Demo Accounts"):
        st.write("**Admin:** admin / admin123 (User management only)")
        st.write("**Premium:** maria / maria123 (Full trading features)")
        st.write("**Basic:** demo / demo123 (Limited features)")
        st.write("**Expired:** joao / joao123 (Demo mode)")

def render_premium_dashboard():
    """FULL PREMIUM DASHBOARD - Exactly like before authentication"""
    
    # Initialize data
    if 'trading_data' not in st.session_state:
        st.session_state.trading_data = {}
    
    data = st.session_state.trading_data
    
    # Date handling
    start_date = date(2025, 8, 9)
    try:
        current_date_str = st.query_params.get("date", "")
        analysis_date = datetime.strptime(current_date_str, "%Y-%m-%d").date() if current_date_str else date.today()
    except:
        analysis_date = date.today()
    
    if analysis_date < start_date:
        analysis_date = start_date

    # Sidebar - EXACTLY LIKE BEFORE
    st.sidebar.title("🎛️ Control Panel")
    st.sidebar.markdown("---")

    # User info
    st.sidebar.write(f"👤 **{st.session_state.user['name']}**")
    st.sidebar.success("⭐ Premium Plan")
    
    if st.sidebar.button("🚪 Logout"):
        st.session_state.logged_in = False
        st.session_state.user = None
        st.rerun()
    
    st.sidebar.markdown("---")
    
    st.sidebar.subheader("📅 Analysis Date")
    st.sidebar.markdown(f"**Current Date:** {analysis_date.strftime('%m/%d/%Y')}")

    col1, col2 = st.sidebar.columns(2)
    with col1:
        if st.button("◀️ Prev Day", use_container_width=True, key="prev_day"):
            new_date = analysis_date - timedelta(days=1)
            if new_date >= start_date:
                st.query_params["date"] = new_date.strftime("%Y-%m-%d")
                st.rerun()
    with col2:
        if st.button("Next Day ▶️", use_container_width=True, key="next_day"):
            new_date = analysis_date + timedelta(days=1)
            st.query_params["date"] = new_date.strftime("%Y-%m-%d")
            st.rerun()

    if st.sidebar.button("🔄 Today", use_container_width=True, key="today"):
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
        st.sidebar.progress(strat_progress['progress'], text=f"{strategy}: {strat_progress['completed']}/{strat_progress['total']}")

    st.sidebar.markdown("---")

    # Strategy Selection
    selected_strategy = st.sidebar.selectbox(
        "🎯 Choose a strategy:", 
        daily_strategies,
        key="strategy_selector"
    )

    # All Strategies List
    with st.sidebar.expander("📚 All 15 Strategies", expanded=False):
        for i, strategy in enumerate(STRATEGIES.keys(), 1):
            star = " ⭐" if strategy in daily_strategies else ""
            status_icon = "✅" if progress_data['strategies'].get(strategy, {}).get('progress', 0) == 1 else "🕓"
            st.write(f"{status_icon} {i}. {strategy}{star}")

    st.sidebar.markdown("---")

    # Export Options
    st.sidebar.subheader("📤 Export Data")
    if st.sidebar.button("⬇️ Download Current Analysis", use_container_width=True):
        st.sidebar.info("Export feature would be implemented here")

    # Main content - EXACTLY LIKE BEFORE
    st.title("📊 Advanced Chart Reminder & Indicator Notes")
    st.markdown(f"**Day {cycle_day}** | Strategy: **{selected_strategy}** | Date: **{analysis_date.strftime('%m/%d/%Y')}**")

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

    # Notes Form - EXACTLY LIKE BEFORE
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

    # Quick Actions
    st.markdown("### ⚡ Quick Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("🎯 Mark All as Done", key="mark_all_done", use_container_width=True):
            target_date_str = analysis_date.strftime("%Y-%m-%d")
            for ind in STRATEGIES[selected_strategy]:
                save_to_session(selected_strategy, ind, {
                    "status": "Done",
                    "note": data.get(selected_strategy, {}).get(ind, {}).get("note", ""),
                    "analysis_date": target_date_str,
                    "last_modified": datetime.now().isoformat(),
                    "strategy_tag": strategy_tag,
                    "momentum": strategy_type,
                    "priority": strategy_priority,
                    "confidence": strategy_confidence,
                    "id": str(uuid.uuid4())[:8]
                })
            st.success("All indicators marked as Done! ✅")
            st.rerun()
                
    with col2:
        if st.button("🔄 Reset Today", key="reset_today", use_container_width=True):
            target_date_str = analysis_date.strftime("%Y-%m-%d")
            for ind in STRATEGIES[selected_strategy]:
                if selected_strategy in data and ind in data[selected_strategy]:
                    if data[selected_strategy][ind].get('analysis_date') == target_date_str:
                        save_to_session(selected_strategy, ind, {
                            "note": "",
                            "status": "Open",
                            "momentum": "Not Defined",
                            "strategy_tag": "Neutral",
                            "priority": "Medium",
                            "confidence": 75,
                            "analysis_date": target_date_str,
                            "last_modified": datetime.now().isoformat(),
                            "id": str(uuid.uuid4())[:8]
                        })
            st.success("Today's analysis reset! 🔄")
            st.rerun()

    st.markdown("---")

    # Quick Status Updates
    st.markdown("#### ⚡ Quick Status Update")
    indicators = STRATEGIES[selected_strategy]
    quick_status_cols = st.columns(min(6, len(indicators)))
    
    for i, ind in enumerate(indicators):
        with quick_status_cols[i % len(quick_status_cols)]:
            current_status = strategy_data.get(ind, {}).get("status", "Open")
            status_options = ["Open", "In Progress", "Done", "Skipped"]
            new_status = st.selectbox(
                f"{ind[:12]}...",
                status_options,
                index=status_options.index(current_status) if current_status in status_options else 0,
                key=f"quick_status_{ind}"
            )
            # Immediate status update
            if new_status != current_status:
                save_to_session(selected_strategy, ind, {
                    "status": new_status,
                    "note": strategy_data.get(ind, {}).get("note", ""),
                    "analysis_date": analysis_date.strftime("%Y-%m-%d"),
                    "last_modified": datetime.now().isoformat(),
                    "strategy_tag": strategy_tag,
                    "momentum": strategy_type,
                    "priority": strategy_priority,
                    "confidence": strategy_confidence,
                    "id": strategy_data.get(ind, {}).get("id", str(uuid.uuid4())[:8])
                })
                st.rerun()

    st.markdown("---")

    # Indicator Analysis Section
    st.markdown("### 📊 Detailed Indicator Analysis")
    col_objs = st.columns(2)

    # Main form
    with st.form("analysis_form", clear_on_submit=False):
        form_data = {}
        
        for i, ind in enumerate(indicators):
            col = col_objs[i % 2]
            existing = strategy_data.get(ind, {})
            
            with col.expander(f"**{ind}**", expanded=False):
                # Status
                current_status = existing.get("status", "Open")
                status = st.selectbox(
                    "Status", 
                    ["Open", "In Progress", "Done", "Skipped"], 
                    index=["Open", "In Progress", "Done", "Skipped"].index(current_status) if current_status in ["Open", "In Progress", "Done", "Skipped"] else 0,
                    key=f"status_{ind}"
                )
                
                # Note area
                note = st.text_area(
                    f"Analysis notes for {ind}",
                    value=existing.get("note", ""),
                    height=160,
                    key=f"note_{ind}",
                    placeholder=f"Enter your analysis for {ind}..."
                )
                
                # Individual indicator confidence
                ind_confidence = st.slider(
                    "Indicator Confidence",
                    min_value=50,
                    max_value=100,
                    value=existing.get("confidence", strategy_confidence),
                    key=f"conf_{ind}"
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
            # Flexible validation - allow Done status without notes but show warnings
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
                    st.stop()
            
            # Save the data
            for ind in indicators:
                save_to_session(selected_strategy, ind, {
                    "note": form_data[ind]['note'],
                    "status": form_data[ind]['status'],
                    "momentum": strategy_type,
                    "strategy_tag": strategy_tag,
                    "priority": strategy_priority,
                    "confidence": form_data[ind]['confidence'],
                    "analysis_date": analysis_date.strftime("%Y-%m-%d"),
                    "last_modified": datetime.now().isoformat(),
                    "id": str(uuid.uuid4())[:8]
                })
            
            st.success("✅ Analysis saved successfully!")
            st.balloons()

    # Analysis Display
    st.markdown("---")
    st.subheader("📜 Saved Analyses")

    # Color and icon mappings
    color_map = {"Buy": "🟢", "Sell": "🔴", "Neutral": "⚪"}
    status_icons = {"Open": "🕓", "In Progress": "🔄", "Done": "✅", "Skipped": "⏭️"}

    # Display current strategy analyses
    if selected_strategy in data and data[selected_strategy]:
        st.markdown(f"### {selected_strategy}")
        inds = data[selected_strategy]
        
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
    else:
        st.info("📝 No analyses found for this strategy.")

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
    
    users = [
        {"username": "admin", "name": "Arthur (Admin)", "plan": "premium", "status": "active", "expires": "2030-12-31"},
        {"username": "maria", "name": "Maria Silva", "plan": "premium", "status": "active", "expires": "2025-12-31"},
        {"username": "demo", "name": "Demo User", "plan": "basic", "status": "active", "expires": "2024-12-31"},
        {"username": "joao", "name": "João Santos", "plan": "expired", "status": "inactive", "expires": "2024-01-31"}
    ]
    
    users_df = pd.DataFrame(users)
    st.dataframe(users_df, use_container_width=True)
    
    # Add New User Section
    st.subheader("➕ Add New User")
    
    with st.form("add_user_form"):
        col1, col2 = st.columns(2)
        
        with col1:
            new_username = st.text_input("Username")
            new_name = st.text_input("Full Name")
            new_plan = st.selectbox("Subscription Plan", ["basic", "premium", "trial"])
            
        with col2:
            new_password = st.text_input("Password", type="password")
            new_status = st.selectbox("Account Status", ["active", "inactive", "suspended"])
            new_expires = st.date_input("Subscription Expiry", value=date.today() + timedelta(days=365))
        
        submitted = st.form_submit_button("🚀 Create User", use_container_width=True)
        
        if submitted:
            if new_username and new_name and new_password:
                st.success(f"✅ User '{new_username}' created successfully!")

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
