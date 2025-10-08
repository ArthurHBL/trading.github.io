# app.py - COMPLETE FIXED VERSION
import streamlit as st
import hashlib
import json
import pandas as pd
import uuid
from datetime import datetime, date, timedelta
from typing import Dict, List, Tuple
import re
import time
import os
import numpy as np
import threading
import shutil

# -------------------------
# SESSION MANAGEMENT
# -------------------------
def init_session():
    """Initialize session state"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {}
    
    if 'show_delete_confirmation' not in st.session_state:
        st.session_state.show_delete_confirmation = False
    if 'user_to_delete' not in st.session_state:
        st.session_state.user_to_delete = None
    if 'show_bulk_delete' not in st.session_state:
        st.session_state.show_bulk_delete = False
    if 'admin_view' not in st.session_state:
        st.session_state.admin_view = 'overview'
    if 'manage_user_plan' not in st.session_state:
        st.session_state.manage_user_plan = None
    if 'show_password_change' not in st.session_state:
        st.session_state.show_password_change = False
    if 'dashboard_view' not in st.session_state:
        st.session_state.dashboard_view = 'main'
    if 'show_settings' not in st.session_state:
        st.session_state.show_settings = False
    if 'show_upgrade' not in st.session_state:
        st.session_state.show_upgrade = False

# -------------------------
# CONFIGURATION
# -------------------------
class Config:
    APP_NAME = "TradingAnalysis Pro"
    VERSION = "2.1.0"
    SUPPORT_EMAIL = "support@tradinganalysis.com"
    
    PLANS = {
        "trial": {"name": "7-Day Trial", "price": 0, "duration": 7, "strategies": 3, "max_sessions": 1},
        "basic": {"name": "Basic Plan", "price": 29, "duration": 30, "strategies": 5, "max_sessions": 1},
        "premium": {"name": "Premium Plan", "price": 79, "duration": 30, "strategies": 15, "max_sessions": 2},
        "professional": {"name": "Professional", "price": 149, "duration": 30, "strategies": 15, "max_sessions": 3}
    }

# -------------------------
# USER MANAGEMENT
# -------------------------
class RobustUserManager:
    def __init__(self):
        self.users_file = "data/users.json"
        self.analytics_file = "data/analytics.json"
        self.backup_dir = "data/backups"
        self.lock = threading.Lock()
        
        self._ensure_directories()
        self._initialize_with_recovery()
    
    def _ensure_directories(self):
        """Create necessary directories"""
        os.makedirs("data", exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _initialize_with_recovery(self):
        """Initialize data with recovery"""
        self.users = self._load_data_with_recovery(self.users_file, "users")
        self.analytics = self._load_data_with_recovery(self.analytics_file, "analytics")
        
        if "admin" not in self.users:
            self.create_default_admin()
            self._immediate_save()
    
    def _load_data_with_recovery(self, filepath, data_type):
        """Load data with recovery"""
        try:
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    return json.load(f)
            else:
                return self._get_default_data(data_type)
        except Exception as e:
            print(f"Error loading {data_type}: {e}")
            return self._get_default_data(data_type)
    
    def _get_default_data(self, data_type):
        """Get default data structure"""
        if data_type == "users":
            default_data = {}
            self.create_default_admin(default_data)
            return default_data
        elif data_type == "analytics":
            return {
                "total_logins": 0,
                "user_registrations": [],
                "login_history": [],
                "plan_changes": []
            }
        return {}
    
    def load_data(self):
        """Public method to reload data - FIXED: Added this missing method"""
        self.users = self._load_data_with_recovery(self.users_file, "users")
        self.analytics = self._load_data_with_recovery(self.analytics_file, "analytics")
        return True

    def _immediate_save(self):
        """Save all data immediately"""
        with self.lock:
            try:
                with open(self.users_file, 'w') as f:
                    json.dump(self.users, f, indent=2)
                with open(self.analytics_file, 'w') as f:
                    json.dump(self.analytics, f, indent=2)
                return True
            except Exception as e:
                print(f"Save failed: {e}")
                return False

    def create_default_admin(self, users_dict=None):
        """Create default admin account"""
        target_dict = users_dict if users_dict is not None else self.users
        target_dict["admin"] = {
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
            "email": "admin@tradinganalysis.com"
        }
    
    def hash_password(self, password):
        """Secure password hashing"""
        salt = st.secrets.get("PASSWORD_SALT", "default-salt-change-in-production")
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def register_user(self, username, password, name, email, plan="trial"):
        """Register new user"""
        if username in self.users:
            return False, "Username already exists"
        
        plan_config = Config.PLANS.get(plan, Config.PLANS["trial"])
        expires = (datetime.now() + timedelta(days=plan_config["duration"])).strftime("%Y-%m-%d")
        
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
            "is_active": True
        }
        
        self.analytics["user_registrations"].append({
            "username": username,
            "plan": plan,
            "timestamp": datetime.now().isoformat()
        })
        
        if self._immediate_save():
            return True, f"Account created successfully! {plan_config['name']} activated."
        else:
            return False, "Error saving user data."

    def create_test_user(self, plan="trial"):
        """Create a test user"""
        test_username = f"test_{int(time.time())}"
        test_email = f"test{int(time.time())}@example.com"
        
        plan_config = Config.PLANS.get(plan, Config.PLANS["trial"])
        expires = (datetime.now() + timedelta(days=plan_config["duration"])).strftime("%Y-%m-%d")
        
        self.users[test_username] = {
            "password_hash": self.hash_password("test12345"),
            "name": f"Test User {test_username}",
            "email": test_email,
            "plan": plan,
            "expires": expires,
            "created": datetime.now().isoformat(),
            "last_login": None,
            "login_count": 0,
            "active_sessions": 0,
            "max_sessions": plan_config["max_sessions"],
            "is_active": True
        }
        
        self.analytics["user_registrations"].append({
            "username": test_username,
            "plan": plan,
            "timestamp": datetime.now().isoformat()
        })
        
        if self._immediate_save():
            return test_username, f"Test user '{test_username}' created with {plan} plan!"
        else:
            return None, "Error creating test user"

    def delete_user(self, username):
        """Delete a user account"""
        if username not in self.users:
            return False, "User not found"
        
        if username == "admin":
            return False, "Cannot delete admin account"
        
        del self.users[username]
        
        if self._immediate_save():
            return True, f"User '{username}' has been deleted"
        else:
            return False, "Error deleting user data"

    def change_user_plan(self, username, new_plan, change_reason=None):
        """Change user's subscription plan"""
        if username not in self.users:
            return False, "User not found"
        
        if username == "admin":
            return False, "Cannot modify admin account plan"
        
        user_data = self.users[username]
        old_plan = user_data.get('plan', 'unknown')
        
        user_data['plan'] = new_plan
        user_data['max_sessions'] = Config.PLANS.get(new_plan, {}).get('max_sessions', 1)
        
        if 'plan_changes' not in self.analytics:
            self.analytics['plan_changes'] = []
        
        self.analytics['plan_changes'].append({
            "username": username,
            "old_plan": old_plan,
            "new_plan": new_plan,
            "timestamp": datetime.now().isoformat()
        })
        
        if self._immediate_save():
            return True, f"User '{username}' plan changed from {old_plan} to {new_plan}"
        else:
            return False, "Error saving plan change"

    def authenticate(self, username, password):
        """Authenticate user"""
        self.analytics["total_logins"] += 1
        self.analytics["login_history"].append({
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "success": False
        })
        
        if username not in self.users:
            self._immediate_save()
            return False, "Invalid username or password"
        
        user = self.users[username]
        
        if not self.verify_password(password, user["password_hash"]):
            return False, "Invalid username or password"
        
        user["last_login"] = datetime.now().isoformat()
        user["login_count"] = user.get("login_count", 0) + 1
        user["active_sessions"] += 1
        
        self.analytics["login_history"][-1]["success"] = True
        
        if self._immediate_save():
            return True, "Login successful"
        else:
            return False, "Error saving login data"
    
    def verify_password(self, password, password_hash):
        return self.hash_password(password) == password_hash
    
    def logout(self, username):
        """Logout user"""
        if username in self.users:
            self.users[username]["active_sessions"] = max(0, self.users[username]["active_sessions"] - 1)
            self._immediate_save()
    
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
            "total_logins": self.analytics.get("total_logins", 0)
        }

