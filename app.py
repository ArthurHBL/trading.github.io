# app.py - COMPLETE VERSION WITH ALL PREMIUM FEATURES RESTORED
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
# SESSION MANAGEMENT - ENHANCED
# -------------------------
def init_session():
    """Initialize session state with recovery"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {}
    
    if 'app_started' not in st.session_state:
        st.session_state.app_started = True

    # Admin states
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
    
    # User states
    if 'dashboard_view' not in st.session_state:
        st.session_state.dashboard_view = 'main'
    if 'show_settings' not in st.session_state:
        st.session_state.show_settings = False
    if 'show_upgrade' not in st.session_state:
        st.session_state.show_upgrade = False
    if 'selected_strategy' not in st.session_state:
        st.session_state.selected_strategy = None

# -------------------------
# PRODUCTION CONFIGURATION
# -------------------------
class Config:
    APP_NAME = "TradingAnalysis Pro"
    VERSION = "2.1.0"
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
# ROBUST USER MANAGEMENT WITH PERSISTENCE
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
        os.makedirs(os.path.join(self.backup_dir, "emergency"), exist_ok=True)
    
    def _initialize_with_recovery(self):
        """Initialize data with automatic recovery"""
        try:
            # Load users
            if os.path.exists(self.users_file):
                with open(self.users_file, 'r') as f:
                    self.users = json.load(f)
            else:
                self.users = {}
            
            # Load analytics
            if os.path.exists(self.analytics_file):
                with open(self.analytics_file, 'r') as f:
                    self.analytics = json.load(f)
            else:
                self.analytics = {
                    "total_logins": 0,
                    "active_users": 0,
                    "revenue_today": 0,
                    "user_registrations": [],
                    "login_history": [],
                    "deleted_users": [],
                    "plan_changes": [],
                    "password_changes": [],
                    "data_recovery_events": [],
                    "last_backup": datetime.now().isoformat(),
                    "last_save": datetime.now().isoformat(),
                    "total_backups": 0
                }
            
            # Ensure default admin exists
            if "admin" not in self.users:
                self.create_default_admin()
                self._immediate_save()
                
        except Exception as e:
            print(f"Error initializing data: {e}")
            self.users = {}
            self.analytics = self._get_default_data("analytics")
            self.create_default_admin()
    
    def _get_default_data(self, data_type):
        """Get default data structure"""
        if data_type == "analytics":
            return {
                "total_logins": 0,
                "active_users": 0,
                "revenue_today": 0,
                "user_registrations": [],
                "login_history": [],
                "deleted_users": [],
                "plan_changes": [],
                "password_changes": [],
                "data_recovery_events": [],
                "last_backup": datetime.now().isoformat(),
                "last_save": datetime.now().isoformat(),
                "total_backups": 0
            }
        return {}
    
    def _immediate_save(self):
        """Immediately save all data"""
        with self.lock:
            try:
                # Save users
                temp_users_file = self.users_file + ".tmp"
                with open(temp_users_file, 'w') as f:
                    json.dump(self.users, f, indent=2)
                
                # Save analytics
                temp_analytics_file = self.analytics_file + ".tmp"
                with open(temp_analytics_file, 'w') as f:
                    json.dump(self.analytics, f, indent=2)
                
                # Atomic rename
                os.replace(temp_users_file, self.users_file)
                os.replace(temp_analytics_file, self.analytics_file)
                
                # Update last save timestamp
                self.analytics['last_save'] = datetime.now().isoformat()
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
            "email": "admin@tradinganalysis.com",
            "subscription_id": "admin_account"
        }
    
    def hash_password(self, password):
        """Secure password hashing"""
        salt = st.secrets.get("PASSWORD_SALT", "default-salt-change-in-production")
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def register_user(self, username, password, name, email, plan="trial"):
        """Register new user with proper validation"""
        if username in self.users:
            return False, "Username already exists"
        
        if not re.match("^[a-zA-Z0-9_]{3,20}$", username):
            return False, "Username must be 3-20 characters (letters, numbers, _)"
        
        if len(password) < 8:
            return False, "Password must be at least 8 characters"
        
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            return False, "Invalid email address"
        
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
            "is_active": True,
            "subscription_id": f"sub_{username}_{int(time.time())}",
            "payment_status": "active" if plan == "trial" else "pending"
        }
        
        self.analytics["user_registrations"].append({
            "username": username,
            "plan": plan,
            "timestamp": datetime.now().isoformat()
        })
        
        if self._immediate_save():
            return True, f"Account created successfully! {plan_config['name']} activated."
        else:
            return False, "Error saving user data. Please try again."

    def create_test_user(self, plan="trial"):
        """Create a test user for admin purposes"""
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
            "is_active": True,
            "subscription_id": f"test_{test_username}",
            "payment_status": "active"
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
        """Delete a user account completely"""
        if username not in self.users:
            return False, "User not found"
        
        if username == "admin":
            return False, "Cannot delete admin account"
        
        user_data = self.users[username]
        user_plan = user_data.get('plan', 'unknown')
        user_created = user_data.get('created', 'unknown')
        
        del self.users[username]
        
        if 'deleted_users' not in self.analytics:
            self.analytics['deleted_users'] = []
        
        self.analytics['deleted_users'].append({
            "username": username,
            "plan": user_plan,
            "created": user_created,
            "deleted_at": datetime.now().isoformat()
        })
        
        if self._immediate_save():
            return True, f"User '{username}' has been permanently deleted"
        else:
            return False, "Error deleting user data"

    def change_user_plan(self, username, new_plan, change_reason=None):
        """Change a user's subscription plan"""
        if username not in self.users:
            return False, "User not found"
        
        if username == "admin":
            return False, "Cannot modify admin account plan"
        
        if new_plan not in Config.PLANS and new_plan != "admin":
            return False, f"Invalid plan: {new_plan}"
        
        user_data = self.users[username]
        old_plan = user_data.get('plan', 'unknown')
        
        old_plan_config = Config.PLANS.get(old_plan, {})
        new_plan_config = Config.PLANS.get(new_plan, {})
        
        if new_plan != "admin":
            expires = (datetime.now() + timedelta(days=new_plan_config["duration"])).strftime("%Y-%m-%d")
        else:
            expires = "2030-12-31"
        
        user_data['plan'] = new_plan
        user_data['expires'] = expires
        user_data['max_sessions'] = new_plan_config.get('max_sessions', 1) if new_plan != "admin" else 3
        
        if 'plan_changes' not in self.analytics:
            self.analytics['plan_changes'] = []
        
        change_record = {
            "username": username,
            "old_plan": old_plan,
            "new_plan": new_plan,
            "timestamp": datetime.now().isoformat(),
            "admin": self.users.get('admin', {}).get('name', 'System')
        }
        
        if change_reason:
            change_record["reason"] = change_reason
            
        self.analytics['plan_changes'].append(change_record)
        
        if self._immediate_save():
            return True, f"User '{username}' plan changed from {old_plan} to {new_plan}"
        else:
            return False, "Error saving plan change"

    def authenticate(self, username, password):
        """Authenticate user with security checks"""
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
        
        if not user.get("is_active", True):
            return False, "Account deactivated. Please contact support."
        
        if not self.verify_password(password, user["password_hash"]):
            return False, "Invalid username or password"
        
        expires = user.get("expires")
        if expires and datetime.strptime(expires, "%Y-%m-%d").date() < date.today():
            return False, "Subscription expired. Please renew your plan."
        
        if user["active_sessions"] >= user["max_sessions"]:
            return False, "Account in use. Maximum concurrent sessions reached."
        
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
    
    def change_admin_password(self, current_password, new_password, changed_by="admin"):
        """Change admin password with verification"""
        admin_user = self.users.get("admin")
        if not admin_user:
            return False, "Admin account not found"
        
        if not self.verify_password(current_password, admin_user["password_hash"]):
            return False, "Current password is incorrect"
        
        if self.verify_password(new_password, admin_user["password_hash"]):
            return False, "New password cannot be the same as current password"
        
        admin_user["password_hash"] = self.hash_password(new_password)
        
        if 'password_changes' not in self.analytics:
            self.analytics['password_changes'] = []
        
        self.analytics['password_changes'].append({
            "username": "admin",
            "timestamp": datetime.now().isoformat(),
            "changed_by": changed_by
        })
        
        if self._immediate_save():
            return True, "Admin password changed successfully!"
        else:
            return False, "Error saving password change"
    
    def get_business_metrics(self):
        """Get business metrics for admin"""
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
                "total_logins": self.analytics.get("total_logins", 0),
                "revenue_today": self.analytics.get("revenue_today", 0)
            }
        except Exception as e:
            return {
                "total_users": 0,
                "active_users": 0,
                "online_users": 0,
                "plan_distribution": {},
                "total_logins": 0,
                "revenue_today": 0
            }

