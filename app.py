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
from PIL import Image

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
    if 'admin_dashboard_mode' not in st.session_state:
        st.session_state.admin_dashboard_mode = None
    # ENHANCED: Image gallery session state
    if 'uploaded_images' not in st.session_state:
        st.session_state.uploaded_images = []
    if 'current_gallery_view' not in st.session_state:
        st.session_state.current_gallery_view = 'gallery'
    if 'selected_image' not in st.session_state:
        st.session_state.selected_image = None
    # NEW: Gallery clearance confirmation
    if 'show_clear_gallery_confirmation' not in st.session_state:
        st.session_state.show_clear_gallery_confirmation = False
    if 'clear_gallery_password' not in st.session_state:
        st.session_state.clear_gallery_password = ""
    if 'clear_gallery_error' not in st.session_state:
        st.session_state.clear_gallery_error = ""
    # NEW: Image viewer state
    if 'current_image_index' not in st.session_state:
        st.session_state.current_image_index = 0
    if 'image_viewer_mode' not in st.session_state:
        st.session_state.image_viewer_mode = False

# -------------------------
# DATA PERSISTENCE SETUP
# -------------------------
def setup_data_persistence():
    """Set up periodic data saving to prevent data loss"""
    current_time = time.time()
    if current_time - st.session_state.last_save_time > 300:  # 5 minutes
        print("💾 Periodic data save...")
        user_manager.save_users()
        user_manager.save_analytics()
        
        # Save strategy analyses data
        try:
            strategy_data = load_data()
            save_data(strategy_data)
        except Exception as e:
            print(f"⚠️ Error saving strategy data: {e}")
            
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
# DATA MANAGEMENT
# -------------------------
SAVE_FILE = "strategy_analyses.json"

def load_data():
    """Load strategy analyses data"""
    if os.path.exists(SAVE_FILE):
        with open(SAVE_FILE, "r", encoding="utf-8") as f:
            try:
                data = json.load(f)
                print(f"✅ Loaded strategy data from {SAVE_FILE}")
                return data
            except Exception as e:
                print(f"❌ Error loading strategy data: {e}")
                # Create backup of corrupted file
                backup_name = f"{SAVE_FILE}.backup.{int(time.time())}"
                os.rename(SAVE_FILE, backup_name)
                print(f"⚠️ Strategy data corrupted. Backed up to {backup_name}")
                return {}
    return {}

def save_data(data):
    """Save strategy analyses data"""
    try:
        # Create backup before saving
        if os.path.exists(SAVE_FILE):
            backup_file = f"{SAVE_FILE}.backup"
            shutil.copy2(SAVE_FILE, backup_file)
        
        with open(SAVE_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"✅ Saved strategy data to {SAVE_FILE}")
    except Exception as e:
        print(f"❌ Error saving strategy data: {e}")
        # Try to save to temporary file
        try:
            temp_file = f"{SAVE_FILE}.temp.{int(time.time())}"
            with open(temp_file, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"⚠️ Saved strategy backup to {temp_file}")
        except Exception as e2:
            print(f"❌ Failed to save strategy backup: {e2}")

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
# EMAIL VALIDATION TOOLS
# -------------------------
def validate_email_syntax(email):
    """Simple email syntax validation"""
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return re.match(pattern, email) is not None

def check_email_quality(email):
    """Check email quality indicators"""
    issues = []
    
    # Common disposable email domains
    disposable_domains = [
        'tempmail.com', 'throwaway.com', 'fake.com', 'guerrillamail.com',
        'mailinator.com', '10minutemail.com', 'yopmail.com', 'trashmail.com',
        'temp-mail.org', 'disposable.com', 'fakeinbox.com', 'getairmail.com'
    ]
    
    # Check syntax
    if not validate_email_syntax(email):
        issues.append("❌ Invalid email syntax")
        return issues
    
    # Check for disposable domains
    domain = email.split('@')[-1].lower()
    if domain in disposable_domains:
        issues.append("⚠️ Possible disposable email")
    
    # Check for common patterns in fake emails
    if 'fake' in email.lower() or 'test' in email.lower() or 'temp' in email.lower():
        issues.append("⚠️ Contains suspicious keywords")
    
    # Check for very short local part
    local_part = email.split('@')[0]
    if len(local_part) < 2:
        issues.append("⚠️ Very short username")
    
    if not issues:
        issues.append("✅ Email appears valid")
    
    return issues

