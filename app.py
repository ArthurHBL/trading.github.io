# app.py - SUPABASE INTEGRATION VERSION
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
import atexit
import numpy as np
import shutil
import io
import base64
from supabase import create_client, Client

# -------------------------
# SUPABASE CONFIGURATION
# -------------------------
class SupabaseConfig:
    # Replace these with your actual Supabase credentials
    SUPABASE_URL = "https://dmshwbwdupyqpqrqcndm.supabase.co"
    SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6ImRtc2h3YndkdXB5cXBxcnFjbmRtIiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDM5NzYwMSwiZXhwIjoyMDc1OTczNjAxfQ.TsxLuUB1dAOMWRdXBhw4KjNMhcieXNErTepiFLdbGzU"
    
    # Table names
    USERS_TABLE = "users"
    ANALYTICS_TABLE = "analytics"
    STRATEGY_ANALYSES_TABLE = "strategy_analyses"
    USER_DATA_TABLE = "user_data"

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    try:
        supabase = create_client(SupabaseConfig.SUPABASE_URL, SupabaseConfig.SUPABASE_KEY)
        # Test connection
        supabase.table(SupabaseConfig.USERS_TABLE).select("count", count="exact").limit(1).execute()
        st.success("✅ Supabase connected successfully")
        return supabase
    except Exception as e:
        st.error(f"❌ Supabase connection failed: {e}")
        return None

# -------------------------
# SESSION MANAGEMENT
# -------------------------
def init_session():
    """Initialize session state variables"""
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {}
    if 'app_started' not in st.session_state:
        st.session_state.app_started = True
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
    if 'selected_strategy' not in st.session_state:
        st.session_state.selected_strategy = None
    if 'analysis_date' not in st.session_state:
        st.session_state.analysis_date = date.today()
    if 'last_save_time' not in st.session_state:
        st.session_state.last_save_time = time.time()
    if 'show_user_credentials' not in st.session_state:
        st.session_state.show_user_credentials = False
    if 'user_to_manage' not in st.session_state:
        st.session_state.user_to_manage = None
    if 'admin_email_verification_view' not in st.session_state:
        st.session_state.admin_email_verification_view = 'pending'
    if 'supabase' not in st.session_state:
        st.session_state.supabase = init_supabase()
    if 'strategy_data' not in st.session_state:
        st.session_state.strategy_data = {}

# -------------------------
# DATA PERSISTENCE SETUP
# -------------------------
def setup_data_persistence():
    """Set up periodic data saving to prevent data loss"""
    current_time = time.time()
    if current_time - st.session_state.last_save_time > 300:  # 5 minutes
        print("💾 Periodic data save...")
        if st.session_state.user:
            # Save user data
            user_data_key = f"{st.session_state.user['username']}_data"
            if user_data_key in st.session_state.user_data:
                save_user_data(st.session_state.user['username'], st.session_state.user_data[user_data_key])
            
            # Save strategy data
            save_data(st.session_state.strategy_data)
            
        st.session_state.last_save_time = current_time

# -------------------------
# PRODUCTION CONFIGURATION
# -------------------------
class Config:
    APP_NAME = "TradingAnalysis Pro"
    VERSION = "2.0.0"
    SUPPORT_EMAIL = "support@tradinganalysis.com"
    BUSINESS_NAME = "TradingAnalysis Inc."
    
    # Simplified Subscription Plans - Only Trial and Premium
    PLANS = {
        "trial": {"name": "7-Day Trial", "price": 0, "duration": 7, "strategies": 3, "max_sessions": 1},
        "premium": {"name": "Premium Plan", "price": 79, "duration": 30, "strategies": 15, "max_sessions": 3}
    }

# -------------------------
# STRATEGIES DEFINITION (15 Strategies)
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
# 5-DAY CYCLE SYSTEM
# -------------------------
def get_daily_strategies(analysis_date):
    """Get 3 strategies for the day based on 5-day cycle"""
    strategy_list = list(STRATEGIES.keys())
    start_date = date(2025, 8, 9)
    days_since_start = (analysis_date - start_date).days
    cycle_day = days_since_start % 5
    start_index = cycle_day * 3
    end_index = start_index + 3
    daily_strategies = strategy_list[start_index:end_index]
    return daily_strategies, cycle_day + 1

def sanitize_key(s: str):
    """Sanitize string for use as key"""
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
    )

# -------------------------
# SUPABASE DATA MANAGEMENT
# -------------------------
def load_data():
    """Load strategy analyses data from Supabase"""
    try:
        if not st.session_state.supabase:
            return {}
            
        response = st.session_state.supabase.table(SupabaseConfig.STRATEGY_ANALYSES_TABLE).select("*").execute()
        data = {}
        for row in response.data:
            strategy = row['strategy_name']
            indicator = row['indicator_name']
            if strategy not in data:
                data[strategy] = {}
            data[strategy][indicator] = {
                "note": row.get('note', ''),
                "status": row.get('status', 'Open'),
                "momentum": row.get('momentum', 'Not Defined'),
                "strategy_tag": row.get('strategy_tag', 'Neutral'),
                "analysis_date": row.get('analysis_date', ''),
                "last_modified": row.get('last_modified', ''),
                "username": row.get('username', '')
            }
        print(f"✅ Loaded strategy data from Supabase: {len(data)} strategies")
        return data
    except Exception as e:
        print(f"❌ Error loading strategy data from Supabase: {e}")
        return {}