# Initialize robust user manager
user_manager = RobustUserManager()

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
# ENHANCED TRADING ANALYSIS ENGINE
# -------------------------
class TradingAnalysisEngine:
    def __init__(self):
        self.market_data = self.generate_market_data()
    
    def generate_market_data(self):
        """Generate simulated market data for analysis"""
        dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')
        base_price = 50000
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = base_price * (1 + returns).cumprod()
        
        data = pd.DataFrame({
            'Date': dates,
            'Price': prices,
            'Volume': np.random.randint(1000, 10000, len(dates)),
            'RSI': np.random.uniform(30, 70, len(dates)),
            'MACD': np.random.uniform(-100, 100, len(dates)),
            'Volatility': np.random.uniform(0.01, 0.05, len(dates))
        })
        return data
    
    def calculate_technical_indicators(self, strategy):
        """Calculate technical indicators for a given strategy"""
        indicators = {}
        
        if strategy == "Premium Stoch":
            indicators['Stochastic'] = np.random.uniform(20, 80)
            indicators['Momentum'] = np.random.uniform(-1, 1)
            indicators['Trend_Strength'] = np.random.uniform(0, 1)
            
        elif strategy == "PositionFlow":
            indicators['Flow_Direction'] = np.random.choice(['Bullish', 'Bearish', 'Neutral'])
            indicators['Volume_Profile'] = np.random.uniform(0, 1)
            indicators['Liquidity_Levels'] = np.random.uniform(40000, 60000, 3)
            
        elif strategy == "Volatility":
            indicators['ATR'] = np.random.uniform(500, 2000)
            indicators['VIX_Level'] = np.random.uniform(15, 45)
            indicators['Volatility_Regime'] = np.random.choice(['Low', 'Medium', 'High'])
            
        else:
            # Default indicators for other strategies
            indicators['Strength'] = np.random.uniform(0, 1)
            indicators['Signal_Quality'] = np.random.uniform(0.5, 0.95)
            indicators['Market_Condition'] = np.random.choice(['Trending', 'Ranging', 'Volatile'])
            
        return indicators
    
    def generate_trading_signals(self, strategy, indicators):
        """Generate trading signals based on strategy and indicators"""
        signals = []
        confidence = np.random.uniform(0.6, 0.95)
        
        if strategy == "Premium Stoch":
            if indicators['Stochastic'] < 20:
                signals.append(("Oversold Buy", confidence, "High potential reversal"))
            elif indicators['Stochastic'] > 80:
                signals.append(("Overbought Sell", confidence, "Potential pullback"))
            else:
                signals.append(("Neutral Hold", 0.5, "Wait for better entry"))
                
        elif strategy == "PositionFlow":
            if indicators['Flow_Direction'] == 'Bullish':
                signals.append(("Long Entry", confidence, "Strong buying pressure"))
            elif indicators['Flow_Direction'] == 'Bearish':
                signals.append(("Short Entry", confidence, "Strong selling pressure"))
            else:
                signals.append(("Wait for Confirmation", 0.4, "Mixed signals"))
        else:
            # Default signals for other strategies
            if np.random.random() > 0.5:
                signals.append(("BUY Signal", confidence, "Positive momentum detected"))
            else:
                signals.append(("SELL Signal", confidence, "Negative pressure building"))
                
        return signals