# -------------------------
# SECURE USER MANAGEMENT WITH PERSISTENCE - COMPLETE VERSION
# -------------------------
class UserManager:
    def __init__(self):
        self.users_file = "users.json"
        self.analytics_file = "analytics.json"
        self._ensure_data_files()
        self.load_data()
    
    def _ensure_data_files(self):
        """Ensure data files exist and are valid"""
        # Create files if they don't exist
        if not os.path.exists(self.users_file):
            self.users = {}
            self.create_default_admin()
            self.save_users()
        else:
            # Verify file is valid JSON
            try:
                with open(self.users_file, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError:
                # Backup corrupted file and create new one
                backup_name = f"{self.users_file}.backup.{int(time.time())}"
                os.rename(self.users_file, backup_name)
                print(f"⚠️ Users file corrupted. Backed up to {backup_name}")
                self.users = {}
                self.create_default_admin()
                self.save_users()
        
        if not os.path.exists(self.analytics_file):
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
        else:
            # Verify analytics file is valid JSON
            try:
                with open(self.analytics_file, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError:
                # Backup corrupted file and create new one
                backup_name = f"{self.analytics_file}.backup.{int(time.time())}"
                os.rename(self.analytics_file, backup_name)
                print(f"⚠️ Analytics file corrupted. Backed up to {backup_name}")
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
    
    def load_data(self):
        """Load users and analytics data with robust error handling"""
        try:
            with open(self.users_file, 'r', encoding='utf-8') as f:
                self.users = json.load(f)
            print(f"✅ Loaded {len(self.users)} users from {self.users_file}")
        except Exception as e:
            print(f"❌ Error loading users: {e}")
            # Try to recover by creating default data
            self.users = {}
            self.create_default_admin()
            self.save_users()
        
        try:
            with open(self.analytics_file, 'r', encoding='utf-8') as f:
                self.analytics = json.load(f)
            print(f"✅ Loaded analytics data")
        except Exception as e:
            print(f"❌ Error loading analytics: {e}")
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
            "email_verified": True,  # Admin email is always verified
            "verification_date": datetime.now().isoformat()
        }
        print("✅ Created default admin account")
    
    def hash_password(self, password):
        """Secure password hashing"""
        salt = "default-salt-change-in-production"
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def save_users(self):
        """Save users to file with robust error handling"""
        try:
            # Create backup before saving
            if os.path.exists(self.users_file):
                backup_file = f"{self.users_file}.backup"
                shutil.copy2(self.users_file, backup_file)
            
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved {len(self.users)} users to {self.users_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving users: {e}")
            # Try to save to temporary file as last resort
            try:
                temp_file = f"{self.users_file}.temp.{int(time.time())}"
                with open(temp_file, 'w', encoding='utf-8') as f:
                    json.dump(self.users, f, indent=2, ensure_ascii=False)
                print(f"⚠️ Saved backup to {temp_file}")
            except Exception as e2:
                print(f"❌ Failed to save backup: {e2}")
            return False
    
    def save_analytics(self):
        """Save analytics data with robust error handling"""
        try:
            with open(self.analytics_file, 'w', encoding='utf-8') as f:
                json.dump(self.analytics, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error saving analytics: {e}")
            return False
    
    def periodic_cleanup(self):
        """Periodic cleanup that doesn't delete user data"""
        # Only reset session counts, don't delete users
        session_reset_count = 0
        for username in self.users:
            if self.users[username].get('active_sessions', 0) > 0:
                self.users[username]['active_sessions'] = 0
                session_reset_count += 1
        
        if session_reset_count > 0:
            print(f"🔄 Reset {session_reset_count} user sessions")
            self.save_users()
    
    def register_user(self, username, password, name, email, plan="trial"):
        """Register new user with proper validation and persistence"""
        # Reload data first to ensure we have latest
        self.load_data()
        
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
            "email_verified": False,  # NEW: Email verification status
            "verification_date": None,  # NEW: When email was verified
            "verification_notes": "",  # NEW: Admin notes for verification
            "verification_admin": None  # NEW: Which admin verified the email
        }
        
        # Update analytics
        if 'user_registrations' not in self.analytics:
            self.analytics['user_registrations'] = []
        
        self.analytics["user_registrations"].append({
            "username": username,
            "plan": plan,
            "timestamp": datetime.now().isoformat()
        })
        
        # Save both files
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
            "payment_status": "active",
            "email_verified": False,  # Test users start unverified
            "verification_date": None,
            "verification_notes": "",
            "verification_admin": None
        }
        
        self.analytics["user_registrations"].append({
            "username": test_username,
            "plan": plan,
            "timestamp": datetime.now().isoformat()
        })
        
        if self.save_users() and self.save_analytics():
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
        if user_data.get('active_sessions', 0) > 0:
            return False, "User has active sessions. Reset sessions first."
        
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
        
        if self.save_users() and self.save_analytics():
            return True, f"User '{username}' has been permanently deleted"
        else:
            return False, "Error deleting user data"

    def change_user_plan(self, username, new_plan):
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
        
        self.analytics['plan_changes'].append({
            "username": username,
            "old_plan": old_plan,
            "new_plan": new_plan,
            "timestamp": datetime.now().isoformat(),
            "admin": self.users.get('admin', {}).get('name', 'System')
        })
        
        if self.save_users() and self.save_analytics():
            return True, f"User '{username}' plan changed from {old_plan} to {new_plan}"
        else:
            return False, "Error saving plan change"

    def authenticate(self, username, password):
        """Authenticate user WITHOUT email verification blocking"""
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
        
        if not user.get("is_active", True):
            return False, "Account deactivated. Please contact support."
        
        # REMOVED: Email verification check - users can login immediately
        # Email verification status is only for admin monitoring
        
        if not self.verify_password(password, user["password_hash"]):
            return False, "Invalid username or password"
        
        expires = user.get("expires")
        if expires and datetime.strptime(expires, "%Y-%m-%d").date() < date.today():
            return False, "Subscription expired. Please renew your plan."
        
        user["last_login"] = datetime.now().isoformat()
        user["login_count"] = user.get("login_count", 0) + 1
        user["active_sessions"] += 1
        
        self.analytics["login_history"][-1]["success"] = True
        
        if self.save_users() and self.save_analytics():
            return True, "Login successful"
        else:
            return False, "Error saving login data"
    
    def verify_password(self, password, password_hash):
        return self.hash_password(password) == password_hash
    
    def logout(self, username):
        """Logout user"""
        if username in self.users:
            self.users[username]["active_sessions"] = max(0, self.users[username]["active_sessions"] - 1)
            self.save_users()
    
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
        
        if self.save_users() and self.save_analytics():
            return True, "Admin password changed successfully!"
        else:
            return False, "Error saving password change"
    
    def get_business_metrics(self):
        """Get business metrics for admin"""
        total_users = len(self.users)
        active_users = sum(1 for u in self.users.values() if u.get('is_active', True))
        online_users = sum(u.get('active_sessions', 0) for u in self.users.values())
        
        plan_counts = {}
        for user in self.users.values():
            plan = user.get('plan', 'unknown')
            plan_counts[plan] = plan_counts.get(plan, 0) + 1
        
        # NEW: Email verification metrics
        verified_users = sum(1 for u in self.users.values() if u.get('email_verified', False))
        unverified_users = total_users - verified_users
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "online_users": online_users,
            "plan_distribution": plan_counts,
            "total_logins": self.analytics.get("total_logins", 0),
            "revenue_today": self.analytics.get("revenue_today", 0),
            "verified_users": verified_users,
            "unverified_users": unverified_users
        }

    # NEW FUNCTION: Export all user credentials
    def export_user_credentials(self):
        """Export all user login credentials to CSV"""
        try:
            rows = []
            for username, user_data in self.users.items():
                # Note: We cannot decrypt passwords, but we can show account details
                rows.append({
                    "username": username,
                    "name": user_data.get("name", ""),
                    "email": user_data.get("email", ""),
                    "plan": user_data.get("plan", ""),
                    "expires": user_data.get("expires", ""),
                    "created": user_data.get("created", ""),
                    "last_login": user_data.get("last_login", ""),
                    "login_count": user_data.get("login_count", 0),
                    "active_sessions": user_data.get("active_sessions", 0),
                    "is_active": user_data.get("is_active", True),
                    "subscription_id": user_data.get("subscription_id", ""),
                    "payment_status": user_data.get("payment_status", ""),
                    "email_verified": user_data.get("email_verified", False),  # NEW
                    "verification_date": user_data.get("verification_date", ""),  # NEW
                    "verification_admin": user_data.get("verification_admin", "")  # NEW
                })
            
            df = pd.DataFrame(rows)
            csv_bytes = df.to_csv(index=False).encode('utf-8')
            return csv_bytes, None
        except Exception as e:
            return None, f"Error exporting user data: {str(e)}"

    # NEW FUNCTION: Change any user's username
    def change_username(self, old_username, new_username, changed_by="admin"):
        """Change a user's username"""
        if old_username not in self.users:
            return False, "User not found"
        
        if new_username in self.users:
            return False, "New username already exists"
        
        if not re.match("^[a-zA-Z0-9_]{3,20}$", new_username):
            return False, "New username must be 3-20 characters (letters, numbers, _)"
        
        # Store user data
        user_data = self.users[old_username]
        
        # Remove old username and add with new username
        del self.users[old_username]
        self.users[new_username] = user_data
        
        # Update analytics
        if 'username_changes' not in self.analytics:
            self.analytics['username_changes'] = []
        
        self.analytics['username_changes'].append({
            "old_username": old_username,
            "new_username": new_username,
            "timestamp": datetime.now().isoformat(),
            "changed_by": changed_by
        })
        
        if self.save_users() and self.save_analytics():
            return True, f"Username changed from '{old_username}' to '{new_username}'"
        else:
            # Rollback if save failed
            del self.users[new_username]
            self.users[old_username] = user_data
            return False, "Error saving username change"

    # NEW FUNCTION: Change any user's password
    def change_user_password(self, username, new_password, changed_by="admin"):
        """Change any user's password (admin function)"""
        if username not in self.users:
            return False, "User not found"
        
        if len(new_password) < 8:
            return False, "Password must be at least 8 characters"
        
        user_data = self.users[username]
        
        # Check if new password is same as current
        if self.verify_password(new_password, user_data["password_hash"]):
            return False, "New password cannot be the same as current password"
        
        user_data["password_hash"] = self.hash_password(new_password)
        
        # Update analytics
        if 'password_changes' not in self.analytics:
            self.analytics['password_changes'] = []
        
        self.analytics['password_changes'].append({
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "changed_by": changed_by,
            "type": "admin_forced_change"
        })
        
        if self.save_users() and self.save_analytics():
            return True, f"Password for '{username}' changed successfully!"
        else:
            return False, "Error saving password change"

    # NEW FUNCTION: Get user credentials for display
    def get_user_credentials_display(self):
        """Get user credentials for display (without password hashes)"""
        users_list = []
        for username, user_data in self.users.items():
            users_list.append({
                "username": username,
                "name": user_data.get("name", ""),
                "email": user_data.get("email", ""),
                "plan": user_data.get("plan", ""),
                "expires": user_data.get("expires", ""),
                "created": user_data.get("created", ""),
                "last_login": user_data.get("last_login", ""),
                "is_active": user_data.get("is_active", True),
                "login_count": user_data.get("login_count", 0),
                "active_sessions": user_data.get("active_sessions", 0),
                "email_verified": user_data.get("email_verified", False),  # NEW
                "verification_date": user_data.get("verification_date", ""),  # NEW
                "verification_admin": user_data.get("verification_admin", "")  # NEW
            })
        return users_list

    # NEW FUNCTION: Verify user email manually
    def verify_user_email(self, username, admin_username, notes=""):
        """Manually verify a user's email address (admin function)"""
        if username not in self.users:
            return False, "User not found"
        
        if username == "admin":
            return False, "Cannot modify admin account verification"
        
        user_data = self.users[username]
        
        if user_data.get("email_verified", False):
            return False, "Email is already verified"
        
        # Update verification status
        user_data["email_verified"] = True
        user_data["verification_date"] = datetime.now().isoformat()
        user_data["verification_admin"] = admin_username
        user_data["verification_notes"] = notes
        
        # Update analytics
        if 'email_verifications' not in self.analytics:
            self.analytics['email_verifications'] = []
        
        self.analytics['email_verifications'].append({
            "username": username,
            "email": user_data.get("email", ""),
            "verified_by": admin_username,
            "timestamp": datetime.now().isoformat(),
            "notes": notes
        })
        
        if self.save_users() and self.save_analytics():
            return True, f"Email for '{username}' has been verified successfully!"
        else:
            return False, "Error saving verification data"

    # NEW FUNCTION: Revoke email verification
    def revoke_email_verification(self, username, admin_username, reason=""):
        """Revoke email verification (admin function)"""
        if username not in self.users:
            return False, "User not found"
        
        if username == "admin":
            return False, "Cannot modify admin account verification"
        
        user_data = self.users[username]
        
        if not user_data.get("email_verified", False):
            return False, "Email is not verified"
        
        # Update verification status
        user_data["email_verified"] = False
        user_data["verification_date"] = None
        user_data["verification_admin"] = None
        user_data["verification_notes"] = reason
        
        # Update analytics
        if 'email_verifications' not in self.analytics:
            self.analytics['email_verifications'] = []
        
        self.analytics['email_verifications'].append({
            "username": username,
            "email": user_data.get("email", ""),
            "action": "revoked",
            "revoked_by": admin_username,
            "timestamp": datetime.now().isoformat(),
            "reason": reason
        })
        
        if self.save_users() and self.save_analytics():
            return True, f"Email verification for '{username}' has been revoked!"
        else:
            return False, "Error saving verification data"

    # NEW FUNCTION: Get email verification statistics
    def get_email_verification_stats(self):
        """Get statistics about email verification status"""
        total_users = len(self.users)
        verified_count = 0
        unverified_count = 0
        pending_verification = []
        recently_verified = []
        
        for username, user_data in self.users.items():
            if username == "admin":
                continue  # Skip admin
            
            if user_data.get("email_verified", False):
                verified_count += 1
                # Get recently verified (last 7 days)
                verification_date = user_data.get("verification_date")
                if verification_date:
                    try:
                        verify_dt = datetime.fromisoformat(verification_date)
                        if (datetime.now() - verify_dt).days <= 7:
                            recently_verified.append({
                                "username": username,
                                "email": user_data.get("email", ""),
                                "verified_date": verification_date,
                                "verified_by": user_data.get("verification_admin", "")
                            })
                    except:
                        pass
            else:
                unverified_count += 1
                pending_verification.append({
                    "username": username,
                    "email": user_data.get("email", ""),
                    "created": user_data.get("created", ""),
                    "plan": user_data.get("plan", "")
                })
        
        return {
            "total_users": total_users - 1,  # Exclude admin
            "verified_count": verified_count,
            "unverified_count": unverified_count,
            "verification_rate": (verified_count / (total_users - 1)) * 100 if total_users > 1 else 0,
            "pending_verification": pending_verification,
            "recently_verified": recently_verified
        }