def save_data(data):
    """Save strategy analyses data to Supabase"""
    try:
        if not st.session_state.supabase:
            return False
            
        # Convert the nested dictionary structure to flat rows for Supabase
        rows = []
        for strategy, indicators in data.items():
            for indicator_name, meta in indicators.items():
                rows.append({
                    "strategy_name": strategy,
                    "indicator_name": indicator_name,
                    "note": meta.get("note", ""),
                    "status": meta.get("status", "Open"),
                    "momentum": meta.get("momentum", "Not Defined"),
                    "strategy_tag": meta.get("strategy_tag", "Neutral"),
                    "analysis_date": meta.get("analysis_date", ""),
                    "last_modified": meta.get("last_modified", datetime.utcnow().isoformat()),
                    "username": meta.get("username", st.session_state.user['username'] if st.session_state.user else 'system')
                })
        
        # Upsert data (update if exists, insert if not)
        if rows:
            response = st.session_state.supabase.table(SupabaseConfig.STRATEGY_ANALYSES_TABLE).upsert(rows).execute()
            print(f"✅ Saved {len(rows)} strategy analysis records to Supabase")
        return True
    except Exception as e:
        print(f"❌ Error saving strategy data to Supabase: {e}")
        return False

def load_user_data(username):
    """Load user-specific data from Supabase"""
    try:
        if not st.session_state.supabase:
            return {
                "saved_analyses": {},
                "favorite_strategies": [],
                "performance_history": [],
                "recent_signals": []
            }
            
        response = st.session_state.supabase.table(SupabaseConfig.USER_DATA_TABLE).select("*").eq("username", username).execute()
        user_data = {
            "saved_analyses": {},
            "favorite_strategies": [],
            "performance_history": [],
            "recent_signals": []
        }
        
        if response.data:
            data = response.data[0].get('user_data', {})
            user_data.update(data)
        
        print(f"✅ Loaded user data for {username}")
        return user_data
    except Exception as e:
        print(f"❌ Error loading user data from Supabase: {e}")
        return {
            "saved_analyses": {},
            "favorite_strategies": [],
            "performance_history": [],
            "recent_signals": []
        }