# Initialize user manager
user_manager = RobustUserManager()

# -------------------------
# TRADING STRATEGIES
# -------------------------
STRATEGIES = {
    "Premium Stoch": ["Overview","VWAP AA","VWAP","Volume Delta","Stoch RSI","SMI","RSI(SMI)","RAINBOW_RSI"],
    "LS Copy": ["Overview","NVT","RoC Bands","RoC","BBWP","PSO","RSI","RAINBOW_RSI"],
    "PositionFlow": ["Overview","VWAP","Chart VWAP","MACZ VWAP","MFI","Fisher Transform","RAINBOW_RSI"],
}

# -------------------------
# TRADING ENGINE
# -------------------------
class TradingAnalysisEngine:
    def __init__(self):
        self.market_data = self.generate_market_data()
    
    def generate_market_data(self):
        """Generate simulated market data"""
        dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')
        base_price = 50000
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = base_price * (1 + returns).cumprod()
        
        return pd.DataFrame({
            'Date': dates,
            'Price': prices,
            'Volume': np.random.randint(1000, 10000, len(dates)),
            'RSI': np.random.uniform(30, 70, len(dates))
        })
    
    def calculate_technical_indicators(self, strategy):
        """Calculate technical indicators"""
        indicators = {
            'Strength': np.random.uniform(0, 1),
            'Signal_Quality': np.random.uniform(0.5, 0.95),
            'Market_Condition': np.random.choice(['Trending', 'Ranging', 'Volatile'])
        }
        return indicators
    
    def generate_trading_signals(self, strategy, indicators):
        """Generate trading signals"""
        signals = []
        confidence = np.random.uniform(0.6, 0.95)
        
        if np.random.random() > 0.5:
            signals.append(("BUY Signal", confidence, "Positive momentum detected"))
        else:
            signals.append(("SELL Signal", confidence, "Negative pressure building"))
                
        return signals