# Initialize user manager
user_manager = UserManager()

# -------------------------
# ENHANCED AUTHENTICATION COMPONENTS
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
                            st.success("🎉 Congratulations! Your account has been created. You can now login!")
                        else:
                            st.error(f"❌ {message}")

# -------------------------
# ENHANCED IMAGE GALLERY FORUM WITH NAVIGATION
# -------------------------
def render_image_gallery():
    """Professional image gallery forum with enhanced navigation"""
    
    # If in image viewer mode, show the image viewer
    if st.session_state.image_viewer_mode:
        render_image_viewer()
        return
    
    # Gallery header
    st.title("🖼️ Trading Analysis Image Gallery")
    st.markdown("Share and discuss trading charts, analysis screenshots, and market insights with the community.")
    
    # Gallery navigation
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        gallery_view = st.radio(
            "Gallery View:",
            ["📸 Image Gallery", "⬆️ Upload Images"],
            horizontal=True,
            key="gallery_nav"
        )
    
    st.markdown("---")
    
    if gallery_view == "⬆️ Upload Images":
        render_image_uploader()
    else:
        render_gallery_display()

def render_image_uploader():
    """Image upload interface"""
    st.subheader("📤 Upload New Images")
    
    with st.container():
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
        ">
        <h3 style="color: white; margin-bottom: 1rem;">🎯 Upload Trading Analysis Images</h3>
        <p style="margin-bottom: 0;">Share your trading charts, technical analysis, market insights, and strategy screenshots.</p>
        <p><strong>Supported formats:</strong> PNG, JPG, JPEG, GIF, BMP</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Image upload section
    uploaded_files = st.file_uploader(
        "Choose trading analysis images to upload", 
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp'], 
        accept_multiple_files=True,
        help="Select one or more trading charts or analysis images"
    )
    
    # Image description
    image_description = st.text_area(
        "Image Description (Optional):",
        placeholder="Describe what this image shows - e.g., 'BTC/USD 4H chart with RSI divergence', 'ETH breakout analysis', etc.",
        height=100
    )
    
    # Strategy tagging
    strategy_tags = st.multiselect(
        "Related Strategies (Optional):",
        list(STRATEGIES.keys()),
        help="Tag relevant trading strategies"
    )
    
    # Upload button
    if st.button("🚀 Upload Images to Gallery", use_container_width=True):
        if uploaded_files:
            for uploaded_file in uploaded_files:
                # Read image file
                image = Image.open(uploaded_file)
                
                # Convert to bytes for display
                img_bytes = io.BytesIO()
                image.save(img_bytes, format=image.format if image.format else 'PNG')
                
                # Store in session state
                st.session_state.uploaded_images.append({
                    'name': uploaded_file.name,
                    'image': image,
                    'bytes': img_bytes.getvalue(),
                    'format': image.format if image.format else 'PNG',
                    'description': image_description,
                    'strategies': strategy_tags,
                    'uploaded_by': st.session_state.user['username'],
                    'timestamp': datetime.now().isoformat(),
                    'likes': 0,
                    'comments': []
                })
            
            st.success(f"✅ Successfully uploaded {len(uploaded_files)} image(s) to the gallery!")
            st.balloons()
            st.rerun()  # Force refresh to show thumbnails immediately
        else:
            st.warning("⚠️ Please select at least one image to upload.")

def render_gallery_display():
    """Display the image gallery with enhanced navigation"""
    st.subheader("📸 Community Image Gallery")
    
    if not st.session_state.uploaded_images:
        st.info("""
        🖼️ **No images in the gallery yet!**
        
        Be the first to share your trading analysis! Upload charts, technical analysis screenshots, 
        or market insights to help the community learn and discuss trading strategies.
        """)
        return
    
    # Gallery stats
    total_images = len(st.session_state.uploaded_images)
    your_images = len([img for img in st.session_state.uploaded_images if img['uploaded_by'] == st.session_state.user['username']])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Images", total_images)
    with col2:
        st.metric("Your Images", your_images)
    with col3:
        total_likes = sum(img['likes'] for img in st.session_state.uploaded_images)
        st.metric("Total Likes", total_likes)
    
    st.markdown("---")
    
    # Filter options
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_author = st.selectbox(
            "Filter by Author:",
            ["All Authors"] + list(set(img['uploaded_by'] for img in st.session_state.uploaded_images))
        )
    with col2:
        filter_strategy = st.selectbox(
            "Filter by Strategy:",
            ["All Strategies"] + list(STRATEGIES.keys())
        )
    with col3:
        sort_by = st.selectbox(
            "Sort by:",
            ["Newest First", "Oldest First", "Most Liked"]
        )
    
    # Apply filters
    filtered_images = st.session_state.uploaded_images.copy()
    
    if filter_author != "All Authors":
        filtered_images = [img for img in filtered_images if img['uploaded_by'] == filter_author]
    
    if filter_strategy != "All Strategies":
        filtered_images = [img for img in filtered_images if filter_strategy in img.get('strategies', [])]
    
    # Apply sorting
    if sort_by == "Newest First":
        filtered_images.sort(key=lambda x: x['timestamp'], reverse=True)
    elif sort_by == "Oldest First":
        filtered_images.sort(key=lambda x: x['timestamp'])
    elif sort_by == "Most Liked":
        filtered_images.sort(key=lambda x: x['likes'], reverse=True)
    
    # Display gallery in a grid
    if not filtered_images:
        st.warning("No images match your current filters.")
        return
    
    # Create responsive grid
    cols = st.columns(3)
    
    for i, img_data in enumerate(filtered_images):
        with cols[i % 3]:
            with st.container():
                st.markdown("""
                <div style='
                    border: 1px solid #ddd;
                    border-radius: 10px;
                    padding: 15px;
                    margin-bottom: 20px;
                    background: white;
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1);
                    transition: transform 0.2s;
                '>
                """, unsafe_allow_html=True)
                
                # FIXED: Display thumbnail immediately without requiring expander click
                st.image(img_data['bytes'], use_container_width=True)
                
                # Image info - always visible
                st.markdown(f"**{img_data['name']}**")
                
                # Description preview
                if img_data.get('description'):
                    # Show first 50 characters of description
                    preview = img_data['description'][:50] + "..." if len(img_data['description']) > 50 else img_data['description']
                    st.caption(preview)
                
                # Strategy tags preview
                if img_data.get('strategies'):
                    tags_preview = ", ".join(img_data['strategies'][:2])  # Show first 2 strategies
                    if len(img_data['strategies']) > 2:
                        tags_preview += f" +{len(img_data['strategies']) - 2} more"
                    st.caption(f"**Strategies:** {tags_preview}")
                
                # Author and date
                st.caption(f"By: **{img_data['uploaded_by']}**")
                upload_time = datetime.fromisoformat(img_data['timestamp']).strftime("%Y-%m-%d %H:%M")
                st.caption(f"Uploaded: {upload_time}")
                
                # Interaction buttons
                col_a, col_b, col_c, col_d = st.columns([1, 1, 1, 2])
                with col_a:
                    if st.button("❤️", key=f"like_{i}", help="Like this image"):
                        img_data['likes'] += 1
                        st.rerun()
                with col_b:
                    st.write(f" {img_data['likes']}")
                with col_c:
                    # ENHANCED: View button for image viewer with better label
                    if st.button("👁️ View", key=f"view_{i}", help="View full image"):
                        # Find the index of this image in the filtered list
                        original_index = st.session_state.uploaded_images.index(img_data)
                        st.session_state.current_image_index = original_index
                        st.session_state.image_viewer_mode = True
                        st.rerun()
                with col_d:
                    # Download button
                    b64_img = base64.b64encode(img_data['bytes']).decode()
                    href = f'<a href="data:image/{img_data["format"].lower()};base64,{b64_img}" download="{img_data["name"]}" style="text-decoration: none;">'
                    st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 4px 8px; text-align: center; text-decoration: none; display: inline-block; font-size: 12px; cursor: pointer; border-radius: 4px; width: 100%;">Download</button></a>', unsafe_allow_html=True)
                
                # Expandable section for full details
                with st.expander("📋 Full Details", expanded=False):
                    # Full description
                    if img_data.get('description'):
                        st.write("**Description:**")
                        st.info(img_data['description'])
                    
                    # All strategy tags
                    if img_data.get('strategies'):
                        st.write("**All Strategies:**")
                        tags = " ".join([f"`{tag}`" for tag in img_data['strategies']])
                        st.markdown(tags)
                    
                    # Additional metadata
                    st.write("**Image Info:**")
                    col_x, col_y = st.columns(2)
                    with col_x:
                        st.write(f"**Format:** {img_data['format']}")
                        st.write(f"**Likes:** {img_data['likes']}")
                    with col_y:
                        st.write(f"**Uploaded by:** {img_data['uploaded_by']}")
                        st.write(f"**Date:** {upload_time}")
                
                st.markdown("</div>", unsafe_allow_html=True)
    
    # Clear gallery button (admin only) - WITH SECURITY IMPROVEMENT
    if st.session_state.user['plan'] == 'admin':
        st.markdown("---")
        
        if st.session_state.show_clear_gallery_confirmation:
            render_clear_gallery_confirmation()
        else:
            if st.button("🗑️ Clear Entire Gallery (Admin Only)", use_container_width=True):
                st.session_state.show_clear_gallery_confirmation = True
                st.session_state.clear_gallery_password = ""
                st.session_state.clear_gallery_error = ""
                st.rerun()

