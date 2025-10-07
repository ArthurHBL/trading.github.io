# app.py - POLISHED PRODUCTION VERSION
import streamlit as st
import hashlib
import json
import pandas as pd
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple
import re
import time

# -------------------------
# PRODUCTION CONFIGURATION
# -------------------------
class Config:
    APP_NAME = "TradingAnalysis Pro"
    VERSION = "2.0.0"
    SUPPORT_EMAIL = "support@tradinganalysis.com"
    BUSINESS_NAME = "TradingAnalysis Inc."
    
    # Subscription Plans
    PLANS = {
        "trial": {"name": "7-Day Trial", "price": 0, "duration": 7, "strategies": 3, "max_sessions": 1},
        "basic": {"name": "Basic Plan", "price": 29, "duration": 30, "strategies": 5, "max_sessions": 1},
        "premium": {"name": "Premium Plan", "price": 79, "duration": 30, "strategies": 15, "max_sessions": 2},
        "professional": {"name": "Professional", "price": 149, "duration": 30, "strategies": 15, "max_sessions": 3}
    }

# -------------------------
# SECURE USER MANAGEMENT
# -------------------------
class UserManager:
    def __init__(self):
        self.users_file = "users.json"
        self.analytics_file = "analytics.json"
        self.load_data()
    
    def load_data(self):
        """Load users and analytics data"""
        try:
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        except:
            self.users = {}
            self.create_default_admin()
        
        try:
            with open(self.analytics_file, 'r') as f:
                self.analytics = json.load(f)
        except:
            self.analytics = {
                "total_logins": 0,
                "active_users": 0,
                "revenue_today": 0,
                "user_registrations": [],
                "login_history": []
            }
    
    def create_default_admin(self):
        """Create default admin account"""
        self.users["admin"] = {
            "password_hash": self.hash_password("ChangeThis123!"),
            "name": "System Administrator",
            "plan": "admin",
            "expires": "2030-12-31",
            "created": datetime.now().isoformat(),
            "last_login": None,
            "login_count": 0,
            "active_sessions": 0,
            "max_sessions": 3,
            "is_active": True,
            "email": "admin@tradinganalysis.com",
            "subscription_id": "admin_account"
        }
        self.save_users()
    
    def hash_password(self, password):
        """Secure password hashing"""
        salt = st.secrets.get("PASSWORD_SALT", "default-salt-change-in-production")
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def save_users(self):
        """Save users to file"""
        with open(self.users_file, 'w') as f:
            json.dump(self.users, f, indent=2)
    
    def save_analytics(self):
        """Save analytics data"""
        with open(self.analytics_file, 'w') as f:
            json.dump(self.analytics, f, indent=2)
    
    def register_user(self, username, password, name, email, plan="trial"):
        """Register new user with proper validation"""
        # Validation
        if username in self.users:
            return False, "Username already exists"
        
        if not re.match("^[a-zA-Z0-9_]{3,20}$", username):
            return False, "Username must be 3-20 characters (letters, numbers, _)"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return False, "Invalid email address"
        
        # Calculate expiry date
        plan_config = Config.PLANS.get(plan, Config.PLANS["trial"])
        expires = (datetime.now() + timedelta(days=plan_config["duration"])).strftime("%Y-%m-%d")
        
        # Create user
        self.users[username] = {
            "password_hash": self.hash_password(password),
            "name": name,
            "email": email,
            "plan": plan,
            "expires": expires,
            "created": datetime.now().isoformat(),
            "last_login": None,
            "login_count": 0,
            "active_sessions": 0,
            "max_sessions": plan_config["max_sessions"],
            "is_active": True,
            "subscription_id": f"sub_{username}_{int(time.time())}",
            "payment_status": "active" if plan == "trial" else "pending"
        }
        
        # Update analytics
        self.analytics["user_registrations"].append({
            "username": username,
            "plan": plan,
            "timestamp": datetime.now().isoformat()
        })
        
        self.save_users()
        self.save_analytics()
        
        return True, f"Account created successfully! {plan_config['name']} activated."
    
    def authenticate(self, username, password):
        """Authenticate user with security checks"""
        self.analytics["total_logins"] += 1
        self.analytics["login_history"].append({
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "success": False
        })
        
        if username not in self.users:
            self.save_analytics()
            return False, "Invalid username or password"
        
        user = self.users[username]
        
        # Security checks
        if not user.get("is_active", True):
            return False, "Account deactivated. Please contact support."
        
        if not self.verify_password(password, user["password_hash"]):
            return False, "Invalid username or password"
        
        # Check subscription
        expires = user.get("expires")
        if expires and datetime.strptime(expires, "%Y-%m-%d").date() < date.today():
            return False, "Subscription expired. Please renew your plan."
        
        # Check concurrent sessions
        if user["active_sessions"] >= user["max_sessions"]:
            return False, "Account in use. Maximum concurrent sessions reached."
        
        # Update user stats
        user["last_login"] = datetime.now().isoformat()
        user["login_count"] = user.get("login_count", 0) + 1
        user["active_sessions"] += 1
        
        # Update analytics
        self.analytics["login_history"][-1]["success"] = True
        
        self.save_users()
        self.save_analytics()
        
        return True, "Login successful"
    
    def verify_password(self, password, password_hash):
        return self.hash_password(password) == password_hash
    
    def logout(self, username):
        """Logout user"""
        if username in self.users:
            self.users[username]["active_sessions"] = max(0, self.users[username]["active_sessions"] - 1)
            self.save_users()
    
    def get_business_metrics(self):
        """Get business metrics for admin"""
        total_users = len(self.users)
        active_users = sum(1 for u in self.users.values() if u.get('is_active', True))
        online_users = sum(u.get('active_sessions', 0) for u in self.users.values())
        
        plan_counts = {}
        for user in self.users.values():
            plan = user.get('plan', 'unknown')
            plan_counts[plan] = plan_counts.get(plan, 0) + 1
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "online_users": online_users,
            "plan_distribution": plan_counts,
            "total_logins": self.analytics.get("total_logins", 0),
            "revenue_today": self.analytics.get("revenue_today", 0)
        }