def save_user_data(username, user_data):
    """Save user-specific data to Supabase"""
    try:
        if not st.session_state.supabase:
            return False
            
        data = {
            "username": username,
            "user_data": user_data,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        response = st.session_state.supabase.table(SupabaseConfig.USER_DATA_TABLE).upsert(data).execute()
        print(f"✅ Saved user data for {username}")
        return True
    except Exception as e:
        print(f"❌ Error saving user data to Supabase: {e}")
        return False

def generate_filtered_csv_bytes(data, target_date):
    """Generate CSV data filtered by date"""
    rows = []
    target_str = target_date.strftime("%Y-%m-%d")
    for strat, inds in data.items():
        for ind_name, meta in inds.items():
            if meta.get("analysis_date") == target_str:
                rows.append({
                    "Strategy": strat,
                    "Indicator": ind_name,
                    "Note": meta.get("note", ""),
                    "Status": meta.get("status", ""),
                    "Momentum": meta.get("momentum", "Not Defined"),
                    "Tag": meta.get("strategy_tag", "Neutral"),
                    "Analysis_Date": meta.get("analysis_date", ""),
                    "Last_Modified": meta.get("last_modified", "")
                })
    df = pd.DataFrame(rows) if rows else pd.DataFrame(columns=["Strategy","Indicator","Note","Status","Momentum","Tag","Analysis_Date","Last_Modified"])
    return df.to_csv(index=False).encode("utf-8")

# -------------------------
# SUPABASE USER MANAGEMENT
# -------------------------
class UserManager:
    def __init__(self):
        self.supabase = st.session_state.supabase
        self.users = {}
        self.analytics = {}
        self.load_data()
    
    def load_data(self):
        """Load users and analytics data from Supabase"""
        try:
            if not self.supabase:
                self._create_default_data()
                return
                
            # Load users
            response = self.supabase.table(SupabaseConfig.USERS_TABLE).select("*").execute()
            self.users = {user['username']: user for user in response.data}
            print(f"✅ Loaded {len(self.users)} users from Supabase")
            
            # Load analytics
            response = self.supabase.table(SupabaseConfig.ANALYTICS_TABLE).select("*").eq("id", 1).execute()
            if response.data:
                self.analytics = response.data[0]['analytics_data']
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
                    "email_verifications": []
                }
                self.save_analytics()
                
        except Exception as e:
            print(f"❌ Error loading data from Supabase: {e}")
            self._create_default_data()
    
    def _create_default_data(self):
        """Create default data structure"""
        self.users = {}
        self.analytics = {
            "total_logins": 0,
            "active_users": 0,
            "revenue_today": 0,
            "user_registrations": [],
            "login_history": [],
            "deleted_users": [],
            "plan_changes": [],
            "password_changes": [],
            "email_verifications": []
        }
        self.create_default_admin()
    
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
            "subscription_id": "admin_account",
            "email_verified": True,
            "verification_date": datetime.now().isoformat()
        }
        self.save_users()
        print("✅ Created default admin account")
    
    def hash_password(self, password):
        """Secure password hashing"""
        salt = "trading-analysis-salt-2024"
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def save_users(self):
        """Save users to Supabase"""
        try:
            if not self.supabase:
                return False
                
            # Convert users to list for Supabase
            users_list = []
            for username, user_data in self.users.items():
                user_data['username'] = username
                users_list.append(user_data)
            
            response = self.supabase.table(SupabaseConfig.USERS_TABLE).upsert(users_list).execute()
            print(f"✅ Saved {len(users_list)} users to Supabase")
            return True
        except Exception as e:
            print(f"❌ Error saving users to Supabase: {e}")
            return False
    
    def save_analytics(self):
        """Save analytics data to Supabase"""
        try:
            if not self.supabase:
                return False
                
            data = {
                "id": 1,  # Single analytics record
                "analytics_data": self.analytics,
                "last_updated": datetime.now().isoformat()
            }
            response = self.supabase.table(SupabaseConfig.ANALYTICS_TABLE).upsert(data).execute()
            return True
        except Exception as e:
            print(f"❌ Error saving analytics to Supabase: {e}")
            return False
    
    def register_user(self, username, password, name, email, plan="trial"):
        """Register new user with Supabase persistence"""
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
            "payment_status": "active" if plan == "trial" else "pending",
            "email_verified": False,
            "verification_date": None,
            "verification_notes": "",
            "verification_admin": None
        }
        
        # Update analytics
        self.analytics["user_registrations"].append({
            "username": username,
            "plan": plan,
            "timestamp": datetime.now().isoformat()
        })
        
        # Save to Supabase
        users_saved = self.save_users()
        analytics_saved = self.save_analytics()
        
        if users_saved and analytics_saved:
            print(f"✅ Successfully registered user: {username}")
            return True, f"Account created successfully! {plan_config['name']} activated."
        else:
            # Remove the user if save failed
            if username in self.users:
                del self.users[username]
            return False, "Error saving user data. Please try again."
    
    def authenticate_user(self, username, password):
        """Authenticate user login"""
        if username not in self.users:
            return False, "Invalid username or password"
        
        user = self.users[username]
        
        if not user.get('is_active', True):
            return False, "Account is deactivated"
        
        if user['password_hash'] != self.hash_password(password):
            return False, "Invalid username or password"
        
        # Check session limits
        if user['active_sessions'] >= user['max_sessions']:
            return False, "Maximum concurrent sessions reached. Please try again later."
        
        # Update user stats
        user['last_login'] = datetime.now().isoformat()
        user['login_count'] = user.get('login_count', 0) + 1
        user['active_sessions'] = user.get('active_sessions', 0) + 1
        
        # Update analytics
        self.analytics["login_history"].append({
            "username": username,
            "timestamp": datetime.now().isoformat()
        })
        self.analytics["total_logins"] = self.analytics.get("total_logins", 0) + 1
        
        self.save_users()
        self.save_analytics()
        
        return True, user
    
    def logout(self, username):
        """Handle user logout"""
        if username in self.users:
            self.users[username]['active_sessions'] = max(0, self.users[username].get('active_sessions', 1) - 1)
            self.save_users()
    
    def update_user_plan(self, username, new_plan):
        """Update user subscription plan"""
        if username not in self.users:
            return False, "User not found"
        
        old_plan = self.users[username]['plan']
        plan_config = Config.PLANS.get(new_plan)
        
        if not plan_config:
            return False, "Invalid plan"
        
        # Update user plan
        self.users[username]['plan'] = new_plan
        self.users[username]['max_sessions'] = plan_config['max_sessions']
        
        # Extend expiry date
        current_expiry = datetime.strptime(self.users[username]['expires'], "%Y-%m-%d").date()
        new_expiry = current_expiry + timedelta(days=plan_config['duration'])
        self.users[username]['expires'] = new_expiry.strftime("%Y-%m-%d")
        
        # Record plan change
        self.analytics["plan_changes"].append({
            "username": username,
            "from_plan": old_plan,
            "to_plan": new_plan,
            "timestamp": datetime.now().isoformat()
        })
        
        self.save_users()
        self.save_analytics()
        
        return True, f"Plan updated to {plan_config['name']}"
    
    def delete_user(self, username):
        """Delete user account"""
        if username not in self.users:
            return False, "User not found"
        
        user_data = self.users[username]
        
        # Record deletion
        self.analytics["deleted_users"].append({
            "username": username,
            "plan": user_data['plan'],
            "timestamp": datetime.now().isoformat()
        })
        
        # Remove user
        del self.users[username]
        
        # Delete user data from Supabase
        try:
            if self.supabase:
                self.supabase.table(SupabaseConfig.USER_DATA_TABLE).delete().eq("username", username).execute()
                self.supabase.table(SupabaseConfig.STRATEGY_ANALYSES_TABLE).delete().eq("username", username).execute()
        except Exception as e:
            print(f"⚠️ Error cleaning up user data: {e}")
        
        self.save_users()
        self.save_analytics()
        
        return True, f"User {username} deleted successfully"
    
    def change_password(self, username, new_password):
        """Change user password"""
        if username not in self.users:
            return False, "User not found"
        
        if len(new_password) < 8:
            return False, "Password must be at least 8 characters"
        
        self.users[username]['password_hash'] = self.hash_password(new_password)
        
        # Record password change
        self.analytics["password_changes"].append({
            "username": username,
            "timestamp": datetime.now().isoformat()
        })
        
        self.save_users()
        self.save_analytics()
        
        return True, "Password changed successfully"
    
    def verify_email(self, username, admin_username, notes=""):
        """Verify user email (admin function)"""
        if username not in self.users:
            return False, "User not found"
        
        self.users[username]['email_verified'] = True
        self.users[username]['verification_date'] = datetime.now().isoformat()
        self.users[username]['verification_admin'] = admin_username
        self.users[username]['verification_notes'] = notes
        
        # Record verification
        self.analytics["email_verifications"].append({
            "username": username,
            "admin": admin_username,
            "timestamp": datetime.now().isoformat(),
            "notes": notes
        })
        
        self.save_users()
        self.save_analytics()
        
        return True, f"Email verified for {username}"
    
    def get_user_stats(self):
        """Get user statistics for admin dashboard"""
        stats = {
            "total_users": len(self.users),
            "active_trials": 0,
            "premium_users": 0,
            "admin_users": 0,
            "verified_emails": 0,
            "unverified_emails": 0,
            "active_sessions": 0
        }
        
        for user in self.users.values():
            if user['plan'] == 'trial':
                stats["active_trials"] += 1
            elif user['plan'] == 'premium':
                stats["premium_users"] += 1
            elif user['plan'] == 'admin':
                stats["admin_users"] += 1
            
            if user.get('email_verified'):
                stats["verified_emails"] += 1
            else:
                stats["unverified_emails"] += 1
            
            stats["active_sessions"] += user.get('active_sessions', 0)
        
        return stats