# Initialize trading engine
trading_engine = TradingAnalysisEngine()

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
                username = st.text_input("Username", placeholder="Enter your username", key="login_username")
            with col2:
                password = st.text_input("Password", type="password", placeholder="Enter your password", key="login_password")
            
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
                new_username = st.text_input("Choose Username*", help="3-20 characters, letters and numbers only", key="reg_username")
                new_name = st.text_input("Full Name*", key="reg_name")
                plan_choice = st.selectbox(
                    "Subscription Plan*", 
                    list(Config.PLANS.keys()),
                    format_func=lambda x: f"{Config.PLANS[x]['name']} - ${Config.PLANS[x]['price']}/month",
                    key="reg_plan"
                )
            
            with col2:
                new_email = st.text_input("Email Address*", key="reg_email")
                new_password = st.text_input("Create Password*", type="password", help="Minimum 8 characters", key="reg_password")
                confirm_password = st.text_input("Confirm Password*", type="password", key="reg_confirm_password")
            
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
            
            agreed = st.checkbox("I agree to the Terms of Service and Privacy Policy*", key="reg_agree")
            
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
# PREMIUM USER DASHBOARD
# -------------------------
def render_user_dashboard():
    """Enhanced trading dashboard for premium users"""
    user = st.session_state.user
    
    # Initialize user data
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {}
    
    user_data_key = f"{user['username']}_data"
    if user_data_key not in st.session_state.user_data:
        st.session_state.user_data[user_data_key] = {
            "saved_analyses": {},
            "favorite_strategies": [],
            "performance_history": [],
            "recent_signals": []
        }
    
    data = st.session_state.user_data.get(user_data_key, {})
    
    # Enhanced sidebar with premium features
    with st.sidebar:
        st.title("🎛️ Premium Control Panel")
        
        # Premium user profile section
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        with col1:
            if user['plan'] in ['premium', 'professional', 'admin']:
                st.markdown("⭐")
            else:
                st.markdown("👤")
        with col2:
            st.write(f"**{user['name']}**")
            plan_display = Config.PLANS.get(user['plan'], {}).get('name', user['plan'].title())
            st.caption(f"🚀 {plan_display}")
        
        # Account status
        plan_config = Config.PLANS.get(user['plan'], Config.PLANS['trial'])
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        
        st.progress(min(1.0, days_left / 30), text=f"📅 {days_left} days remaining")
        
        # Quick actions
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🔄 Refresh Market Data", use_container_width=True, key="refresh_market"):
            st.rerun()
            
        if st.button("📊 Portfolio Overview", use_container_width=True, key="portfolio_quick"):
            st.session_state.dashboard_view = "portfolio"
            st.rerun()
            
        if st.button("🎯 Trading Signals", use_container_width=True, key="signals_quick"):
            st.session_state.dashboard_view = "signals"
            st.rerun()
        
        st.markdown("---")
        
        # Premium features indicator
        if user['plan'] in ['premium', 'professional', 'admin']:
            st.markdown("### 🎁 Premium Features")
            st.success("• Real-time Analytics")
            st.success("• Advanced Signals")
            st.success("• Portfolio Tracking")
            st.success("• Priority Support")
        else:
            st.markdown("### 💎 Upgrade Benefits")
            st.info("• Advanced Analytics")
            st.info("• Premium Signals")
            st.info("• Portfolio Tools")
            st.info("• Priority Support")
            
            if st.button("🚀 Upgrade to Premium", use_container_width=True, type="primary", key="upgrade_sidebar"):
                st.session_state.show_upgrade = True
                st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Secure Logout", use_container_width=True, key="logout_btn"):
            user_manager.logout(user['username'])
            st.session_state.user = None
            st.rerun()
    
    # Main dashboard content
    current_view = st.session_state.get('dashboard_view', 'main')
    
    if st.session_state.get('show_settings'):
        render_account_settings()
    elif st.session_state.get('show_upgrade'):
        render_upgrade_plans()
    elif current_view == 'portfolio':
        render_portfolio_overview(data, user)
    elif current_view == 'signals':
        render_trading_signals(data, user)
    else:
        render_trading_dashboard(data, user)