trading_engine = TradingAnalysisEngine()

# -------------------------
# AUTHENTICATION COMPONENTS
# -------------------------
def render_login():
    """Login/registration interface"""
    st.title(f"🔐 Welcome to {Config.APP_NAME}")
    
    tab1, tab2 = st.tabs(["🚀 Login", "📝 Register"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("Sign In")
            
            username = st.text_input("Username", placeholder="Enter your username")
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
            
            new_username = st.text_input("Choose Username", help="3-20 characters")
            new_name = st.text_input("Full Name")
            new_email = st.text_input("Email Address")
            new_password = st.text_input("Create Password", type="password")
            confirm_password = st.text_input("Confirm Password", type="password")
            plan_choice = st.selectbox("Subscription Plan", list(Config.PLANS.keys()),
                                     format_func=lambda x: Config.PLANS[x]['name'])
            
            submitted = st.form_submit_button("🚀 Create Account", use_container_width=True)
            
            if submitted:
                if not all([new_username, new_name, new_email, new_password, confirm_password]):
                    st.error("❌ Please fill in all required fields")
                elif new_password != confirm_password:
                    st.error("❌ Passwords do not match")
                else:
                    with st.spinner("Creating your account..."):
                        success, message = user_manager.register_user(
                            new_username, new_password, new_name, new_email, plan_choice
                        )
                        if success:
                            st.success(f"✅ {message}")
                            st.balloons()
                        else:
                            st.error(f"❌ {message}")

# -------------------------
# USER DASHBOARD
# -------------------------
def render_user_dashboard():
    """User trading dashboard"""
    user = st.session_state.user
    
    with st.sidebar:
        st.title("🎛️ Control Panel")
        st.write(f"**{user['name']}**")
        st.caption(f"Plan: {user['plan'].title()}")
        
        if st.button("🚪 Logout", use_container_width=True):
            user_manager.logout(user['username'])
            st.session_state.user = None
            st.rerun()
    
    st.title("📊 Trading Analysis")
    
    # Market overview
    st.subheader("🌍 Market Overview")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        current_price = trading_engine.market_data['Price'].iloc[-1]
        st.metric("BTC/USD", f"${current_price:,.0f}")
    
    with col2:
        st.metric("24h Volume", "$42.8B")
    
    with col3:
        rsi = trading_engine.market_data['RSI'].iloc[-1]
        st.metric("RSI", f"{rsi:.1f}")
    
    # Strategy selection
    st.subheader("🎯 Trading Strategies")
    
    plan_config = Config.PLANS.get(user['plan'], Config.PLANS['trial'])
    available_strategies = list(STRATEGIES.keys())[:plan_config['strategies']]
    
    selected_strategy = st.selectbox("Select Strategy", available_strategies)
    
    if selected_strategy:
        st.subheader(f"📈 {selected_strategy} Analysis")
        
        # Generate analysis
        indicators = trading_engine.calculate_technical_indicators(selected_strategy)
        signals = trading_engine.generate_trading_signals(selected_strategy, indicators)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Technical Indicators**")
            for key, value in indicators.items():
                if isinstance(value, float):
                    st.metric(key.replace('_', ' '), f"{value:.2f}")
                else:
                    st.write(f"**{key.replace('_', ' ')}:** {value}")
        
        with col2:
            st.write("**Trading Signals**")
            if signals:
                for signal_type, confidence, reasoning in signals:
                    st.success(f"**{signal_type}**")
                    st.write(f"Confidence: {confidence:.0%}")
                    st.write(f"Reason: {reasoning}")
            else:
                st.info("No strong signals detected")

# -------------------------
# ADMIN DASHBOARD
# -------------------------
def render_admin_dashboard():
    """Admin dashboard"""
    
    with st.sidebar:
        st.title("👑 Admin Panel")
        st.write(f"Welcome, **{st.session_state.user['name']}**")
        
        if st.button("🚪 Logout", use_container_width=True):
            user_manager.logout(st.session_state.user['username'])
            st.session_state.user = None
            st.rerun()
        
        st.markdown("---")
        st.subheader("Navigation")
        
        if st.button("📊 Business Overview", use_container_width=True):
            st.session_state.admin_view = "overview"
            st.rerun()
        
        if st.button("👥 Manage Users", use_container_width=True):
            st.session_state.admin_view = "users"
            st.rerun()
        
        if st.button("🔄 Refresh Data", use_container_width=True):
            user_manager.load_data()  # FIXED: This method now exists
            st.success("Data refreshed!")
            st.rerun()
    
    # Main admin content
    st.title("👑 Business Administration")
    
    current_view = st.session_state.get('admin_view', 'overview')
    
    if current_view == 'overview':
        render_admin_overview()
    elif current_view == 'users':
        render_admin_user_management()

def render_admin_overview():
    """Admin overview"""
    st.subheader("📈 Business Overview")
    
    metrics = user_manager.get_business_metrics()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", metrics["total_users"])
    with col2:
        st.metric("Active Users", metrics["active_users"])
    with col3:
        st.metric("Online Now", metrics["online_users"])
    with col4:
        st.metric("Total Logins", metrics["total_logins"])
    
    st.markdown("---")
    
    # Plan distribution
    st.subheader("📊 Plan Distribution")
    plan_data = metrics["plan_distribution"]
    
    if plan_data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Users by Plan:**")
            for plan, count in plan_data.items():
                plan_name = Config.PLANS.get(plan, {}).get('name', plan.title())
                st.write(f"• {plan_name}: {count} users")
        
        with col2:
            total = sum(plan_data.values())
            for plan, count in plan_data.items():
                percentage = (count / total) * 100 if total > 0 else 0
                plan_name = Config.PLANS.get(plan, {}).get('name', plan.title())
                st.write(f"{plan_name}: {count} ({percentage:.1f}%)")
                st.progress(percentage / 100)

def render_admin_user_management():
    """User management"""
    st.subheader("👥 User Management")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Refresh List", use_container_width=True):
            st.rerun()
    with col2:
        if st.button("🆕 Create Test User", use_container_width=True):
            created_username, msg = user_manager.create_test_user("trial")
            if created_username:
                st.success(msg)
            else:
                st.error(msg)
            st.rerun()
    with col3:
        if st.button("📊 User Analytics", use_container_width=True):
            st.info("User analytics would be displayed here")
    
    st.markdown("---")
    
    # User table
    st.write("**All Users:**")
    
    for username, user_data in user_manager.users.items():
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 2, 1])
            
            with col1:
                st.write(f"**{username}**")
                st.caption(user_data['name'])
            
            with col2:
                st.write(user_data['email'])
            
            with col3:
                current_plan = user_data['plan']
                plan_display = Config.PLANS.get(current_plan, {}).get('name', current_plan.title())
                st.write(f"`{plan_display}`")
            
            with col4:
                expires = user_data['expires']
                days_left = (datetime.strptime(expires, "%Y-%m-%d").date() - date.today()).days
                st.write(f"Expires: {expires}")
                st.caption(f"{days_left} days left")
            
            with col5:
                if username != "admin":
                    if st.button("⚙️", key=f"manage_{username}"):
                        st.session_state.manage_user_plan = username
                        st.rerun()

# -------------------------
# MAIN APPLICATION
# -------------------------
def main():
    init_session()
    
    st.set_page_config(
        page_title=Config.APP_NAME,
        layout="wide",
        page_icon="📊"
    )
    
    if not st.session_state.user:
        render_login()
    else:
        if st.session_state.user['plan'] == 'admin':
            render_admin_dashboard()
        else:
            render_user_dashboard()

if __name__ == "__main__":
    main()