def render_image_viewer():
    """Enhanced image viewer with navigation controls"""
    if not st.session_state.uploaded_images:
        st.warning("No images in gallery")
        st.session_state.image_viewer_mode = False
        st.rerun()
        return
    
    current_index = st.session_state.current_image_index
    total_images = len(st.session_state.uploaded_images)
    img_data = st.session_state.uploaded_images[current_index]
    
    # Header with navigation
    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    
    with col1:
        if st.button("⬅️ Back to Gallery", use_container_width=True):
            st.session_state.image_viewer_mode = False
            st.rerun()
    
    with col2:
        st.markdown(f"### Image {current_index + 1} of {total_images}")
    
    with col3:
        st.markdown(f"### {img_data['name']}")
    
    with col4:
        if st.button("📋 Gallery", use_container_width=True):
            st.session_state.image_viewer_mode = False
            st.rerun()
    
    st.markdown("---")
    
    # Main image display
    col1, col2, col3 = st.columns([1, 8, 1])
    
    with col1:
        if st.button("◀️ Previous", use_container_width=True, key="prev_img"):
            st.session_state.current_image_index = (current_index - 1) % total_images
            st.rerun()
    
    with col2:
        # Display the main image
        st.image(img_data['bytes'], use_container_width=True)
    
    with col3:
        if st.button("Next ▶️", use_container_width=True, key="next_img"):
            st.session_state.current_image_index = (current_index + 1) % total_images
            st.rerun()
    
    # Image information and controls below
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Image details
        st.subheader("Image Details")
        
        # Description
        if img_data.get('description'):
            st.write("**Description:**")
            st.info(img_data['description'])
        else:
            st.write("**Description:** No description provided")
        
        # Strategy tags
        if img_data.get('strategies'):
            st.write("**Related Strategies:**")
            tags = " ".join([f"`{tag}`" for tag in img_data['strategies']])
            st.markdown(tags)
        
        # Author and metadata
        st.write("**Upload Information:**")
        col_meta1, col_meta2 = st.columns(2)
        with col_meta1:
            st.write(f"**Author:** {img_data['uploaded_by']}")
            st.write(f"**Likes:** {img_data['likes']} ❤️")
        with col_meta2:
            upload_time = datetime.fromisoformat(img_data['timestamp']).strftime("%Y-%m-%d %H:%M")
            st.write(f"**Uploaded:** {upload_time}")
            st.write(f"**Format:** {img_data['format']}")
    
    with col2:
        # Quick navigation and actions
        st.subheader("Quick Navigation")
        
        # Image selector
        selected_index = st.selectbox(
            "Jump to Image:",
            range(total_images),
            format_func=lambda i: f"Image {i+1}: {st.session_state.uploaded_images[i]['name'][:20]}...",
            index=current_index,
            key="image_selector"
        )
        
        if selected_index != current_index:
            st.session_state.current_image_index = selected_index
            st.rerun()
        
        st.markdown("---")
        
        # Action buttons
        st.subheader("Actions")
        
        # Like button
        if st.button(f"❤️ Like ({img_data['likes']})", use_container_width=True, key="viewer_like"):
            img_data['likes'] += 1
            st.rerun()
        
        # Download button
        b64_img = base64.b64encode(img_data['bytes']).decode()
        href = f'<a href="data:image/{img_data["format"].lower()};base64,{b64_img}" download="{img_data["name"]}" style="text-decoration: none;">'
        st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 10px; text-align: center; text-decoration: none; display: inline-block; font-size: 14px; cursor: pointer; border-radius: 4px; width: 100%;">⬇️ Download Image</button></a>', unsafe_allow_html=True)
    
    # Navigation controls at bottom
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("⏮️ First", use_container_width=True):
            st.session_state.current_image_index = 0
            st.rerun()
    
    with col2:
        if st.button("◀️ Previous", use_container_width=True):
            st.session_state.current_image_index = (current_index - 1) % total_images
            st.rerun()
    
    with col3:
        if st.button("📋 Gallery", use_container_width=True):
            st.session_state.image_viewer_mode = False
            st.rerun()
    
    with col4:
        if st.button("Next ▶️", use_container_width=True):
            st.session_state.current_image_index = (current_index + 1) % total_images
            st.rerun()
    
    with col5:
        if st.button("Last ⏭️", use_container_width=True):
            st.session_state.current_image_index = total_images - 1
            st.rerun()

def render_clear_gallery_confirmation():
    """Security confirmation for clearing gallery - REQUIRES ADMIN PASSWORD"""
    st.warning("🚨 **SECURITY CONFIRMATION REQUIRED**")
    
    with st.container():
        st.error("""
        ⚠️ **DESTRUCTIVE ACTION - IRREVERSIBLE**
        
        You are about to permanently delete ALL images from the gallery.
        This action cannot be undone!
        
        **Total images to be deleted:** {} images
        """.format(len(st.session_state.uploaded_images)))
        
        admin_password = st.text_input(
            "🔒 Enter Admin Password to Confirm:",
            type="password",
            placeholder="Enter your admin password to proceed",
            help="This is a security measure to prevent accidental data loss",
            value=st.session_state.clear_gallery_password,
            key="admin_password_input"
        )
        
        # Update session state with password input
        st.session_state.clear_gallery_password = admin_password
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ CONFIRM DELETE ALL IMAGES", use_container_width=True, type="primary"):
                if not admin_password:
                    st.session_state.clear_gallery_error = "❌ Please enter your admin password to confirm"
                    st.rerun()
                else:
                    # Verify admin password
                    success, message = user_manager.authenticate("admin", admin_password)
                    if success:
                        # Password verified - proceed with deletion
                        image_count = len(st.session_state.uploaded_images)
                        st.session_state.uploaded_images = []
                        st.session_state.show_clear_gallery_confirmation = False
                        st.session_state.clear_gallery_password = ""
                        st.session_state.clear_gallery_error = ""
                        st.session_state.image_viewer_mode = False  # Exit viewer if active
                        st.success(f"✅ Gallery cleared! {image_count} images have been permanently deleted.")
                        st.rerun()
                    else:
                        st.session_state.clear_gallery_error = "❌ Invalid admin password. Gallery clearance cancelled."
                        st.rerun()
        
        with col2:
            if st.button("❌ CANCEL", use_container_width=True):
                st.session_state.show_clear_gallery_confirmation = False
                st.session_state.clear_gallery_password = ""
                st.session_state.clear_gallery_error = ""
                st.rerun()
        
        # Display error message if any
        if st.session_state.clear_gallery_error:
            st.error(st.session_state.clear_gallery_error)

# -------------------------
# ENHANCED ADMIN DASHBOARD SELECTION INTERFACE
# -------------------------
def render_admin_dashboard_selection():
    """Interface for admin to choose between admin dashboard and premium dashboard"""
    st.title("👑 Admin Portal - Choose Dashboard")
    st.markdown("---")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.subheader("🛠️ Admin Management Dashboard")
        st.markdown("""
        **Full System Control:**
        - User management & analytics
        - Email verification
        - Plan management
        - Business metrics
        - System configuration
        - Revenue reporting
        - Bulk operations
        """)
        if st.button("🚀 Go to Admin Dashboard", use_container_width=True, key="admin_dash"):
            st.session_state.admin_dashboard_mode = "admin"
            st.rerun()
    
    with col2:
        st.subheader("📊 Premium Signal Dashboard")
        st.markdown("""
        **Signal Management:**
        - Edit trading signals & strategies
        - Update market analysis
        - Manage 5-day cycle
        - Signal observation mode
        - Real-time updates
        - Advanced analytics
        - Export functionality
        """)
        if st.button("📈 Go to Premium Dashboard", use_container_width=True, key="premium_dash"):
            st.session_state.admin_dashboard_mode = "premium"
            st.rerun()
    
    with col3:
        st.subheader("🖼️ Image Gallery Forum")
        st.markdown("""
        **Community Features:**
        - Upload trading charts
        - Share analysis images
        - Community discussions
        - Strategy visualization
        - Market insights sharing
        - Enhanced image viewer
        - Navigation controls
        """)
        if st.button("🖼️ Go to Image Gallery", use_container_width=True, key="gallery_dash"):
            st.session_state.admin_dashboard_mode = "gallery"
            st.rerun()
    
    st.markdown("---")
    st.info("💡 **Tip:** Use different dashboards for different management tasks.")

# -------------------------
# COMPLETE ADMIN MANAGEMENT DASHBOARD WITH ALL FEATURES
# -------------------------
def render_admin_management_dashboard():
    """Complete admin management dashboard with all rich features"""
    st.title("🛠️ Admin Management Dashboard")
    
    # Get business metrics
    metrics = user_manager.get_business_metrics()
    
    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Users", metrics["total_users"])
    with col2:
        st.metric("Active Users", metrics["active_users"])
    with col3:
        st.metric("Online Now", metrics["online_users"])
    with col4:
        st.metric("Verified Users", metrics["verified_users"])
    with col5:
        st.metric("Unverified Users", metrics["unverified_users"])
    
    st.markdown("---")
    
    # Current view based on admin_view state
    current_view = st.session_state.get('admin_view', 'overview')
    
    if current_view == 'analytics':
        render_admin_analytics()
    elif current_view == 'users':
        render_admin_user_management()
    elif current_view == 'email_verification':
        render_email_verification_interface()
    elif current_view == 'revenue':
        render_admin_revenue()
    else:
        render_admin_overview()