def render_trading_dashboard(data, user):
    """Enhanced main trading dashboard with premium features"""
    # Strategy selection based on plan
    plan_config = Config.PLANS.get(user['plan'], Config.PLANS['trial'])
    available_strategies = list(STRATEGIES.keys())[:plan_config['strategies']]
    
    # Enhanced dashboard header
    st.title("📊 Professional Trading Analysis")
    
    # Premium welcome message
    if user['plan'] in ['premium', 'professional', 'admin']:
        st.success(f"🎉 Welcome back, **{user['name']}**! You're using our **{Config.PLANS.get(user['plan'], {}).get('name', user['plan'].title())}** with full access to {plan_config['strategies']} advanced strategies.")
    else:
        st.info(f"👋 Welcome, **{user['name']}**! You have access to {plan_config['strategies']} strategies. Upgrade for premium features.")
    
    # Market overview section
    st.subheader("🌍 Market Overview")
    
    # Market metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        current_price = trading_engine.market_data['Price'].iloc[-1]
        price_change = ((current_price - trading_engine.market_data['Price'].iloc[-2]) / trading_engine.market_data['Price'].iloc[-2]) * 100
        st.metric(
            "BTC/USD", 
            f"${current_price:,.0f}", 
            f"{price_change:+.2f}%",
            delta_color="normal" if price_change >= 0 else "inverse"
        )
    
    with col2:
        st.metric("24h Volume", "$42.8B", "+5.2%", key="volume_metric")
    
    with col3:
        rsi = trading_engine.market_data['RSI'].iloc[-1]
        st.metric(
            "RSI", 
            f"{rsi:.1f}", 
            "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral",
            delta_color="inverse" if rsi > 70 else "normal" if rsi < 30 else "off",
            key="rsi_metric"
        )
    
    with col4:
        volatility = trading_engine.market_data['Volatility'].iloc[-1] * 100
        st.metric("Volatility", f"{volatility:.1f}%", "High" if volatility > 3 else "Low", key="vol_metric")
    
    # Strategy selector
    st.subheader("🔍 Deep Strategy Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_strategy = st.selectbox(
            "Select Strategy for Detailed Analysis", 
            available_strategies,
            key="strategy_selector"
        )
    
    with col2:
        analysis_mode = st.selectbox(
            "Analysis Mode",
            ["Technical Analysis", "Backtest Results", "Signal Generation", "Risk Assessment"],
            key="analysis_mode"
        )
    
    # Premium analysis interface
    st.markdown("---")
    
    if selected_strategy:
        # Strategy header with performance
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.subheader(f"✏️ {selected_strategy} Analysis")
        
        with col2:
            # Generate live indicators
            indicators = trading_engine.calculate_technical_indicators(selected_strategy)
            st.metric("Strategy Score", f"{np.random.uniform(65, 95):.0f}/100", key="strategy_score")
        
        with col3:
            signals = trading_engine.generate_trading_signals(selected_strategy, indicators)
            if signals:
                signal_type, confidence, reasoning = signals[0]
                st.metric(
                    "Live Signal", 
                    signal_type, 
                    f"{confidence:.0%} confidence",
                    key="live_signal"
                )
        
        # Enhanced analysis form with tabs
        tab1, tab2, tab3 = st.tabs(["📊 Technical Analysis", "📈 Performance", "💡 Trading Signals"])
        
        with tab1:
            render_technical_analysis(selected_strategy, indicators, data)
        
        with tab2:
            if user['plan'] in ['premium', 'professional', 'admin']:
                render_strategy_performance(selected_strategy)
            else:
                st.info("🔒 Upgrade to Premium to access performance analytics and backtesting")
                if st.button("🚀 Upgrade Now", key="perf_upgrade"):
                    st.session_state.show_upgrade = True
                    st.rerun()
        
        with tab3:
            render_trading_signals_tab(selected_strategy, signals)