# Initialize user manager
user_manager = UserManager()

# -------------------------
# AUTHENTICATION UI
# -------------------------
def render_login():
    """Render login/registration interface"""
    st.markdown(f'<h1 class="main-header">🚀 {Config.APP_NAME}</h1>', unsafe_allow_html=True)
    
    tab1, tab2 = st.tabs(["🔐 Login", "📝 Register"])
    
    with tab1:
        with st.form("login_form"):
            st.subheader("User Login")
            username = st.text_input("Username", placeholder="Enter your username")
            password = st.text_input("Password", type="password", placeholder="Enter your password")
            
            col1, col2 = st.columns([3, 1])
            with col1:
                login_btn = st.form_submit_button("🚀 Login", use_container_width=True)
            with col2:
                admin_btn = st.form_submit_button("👑 Admin", use_container_width=True)
            
            if login_btn or admin_btn:
                if not username or not password:
                    st.error("Please enter both username and password")
                else:
                    success, result = user_manager.authenticate_user(username, password)
                    if success:
                        st.session_state.user = result
                        st.session_state.strategy_data = load_data()
                        st.success(f"Welcome back, {result['name']}!")
                        time.sleep(1)
                        st.rerun()
                    else:
                        st.error(result)
    
    with tab2:
        with st.form("register_form"):
            st.subheader("Create New Account")
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Choose Username", placeholder="3-20 characters")
                new_name = st.text_input("Full Name", placeholder="Your full name")
            with col2:
                new_password = st.text_input("Password", type="password", placeholder="Min. 8 characters")
                new_email = st.text_input("Email Address", placeholder="your@email.com")
            
            plan_choice = st.selectbox(
                "Subscription Plan",
                options=list(Config.PLANS.keys()),
                format_func=lambda x: f"{Config.PLANS[x]['name']} - ${Config.PLANS[x]['price']}/month"
            )
            
            if st.form_submit_button("✨ Create Account", use_container_width=True):
                if not all([new_username, new_password, new_name, new_email]):
                    st.error("Please fill in all fields")
                else:
                    success, message = user_manager.register_user(new_username, new_password, new_name, new_email, plan_choice)
                    if success:
                        st.success(message)
                        # Auto-login after registration
                        success, result = user_manager.authenticate_user(new_username, new_password)
                        if success:
                            st.session_state.user = result
                            st.session_state.strategy_data = load_data()
                            st.rerun()
                    else:
                        st.error(message)

# -------------------------
# USER DASHBOARD
# -------------------------
def render_user_dashboard():
    """Redesigned trading dashboard with Supabase integration"""
    user = st.session_state.user
    
    # Load user-specific data from Supabase
    user_data_key = f"{user['username']}_data"
    if user_data_key not in st.session_state.user_data:
        st.session_state.user_data[user_data_key] = load_user_data(user['username'])
    
    data = st.session_state.user_data[user_data_key]
    
    # Date navigation
    start_date = date(2025, 8, 9)
    query_params = st.query_params
    current_date_str = query_params.get("date", "")
    
    if current_date_str:
        try:
            analysis_date = datetime.strptime(current_date_str, "%Y-%m-%d").date()
            st.session_state.analysis_date = analysis_date
        except ValueError:
            analysis_date = st.session_state.get('analysis_date', date.today())
    else:
        analysis_date = st.session_state.get('analysis_date', date.today())
    
    if analysis_date < start_date:
        analysis_date = start_date
        st.session_state.analysis_date = start_date
    
    # Sidebar
    with st.sidebar:
        st.title("🎛️ Control Panel")
        st.markdown("---")
        st.write(f"**👤 {user['name']}**")
        plan_display = Config.PLANS.get(user['plan'], {}).get('name', user['plan'].title())
        st.caption(f"🚀 {plan_display}")
        
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.progress(min(1.0, days_left / 30), text=f"📅 {days_left} days remaining")
        
        st.markdown("---")
        st.subheader("📅 5-Day Cycle")
        st.markdown(f"**Current Date:** {analysis_date.strftime('%m/%d/%Y')}")
        
        col1, col2 = st.columns(2)
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
        
        if st.button("🔄 Today", use_container_width=True, key="today_btn"):
            st.query_params["date"] = date.today().strftime("%Y-%m-%d")
            st.rerun()
        
        daily_strategies, cycle_day = get_daily_strategies(analysis_date)
        st.info(f"**Day {cycle_day} of 5-day cycle**")
        
        st.markdown("**Today's Focus:**")
        for strategy in daily_strategies:
            st.write(f"• {strategy}")
        
        st.markdown("---")
        selected_strategy = st.selectbox("Choose Strategy:", daily_strategies, key="strategy_selector")
        st.markdown("---")
        
        st.subheader("📊 Navigation")
        nav_options = {
            "📈 Trading Dashboard": "main",
            "📝 Strategy Notes": "notes", 
            "⚙️ Account Settings": "settings"
        }
        
        for label, view in nav_options.items():
            if st.button(label, use_container_width=True, key=f"nav_{view}"):
                st.session_state.dashboard_view = view
                st.rerun()
        
        st.markdown("---")
        csv_bytes = generate_filtered_csv_bytes(st.session_state.strategy_data, analysis_date)
        st.subheader("📄 Export Data")
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_bytes,
            file_name=f"strategy_analyses_{analysis_date.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.markdown("---")
        if st.button("🚪 Secure Logout", use_container_width=True):
            # Save user data before logout
            save_user_data(user['username'], data)
            user_manager.logout(user['username'])
            st.session_state.user = None
            st.rerun()
    
    # Main dashboard content
    current_view = st.session_state.get('dashboard_view', 'main')
    
    if st.session_state.get('show_settings'):
        render_account_settings()
    elif st.session_state.get('show_upgrade'):
        render_upgrade_plans()
    elif current_view == 'notes':
        render_strategy_notes(st.session_state.strategy_data, daily_strategies, cycle_day, analysis_date, selected_strategy)
    elif current_view == 'settings':
        render_account_settings()
    else:
        render_trading_dashboard(data, user, daily_strategies, cycle_day, analysis_date, selected_strategy)