def render_admin_overview():
    """Admin overview with business metrics"""
    st.subheader("📈 Business Overview")
    
    # Get business metrics
    metrics = user_manager.get_business_metrics()
    
    # Plan distribution
    st.subheader("📊 Plan Distribution")
    plan_data = metrics["plan_distribution"]
    
    if plan_data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Users by Plan:**")
            for plan, count in plan_data.items():
                if plan != "admin":  # Don't show admin in distribution
                    plan_name = Config.PLANS.get(plan, {}).get('name', plan.title())
                    st.write(f"• {plan_name}: {count} users")
        
        with col2:
            # Simple chart using progress bars
            total = sum(count for plan, count in plan_data.items() if plan != "admin")
            if total > 0:
                for plan, count in plan_data.items():
                    if plan != "admin":
                        percentage = (count / total) * 100
                        plan_name = Config.PLANS.get(plan, {}).get('name', plan.title())
                        st.write(f"{plan_name}: {count} ({percentage:.1f}%)")
                        st.progress(percentage / 100)
    
    st.markdown("---")
    
    # Recent activity
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🕒 Recent Registrations")
        recent_registrations = user_manager.analytics.get("user_registrations", [])[-5:]
        if recent_registrations:
            for reg in reversed(recent_registrations):
                plan_name = Config.PLANS.get(reg['plan'], {}).get('name', reg['plan'].title())
                st.write(f"• {reg['username']} - {plan_name} - {reg['timestamp'][:16]}")
        else:
            st.info("No recent registrations")
    
    with col2:
        st.subheader("🔄 Recent Plan Changes")
        recent_plan_changes = user_manager.analytics.get("plan_changes", [])[-5:]
        if recent_plan_changes:
            for change in reversed(recent_plan_changes):
                old_plan = Config.PLANS.get(change['old_plan'], {}).get('name', change['old_plan'].title())
                new_plan = Config.PLANS.get(change['new_plan'], {}).get('name', change['new_plan'].title())
                st.write(f"• {change['username']}: {old_plan} → {new_plan}")
                st.caption(f"{change['timestamp'][:16]}")
        else:
            st.info("No recent plan changes")

def render_admin_analytics():
    """Detailed analytics view"""
    st.subheader("📈 Detailed Analytics")
    
    # Login analytics
    st.write("**Login Activity**")
    total_logins = user_manager.analytics.get("total_logins", 0)
    successful_logins = len([x for x in user_manager.analytics.get("login_history", []) if x.get('success')])
    failed_logins = total_logins - successful_logins
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Login Attempts", total_logins)
    with col2:
        st.metric("Successful Logins", successful_logins)
    with col3:
        st.metric("Failed Logins", failed_logins)
    
    # Email verification analytics
    st.markdown("---")
    st.subheader("📧 Email Verification Analytics")
    
    stats = user_manager.get_email_verification_stats()
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", stats["total_users"])
    with col2:
        st.metric("Verified", stats["verified_count"])
    with col3:
        st.metric("Unverified", stats["unverified_count"])
    with col4:
        st.metric("Verification Rate", f"{stats['verification_rate']:.1f}%")
    
    # User growth
    st.markdown("---")
    st.subheader("📈 User Growth")
    
    registrations = user_manager.analytics.get("user_registrations", [])
    if registrations:
        # Group by date
        reg_by_date = {}
        for reg in registrations:
            date_str = reg['timestamp'][:10]
            reg_by_date[date_str] = reg_by_date.get(date_str, 0) + 1
        
        # Display as table
        st.write("**Registrations by Date:**")
        reg_df = pd.DataFrame(list(reg_by_date.items()), columns=['Date', 'Registrations'])
        reg_df = reg_df.sort_values('Date', ascending=False).head(10)
        st.dataframe(reg_df, use_container_width=True)
    else:
        st.info("No registration data available")

def render_admin_user_management():
    """Complete user management interface"""
    st.subheader("👥 User Management")
    
    # User actions
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("🔄 Refresh User List", use_container_width=True, key="um_refresh"):
            st.rerun()
    with col2:
        if st.button("📧 Email Verification", use_container_width=True, key="um_email_verify"):
            st.session_state.admin_view = "email_verification"
            st.rerun()
    with col3:
        if st.button("🔐 User Credentials", use_container_width=True, key="um_credentials"):
            st.session_state.show_user_credentials = True
            st.rerun()
    with col4:
        if st.button("🆕 Create Test User", use_container_width=True, key="um_test"):
            created_username, msg = user_manager.create_test_user("trial")
            if created_username:
                st.success(msg)
            else:
                st.error(msg)
            st.rerun()
    with col5:
        if st.button("🗑️ Bulk Delete Inactive", use_container_width=True, key="um_bulk"):
            st.session_state.show_bulk_delete = True
            st.rerun()
    with col6:
        if st.button("🔐 Change Admin Password", use_container_width=True, key="um_password"):
            st.session_state.show_password_change = True
            st.rerun()
    
    st.markdown("---")
    
    # Enhanced User table with quick actions including email verification
    st.write("**All Users - Quick Management:**")
    
    # Display users with quick plan change and verification options
    for username, user_data in user_manager.users.items():
        with st.container():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 2, 2, 1, 1, 1])
            
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
                # Email verification status with better visual design
                if user_data.get('email_verified', False):
                    st.markdown(
                        """
                        <div style="
                            background: linear-gradient(135deg, #10B981 0%, #059669 100%);
                            color: white;
                            padding: 2px 8px;
                            border-radius: 12px;
                            font-size: 0.7rem;
                            font-weight: 600;
                            text-align: center;
                            border: 1px solid #047857;
                            min-width: 60px;
                            display: inline-block;
                        ">✅ Verified</div>
                        """, 
                        unsafe_allow_html=True
                    )
                else:
                    st.markdown(
                        """
                        <div style="
                            background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
                            color: white;
                            padding: 2px 8px;
                            border-radius: 12px;
                            font-size: 0.7rem;
                            font-weight: 600;
                            text-align: center;
                            border: 1px solid #B91C1C;
                            min-width: 60px;
                            display: inline-block;
                        ">❌ Unverified</div>
                        """, 
                        unsafe_allow_html=True
                    )
            
            with col6:
                if username != "admin":
                    # Quick upgrade to premium
                    if current_plan != "premium":
                        if st.button("⭐", key=f"quick_premium_{username}", help="Upgrade to Premium"):
                            success, message = user_manager.change_user_plan(username, "premium")
                            if success:
                                st.success(message)
                                time.sleep(1)
                                st.rerun()
                            else:
                                st.error(message)
                    else:
                        st.write("⭐")
            
            with col7:
                if username != "admin":
                    if st.button("⚙️", key=f"manage_{username}", help="Manage Plan"):
                        st.session_state.manage_user_plan = username
                        st.rerun()

def render_admin_revenue():
    """Revenue and financial reporting"""
    st.subheader("💰 Revenue Analytics")
    
    # Revenue metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Estimated MRR", "$1,250")
    with col2:
        st.metric("Active Subscriptions", "28")
    with col3:
        st.metric("Trial Conversions", "12%")
    
    st.markdown("---")
    
    # Revenue by plan
    st.write("**Revenue by Plan Type:**")
    
    revenue_data = {
        "Trial": {"users": 0, "revenue": 0},
        "Premium": {"users": 0, "revenue": 0}
    }
    
    for user_data in user_manager.users.values():
        plan = user_data.get("plan", "trial")
        if plan == "premium":
            revenue_data["Premium"]["users"] += 1
            revenue_data["Premium"]["revenue"] += Config.PLANS.get(plan, {}).get("price", 0)
        else:
            revenue_data["Trial"]["users"] += 1
    
    # Display revenue table
    revenue_df = pd.DataFrame([
        {"Plan": "Trial", "Users": revenue_data["Trial"]["users"], "Monthly Revenue": revenue_data["Trial"]["revenue"]},
        {"Plan": "Premium", "Users": revenue_data["Premium"]["users"], "Monthly Revenue": revenue_data["Premium"]["revenue"]}
    ])
    
    st.dataframe(revenue_df, use_container_width=True)
    
    st.markdown("---")
    st.info("💡 **Note:** Revenue analytics are simulated. Integrate with Stripe or PayPal for real payment data.")