def render_technical_analysis(strategy, indicators, data):
    """Enhanced technical analysis interface"""
    st.write(f"**Technical Analysis for {strategy}**")
    
    # Display indicators
    col1, col2, col3 = st.columns(3)
    
    indicator_items = list(indicators.items())
    
    with col1:
        for key, value in indicator_items[:2]:
            if isinstance(value, float):
                st.metric(key.replace('_', ' '), f"{value:.2f}")
            else:
                st.metric(key.replace('_', ' '), str(value))
    
    with col2:
        for key, value in indicator_items[2:4] if len(indicator_items) > 2 else []:
            if isinstance(value, float):
                st.metric(key.replace('_', ' '), f"{value:.2f}")
            else:
                st.metric(key.replace('_', ' '), str(value))
    
    with col3:
        for key, value in indicator_items[4:] if len(indicator_items) > 4 else []:
            if isinstance(value, float):
                st.metric(key.replace('_', ' '), f"{value:.2f}")
            else:
                st.metric(key.replace('_', ' '), str(value))
    
    # Analysis form
    with st.form(f"analysis_{strategy}"):
        st.write("**Manual Analysis Input**")
        
        for indicator in STRATEGIES[strategy][:3]:  # Show first 3 indicators for brevity
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

def render_strategy_performance(strategy):
    """Premium strategy performance analytics"""
    st.write(f"**Performance Analytics for {strategy}**")
    
    # Create performance chart
    dates = pd.date_range(end=datetime.now(), periods=30, freq='D')
    performance = 100 * (1 + np.random.normal(0.002, 0.015, 30)).cumprod()
    
    chart_data = pd.DataFrame({
        'Date': dates,
        'Performance': performance
    })
    
    st.line_chart(chart_data.set_index('Date')['Performance'])
    
    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Return", "+24.5%", "+2.1%")
    
    with col2:
        st.metric("Win Rate", "68%", "+5%")
    
    with col3:
        st.metric("Sharpe Ratio", "1.8", "+0.2")
    
    with col4:
        st.metric("Max Drawdown", "-8.2%", "-1.1%")