def render_trading_dashboard(data, user, daily_strategies, cycle_day, analysis_date, selected_strategy):
    """Main trading dashboard view"""
    st.title("📈 Trading Analysis Dashboard")
    
    # Header metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Cycle Day", f"Day {cycle_day}/5")
    with col2:
        st.metric("Active Strategies", len(daily_strategies))
    with col3:
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Plan Days Left", days_left)
    with col4:
        st.metric("Analysis Date", analysis_date.strftime("%m/%d/%Y"))
    
    st.markdown("---")
    
    # Strategy Overview
    st.subheader(f"🎯 Today's Strategy: {selected_strategy}")
    
    # Strategy indicators
    indicators = STRATEGIES[selected_strategy]
    
    # Check for existing analysis
    existing_analysis = st.session_state.strategy_data.get(selected_strategy, {})
    
    if existing_analysis:
        st.info(f"📊 Found {len(existing_analysis)} analyzed indicators for this strategy")
        
        # Show analysis summary
        status_counts = {}
        for ind_data in existing_analysis.values():
            status = ind_data.get('status', 'Open')
            status_counts[status] = status_counts.get(status, 0) + 1
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Done", status_counts.get('Done', 0))
        with col2:
            st.metric("In Progress", status_counts.get('In Progress', 0))
        with col3:
            st.metric("Open", status_counts.get('Open', 0))
        with col4:
            st.metric("Skipped", status_counts.get('Skipped', 0))
    else:
        st.warning("No analysis recorded for this strategy yet. Click 'Strategy Notes' to start analyzing.")
    
    # Quick actions
    st.markdown("---")
    st.subheader("🚀 Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("📝 Analyze Strategy", use_container_width=True):
            st.session_state.dashboard_view = 'notes'
            st.rerun()
    with col2:
        if st.button("⭐ Favorite Strategy", use_container_width=True):
            if selected_strategy not in data['favorite_strategies']:
                data['favorite_strategies'].append(selected_strategy)
                save_user_data(user['username'], data)
                st.success(f"Added {selected_strategy} to favorites!")
            else:
                st.info("Strategy already in favorites")
    with col3:
        if st.button("📊 View Analytics", use_container_width=True):
            st.session_state.dashboard_view = 'analytics'
            st.rerun()
    
    # Recent activity
    if data.get('recent_signals'):
        st.markdown("---")
        st.subheader("📋 Recent Signals")
        for signal in data['recent_signals'][-5:]:
            st.write(f"• {signal}")

def render_strategy_notes(strategy_data, daily_strategies, cycle_day, analysis_date, selected_strategy):
    """Detailed strategy notes interface with Supabase saving"""
    st.title("📝 Strategy Analysis Notes")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.subheader(f"Day {cycle_day} - {selected_strategy}")
    with col2:
        st.metric("Analysis Date", analysis_date.strftime("%m/%d/%Y"))
    with col3:
        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            st.session_state.dashboard_view = 'main'
            st.rerun()
    
    st.markdown("---")
    
    # Notes Form
    with st.form("detailed_notes_form"):
        st.subheader(f"Detailed Analysis - {selected_strategy}")
        
        existing_data = strategy_data.get(selected_strategy, {})
        current_strategy_tag = next(iter(existing_data.values()), {}).get("strategy_tag", "Neutral")
        current_strategy_type = next(iter(existing_data.values()), {}).get("momentum", "Not Defined")
        
        col1, col2 = st.columns(2)
        with col1:
            strategy_tag = st.selectbox("Strategy Tag:", ["Neutral", "Buy", "Sell"], 
                                      index=["Neutral","Buy","Sell"].index(current_strategy_tag))
        with col2:
            strategy_type = st.selectbox("Strategy Type:", ["Momentum", "Extreme", "Not Defined"], 
                                       index=["Momentum","Extreme","Not Defined"].index(current_strategy_type))
        
        st.markdown("---")
        
        indicators = STRATEGIES[selected_strategy]
        col_objs = st.columns(3)
        
        for i, indicator in enumerate(indicators):
            col = col_objs[i % 3]
            key_note = f"note__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"
            key_status = f"status__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"
            
            existing = existing_data.get(indicator, {})
            default_note = existing.get("note", "")
            default_status = existing.get("status", "Open")
            
            with col.expander(f"**{indicator}**", expanded=False):
                st.text_area(
                    f"Analysis Notes", 
                    value=default_note, 
                    key=key_note, 
                    height=140,
                    placeholder=f"Enter analysis for {indicator}..."
                )
                st.selectbox(
                    "Status", 
                    ["Open", "In Progress", "Done", "Skipped"], 
                    index=["Open", "In Progress", "Done", "Skipped"].index(default_status) if default_status in ["Open", "In Progress", "Done", "Skipped"] else 0,
                    key=key_status
                )
        
        submitted = st.form_submit_button("💾 Save All Notes", use_container_width=True)
        if submitted:
            if selected_strategy not in strategy_data:
                strategy_data[selected_strategy] = {}
            
            for indicator in indicators:
                key_note = f"note__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"
                key_status = f"status__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"
                
                strategy_data[selected_strategy][indicator] = {
                    "note": st.session_state.get(key_note, ""),
                    "status": st.session_state.get(key_status, "Open"),
                    "momentum": strategy_type,
                    "strategy_tag": strategy_tag,
                    "analysis_date": analysis_date.strftime("%Y-%m-%d"),
                    "last_modified": datetime.utcnow().isoformat() + "Z",
                    "username": st.session_state.user['username']
                }
            
            # Save to Supabase
            if save_data(strategy_data):
                st.success("✅ All notes saved successfully to database!")
                st.session_state.strategy_data = strategy_data
            else:
                st.error("❌ Failed to save notes to database")
    
    # Display saved analyses
    if selected_strategy in strategy_data and strategy_data[selected_strategy]:
        st.markdown("---")
        st.subheader("💾 Saved Analysis Summary")
        
        analysis_df = []
        for indicator, meta in strategy_data[selected_strategy].items():
            analysis_df.append({
                "Indicator": indicator,
                "Status": meta.get("status", "Open"),
                "Note Preview": (meta.get("note", "")[:50] + "...") if len(meta.get("note", "")) > 50 else meta.get("note", ""),
                "Last Modified": meta.get("last_modified", "")[:19]
            })
        
        if analysis_df:
            st.dataframe(pd.DataFrame(analysis_df), use_container_width=True)

def render_account_settings():
    """User account settings page"""
    st.title("⚙️ Account Settings")
    
    user = st.session_state.user
    user_data_key = f"{user['username']}_data"
    data = st.session_state.user_data[user_data_key]
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("👤 Profile Information")
        st.info(f"**Username:** {user['username']}")
        st.info(f"**Email:** {user['email']}")
        st.info(f"**Plan:** {Config.PLANS.get(user['plan'], {}).get('name', user['plan'].title())}")
        st.info(f"**Account Created:** {user['created'][:10]}")
        st.info(f"**Expiry Date:** {user['expires']}")
        
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        if days_left <= 7:
            st.warning(f"Your plan expires in {days_left} days. Consider upgrading to continue access.")
        
        st.subheader("🔒 Security")
        if st.button("🔄 Change Password", use_container_width=True):
            st.session_state.show_password_change = True
        
        if st.session_state.show_password_change:
            with st.form("change_password_form"):
                new_password = st.text_input("New Password", type="password", placeholder="Minimum 8 characters")
                confirm_password = st.text_input("Confirm Password", type="password", placeholder="Re-enter new password")
                
                if st.form_submit_button("💾 Update Password", use_container_width=True):
                    if new_password != confirm_password:
                        st.error("Passwords do not match")
                    elif len(new_password) < 8:
                        st.error("Password must be at least 8 characters")
                    else:
                        success, message = user_manager.change_password(user['username'], new_password)
                        if success:
                            st.success(message)
                            st.session_state.show_password_change = False
                            st.rerun()
                        else:
                            st.error(message)
    
    with col2:
        st.subheader("🚀 Plan Options")
        
        current_plan = user['plan']
        for plan_id, plan_config in Config.PLANS.items():
            with st.container():
                st.write(f"**{plan_config['name']}**")
                st.write(f"${plan_config['price']}/month")
                st.write(f"{plan_config['strategies']} strategies")
                st.write(f"{plan_config['max_sessions']} sessions")
                
                if plan_id == current_plan:
                    st.success("Current Plan")
                elif plan_id == "premium" and current_plan == "trial":
                    if st.button(f"Upgrade to {plan_config['name']}", key=f"upgrade_{plan_id}", use_container_width=True):
                        success, message = user_manager.update_user_plan(user['username'], plan_id)
                        if success:
                            st.session_state.user = user_manager.users[user['username']]
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
        
        st.markdown("---")
        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            st.session_state.dashboard_view = 'main'
            st.session_state.show_settings = False
            st.rerun()

def render_upgrade_plans():
    """Plan upgrade interface"""
    st.title("🚀 Upgrade Your Plan")
    
    user = st.session_state.user
    current_plan = user['plan']
    
    st.warning(f"You are currently on the {Config.PLANS.get(current_plan, {}).get('name', current_plan)} plan.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        for plan_id, plan_config in Config.PLANS.items():
            if plan_id != current_plan:
                with st.container():
                    st.subheader(plan_config['name'])
                    st.write(f"## ${plan_config['price']}")
                    st.write("/month")
                    st.write(f"✅ {plan_config['strategies']} Strategies")
                    st.write(f"✅ {plan_config['max_sessions']} Concurrent Sessions")
                    st.write(f"✅ {plan_config['duration']} Days Access")
                    
                    if st.button(f"Upgrade to {plan_config['name']}", key=f"upgrade_{plan_id}", use_container_width=True):
                        success, message = user_manager.update_user_plan(user['username'], plan_id)
                        if success:
                            st.session_state.user = user_manager.users[user['username']]
                            st.success(f"🎉 {message}")
                            time.sleep(2)
                            st.session_state.show_upgrade = False
                            st.rerun()
                        else:
                            st.error(message)
    
    with col2:
        st.info("""
        **💎 Premium Benefits:**
        
        - Access to all 15 trading strategies
        - 3 concurrent sessions
        - Priority email support
        - Advanced analytics
        - Custom strategy builder
        - Export capabilities
        """)
    
    st.markdown("---")
    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        st.session_state.show_upgrade = False
        st.rerun()

# -------------------------
# ADMIN DASHBOARD
# -------------------------
def render_admin_dashboard():
    """Admin dashboard for user management"""
    st.title("👑 Administration Dashboard")
    
    # Admin navigation
    admin_views = {
        "📊 Overview": "overview",
        "👥 User Management": "users", 
        "📈 Analytics": "analytics",
        "✅ Email Verification": "verification"
    }
    
    cols = st.columns(len(admin_views))
    for i, (label, view) in enumerate(admin_views.items()):
        with cols[i]:
            if st.button(label, use_container_width=True, key=f"admin_nav_{view}"):
                st.session_state.admin_view = view
                st.rerun()
    
    st.markdown("---")
    
    # Render selected admin view
    if st.session_state.admin_view == "overview":
        render_admin_overview()
    elif st.session_state.admin_view == "users":
        render_user_management()
    elif st.session_state.admin_view == "analytics":
        render_admin_analytics()
    elif st.session_state.admin_view == "verification":
        render_email_verification()

def render_admin_overview():
    """Admin overview dashboard"""
    stats = user_manager.get_user_stats()
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", stats["total_users"])
    with col2:
        st.metric("Active Trials", stats["active_trials"])
    with col3:
        st.metric("Premium Users", stats["premium_users"])
    with col4:
        st.metric("Active Sessions", stats["active_sessions"])
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Verified Emails", stats["verified_emails"])
    with col2:
        st.metric("Unverified Emails", stats["unverified_emails"])
    
    st.markdown("---")
    
    # Recent activity
    st.subheader("Recent Activity")
    
    # Recent registrations
    recent_registrations = user_manager.analytics.get("user_registrations", [])[-10:]
    if recent_registrations:
        st.write("**Recent Registrations:**")
        for reg in reversed(recent_registrations):
            st.write(f"- {reg['username']} ({reg['plan']}) - {reg['timestamp'][:16]}")
    else:
        st.info("No recent registrations")
    
    # Recent logins
    recent_logins = user_manager.analytics.get("login_history", [])[-10:]
    if recent_logins:
        st.write("**Recent Logins:**")
        for login in reversed(recent_logins):
            st.write(f"- {login['username']} - {login['timestamp'][:16]}")
    
    # Quick actions
    st.markdown("---")
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True):
            user_manager.load_data()
            st.rerun()
    with col2:
        if st.button("📧 Email Verification", use_container_width=True):
            st.session_state.admin_view = "verification"
            st.rerun()
    with col3:
        if st.button("👥 User Management", use_container_width=True):
            st.session_state.admin_view = "users"
            st.rerun()

def render_user_management():
    """User management interface"""
    st.subheader("👥 User Management")
    
    # Search and filter
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        search_term = st.text_input("🔍 Search users", placeholder="Username, email, or name")
    with col2:
        plan_filter = st.selectbox("Filter by plan", ["All", "trial", "premium", "admin"])
    with col3:
        verification_filter = st.selectbox("Email status", ["All", "Verified", "Unverified"])
    
    # User list
    st.markdown("---")
    
    users_to_display = []
    for username, user_data in user_manager.users.items():
        if search_term and search_term.lower() not in username.lower() and search_term.lower() not in user_data.get('email', '').lower() and search_term.lower() not in user_data.get('name', '').lower():
            continue
        
        if plan_filter != "All" and user_data.get('plan') != plan_filter:
            continue
            
        if verification_filter == "Verified" and not user_data.get('email_verified'):
            continue
        elif verification_filter == "Unverified" and user_data.get('email_verified'):
            continue
            
        users_to_display.append((username, user_data))
    
    if not users_to_display:
        st.info("No users match the current filters")
        return
    
    for username, user_data in users_to_display:
        with st.expander(f"👤 {username} - {user_data.get('name', 'N/A')} ({user_data.get('plan', 'N/A')})"):
            col1, col2 = st.columns([3, 1])
            
            with col1:
                st.write(f"**Email:** {user_data.get('email', 'N/A')}")
                st.write(f"**Plan:** {user_data.get('plan', 'N/A')}")
                st.write(f"**Created:** {user_data.get('created', 'N/A')[:10]}")
                st.write(f"**Expires:** {user_data.get('expires', 'N/A')}")
                st.write(f"**Last Login:** {user_data.get('last_login', 'Never')[:19] if user_data.get('last_login') else 'Never'}")
                st.write(f"**Login Count:** {user_data.get('login_count', 0)}")
                st.write(f"**Active Sessions:** {user_data.get('active_sessions', 0)}")
                
                # Email verification status
                if user_data.get('email_verified'):
                    st.success("✅ Email Verified")
                    if user_data.get('verification_date'):
                        st.write(f"Verified on: {user_data.get('verification_date')[:10]}")
                else:
                    st.error("❌ Email Not Verified")
            
            with col2:
                # Plan management
                new_plan = st.selectbox(
                    "Change Plan", 
                    ["trial", "premium", "admin"],
                    index=["trial", "premium", "admin"].index(user_data.get('plan', 'trial')),
                    key=f"plan_{username}"
                )
                
                if new_plan != user_data.get('plan'):
                    if st.button("Update Plan", key=f"update_plan_{username}"):
                        success, message = user_manager.update_user_plan(username, new_plan)
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                # Email verification
                if not user_data.get('email_verified'):
                    if st.button("Verify Email", key=f"verify_{username}"):
                        success, message = user_manager.verify_email(username, st.session_state.user['username'], "Manual verification by admin")
                        if success:
                            st.success(message)
                            st.rerun()
                        else:
                            st.error(message)
                
                # Delete user
                if st.button("🗑️ Delete", key=f"delete_{username}"):
                    st.session_state.user_to_delete = username
                    st.session_state.show_delete_confirmation = True
                    st.rerun()
    
    # Delete confirmation
    if st.session_state.show_delete_confirmation and st.session_state.user_to_delete:
        st.markdown("---")
        st.warning(f"⚠️ Are you sure you want to delete user '{st.session_state.user_to_delete}'? This action cannot be undone.")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ Confirm Delete", use_container_width=True):
                success, message = user_manager.delete_user(st.session_state.user_to_delete)
                if success:
                    st.success(message)
                else:
                    st.error(message)
                st.session_state.show_delete_confirmation = False
                st.session_state.user_to_delete = None
                st.rerun()
        with col2:
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.show_delete_confirmation = False
                st.session_state.user_to_delete = None
                st.rerun()

def render_admin_analytics():
    """Admin analytics dashboard"""
    st.subheader("📈 System Analytics")
    
    analytics = user_manager.analytics
    
    # Key metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Logins", analytics.get("total_logins", 0))
    with col2:
        st.metric("User Registrations", len(analytics.get("user_registrations", [])))
    with col3:
        st.metric("Plan Changes", len(analytics.get("plan_changes", [])))
    
    # Registration trends
    st.markdown("---")
    st.subheader("User Registration Trends")
    
    registrations_by_date = {}
    for reg in analytics.get("user_registrations", []):
        date_str = reg['timestamp'][:10]
        registrations_by_date[date_str] = registrations_by_date.get(date_str, 0) + 1
    
    if registrations_by_date:
        reg_df = pd.DataFrame(list(registrations_by_date.items()), columns=['Date', 'Registrations'])
        reg_df = reg_df.sort_values('Date').tail(30)  # Last 30 days
        st.line_chart(reg_df.set_index('Date'))
    else:
        st.info("No registration data available")
    
    # Plan distribution
    st.markdown("---")
    st.subheader("Plan Distribution")
    
    plan_counts = {}
    for user in user_manager.users.values():
        plan = user.get('plan', 'unknown')
        plan_counts[plan] = plan_counts.get(plan, 0) + 1
    
    if plan_counts:
        plan_df = pd.DataFrame(list(plan_counts.items()), columns=['Plan', 'Count'])
        st.bar_chart(plan_df.set_index('Plan'))
    
    # Recent activity log
    st.markdown("---")
    st.subheader("Recent Activity Log")
    
    all_activities = []
    
    # Add registrations
    for reg in analytics.get("user_registrations", []):
        all_activities.append({
            "timestamp": reg['timestamp'],
            "type": "Registration",
            "user": reg['username'],
            "details": f"Registered for {reg['plan']} plan"
        })
    
    # Add plan changes
    for change in analytics.get("plan_changes", []):
        all_activities.append({
            "timestamp": change['timestamp'],
            "type": "Plan Change",
            "user": change['username'],
            "details": f"Changed from {change['from_plan']} to {change['to_plan']}"
        })
    
    # Add email verifications
    for verification in analytics.get("email_verifications", []):
        all_activities.append({
            "timestamp": verification['timestamp'],
            "type": "Email Verification",
            "user": verification['username'],
            "details": f"Verified by {verification['admin']}"
        })
    
    # Sort by timestamp and get recent
    all_activities.sort(key=lambda x: x['timestamp'], reverse=True)
    recent_activities = all_activities[:20]
    
    if recent_activities:
        for activity in recent_activities:
            st.write(f"**{activity['type']}** - {activity['timestamp'][:16]} - {activity['user']}")
            st.caption(activity['details'])
    else:
        st.info("No recent activity")

def render_email_verification():
    """Email verification management"""
    st.subheader("✅ Email Verification Management")
    
    # Tabs for different views
    tab1, tab2 = st.tabs(["📋 Pending Verification", "✅ Verified Users"])
    
    with tab1:
        st.write("**Users Pending Email Verification**")
        
        pending_users = []
        for username, user_data in user_manager.users.items():
            if not user_data.get('email_verified') and user_data.get('plan') != 'admin':
                pending_users.append((username, user_data))
        
        if not pending_users:
            st.success("🎉 All users have verified their email addresses!")
        else:
            st.info(f"Found {len(pending_users)} users pending verification")
            
            for username, user_data in pending_users:
                with st.expander(f"👤 {username} - {user_data.get('email', 'N/A')}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Name:** {user_data.get('name', 'N/A')}")
                        st.write(f"**Plan:** {user_data.get('plan', 'N/A')}")
                        st.write(f"**Registered:** {user_data.get('created', 'N/A')[:10]}")
                        st.write(f"**Last Login:** {user_data.get('last_login', 'Never')[:19] if user_data.get('last_login') else 'Never'}")
                    
                    with col2:
                        if st.button("Verify Email", key=f"verify_pending_{username}", use_container_width=True):
                            success, message = user_manager.verify_email(username, st.session_state.user['username'], "Manual verification by admin")
                            if success:
                                st.success(message)
                                st.rerun()
                            else:
                                st.error(message)
                        
                        if st.button("Send Reminder", key=f"remind_{username}", use_container_width=True):
                            st.info(f"Reminder email would be sent to {user_data.get('email')}")
                            # In a real implementation, you would integrate with an email service here
    
    with tab2:
        st.write("**Verified Users**")
        
        verified_users = []
        for username, user_data in user_manager.users.items():
            if user_data.get('email_verified'):
                verified_users.append((username, user_data))
        
        if verified_users:
            for username, user_data in verified_users:
                with st.expander(f"👤 {username} - {user_data.get('email', 'N/A')}"):
                    st.write(f"**Name:** {user_data.get('name', 'N/A')}")
                    st.write(f"**Plan:** {user_data.get('plan', 'N/A')}")
                    st.write(f"**Verified on:** {user_data.get('verification_date', 'N/A')[:10]}")
                    st.write(f"**Verified by:** {user_data.get('verification_admin', 'System')}")
                    
                    if user_data.get('verification_notes'):
                        st.write(f"**Notes:** {user_data.get('verification_notes')}")
        else:
            st.info("No verified users found")

# -------------------------
# MAIN APPLICATION
# -------------------------
def main():
    init_session()
    
    # Setup data persistence
    setup_data_persistence()
    
    # CSS
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
    .verification-badge {
        font-size: 0.7rem !important;
        padding: 2px 8px !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        min-width: 60px !important;
        display: inline-block !important;
        text-align: center !important;
        border: 1px solid !important;
    }
    .verified-badge {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        border-color: #047857 !important;
    }
    .unverified-badge {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
        color: white;
        border-color: #B91C1C !important;
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