# -------------------------
# ENHANCED PREMIUM SIGNAL DASHBOARD WITH ALL FEATURES
# -------------------------
def render_premium_signal_dashboard():
    """Premium signal dashboard where admin can edit signals with full functionality"""
    
    # User-specific data isolation
    user = st.session_state.user
    user_data_key = f"{user['username']}_data"
    if user_data_key not in st.session_state.user_data:
        st.session_state.user_data[user_data_key] = {
            "saved_analyses": {},
            "favorite_strategies": [],
            "performance_history": [],
            "recent_signals": []
        }
    
    data = st.session_state.user_data[user_data_key]
    
    # Load strategy analyses data
    strategy_data = load_data()
    
    # Date navigation
    start_date = date(2025, 8, 9)
    
    # Get date from URL parameters or session state
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
    
    # Ensure analysis_date is not before start_date
    if analysis_date < start_date:
        analysis_date = start_date
        st.session_state.analysis_date = start_date
    
    # Clean sidebar with 5-day cycle system
    with st.sidebar:
        st.title("🎛️ Admin Signal Control Panel")
        
        # Admin profile section
        st.markdown("---")
        st.write(f"**👑 {user['name']}**")
        st.success("🛠️ Admin Signal Editor")
        
        st.markdown("---")
        
        # 5-Day Cycle System with Date Navigation
        st.subheader("📅 5-Day Cycle")
        
        # Display current date
        st.markdown(f"**Current Date:** {analysis_date.strftime('%m/%d/%Y')}")
        
        # Date navigation
        col1, col2 = st.columns(2)
        with col1:
            if st.button("◀️ Prev Day", use_container_width=True, key="prev_day"):
                new_date = analysis_date - timedelta(days=1)
                if new_date >= start_date:
                    st.query_params["date"] = new_date.strftime("%Y-%m-%d")
                    st.rerun()
                else:
                    st.warning("Cannot go before start date")
        with col2:
            if st.button("Next Day ▶️", use_container_width=True, key="next_day"):
                new_date = analysis_date + timedelta(days=1)
                st.query_params["date"] = new_date.strftime("%Y-%m-%d")
                st.rerun()
        
        # Quick date reset button
        if st.button("🔄 Today", use_container_width=True, key="today_btn"):
            st.query_params["date"] = date.today().strftime("%Y-%m-%d")
            st.rerun()
        
        # Cycle information
        daily_strategies, cycle_day = get_daily_strategies(analysis_date)
        st.info(f"**Day {cycle_day} of 5-day cycle**")
        
        # Today's focus strategies
        st.markdown("**Today's Focus:**")
        for strategy in daily_strategies:
            st.write(f"• {strategy}")
        
        st.markdown("---")
        
        # Strategy selection
        selected_strategy = st.selectbox(
            "Choose Strategy to Edit:", 
            daily_strategies,
            key="strategy_selector"
        )
        
        st.markdown("---")
        
        # Navigation
        st.subheader("📊 Navigation")
        nav_options = {
            "📈 Signal Dashboard": "main",
            "📝 Edit Signals": "notes", 
            "⚙️ Admin Settings": "settings"
        }
        
        for label, view in nav_options.items():
            if st.button(label, use_container_width=True, key=f"nav_{view}"):
                st.session_state.dashboard_view = view
                st.rerun()
        
        st.markdown("---")
        
        # Export functionality
        csv_bytes = generate_filtered_csv_bytes(strategy_data, analysis_date)
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
            user_manager.logout(user['username'])
            st.session_state.user = None
            st.session_state.admin_dashboard_mode = None
            st.rerun()
    
    # Main dashboard content
    current_view = st.session_state.get('dashboard_view', 'main')
    
    if current_view == 'notes':
        render_admin_strategy_notes(strategy_data, daily_strategies, cycle_day, analysis_date, selected_strategy)
    elif current_view == 'settings':
        render_admin_account_settings()
    else:
        render_admin_trading_dashboard(data, user, daily_strategies, cycle_day, analysis_date, selected_strategy)

def render_admin_trading_dashboard(data, user, daily_strategies, cycle_day, analysis_date, selected_strategy):
    """Admin trading dashboard with editing capabilities"""
    st.title("📊 Admin Signal Dashboard")
    
    # Welcome and cycle info
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.success(f"👑 Welcome back, **{user['name']}**! You're in **Admin Signal Mode** with full editing access.")
    with col2:
        st.metric("Cycle Day", f"Day {cycle_day}/5")
    with col3:
        st.metric("Admin Mode", "Unlimited")
    
    st.markdown("---")
    
    # Progress indicators for today's strategies
    st.subheader("📋 Today's Strategy Progress")
    cols = st.columns(3)
    
    strategy_data = load_data()
    for i, strategy in enumerate(daily_strategies):
        with cols[i]:
            strategy_completed = False
            if strategy in strategy_data:
                # Check if all indicators have notes for today
                today_indicators = [ind for ind, meta in strategy_data[strategy].items() 
                                  if meta.get("analysis_date") == analysis_date.strftime("%Y-%m-%d")]
                if len(today_indicators) == len(STRATEGIES[strategy]):
                    strategy_completed = True
            
            if strategy_completed:
                st.success(f"✅ {strategy}")
            elif strategy == selected_strategy:
                st.info(f"📝 {strategy} (current)")
            else:
                st.warning(f"🕓 {strategy}")
    
    st.markdown("---")
    
    # Selected strategy analysis - ADMIN EDITING ENABLED
    st.subheader(f"🔍 {selected_strategy} Analysis - ADMIN EDIT MODE")
    
    # Quick analysis form
    with st.form(f"quick_analysis_{selected_strategy}"):
        col1, col2 = st.columns(2)
        with col1:
            strategy_tag = st.selectbox("Strategy Tag:", ["Neutral", "Buy", "Sell"], key=f"tag_{selected_strategy}")
        with col2:
            strategy_type = st.selectbox("Strategy Type:", ["Momentum", "Extreme", "Not Defined"], key=f"type_{selected_strategy}")
        
        # Quick notes
        quick_note = st.text_area(
            "Quick Analysis Notes:", 
            height=100,
            placeholder=f"Enter your analysis notes for {selected_strategy}...",
            key=f"quick_note_{selected_strategy}"
        )
        
        if st.form_submit_button("💾 Save Quick Analysis", use_container_width=True):
            # Save quick analysis
            if 'saved_analyses' not in data:
                data['saved_analyses'] = {}
            data['saved_analyses'][selected_strategy] = {
                "timestamp": datetime.now(),
                "tag": strategy_tag,
                "type": strategy_type,
                "note": quick_note
            }
            st.success("✅ Quick analysis saved!")
    
    st.markdown("---")
    
    # Detailed analysis button
    if st.button("📝 Open Detailed Analysis Editor", use_container_width=True):
        st.session_state.dashboard_view = 'notes'
        st.rerun()
    
    # Recent activity
    if data.get('saved_analyses'):
        st.markdown("---")
        st.subheader("📜 Recent Analyses")
        for strategy, analysis in list(data['saved_analyses'].items())[-3:]:
            with st.expander(f"{strategy} - {analysis['timestamp'].strftime('%H:%M')}"):
                st.write(f"**Tag:** {analysis['tag']} | **Type:** {analysis['type']}")
                st.write(analysis.get('note', 'No notes'))

def render_admin_strategy_notes(strategy_data, daily_strategies, cycle_day, analysis_date, selected_strategy):
    """Detailed strategy notes interface with full admin editing"""
    st.title("📝 Admin Signal Editor")
    
    # Header with cycle info
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.subheader(f"Day {cycle_day} - {selected_strategy} - ADMIN EDIT MODE")
    with col2:
        st.metric("Analysis Date", analysis_date.strftime("%m/%d/%Y"))
    with col3:
        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            st.session_state.dashboard_view = 'main'
            st.rerun()
    
    st.markdown("---")
    
    # Notes Form - ADMIN VERSION WITH FULL ACCESS
    with st.form("admin_detailed_notes_form"):
        st.subheader(f"Admin Signal Editor - {selected_strategy}")
        
        # Load existing data for this strategy
        existing_data = strategy_data.get(selected_strategy, {})
        current_strategy_tag = next(iter(existing_data.values()), {}).get("strategy_tag", "Neutral")
        current_strategy_type = next(iter(existing_data.values()), {}).get("momentum", "Not Defined")
        
        # Strategy-level settings
        col1, col2 = st.columns(2)
        with col1:
            strategy_tag = st.selectbox("Strategy Tag:", ["Neutral", "Buy", "Sell"], 
                                      index=["Neutral","Buy","Sell"].index(current_strategy_tag))
        with col2:
            strategy_type = st.selectbox("Strategy Type:", ["Momentum", "Extreme", "Not Defined"], 
                                       index=["Momentum","Extreme","Not Defined"].index(current_strategy_type))
        
        st.markdown("---")
        
        # Indicator analysis in columns - ADMIN CAN EDIT ALL
        indicators = STRATEGIES[selected_strategy]
        col_objs = st.columns(3)
        
        for i, indicator in enumerate(indicators):
            col = col_objs[i % 3]
            key_note = f"note__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"
            key_status = f"status__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"
            
            existing = existing_data.get(indicator, {})
            default_note = existing.get("note", "")
            default_status = existing.get("status", "Open")
            
            with col.expander(f"**{indicator}** - ADMIN EDIT", expanded=False):
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
        
        # Save button
        submitted = st.form_submit_button("💾 Save All Signals (Admin)", use_container_width=True)
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
                    "modified_by": "admin"  # Mark as admin-edited
                }
            
            save_data(strategy_data)
            st.success("✅ All signals saved successfully! (Admin Mode)")
    
    # Display saved analyses
    st.markdown("---")
    st.subheader("📜 Saved Signals - ADMIN VIEW")
    
    view_options = ["Today's Focus"] + daily_strategies
    filter_strategy = st.selectbox("Filter by strategy:", view_options, index=0)
    
    if filter_strategy == "Today's Focus":
        strategies_to_show = daily_strategies
    else:
        strategies_to_show = [filter_strategy]
    
    color_map = {"Buy": "🟢 Buy", "Sell": "🔴 Sell", "Neutral": "⚪ Neutral"}
    
    for strat in strategies_to_show:
        if strat in strategy_data:
            st.markdown(f"### {strat}")
            inds = strategy_data.get(strat, {})
            if not inds:
                st.info("No saved signals for this strategy.")
                continue
            
            strategy_tag = next(iter(inds.values())).get("strategy_tag", "Neutral")
            st.markdown(f"**Strategy Tag:** {color_map.get(strategy_tag, strategy_tag)}")
            st.markdown("---")
            
            for ind_name, meta in inds.items():
                if meta.get("analysis_date") == analysis_date.strftime("%Y-%m-%d"):
                    momentum_type = meta.get("momentum", "Not Defined")
                    status_icon = "✅ Done" if meta.get("status", "Open") == "Done" else "🕓 Open"
                    modified_by = meta.get("modified_by", "system")
                    with st.expander(f"{ind_name} ({momentum_type}) — {status_icon} — Edited by: {modified_by}", expanded=False):
                        st.write(meta.get("note", "") or "_No notes yet_")
                        st.caption(f"Last updated: {meta.get('last_modified', 'N/A')}")
            st.markdown("---")