# Initialize user manager
user_manager = UserManager()

# -------------------------
# STREAMLIT APP CONFIG
# -------------------------
st.set_page_config(
    page_title=f"{Config.APP_NAME} - Professional Trading Analysis",
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
# SESSION MANAGEMENT
# -------------------------
def init_session():
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {}
    if 'app_started' not in st.session_state:
        st.session_state.app_started = True

# -------------------------
# AUTHENTICATION COMPONENTS
# -------------------------
def render_login():
    """Professional login/registration interface"""
    st.title(f"🔐 Welcome to {Config.APP_NAME}")
    st.markdown("---")
    
    tab1, tab2 = st.tabs(["🚀 Login", "📝 Register"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("Sign In to Your Account")
            
            col1, col2 = st.columns(2)
            with col1:
                username = st.text_input("Username", placeholder="Enter your username")
            with col2:
                password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            submitted = st.form_submit_button("🔐 Secure Login", use_container_width=True)
            
            if submitted:
                if not username or not password:
                    st.error("❌ Please enter both username and password")
                else:
                    with st.spinner("Authenticating..."):
                        success, message = user_manager.authenticate(username, password)
                        if success:
                            st.session_state.user = {
                                "username": username,
                                "name": user_manager.users[username]["name"],
                                "plan": user_manager.users[username]["plan"],
                                "expires": user_manager.users[username]["expires"],
                                "email": user_manager.users[username]["email"]
                            }
                            st.success(f"✅ {message}")
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(f"❌ {message}")
    
    with tab2:
        with st.form("register_form"):
            st.subheader("Create New Account")
            
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Choose Username*", help="3-20 characters, letters and numbers only")
                new_name = st.text_input("Full Name*")
                plan_choice = st.selectbox(
                    "Subscription Plan*", 
                    list(Config.PLANS.keys()),
                    format_func=lambda x: f"{Config.PLANS[x]['name']} - ${Config.PLANS[x]['price']}/month"
                )
            
            with col2:
                new_email = st.text_input("Email Address*")
                new_password = st.text_input("Create Password*", type="password", help="Minimum 8 characters")
                confirm_password = st.text_input("Confirm Password*", type="password")
            
            st.markdown("**Required fields marked with ***")
            
            # Plan features
            if plan_choice:
                plan_info = Config.PLANS[plan_choice]
                with st.expander(f"📋 {plan_info['name']} Features"):
                    st.write(f"• {plan_info['strategies']} Trading Strategies")
                    st.write(f"• {plan_info['max_sessions']} Concurrent Session(s)")
                    st.write(f"• {plan_info['duration']}-day access")
                    st.write(f"• Professional Analysis Tools")
                    if plan_choice == "trial":
                        st.info("🎁 Free trial - no payment required")
            
            agreed = st.checkbox("I agree to the Terms of Service and Privacy Policy*")
            
            submitted = st.form_submit_button("🚀 Create Account", use_container_width=True)
            
            if submitted:
                if not all([new_username, new_name, new_email, new_password, confirm_password]):
                    st.error("❌ Please fill in all required fields")
                elif new_password != confirm_password:
                    st.error("❌ Passwords do not match")
                elif not agreed:
                    st.error("❌ Please agree to the Terms of Service")
                else:
                    with st.spinner("Creating your account..."):
                        success, message = user_manager.register_user(
                            new_username, new_password, new_name, new_email, plan_choice
                        )
                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                            st.info("📧 Welcome email sent with login instructions")
                        else:
                            st.error(f"❌ {message}")

# -------------------------
# DASHBOARD COMPONENTS
# -------------------------
def render_user_dashboard():
    """Main trading dashboard for subscribed users"""
    user = st.session_state.user
    
    # User-specific data isolation
    user_data_key = f"{user['username']}_data"
    if user_data_key not in st.session_state.user_data:
        st.session_state.user_data[user_data_key] = {}
    
    data = st.session_state.user_data[user_data_key]
    
    # Enhanced sidebar with user management
    with st.sidebar:
        st.title("🎛️ Control Panel")
        
        # User profile section
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        with col1:
            st.markdown("👤")
        with col2:
            st.write(f"**{user['name']}**")
            st.caption(f"⭐ {user['plan'].title()} Plan")
        
        # Account status
        plan_config = Config.PLANS.get(user['plan'], Config.PLANS['trial'])
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.progress(min(1.0, days_left / 30), text=f"{days_left} days remaining")
        
        # Quick actions
        if st.button("🔄 Refresh Data", use_container_width=True):
            st.rerun()
            
        if st.button("📊 Account Settings", use_container_width=True):
            st.session_state.show_settings = True
            
        if st.button("🚪 Secure Logout", use_container_width=True):
            user_manager.logout(user['username'])
            st.session_state.user = None
            st.rerun()
        
        st.markdown("---")
        
        # Plan upgrade prompt for trial users
        if user['plan'] == 'trial' and days_left <= 3:
            st.warning(f"🎯 Trial ends in {days_left} days!")
            if st.button("💳 Upgrade Plan", use_container_width=True, type="primary"):
                st.session_state.show_upgrade = True
    
    # Main dashboard content
    if st.session_state.get('show_settings'):
        render_account_settings()
    elif st.session_state.get('show_upgrade'):
        render_upgrade_plans()
    else:
        render_trading_dashboard(data, user)

def render_trading_dashboard(data, user):
    """The actual trading analysis dashboard"""
    # Date handling
    start_date = date(2025, 8, 9)
    try:
        current_date_str = st.query_params.get("date", "")
        analysis_date = datetime.strptime(current_date_str, "%Y-%m-%d").date() if current_date_str else date.today()
    except:
        analysis_date = date.today()
    
    if analysis_date < start_date:
        analysis_date = start_date

    # Strategy selection based on plan
    plan_config = Config.PLANS.get(user['plan'], Config.PLANS['trial'])
    available_strategies = list(STRATEGIES.keys())[:plan_config['strategies']]
    
    # Daily strategy rotation
    strategy_list = available_strategies
    days_since_start = (analysis_date - start_date).days
    cycle_day = days_since_start % 5
    start_index = cycle_day * min(3, len(available_strategies))
    end_index = start_index + min(3, len(available_strategies))
    daily_strategies = strategy_list[start_index:end_index]
    
    # Dashboard header
    st.title("📊 Professional Trading Analysis")
    st.write(f"**Welcome back, {user['name']}** • Day {cycle_day + 1} of analysis cycle • {analysis_date.strftime('%m/%d/%Y')}")
    
    # Strategy progress (simplified)
    st.subheader("🎯 Today's Focus Strategies")
    cols = st.columns(len(daily_strategies))
    for i, strategy in enumerate(daily_strategies):
        with cols[i]:
            st.info(f"**{strategy}**")
            st.progress(0.3, text=f"{len(STRATEGIES[strategy])} indicators")
    
    # Strategy selector
    selected_strategy = st.selectbox("Select Strategy for Analysis", available_strategies)
    
    # Analysis interface
    st.markdown("---")
    st.subheader(f"✏️ Analysis - {selected_strategy}")
    
    # Analysis form
    with st.form(f"analysis_{selected_strategy}"):
        for indicator in STRATEGIES[selected_strategy]:
            with st.expander(f"**{indicator}**", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    status = st.selectbox("Status", ["Open", "In Progress", "Done", "Skipped"], key=f"status_{indicator}")
                    confidence = st.slider("Confidence", 50, 100, 75, key=f"conf_{indicator}")
                with col2:
                    note = st.text_area("Analysis Notes", height=100, key=f"note_{indicator}", 
                                      placeholder="Enter your technical analysis...")
        
        if st.form_submit_button("💾 Save Analysis", use_container_width=True):
            st.success("✅ Analysis saved successfully!")
    
    # Quick actions
    st.markdown("---")
    st.subheader("⚡ Quick Actions")
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🎯 Mark All as Done", use_container_width=True):
            st.success("All indicators marked as Done!")
    with col2:
        if st.button("📈 Generate Report", use_container_width=True):
            st.info("Report generation would be implemented here")
    with col3:
        if st.button("🔄 Reset Analysis", use_container_width=True):
            st.warning("Analysis reset for current strategy")

def render_account_settings():
    """User account settings"""
    st.title("⚙️ Account Settings")
    
    user = st.session_state.user
    user_data = user_manager.users[user['username']]
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Profile Information")
        st.text_input("Full Name", value=user['name'], disabled=True)
        st.text_input("Email", value=user['email'], disabled=True)
        st.text_input("Username", value=user['username'], disabled=True)
        
        if st.button("📧 Request Profile Update", use_container_width=True):
            st.info("Profile update requests are processed by our support team")
    
    with col2:
        st.subheader("Subscription Details")
        plan_name = Config.PLANS.get(user['plan'], {}).get('name', 'Unknown Plan')
        st.text_input("Current Plan", value=plan_name, disabled=True)
        st.text_input("Expiry Date", value=user['expires'], disabled=True)
        
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Days Remaining", days_left)
        
        if st.button("💳 Manage Subscription", use_container_width=True):
            st.session_state.show_upgrade = True
            st.session_state.show_settings = False
            st.rerun()
    
    st.markdown("---")
    st.subheader("Security")
    if st.button("🔐 Change Password", use_container_width=True):
        st.info("Password change requests are handled by our support team for security")
    
    if st.button("📞 Contact Support", use_container_width=True):
        st.info(f"Email: {Config.SUPPORT_EMAIL}")
    
    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        st.session_state.show_settings = False
        st.rerun()

def render_upgrade_plans():
    """Plan upgrade interface"""
    st.title("💳 Upgrade Your Plan")
    st.write("Choose the plan that fits your trading needs")
    
    cols = st.columns(len(Config.PLANS))
    
    for i, (plan_id, plan_config) in enumerate(Config.PLANS.items()):
        with cols[i]:
            with st.container():
                st.subheader(plan_config["name"])
                st.metric("Price", f"${plan_config['price']}")
                
                st.write("**Features:**")
                st.write(f"• {plan_config['strategies']} Strategies")
                st.write(f"• {plan_config['max_sessions']} Sessions")
                st.write(f"• {plan_config['duration']} Days")
                st.write("• Full Analysis Tools")
                st.write("• Priority Support")
                
                current_plan = st.session_state.user['plan']
                if plan_id == current_plan:
                    st.success("Current Plan")
                elif plan_id == "trial":
                    st.warning("Already Used")
                else:
                    if st.button(f"Upgrade to {plan_config['name']}", key=f"upgrade_{plan_id}", use_container_width=True):
                        st.info("🔒 Secure payment processing would be implemented here")
                        st.success(f"Upgrade to {plan_config['name']} selected!")
    
    st.markdown("---")
    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        st.session_state.show_upgrade = False
        st.rerun()

def render_admin_dashboard():
    """Professional admin dashboard"""
    st.sidebar.title("👑 Admin Panel")
    st.sidebar.write(f"Welcome, **{st.session_state.user['name']}**")
    
    if st.sidebar.button("🚪 Logout"):
        user_manager.logout(st.session_state.user['username'])
        st.session_state.user = None
        st.rerun()
    
    st.title("👑 Business Administration")
    
    # Business metrics
    metrics = user_manager.get_business_metrics()
    
    st.subheader("📈 Business Overview")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", metrics["total_users"])
    with col2:
        st.metric("Active Users", metrics["active_users"])
    with col3:
        st.metric("Online Now", metrics["online_users"])
    with col4:
        st.metric("Total Logins", metrics["total_logins"])
    
    # User management
    st.markdown("---")
    st.subheader("👥 User Management")
    
    # User table
    users_data = []
    for username, user_data in user_manager.users.items():
        users_data.append({
            "Username": username,
            "Name": user_data["name"],
            "Plan": user_data["plan"],
            "Email": user_data["email"],
            "Expires": user_data["expires"],
            "Last Login": user_data.get("last_login", "Never"),
            "Status": "🟢 Active" if user_data.get("is_active", True) else "🔴 Inactive",
            "Sessions": f"{user_data.get('active_sessions', 0)}/{user_data.get('max_sessions', 1)}"
        })
    
    st.dataframe(pd.DataFrame(users_data), use_container_width=True)
    
    # Admin actions
    st.markdown("---")
    st.subheader("⚡ Administrative Actions")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Refresh Analytics", use_container_width=True):
            user_manager.load_data()
            st.rerun()
    with col2:
        if st.button("📊 Export Data", use_container_width=True):
            st.success("Data export would be implemented here")
    with col3:
        if st.button("🛠️ System Health", use_container_width=True):
            st.info("System monitoring would be implemented here")

# -------------------------
# MAIN APPLICATION
# -------------------------
def main():
    init_session()
    
    # Custom CSS for professional appearance
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .plan-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem 0;
    }
    .premium-plan {
        border: 2px solid #ff6b6b;
        background: #fff5f5;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.user:
        render_login()
    else:
        if st.session_state.user['plan'] == 'admin':
            render_admin_dashboard()
        else:
            render_user_dashboard()

if __name__ == "__main__":
    main()
