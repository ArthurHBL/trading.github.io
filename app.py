# app.py - COMPLETE FIXED VERSION
import streamlit as st
import hashlib
import json
import pandas as pd
import uuid
from datetime import datetime, date, timedelta
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
    defaults = {
        'user': None,
        'user_data': {},
        'app_started': True,
        'show_delete_confirmation': False,
        'user_to_delete': None,
        'show_bulk_delete': False,
        'admin_view': 'overview',
        'manage_user_plan': None,
        'show_password_change': False,
        'dashboard_view': 'main',
        'show_settings': False,
        'show_upgrade': False,
        'selected_strategy': None
    }
    
    for key, value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = value

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
class UserManager:
    def __init__(self):
        self.users_file = "data/users.json"
        self.analytics_file = "data/analytics.json"
        self.backup_dir = "data/backups"
        self.lock = threading.Lock()
        
        self._ensure_directories()
        self._initialize_data()
    
    def _ensure_directories(self):
        """Create necessary directories"""
        os.makedirs("data", exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
    
    def _initialize_data(self):
        """Initialize data with recovery"""
        try:
            # Load users
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            else:
                self.users = {}
                self.create_default_admin()
            
            # Load analytics
            if os.path.exists(self.analytics_file):
                with open(self.analytics_file, 'r') as f:
                    self.analytics = json.load(f)
            else:
                self.analytics = {
                    "total_logins": 0,
                    "user_registrations": [],
                    "login_history": []
                }
                
        except Exception as e:
            print(f"Error loading data: {e}")
            self.users = {}
            self.analytics = {
                "total_logins": 0,
                "user_registrations": [],
                "login_history": []
            }
            self.create_default_admin()
    
    def create_default_admin(self):
        """Create default admin account"""
        self.users["admin"] = {
            "password_hash": self.hash_password("admin123"),
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
        self._save_data()
    
    def hash_password(self, password):
        """Secure password hashing"""
        salt = "default-salt-change-in-production"
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def _save_data(self):
        """Save all data"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
            with open(self.analytics_file, 'w') as f:
                json.dump(self.analytics, f, indent=2)
            return True
        except Exception as e:
            print(f"Error saving data: {e}")
            return False
    
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
        
        if self._save_data():
            return True, f"Account created successfully! {plan_config['name']} activated."
        else:
            return False, "Error saving user data."
    
    def authenticate(self, username, password):
        """Authenticate user"""
        self.analytics["total_logins"] += 1
        
        if username not in self.users:
            return False, "Invalid username or password"
        
        user = self.users[username]
        
        if not self.verify_password(password, user["password_hash"]):
            return False, "Invalid username or password"
        
        expires = user.get("expires")
        if expires and datetime.strptime(expires, "%Y-%m-%d").date() < date.today():
            return False, "Subscription expired"
        
        if user["active_sessions"] >= user["max_sessions"]:
            return False, "Maximum sessions reached"
        
        user["last_login"] = datetime.now().isoformat()
        user["login_count"] = user.get("login_count", 0) + 1
        user["active_sessions"] += 1
        
        self._save_data()
        return True, "Login successful"
    
    def verify_password(self, password, password_hash):
        return self.hash_password(password) == password_hash
    
    def logout(self, username):
        """Logout user"""
        if username in self.users:
            self.users[username]["active_sessions"] = max(0, self.users[username]["active_sessions"] - 1)
            self._save_data()
    
    def get_business_metrics(self):
        """Get business metrics"""
        try:
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
        except Exception as e:
            return {
                "total_users": 0,
                "active_users": 0,
                "online_users": 0,
                "plan_distribution": {},
                "total_logins": 0
            }

# Initialize user manager
user_manager = UserManager()

# -------------------------
# TRADING ENGINE
# -------------------------
class TradingEngine:
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
    
    def calculate_indicators(self, strategy):
        """Calculate technical indicators"""
        return {
            'Strength': np.random.uniform(0, 1),
            'Signal_Quality': np.random.uniform(0.5, 0.95),
            'Market_Condition': np.random.choice(['Trending', 'Ranging', 'Volatile'])
        }
    
    def generate_signals(self, strategy, indicators):
        """Generate trading signals"""
        confidence = np.random.uniform(0.6, 0.95)
        if np.random.random() > 0.5:
            return [("BUY Signal", confidence, "Positive momentum")]
        else:
            return [("SELL Signal", confidence, "Negative pressure")]

trading_engine = TradingEngine()

# -------------------------
# AUTHENTICATION INTERFACE
# -------------------------
def render_login():
    """Login/registration interface"""
    st.title(f"🔐 {Config.APP_NAME}")
    
    tab1, tab2 = st.tabs(["🚀 Login", "📝 Register"])
    
    with tab1:
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            
            if st.form_submit_button("Login"):
                if username and password:
                    success, message = user_manager.authenticate(username, password)
                    if success:
                        st.session_state.user = {
                            "username": username,
                            "name": user_manager.users[username]["name"],
                            "plan": user_manager.users[username]["plan"]
                        }
                        st.success(message)
                        st.rerun()
                    else:
                        st.error(message)
    
    with tab2:
        with st.form("register_form"):
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Username")
                new_name = st.text_input("Full Name")
                plan_choice = st.selectbox("Plan", list(Config.PLANS.keys()))
            with col2:
                new_email = st.text_input("Email")
                new_password = st.text_input("Password", type="password")
                confirm_password = st.text_input("Confirm Password", type="password")
            
            if st.form_submit_button("Create Account"):
                if all([new_username, new_name, new_email, new_password]):
                    if new_password == confirm_password:
                        success, message = user_manager.register_user(
                            new_username, new_password, new_name, new_email, plan_choice
                        )
                        if success:
                            st.success(message)
                        else:
                            st.error(message)
                    else:
                        st.error("Passwords don't match")
                else:
                    st.error("Please fill all fields")

# -------------------------
# USER DASHBOARD
# -------------------------
def render_user_dashboard():
    """User trading dashboard"""
    user = st.session_state.user
    
    with st.sidebar:
        st.write(f"Welcome, **{user['name']}**")
        st.write(f"Plan: {user['plan']}")
        
        if st.button("Logout"):
            user_manager.logout(user['username'])
            st.session_state.user = None
            st.rerun()
    
    st.title("📊 Trading Dashboard")
    
    # Market overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        price = trading_engine.market_data['Price'].iloc[-1]
        st.metric("BTC/USD", f"${price:,.0f}")
    with col2:
        st.metric("24h Volume", "$42.8B")
    with col3:
        rsi = trading_engine.market_data['RSI'].iloc[-1]
        st.metric("RSI", f"{rsi:.1f}")
    with col4:
        st.metric("Trend", "Bullish")
    
    # Strategy analysis
    st.subheader("Strategy Analysis")
    strategy = st.selectbox("Select Strategy", ["Premium Stoch", "PositionFlow", "Volatility"])
    
    if strategy:
        indicators = trading_engine.calculate_indicators(strategy)
        signals = trading_engine.generate_signals(strategy, indicators)
        
        col1, col2 = st.columns(2)
        with col1:
            st.write("**Indicators:**")
            for key, value in indicators.items():
                st.write(f"{key}: {value:.2f}")
        
        with col2:
            st.write("**Signals:**")
            for signal in signals:
                st.write(f"• {signal[0]} ({signal[1]:.0%} confidence)")
                st.write(f"  {signal[2]}")

# -------------------------
# ADMIN DASHBOARD
# -------------------------
def render_admin_dashboard():
    """Admin management dashboard"""
    
    with st.sidebar:
        st.title("👑 Admin Panel")
        st.write(f"Welcome, **{st.session_state.user['name']}**")
        
        if st.button("Logout"):
            user_manager.logout(st.session_state.user['username'])
            st.session_state.user = None
            st.rerun()
        
        st.subheader("Navigation")
        if st.button("Business Overview"):
            st.session_state.admin_view = "overview"
            st.rerun()
        if st.button("User Management"):
            st.session_state.admin_view = "users"
            st.rerun()
    
    # Main content
    st.title("Business Administration")
    
    current_view = st.session_state.get('admin_view', 'overview')
    
    if current_view == 'overview':
        render_admin_overview()
    elif current_view == 'users':
        render_admin_users()

def render_admin_overview():
    """Admin overview page"""
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
    
    # Plan distribution
    st.subheader("Plan Distribution")
    plan_data = metrics["plan_distribution"]
    if plan_data:
        for plan, count in plan_data.items():
            plan_name = Config.PLANS.get(plan, {}).get('name', plan)
            st.write(f"• {plan_name}: {count} users")

def render_admin_users():
    """User management page"""
    st.subheader("👥 User Management")
    
    # Create test user
    if st.button("Create Test User"):
        test_user = f"test_{int(time.time())}"
        user_manager.users[test_user] = {
            "password_hash": user_manager.hash_password("test123"),
            "name": f"Test User {test_user}",
            "email": f"{test_user}@example.com",
            "plan": "trial",
            "expires": (datetime.now() + timedelta(days=7)).strftime("%Y-%m-%d"),
            "created": datetime.now().isoformat(),
            "last_login": None,
            "login_count": 0,
            "active_sessions": 0,
            "max_sessions": 1,
            "is_active": True
        }
        user_manager._save_data()
        st.success(f"Test user '{test_user}' created!")
        st.rerun()
    
    # Users table
    st.write("**All Users:**")
    for username, user_data in user_manager.users.items():
        with st.expander(f"{username} - {user_data['name']}"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"Email: {user_data['email']}")
                st.write(f"Plan: {user_data['plan']}")
                st.write(f"Status: {'Active' if user_data['is_active'] else 'Inactive'}")
            with col2:
                st.write(f"Created: {user_data['created'][:10]}")
                st.write(f"Last Login: {user_data.get('last_login', 'Never')[:16]}")
                st.write(f"Login Count: {user_data.get('login_count', 0)}")
            
            if username != "admin":
                if st.button(f"Delete {username}", key=f"del_{username}"):
                    if st.session_state.get('user_to_delete') == username:
                        del user_manager.users[username]
                        user_manager._save_data()
                        st.success(f"User {username} deleted!")
                        st.rerun()
                    else:
                        st.session_state.user_to_delete = username
                        st.warning(f"Click again to confirm deletion of {username}")

# -------------------------
# MAIN APPLICATION
# -------------------------
def main():
    init_session()
    
    # Custom CSS
    st.markdown("""
    <style>
    .main-header {
        font-size: 2.5rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
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