def render_admin_account_settings():
    """Admin account settings in premium mode"""
    st.title("⚙️ Admin Settings - Premium Mode")
    
    user = st.session_state.user
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Admin Profile")
        st.text_input("Full Name", value=user['name'], disabled=True)
        st.text_input("Email", value=user['email'], disabled=True)
        st.text_input("Username", value=user['username'], disabled=True)
        
    with col2:
        st.subheader("Admin Privileges")
        st.text_input("Role", value="System Administrator", disabled=True)
        st.text_input("Access Level", value="Full System Access", disabled=True)
        st.text_input("Signal Editing", value="Enabled", disabled=True)
    
    st.markdown("---")
    st.subheader("Quick Actions")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🛠️ Switch to Admin Dashboard", use_container_width=True):
            st.session_state.admin_dashboard_mode = "admin"
            st.rerun()
    
    with col2:
        if st.button("📊 Refresh All Data", use_container_width=True):
            user_manager.load_data()
            st.rerun()
    
    with col3:
        if st.button("⬅️ Back to Signals", use_container_width=True):
            st.session_state.dashboard_view = 'main'
            st.rerun()

# -------------------------
# ENHANCED USER DASHBOARD - OBSERVE ONLY (SAME LAYOUT AS ADMIN BUT READ-ONLY)
# -------------------------
def render_user_dashboard():
    """User dashboard - READ ONLY for regular users with same layout as admin"""
    user = st.session_state.user
    
    # User-specific data isolation
    user_data_key = f"{user['username']}_data"
    if user_data_key not in st.session_state.user_data:
        st.session_state.user_data[user_data_key] = {
            "saved_analyses": {},
            "favorite_strategies": [],
            "performance_history": [],
            "recent_signals": []
        }
    
    data = st.session_state.user_data[user_data_key]
    
    # Load strategy analyses data
    strategy_data = load_data()
    
    # Date navigation
    start_date = date(2025, 8, 9)
    
    # Get date from URL parameters or session state
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
    
    # Ensure analysis_date is not before start_date
    if analysis_date < start_date:
        analysis_date = start_date
        st.session_state.analysis_date = start_date
    
    # Clean sidebar with 5-day cycle system - SAME AS ADMIN BUT READ ONLY
    with st.sidebar:
        st.title("🎛️ Signal Dashboard")
        
        # User profile section
        st.markdown("---")
        st.write(f"**👤 {user['name']}**")
        plan_display = Config.PLANS.get(user['plan'], {}).get('name', user['plan'].title())
        st.caption(f"🚀 {plan_display}")
        
        # Account status with progress
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.progress(min(1.0, days_left / 30), text=f"📅 {days_left} days remaining")
        
        st.markdown("---")
        
        # 5-Day Cycle System - SAME AS ADMIN
        st.subheader("📅 5-Day Cycle")
        
        # Display current date
        st.markdown(f"**Current Date:** {analysis_date.strftime('%m/%d/%Y')}")
        
        # Date navigation - READ ONLY FOR USERS
        col1, col2 = st.columns(2)
        with col1:
            if st.button("◀️ Prev Day", use_container_width=True, key="prev_day"):
                new_date = analysis_date - timedelta(days=1)
                if new_date >= start_date:
                    st.query_params["date"] = new_date.strftime("%Y-%m-%d")
                    st.rerun()
                else:
                    st.warning("Cannot go before start date")
        with col2:
            if st.button("Next Day ▶️", use_container_width=True, key="next_day"):
                new_date = analysis_date + timedelta(days=1)
                st.query_params["date"] = new_date.strftime("%Y-%m-%d")
                st.rerun()
        
        # Quick date reset button
        if st.button("🔄 Today", use_container_width=True, key="today_btn"):
            st.query_params["date"] = date.today().strftime("%Y-%m-%d")
            st.rerun()
        
        # Cycle information
        daily_strategies, cycle_day = get_daily_strategies(analysis_date)
        st.info(f"**Day {cycle_day} of 5-day cycle**")
        
        # Today's focus strategies
        st.markdown("**Today's Focus:**")
        for strategy in daily_strategies:
            st.write(f"• {strategy}")
        
        st.markdown("---")
        
        # Strategy selection - READ ONLY
        selected_strategy = st.selectbox(
            "Choose Strategy to View:", 
            daily_strategies,
            key="strategy_selector"
        )
        
        st.markdown("---")
        
        # Navigation - SIMPLIFIED FOR USERS
        st.subheader("📊 Navigation")
        if st.button("📈 View Signals", use_container_width=True, key="nav_main"):
            st.session_state.dashboard_view = 'main'
            st.rerun()
        
        if st.button("📋 Strategy Details", use_container_width=True, key="nav_notes"):
            st.session_state.dashboard_view = 'notes'
            st.rerun()
        
        if st.button("⚙️ Account Settings", use_container_width=True, key="nav_settings"):
            st.session_state.dashboard_view = 'settings'
            st.rerun()
        
        st.markdown("---")
        
        # Export functionality - READ ONLY
        csv_bytes = generate_filtered_csv_bytes(strategy_data, analysis_date)
        st.subheader("📄 Export Data")
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_bytes,
            file_name=f"strategy_analyses_{analysis_date.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True
        )
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True):
            user_manager.logout(user['username'])
            st.session_state.user = None
            st.rerun()
    
    # Main dashboard content - READ ONLY for users but same layout as admin
    current_view = st.session_state.get('dashboard_view', 'main')
    
    if current_view == 'notes':
        render_user_strategy_notes(strategy_data, daily_strategies, cycle_day, analysis_date, selected_strategy)
    elif current_view == 'settings':
        render_user_account_settings()
    else:
        render_user_trading_dashboard(data, user, daily_strategies, cycle_day, analysis_date, selected_strategy)

def render_user_trading_dashboard(data, user, daily_strategies, cycle_day, analysis_date, selected_strategy):
    """User trading dashboard - SAME LAYOUT AS ADMIN BUT READ ONLY"""
    st.title("📊 Trading Signal Dashboard")
    
    # Welcome message - DIFFERENT FROM ADMIN
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if user['plan'] == 'premium':
            st.success(f"🎉 Welcome back, **{user['name']}**! You're viewing Premium Signals.")
        else:
            st.info(f"👋 Welcome, **{user['name']}**! You have access to {Config.PLANS[user['plan']]['strategies']} strategies.")
    with col2:
        st.metric("Cycle Day", f"Day {cycle_day}/5")
    with col3:
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Plan Days", days_left)
    
    st.markdown("---")
    
    # Progress indicators for today's strategies - SAME AS ADMIN BUT READ ONLY
    st.subheader("📋 Today's Strategy Progress")
    cols = st.columns(3)
    
    strategy_data = load_data()
    for i, strategy in enumerate(daily_strategies):
        with cols[i]:
            strategy_completed = False
            if strategy in strategy_data:
                # Check if all indicators have notes for today
                today_indicators = [ind for ind, meta in strategy_data[strategy].items() 
                                  if meta.get("analysis_date") == analysis_date.strftime("%Y-%m-%d")]
                if len(today_indicators) == len(STRATEGIES[strategy]):
                    strategy_completed = True
            
            if strategy_completed:
                st.success(f"✅ {strategy}")
            elif strategy == selected_strategy:
                st.info(f"📊 {strategy} (viewing)")
            else:
                st.warning(f"🕓 {strategy}")
    
    st.markdown("---")
    
    # Selected strategy analysis - READ ONLY FOR USERS
    st.subheader(f"🔍 {selected_strategy} Analysis - VIEW MODE")
    
    # Display existing analysis - NO EDITING CAPABILITY
    strategy_data = load_data()
    existing_data = strategy_data.get(selected_strategy, {})
    
    if existing_data:
        # Get strategy-level info from first indicator
        first_indicator = next(iter(existing_data.values()), {})
        strategy_tag = first_indicator.get("strategy_tag", "Neutral")
        strategy_type = first_indicator.get("momentum", "Not Defined")
        modified_by = first_indicator.get("modified_by", "System")
        
        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Signal:** {strategy_tag}")
        with col2:
            st.info(f"**Type:** {strategy_type}")
        with col3:
            st.info(f"**Provider:** {modified_by}")
        
        # Display analysis note - READ ONLY
        note = first_indicator.get("note", "")
        if note:
            st.text_area("Analysis:", value=note, height=100, disabled=True, key=f"note_{selected_strategy}")
        else:
            st.info("No analysis available yet for this strategy.")
    else:
        st.warning("No signal data available for this strategy yet.")
    
    st.markdown("---")
    
    # Detailed view button - LEADS TO READ-ONLY DETAILED VIEW
    if st.button("📋 View Detailed Analysis", use_container_width=True):
        st.session_state.dashboard_view = 'notes'
        st.rerun()
    
    # Recent activity - READ ONLY
    if data.get('saved_analyses'):
        st.markdown("---")
        st.subheader("📜 Your Recent Views")
        for strategy, analysis in list(data['saved_analyses'].items())[-3:]:
            with st.expander(f"{strategy} - {analysis['timestamp'].strftime('%H:%M')}"):
                st.write(f"**Tag:** {analysis['tag']} | **Type:** {analysis['type']}")
                st.write(analysis.get('note', 'No notes'))