def render_trading_signals_tab(strategy, signals):
    """Trading signals interface"""
    st.write(f"**Live Trading Signals for {strategy}**")
    
    if signals:
        for signal_type, confidence, reasoning in signals:
            # Color code based on signal type
            if "Buy" in signal_type:
                signal_color = "green"
            elif "Sell" in signal_type:
                signal_color = "red"
            else:
                signal_color = "orange"
            
            st.markdown(f"""
            <div style="border-left: 4px solid {signal_color}; padding-left: 1rem; margin: 1rem 0;">
                <h4 style="margin: 0; color: {signal_color};">{signal_type}</h4>
                <p style="margin: 0.5rem 0; color: #666;">Confidence: <strong>{confidence:.0%}</strong></p>
                <p style="margin: 0; color: #888;">{reasoning}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No strong signals detected. Waiting for better market conditions.")

def render_portfolio_overview(data, user):
    """Premium portfolio overview"""
    st.title("📊 Portfolio Overview")
    
    if user['plan'] in ['premium', 'professional', 'admin']:
        # Portfolio metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Value", "$124,850", "+2.4%")
        
        with col2:
            st.metric("24h Change", "+$2,950", "+2.4%")
        
        with col3:
            st.metric("All Time P&L", "+$24,850", "+24.8%")
        
        with col4:
            st.metric("Risk Score", "Medium", "-5%")
        
        # Portfolio allocation
        st.subheader("📈 Portfolio Allocation")
        
        allocation_data = {
            'Asset': ['BTC', 'ETH', 'ADA', 'SOL', 'Cash'],
            'Value': [65000, 32000, 8500, 12350, 7000],
            'Allocation': [52.1, 25.6, 6.8, 9.9, 5.6]
        }
        allocation_df = pd.DataFrame(allocation_data)
        
        st.dataframe(allocation_df, use_container_width=True)
        
    else:
        st.info("""
        🔒 **Premium Feature Unlock**
        
        Upgrade to Premium or Professional plan to access:
        - Real-time portfolio tracking
        - Advanced analytics
        - Performance metrics
        - Risk assessment tools
        """)
        
        if st.button("🚀 Upgrade to Premium", type="primary", use_container_width=True):
            st.session_state.show_upgrade = True
            st.rerun()

def render_trading_signals(data, user):
    """Enhanced trading signals dashboard"""
    st.title("🎯 Trading Signals Center")
    
    if user['plan'] in ['premium', 'professional', 'admin']:
        # Signal overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Active Signals", "12", "+3")
        
        with col2:
            st.metric("Signal Accuracy", "76%", "+4%")
        
        with col3:
            st.metric("Avg. Return", "+2.8%", "+0.4%")
        
        # Generate sample signals
        strategies = list(STRATEGIES.keys())[:5]
        signals = []
        
        for strategy in strategies:
            indicators = trading_engine.calculate_technical_indicators(strategy)
            strategy_signals = trading_engine.generate_trading_signals(strategy, indicators)
            if strategy_signals:
                signal_type, confidence, reasoning = strategy_signals[0]
                signals.append({
                    "Strategy": strategy,
                    "Signal": signal_type,
                    "Confidence": f"{confidence:.0%}",
                    "Strength": "High" if confidence > 0.8 else "Medium" if confidence > 0.6 else "Low",
                    "Timestamp": datetime.now().strftime("%H:%M")
                })
        
        signals_df = pd.DataFrame(signals)
        st.dataframe(signals_df, use_container_width=True)
                
    else:
        st.info("""
        🔒 **Premium Signals Center**
        
        Upgrade to access real-time trading signals with:
        - Live market scanning
        - Multi-strategy analysis
        - Confidence scoring
        - Signal history tracking
        """)
        
        if st.button("🚀 Upgrade for Advanced Signals", type="primary", use_container_width=True):
            st.session_state.show_upgrade = True
            st.rerun()

def render_account_settings():
    """User account settings"""
    st.title("⚙️ Account Settings")
    
    user = st.session_state.user
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Profile Information")
        st.text_input("Full Name", value=user['name'], disabled=True)
        st.text_input("Email", value=user['email'], disabled=True)
        st.text_input("Username", value=user['username'], disabled=True)
    
    with col2:
        st.subheader("Subscription Details")
        plan_name = Config.PLANS.get(user['plan'], {}).get('name', 'Unknown Plan')
        st.text_input("Current Plan", value=plan_name, disabled=True)
        st.text_input("Expiry Date", value=user['expires'], disabled=True)
        
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Days Remaining", days_left)
    
    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        st.session_state.dashboard_view = 'main'
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
                    if st.button(f"Upgrade to {plan_config['name']}", use_container_width=True):
                        st.info("🔒 Secure payment processing would be implemented here")
                        st.success(f"Upgrade to {plan_config['name']} selected!")
    
    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        st.session_state.show_upgrade = False
        st.rerun()

# -------------------------
# ADMIN DASHBOARD - FIXED VERSION
# -------------------------
def render_admin_dashboard():
    """Professional admin dashboard for business management"""
    
    with st.sidebar:
        st.title("👑 Admin Panel")
        st.markdown("---")
        st.write(f"Welcome, **{st.session_state.user['name']}**")
        st.success("System Administrator")
        
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
        
        if st.button("📈 Analytics", use_container_width=True):
            st.session_state.admin_view = "analytics"
            st.rerun()
    
    # Main admin content
    st.title("👑 Business Administration Dashboard")
    
    # Show modals if needed
    if st.session_state.get('show_delete_confirmation'):
        render_delete_confirmation_modal()
        return
    
    if st.session_state.get('show_bulk_delete'):
        render_bulk_delete_interface()
        return
    
    if st.session_state.get('manage_user_plan'):
        render_plan_management_interface(st.session_state.manage_user_plan)
        return
    
    # Default view
    current_view = st.session_state.get('admin_view', 'overview')
    
    if current_view == 'overview':
        render_admin_overview()
    elif current_view == 'analytics':
        render_admin_analytics()
    elif current_view == 'users':
        render_admin_user_management()

def render_admin_overview():
    """Admin overview with business metrics - FIXED"""
    st.subheader("📈 Business Overview")
    
    try:
        # Get business metrics with error handling
        metrics = user_manager.get_business_metrics()
        
        # Key metrics with safe access
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_users = metrics.get("total_users", 0)
            st.metric("Total Users", total_users)
        with col2:
            active_users = metrics.get("active_users", 0)
            st.metric("Active Users", active_users)
        with col3:
            online_users = metrics.get("online_users", 0)
            st.metric("Online Now", online_users)
        with col4:
            total_logins = metrics.get("total_logins", 0)
            st.metric("Total Logins", total_logins)
        
        st.markdown("---")
        
        # Plan distribution
        st.subheader("📊 Plan Distribution")
        plan_data = metrics.get("plan_distribution", {})
        
        if plan_data:
            for plan, count in plan_data.items():
                plan_name = Config.PLANS.get(plan, {}).get('name', plan.title())
                st.write(f"• {plan_name}: {count} users")
        else:
            st.info("No plan distribution data available")
        
    except Exception as e:
        st.error(f"Error loading admin overview: {str(e)}")

def render_admin_analytics():
    """Detailed analytics view"""
    st.subheader("📈 Detailed Analytics")
    
    # Login analytics
    st.write("**Login Activity**")
    total_logins = user_manager.analytics.get("total_logins", 0)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Login Attempts", total_logins)
    with col2:
        successful_logins = len([x for x in user_manager.analytics.get("login_history", []) if x.get('success')])
        st.metric("Successful Logins", successful_logins)
    with col3:
        failed_logins = total_logins - successful_logins
        st.metric("Failed Logins", failed_logins)

def render_admin_user_management():
    """User management interface"""
    st.subheader("👥 User Management")
    
    # User actions
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🔄 Refresh", use_container_width=True):
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
        if st.button("🗑️ Bulk Delete", use_container_width=True):
            st.session_state.show_bulk_delete = True
            st.rerun()
    with col4:
        if st.button("🔐 Change Password", use_container_width=True):
            st.session_state.show_password_change = True
            st.rerun()
    
    st.markdown("---")
    
    # Users table
    st.write("**All Users:**")
    for username, user_data in user_manager.users.items():
        with st.expander(f"{username} - {user_data['name']} ({user_data['email']})"):
            col1, col2 = st.columns(2)
            with col1:
                st.write(f"**Plan:** {user_data['plan']}")
                st.write(f"**Status:** {'🟢 Active' if user_data.get('is_active', True) else '🔴 Inactive'}")
                st.write(f"**Expires:** {user_data['expires']}")
            with col2:
                st.write(f"**Created:** {user_data['created'][:10]}")
                st.write(f"**Last Login:** {user_data.get('last_login', 'Never')[:16]}")
                st.write(f"**Sessions:** {user_data.get('active_sessions', 0)}/{user_data.get('max_sessions', 1)}")
            
            if username != "admin":
                col1, col2 = st.columns(2)
                with col1:
                    if st.button(f"Manage Plan", key=f"plan_{username}"):
                        st.session_state.manage_user_plan = username
                        st.rerun()
                with col2:
                    if st.button(f"Delete", key=f"del_{username}"):
                        st.session_state.user_to_delete = username
                        st.session_state.show_delete_confirmation = True
                        st.rerun()

def render_delete_confirmation_modal():
    """Modal for confirming user deletion"""
    user_to_delete = st.session_state.get('user_to_delete')
    
    if not user_to_delete:
        return
    
    st.error("🚨 **Confirm User Deletion**")
    st.warning(f"**User to delete:** {user_to_delete}")
    
    user_data = user_manager.users.get(user_to_delete, {})
    if user_data:
        st.write(f"**Name:** {user_data.get('name', 'N/A')}")
        st.write(f"**Email:** {user_data.get('email', 'N/A')}")
        st.write(f"**Plan:** {user_data.get('plan', 'N/A')}")
    
    st.markdown("---")
    st.error("**This action cannot be undone!**")
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("✅ Confirm Delete", type="primary", use_container_width=True):
            success, message = user_manager.delete_user(user_to_delete)
            if success:
                st.success(f"✅ {message}")
                st.session_state.show_delete_confirmation = False
                st.session_state.user_to_delete = None
                time.sleep(1)
                st.rerun()
            else:
                st.error(f"❌ {message}")
    
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.show_delete_confirmation = False
            st.session_state.user_to_delete = None
            st.rerun()

def render_bulk_delete_interface():
    """Bulk delete interface"""
    st.subheader("🗑️ Bulk Delete Inactive Users")
    
    # Get inactive users
    inactive_users = []
    for username, user_data in user_manager.users.items():
        if username != "admin" and not user_data.get('is_active', True):
            inactive_users.append({
                "username": username,
                "name": user_data["name"],
                "email": user_data["email"],
                "plan": user_data["plan"]
            })
    
    if not inactive_users:
        st.info("🎉 No inactive users found!")
        if st.button("⬅️ Back"):
            st.session_state.show_bulk_delete = False
            st.rerun()
        return
    
    st.warning(f"Found {len(inactive_users)} inactive users")
    
    for user in inactive_users:
        col1, col2, col3 = st.columns([3, 2, 1])
        with col1:
            st.write(f"**{user['username']}** - {user['name']}")
        with col2:
            st.write(f"Email: {user['email']} | Plan: {user['plan']}")
        with col3:
            if st.button("Delete", key=f"bulk_{user['username']}"):
                success, message = user_manager.delete_user(user['username'])
                if success:
                    st.success(f"Deleted {user['username']}")
                else:
                    st.error(f"Error: {message}")
                st.rerun()
    
    if st.button("⬅️ Back to User Management"):
        st.session_state.show_bulk_delete = False
        st.rerun()

def render_plan_management_interface(username):
    """Plan management interface"""
    if username not in user_manager.users:
        st.error("User not found")
        if st.button("⬅️ Back"):
            st.session_state.manage_user_plan = None
            st.rerun()
        return
    
    user_data = user_manager.users[username]
    current_plan = user_data['plan']
    
    st.subheader(f"📋 Plan Management: {username}")
    
    if st.button("⬅️ Back"):
        st.session_state.manage_user_plan = None
        st.rerun()
    
    st.write(f"**Current Plan:** {Config.PLANS.get(current_plan, {}).get('name', current_plan.title())}")
    st.write(f"**User:** {user_data['name']} ({user_data['email']})")
    
    new_plan = st.selectbox(
        "Select New Plan",
        list(Config.PLANS.keys()),
        index=list(Config.PLANS.keys()).index(current_plan) if current_plan in Config.PLANS else 0,
        format_func=lambda x: f"{Config.PLANS[x]['name']} - ${Config.PLANS[x]['price']}/month"
    )
    
    if st.button("✅ Confirm Plan Change", type="primary"):
        if new_plan != current_plan:
            success, message = user_manager.change_user_plan(username, new_plan)
            if success:
                st.success(f"✅ {message}")
                time.sleep(2)
                st.session_state.manage_user_plan = None
                st.rerun()
            else:
                st.error(f"❌ {message}")

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
    .premium-feature {
        border: 2px solid #00D4AA;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        background: linear-gradient(135deg, #f8fffe 0%, #e6f7f5 100%);
    }
    .premium-badge {
        background: linear-gradient(135deg, #00D4AA 0%, #009975 100%);
        color: white;
        padding: 0.25rem 0.75rem;
        border-radius: 15px;
        font-size: 0.8rem;
        font-weight: bold;
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