def render_user_strategy_notes(strategy_data, daily_strategies, cycle_day, analysis_date, selected_strategy):
    """Detailed strategy notes interface - READ ONLY FOR USERS"""
    st.title("📋 Strategy Details")
    
    # Header with cycle info
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        st.subheader(f"Day {cycle_day} - {selected_strategy} - VIEW MODE")
    with col2:
        st.metric("Analysis Date", analysis_date.strftime("%m/%d/%Y"))
    with col3:
        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            st.session_state.dashboard_view = 'main'
            st.rerun()
    
    st.markdown("---")
    
    # Display existing data - READ ONLY
    existing_data = strategy_data.get(selected_strategy, {})
    
    if not existing_data:
        st.warning("No signal data available for this strategy yet.")
        return
    
    # Strategy-level info
    first_indicator = next(iter(existing_data.values()), {})
    strategy_tag = first_indicator.get("strategy_tag", "Neutral")
    strategy_type = first_indicator.get("momentum", "Not Defined")
    modified_by = first_indicator.get("modified_by", "System")
    
    col1, col2 = st.columns(2)
    with col1:
        st.info(f"**Overall Signal:** {strategy_tag}")
    with col2:
        st.info(f"**Strategy Type:** {strategy_type}")
    
    st.markdown("---")
    
    # Indicator analysis in columns - READ ONLY
    st.subheader("📊 Indicator Analysis")
    
    indicators = STRATEGIES[selected_strategy]
    col_objs = st.columns(3)
    
    for i, indicator in enumerate(indicators):
        col = col_objs[i % 3]
        existing = existing_data.get(indicator, {})
        note = existing.get("note", "")
        status = existing.get("status", "Open")
        
        with col.expander(f"**{indicator}** - {status}", expanded=False):
            if note:
                st.text_area(
                    f"Analysis", 
                    value=note, 
                    height=120, 
                    disabled=True,
                    key=f"view_{sanitize_key(selected_strategy)}_{sanitize_key(indicator)}"
                )
            else:
                st.info("No analysis available for this indicator.")
            
            st.caption(f"Status: {status}")
            if existing.get("last_modified"):
                st.caption(f"Last updated: {existing['last_modified'][:16]}")

def render_user_account_settings():
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
        plan_name = Config.PLANS.get(user['plan'], {}).get('name', user['plan'].title())
        st.text_input("Current Plan", value=plan_name, disabled=True)
        st.text_input("Expiry Date", value=user['expires'], disabled=True)
        
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Days Remaining", days_left)
    
    st.markdown("---")
    
    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        st.session_state.dashboard_view = 'main'
        st.rerun()

# -------------------------
# COMPLETE ADMIN DASHBOARD WITH DUAL MODE
# -------------------------
def render_admin_dashboard():
    """Professional admin dashboard with dual mode selection"""
    
    # If admin hasn't chosen a dashboard mode, show selection
    if st.session_state.get('admin_dashboard_mode') is None:
        render_admin_dashboard_selection()
        return
    
    # Always render the sidebar first, regardless of current view
    with st.sidebar:
        st.title("👑 Admin Panel")
        st.markdown("---")
        st.write(f"Welcome, **{st.session_state.user['name']}**")
        
        # Show current mode
        current_mode = st.session_state.admin_dashboard_mode
        if current_mode == "admin":
            st.success("🛠️ Admin Management Mode")
        elif current_mode == "premium":
            st.success("📊 Premium Signal Mode")
        else:
            st.success("🖼️ Image Gallery Mode")
        
        # Dashboard mode switcher
        st.markdown("---")
        st.subheader("Dashboard Mode")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🛠️ Admin", use_container_width=True, 
                        type="primary" if current_mode == "admin" else "secondary"):
                st.session_state.admin_dashboard_mode = "admin"
                st.rerun()
        with col2:
            if st.button("📊 Premium", use_container_width=True,
                        type="primary" if current_mode == "premium" else "secondary"):
                st.session_state.admin_dashboard_mode = "premium"
                st.rerun()
        with col3:
            if st.button("🖼️ Gallery", use_container_width=True,
                        type="primary" if current_mode == "gallery" else "secondary"):
                st.session_state.admin_dashboard_mode = "gallery"
                st.rerun()
        
        st.markdown("---")
        
        # Logout button should always work
        if st.button("🚪 Logout", use_container_width=True, key="sidebar_logout"):
            user_manager.logout(st.session_state.user['username'])
            st.session_state.user = None
            st.session_state.admin_dashboard_mode = None
            st.rerun()
        
        # Show different sidebar options based on mode
        if current_mode == "admin":
            render_admin_sidebar_options()
        elif current_mode == "premium":
            render_premium_sidebar_options()
        else:
            # Gallery mode - FIXED: Better button labels
            st.subheader("Gallery Actions")
            if st.button("🖼️ Full Gallery", use_container_width=True):
                st.session_state.current_gallery_view = "gallery"
                st.session_state.image_viewer_mode = False
                st.rerun()
            if st.button("📤 Upload Images", use_container_width=True):
                st.session_state.current_gallery_view = "upload"
                st.session_state.image_viewer_mode = False
                st.rerun()
    
    # Main admin content based on selected mode
    if st.session_state.get('admin_dashboard_mode') == "admin":
        render_admin_management_dashboard()
    elif st.session_state.get('admin_dashboard_mode') == "premium":
        render_premium_signal_dashboard()
    else:
        render_image_gallery()

def render_admin_sidebar_options():
    """Sidebar options for admin management mode"""
    st.subheader("Admin Actions")
    
    if st.button("🔄 Refresh All Data", use_container_width=True, key="sidebar_refresh"):
        user_manager.load_data()
        st.rerun()
    
    if st.button("📊 Business Overview", use_container_width=True, key="sidebar_overview"):
        st.session_state.admin_view = "overview"
        st.rerun()
    
    if st.button("📈 View Analytics", use_container_width=True, key="sidebar_analytics"):
        st.session_state.admin_view = "analytics"
        st.rerun()
    
    if st.button("👥 Manage Users", use_container_width=True, key="sidebar_users"):
        st.session_state.admin_view = "users"
        st.rerun()
    
    if st.button("📧 Email Verification", use_container_width=True, key="sidebar_email_verify"):
        st.session_state.admin_view = "email_verification"
        st.rerun()
    
    if st.button("💰 Revenue Report", use_container_width=True, key="sidebar_revenue"):
        st.session_state.admin_view = "revenue"
        st.rerun()

def render_premium_sidebar_options():
    """Sidebar options for premium signal mode"""
    st.subheader("Signal Actions")
    
    if st.button("📈 Signal Dashboard", use_container_width=True, key="premium_today"):
        st.session_state.dashboard_view = "main"
        st.rerun()
    
    if st.button("📝 Edit Signals", use_container_width=True, key="premium_edit"):
        st.session_state.dashboard_view = "notes"
        st.rerun()
    
    if st.button("⚙️ Admin Settings", use_container_width=True, key="premium_settings"):
        st.session_state.dashboard_view = "settings"
        st.rerun()
    
    if st.button("🔄 Refresh Signals", use_container_width=True, key="premium_refresh"):
        st.rerun()

# -------------------------
# ADDITIONAL COMPONENTS FROM FIRST CODE (Email Verification, etc.)
# -------------------------
def render_email_verification_interface():
    """Email verification interface (simplified for this version)"""
    st.subheader("📧 Email Verification")
    st.info("Email verification management interface would be implemented here")
    # Full implementation from first code can be added here

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
# MAIN APPLICATION
# -------------------------
def main():
    init_session()
    
    # Setup data persistence
    setup_data_persistence()
    
    # Enhanced CSS for premium appearance
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
    .admin-feature {
        border: 2px solid #8B5CF6;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        background: linear-gradient(135deg, #f8f7ff 0%, #ede9fe 100%);
    }
    .gallery-feature {
        border: 2px solid #F59E0B;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        background: linear-gradient(135deg, #FFFBEB 0%, #FEF3C7 100%);
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
    .image-container {
        display: flex;
        flex-wrap: wrap;
        gap: 20px;
        justify-content: center;
        margin-top: 20px;
    }
    .image-card {
        border: 1px solid #ddd;
        border-radius: 10px;
        padding: 10px;
        width: 250px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
        transition: transform 0.2s;
        background-color: white;
    }
    .image-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 6px 12px rgba(0, 0, 0, 0.15);
    }
    .upload-section {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin-bottom: 30px;
    }
    .stButton button {
        width: 100%;
    }
    .security-warning {
        background: linear-gradient(135deg, #FFE4E6 0%, #FECACA 100%);
        border: 2px solid #EF4444;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
    }
    .image-viewer-nav {
        display: flex;
        justify-content: center;
        gap: 10px;
        margin: 20px 0;
    }
    </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.user:
        render_login()
    else:
        if st.session_state.user['plan'] == 'admin':
            render_admin_dashboard()
        else:
            # For regular users, show either trading dashboard or gallery
            if st.session_state.get('current_gallery_view') == 'gallery' or st.session_state.image_viewer_mode:
                render_image_gallery()
            else:
                render_user_dashboard()

if __name__ == "__main__":
    main()
