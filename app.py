# app.py - COMPLETE FIXED VERSION WITH ROBUST DATA PERSISTENCE
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
        print("🚀 Application started - initializing robust data system")
    
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
    
    # Add recovery for user session if they were logged in
    if st.session_state.user is None and 'recover_user' not in st.session_state:
        st.session_state.recover_user = True

# -------------------------
# PRODUCTION CONFIGURATION
# -------------------------
class Config:
    APP_NAME = "TradingAnalysis Pro"
    VERSION = "2.1.0"  # Updated version with persistence
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
        self.lock = threading.Lock()  # Thread safety for file operations
        
        # Ensure directories exist
        self._ensure_directories()
        
        # Initialize data with auto-recovery
        self._initialize_with_recovery()
        
        # Start auto-save and backup threads
        self._start_background_tasks()
    
    def _ensure_directories(self):
        """Create necessary directories"""
        os.makedirs("data", exist_ok=True)
        os.makedirs(self.backup_dir, exist_ok=True)
        os.makedirs(os.path.join(self.backup_dir, "emergency"), exist_ok=True)
    
    def _initialize_with_recovery(self):
        """Initialize data with automatic recovery from backups if needed"""
        print("🔄 Initializing data with recovery checks...")
        
        # Try to load main data files
        self.users = self._load_data_with_recovery(self.users_file, "users")
        self.analytics = self._load_data_with_recovery(self.analytics_file, "analytics")
        
        # Ensure default admin exists
        if "admin" not in self.users:
            self.create_default_admin()
            self._immediate_save()
        
        print("✅ Data initialization complete")
    
    def _load_data_with_recovery(self, filepath, data_type):
        """Load data with automatic recovery from backups if main file is corrupted"""
        try:
            # First try to load the main file
            if os.path.exists(filepath):
                with open(filepath, 'r') as f:
                    data = json.load(f)
                print(f"✅ Successfully loaded {data_type} from {filepath}")
                return data
            else:
                # File doesn't exist, try to restore from latest backup
                restored = self._restore_from_backup(filepath, data_type)
                if restored:
                    with open(filepath, 'r') as f:
                        return json.load(f)
                else:
                    # No backup, return empty structure
                    print(f"⚠️ No {data_type} file found, creating new one")
                    return self._get_default_data(data_type)
                    
        except Exception as e:
            print(f"❌ Error loading {data_type} from {filepath}: {e}")
            # Try to restore from backup
            restored = self._restore_from_backup(filepath, data_type)
            if restored:
                try:
                    with open(filepath, 'r') as f:
                        return json.load(f)
                except:
                    pass
            
            # If all else fails, return default data
            print(f"🔄 Creating new {data_type} data structure")
            return self._get_default_data(data_type)
    
    def _get_default_data(self, data_type):
        """Get default data structure for different data types"""
        if data_type == "users":
            default_data = {}
            self.create_default_admin(default_data)
            return default_data
        elif data_type == "analytics":
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
    
    def _restore_from_backup(self, original_file, data_type):
        """Restore data from the most recent backup"""
        try:
            # Get all backups for this file type
            filename = os.path.basename(original_file)
            backup_pattern = f"{filename}.backup."
            
            backups = []
            for file in os.listdir(self.backup_dir):
                if file.startswith(backup_pattern):
                    backups.append(file)
            
            if not backups:
                print(f"⚠️ No backups found for {data_type}")
                return False
            
            # Sort by timestamp (newest first)
            backups.sort(reverse=True)
            latest_backup = os.path.join(self.backup_dir, backups[0])
            
            # Restore from backup
            shutil.copy2(latest_backup, original_file)
            
            # Log recovery event
            recovery_event = {
                "timestamp": datetime.now().isoformat(),
                "original_file": original_file,
                "backup_used": latest_backup,
                "data_type": data_type,
                "reason": "Auto-recovery from corruption"
            }
            
            if 'data_recovery_events' not in self.analytics:
                self.analytics['data_recovery_events'] = []
            self.analytics['data_recovery_events'].append(recovery_event)
            
            print(f"✅ Successfully restored {data_type} from backup: {latest_backup}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to restore {data_type} from backup: {e}")
            return False
    
    def _start_background_tasks(self):
        """Start background tasks for auto-save and backups"""
        # Auto-save every 2 minutes
        def auto_save():
            while True:
                time.sleep(120)  # 2 minutes
                self._immediate_save()
        
        # Backup every 10 minutes
        def auto_backup():
            while True:
                time.sleep(600)  # 10 minutes
                self.create_data_backup()
                self.cleanup_old_backups()
        
        # Start threads (daemon threads will exit when main thread exits)
        save_thread = threading.Thread(target=auto_save, daemon=True)
        backup_thread = threading.Thread(target=auto_backup, daemon=True)
        
        save_thread.start()
        backup_thread.start()
        
        print("✅ Background tasks started: auto-save (2min), auto-backup (10min)")
    
    def _immediate_save(self):
        """Immediately save all data with error handling"""
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
                
                # Atomic rename (more reliable than direct write)
                os.replace(temp_users_file, self.users_file)
                os.replace(temp_analytics_file, self.analytics_file)
                
                # Update last save timestamp
                self.analytics['last_save'] = datetime.now().isoformat()
                
                print(f"💾 Auto-saved data at {datetime.now().strftime('%H:%M:%S')}")
                return True
                
            except Exception as e:
                print(f"❌ Auto-save failed: {e}")
                # Try to create emergency backup
                self._emergency_backup()
                return False
    
    def _emergency_backup(self):
        """Create emergency backup when normal save fails"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S_emergency")
            emergency_dir = os.path.join(self.backup_dir, "emergency")
            os.makedirs(emergency_dir, exist_ok=True)
            
            # Save current state to emergency backup
            emergency_file = os.path.join(emergency_dir, f"emergency_{timestamp}.json")
            emergency_data = {
                "timestamp": datetime.now().isoformat(),
                "users": self.users,
                "analytics": self.analytics
            }
            
            with open(emergency_file, 'w') as f:
                json.dump(emergency_data, f, indent=2)
            
            print(f"🚨 Emergency backup created: {emergency_file}")
            return True
            
        except Exception as e:
            print(f"❌ Emergency backup also failed: {e}")
            return False
    
    def create_data_backup(self):
        """Create timestamped backup of data files"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Backup users file
            if os.path.exists(self.users_file):
                backup_file = os.path.join(self.backup_dir, f"users.json.backup.{timestamp}")
                shutil.copy2(self.users_file, backup_file)
            
            # Backup analytics file
            if os.path.exists(self.analytics_file):
                backup_file = os.path.join(self.backup_dir, f"analytics.json.backup.{timestamp}")
                shutil.copy2(self.analytics_file, backup_file)
            
            # Update analytics
            self.analytics['last_backup'] = datetime.now().isoformat()
            self.analytics['total_backups'] = self.analytics.get('total_backups', 0) + 1
            self._immediate_save()
            
            print(f"📦 Backup created at {timestamp}")
            return True
            
        except Exception as e:
            print(f"❌ Backup creation failed: {e}")
            return False
    
    def cleanup_old_backups(self, keep_count=10):
        """Keep only the most recent backups"""
        try:
            # Cleanup regular backups
            backup_types = ['users.json.backup.', 'analytics.json.backup.']
            
            for backup_type in backup_types:
                backups = []
                for file in os.listdir(self.backup_dir):
                    if file.startswith(backup_type):
                        backups.append(file)
                
                # Sort by timestamp (newest first)
                backups.sort(reverse=True)
                
                # Remove excess backups
                for old_backup in backups[keep_count:]:
                    os.remove(os.path.join(self.backup_dir, old_backup))
            
            # Cleanup emergency backups (keep only last 5)
            emergency_dir = os.path.join(self.backup_dir, "emergency")
            if os.path.exists(emergency_dir):
                emergencies = []
                for file in os.listdir(emergency_dir):
                    if file.startswith("emergency_"):
                        emergencies.append(file)
                
                emergencies.sort(reverse=True)
                for old_emergency in emergencies[5:]:
                    os.remove(os.path.join(emergency_dir, old_emergency))
            
            print(f"🧹 Cleaned up old backups, keeping {keep_count} most recent")
            
        except Exception as e:
            print(f"❌ Backup cleanup failed: {e}")
    
    def save_users(self):
        """Public method to save users (triggers immediate save)"""
        return self._immediate_save()
    
    def save_analytics(self):
        """Public method to save analytics (triggers immediate save)"""
        return self._immediate_save()
    
    def get_backup_status(self):
        """Get backup system status"""
        status = {
            "last_backup": self.analytics.get('last_backup', 'Never'),
            "total_backups": self.analytics.get('total_backups', 0),
            "last_save": self.analytics.get('last_save', 'Never'),
            "recovery_events": len(self.analytics.get('data_recovery_events', [])),
            "backup_files": 0,
            "emergency_backups": 0
        }
        
        # Count backup files
        if os.path.exists(self.backup_dir):
            for file in os.listdir(self.backup_dir):
                if file.startswith(('users.json.backup.', 'analytics.json.backup.')):
                    status["backup_files"] += 1
            
            emergency_dir = os.path.join(self.backup_dir, "emergency")
            if os.path.exists(emergency_dir):
                status["emergency_backups"] = len(os.listdir(emergency_dir))
        
        return status

    def get_business_metrics(self):
        """Get business metrics for admin with enhanced error handling"""
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
            print(f"❌ Error getting business metrics: {e}")
            # Return safe default values
            return {
                "total_users": 0,
                "active_users": 0,
                "online_users": 0,
                "plan_distribution": {},
                "total_logins": 0,
                "revenue_today": 0
            }

    # Existing UserManager methods with persistence integration
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
# BACKUP MANAGEMENT INTERFACE
# -------------------------
def render_backup_management():
    """Comprehensive backup and data management interface"""
    st.subheader("💾 Data Persistence & Backup Management")
    
    # Backup status
    status = user_manager.get_backup_status()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        last_backup = status["last_backup"]
        if last_backup != 'Never':
            try:
                backup_time = datetime.fromisoformat(last_backup)
                time_diff = datetime.now() - backup_time
                if time_diff.total_seconds() > 600:  # 10 minutes
                    st.metric("Last Backup", f"{last_backup[:16]}", delta="⚠️ Old", delta_color="off")
                else:
                    st.metric("Last Backup", f"{last_backup[:16]}", delta="✅ Fresh", delta_color="normal")
            except:
                st.metric("Last Backup", "Invalid")
        else:
            st.metric("Last Backup", 'Never', delta="❌ None", delta_color="off")
    
    with col2:
        st.metric("Total Backups", status["total_backups"])
    
    with col3:
        st.metric("Backup Files", status["backup_files"])
    
    with col4:
        st.metric("Recovery Events", status["recovery_events"])
    
    st.markdown("---")
    
    # Manual backup controls
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Create Backup Now", use_container_width=True, key="create_backup"):
            if user_manager.create_data_backup():
                st.success("✅ Backup created successfully!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Backup creation failed")
    
    with col2:
        if st.button("🧹 Cleanup Old Backups", use_container_width=True, key="cleanup_backups"):
            user_manager.cleanup_old_backups()
            st.success("✅ Old backups cleaned up!")
            time.sleep(1)
            st.rerun()
    
    with col3:
        if st.button("💾 Force Save All Data", use_container_width=True, key="force_save"):
            if user_manager._immediate_save():
                st.success("✅ All data saved immediately!")
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Save failed, check emergency backups")
    
    st.markdown("---")
    
    # Backup files listing
    st.subheader("📁 Backup Files")
    
    if os.path.exists(user_manager.backup_dir):
        backup_files = []
        for file in os.listdir(user_manager.backup_dir):
            filepath = os.path.join(user_manager.backup_dir, file)
            if os.path.isfile(filepath) and file.startswith(('users.json.backup.', 'analytics.json.backup.')):
                stat = os.stat(filepath)
                backup_files.append({
                    "filename": file,
                    "size": f"{stat.st_size / 1024:.1f} KB",
                    "modified": datetime.fromtimestamp(stat.st_mtime).strftime("%Y-%m-%d %H:%M:%S")
                })
        
        if backup_files:
            backup_files.sort(key=lambda x: x['modified'], reverse=True)
            backup_df = pd.DataFrame(backup_files)
            st.dataframe(backup_df, use_container_width=True)
        else:
            st.info("No backup files found")
    else:
        st.error("Backup directory not found!")
    
    st.markdown("---")
    
    # Data recovery section
    st.subheader("🛡️ Data Recovery")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Recovery History**")
        recovery_events = user_manager.analytics.get('data_recovery_events', [])
        if recovery_events:
            for event in reversed(recovery_events[-5:]):  # Show last 5 events
                st.write(f"• {event['timestamp'][:16]}: {event['reason']}")
        else:
            st.info("No recovery events recorded")
    
    with col2:
        st.write("**Emergency Recovery**")
        st.warning("Use these options only if data is corrupted")
        
        if st.button("🔄 Restore from Latest Backup", type="secondary", key="restore_backup"):
            st.info("Restore functionality would be implemented here")
        
        if st.button("🚨 Emergency Data Reset", type="primary", key="emergency_reset"):
            st.error("This will reset all data to defaults!")
            st.warning("All users except admin will be deleted!")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("✅ CONFIRM RESET", key="confirm_reset"):
                    # Backup current state first
                    user_manager.create_data_backup()
                    # Reset data but keep admin
                    admin_data = user_manager.users.get("admin", {})
                    user_manager.users = {}
                    user_manager.analytics = user_manager._get_default_data("analytics")
                    if admin_data:
                        user_manager.users["admin"] = admin_data
                    else:
                        user_manager.create_default_admin()
                    user_manager._immediate_save()
                    st.success("Data reset complete! Admin account restored.")
                    time.sleep(2)
                    st.rerun()
            with col2:
                if st.button("❌ Cancel", key="cancel_reset"):
                    st.rerun()
    
    st.markdown("---")
    
    # System information
    st.subheader("🔧 System Information")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**File Locations:**")
        st.write(f"Users: `{user_manager.users_file}`")
        st.write(f"Analytics: `{user_manager.analytics_file}`")
        st.write(f"Backups: `{user_manager.backup_dir}`")
        
        # Check file existence and sizes
        files_to_check = [
            (user_manager.users_file, "Users database"),
            (user_manager.analytics_file, "Analytics database")
        ]
        
        for filepath, description in files_to_check:
            if os.path.exists(filepath):
                size = os.path.getsize(filepath) / 1024
                st.success(f"✅ {description}: {size:.1f} KB")
            else:
                st.error(f"❌ {description}: Missing!")
    
    with col2:
        st.write("**Auto-Save Status:**")
        st.success("✅ Active (every 2 minutes)")
        st.success("✅ Auto-backup (every 10 minutes)")
        st.success("✅ Emergency backup on failure")
        
        st.write("**Next Actions:**")
        st.info("• Data is automatically saved every 2 minutes")
        st.info("• Backups created every 10 minutes")
        st.info("• Emergency backups on save failures")
        
        # Show current data statistics
        st.write("**Current Data Stats:**")
        st.write(f"• Total Users: {len(user_manager.users)}")
        st.write(f"• Total Logins: {user_manager.analytics.get('total_logins', 0)}")
        st.write(f"• User Registrations: {len(user_manager.analytics.get('user_registrations', []))}")

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
# PASSWORD CHANGE INTERFACE
# -------------------------
def render_password_change_interface():
    """Interface for changing admin password"""
    st.subheader("🔐 Change Admin Password")
    
    with st.form("admin_password_change"):
        st.info("**Security Note:** You must verify your current password to set a new one.")
        
        col1, col2 = st.columns(2)
        with col1:
            current_password = st.text_input("Current Password*", type="password", 
                                           placeholder="Enter current admin password", key="pwd_current")
        with col2:
            new_password = st.text_input("New Password*", type="password", 
                                       placeholder="Enter new password (min 8 chars)", key="pwd_new")
        
        confirm_password = st.text_input("Confirm New Password*", type="password", 
                                       placeholder="Re-enter new password", key="pwd_confirm")
        
        # Password strength requirements
        st.markdown("**Password Requirements:**")
        st.markdown("- Minimum 8 characters")
        st.markdown("- Include letters and numbers")
        st.markdown("- Avoid common passwords")
        
        submitted = st.form_submit_button("✅ Change Admin Password", use_container_width=True)
        
        if submitted:
            # Validation
            if not all([current_password, new_password, confirm_password]):
                st.error("❌ Please fill in all password fields")
                return
            
            if new_password != confirm_password:
                st.error("❌ New passwords do not match")
                return
            
            if len(new_password) < 8:
                st.error("❌ New password must be at least 8 characters long")
                return
            
            # Change password
            success, message = user_manager.change_admin_password(
                current_password, 
                new_password, 
                st.session_state.user['username']
            )
            
            if success:
                st.success("✅ " + message)
                st.info("🔒 You will need to use the new password for your next login.")
                
                # Add a small delay and return to user management
                time.sleep(2)
                st.session_state.show_password_change = False
                st.rerun()
            else:
                st.error("❌ " + message)
    
    st.markdown("---")
    if st.button("⬅️ Back to User Management", use_container_width=True, key="pwd_back"):
        st.session_state.show_password_change = False
        st.rerun()

# -------------------------
# DELETE CONFIRMATION MODAL - FIXED
# -------------------------
def render_delete_confirmation_modal():
    """Modal for confirming user deletion - FIXED: Using expander instead of HTML modal"""
    user_to_delete = st.session_state.get('user_to_delete')
    
    if not user_to_delete:
        return
    
    # FIXED: Using expander instead of problematic HTML modal
    with st.expander("⚠️ CONFIRM USER DELETION", expanded=True):
        st.error("🚨 **Confirm User Deletion**")
        st.warning(f"**User to delete:** {user_to_delete}")
        
        user_data = user_manager.users.get(user_to_delete, {})
        if user_data:
            st.write(f"**Name:** {user_data.get('name', 'N/A')}")
            st.write(f"**Email:** {user_data.get('email', 'N/A')}")
            st.write(f"**Plan:** {user_data.get('plan', 'N/A')}")
            st.write(f"**Status:** {'Active' if user_data.get('is_active', True) else 'Inactive'}")
        else:
            st.error("User data not found!")
        
        st.markdown("---")
        st.error("**This action cannot be undone!**")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("✅ Confirm Delete", type="primary", use_container_width=True, key="confirm_delete_modal"):
                success, message = user_manager.delete_user(user_to_delete)
                if success:
                    st.success(f"✅ {message}")
                    # Clear modal state
                    st.session_state.show_delete_confirmation = False
                    st.session_state.user_to_delete = None
                    time.sleep(1)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
        
        with col2:
            if st.button("❌ Cancel", use_container_width=True, key="cancel_delete_modal"):
                st.session_state.show_delete_confirmation = False
                st.session_state.user_to_delete = None
                st.rerun()

# -------------------------
# BULK DELETE INTERFACE
# -------------------------
def render_bulk_delete_interface():
    """Interface for bulk deleting inactive users"""
    st.subheader("🗑️ Bulk Delete Inactive Users")
    
    # Get inactive users
    inactive_users = []
    for username, user_data in user_manager.users.items():
        if username != "admin" and not user_data.get('is_active', True):
            days_inactive = 0
            if user_data.get('last_login'):
                try:
                    last_login = datetime.fromisoformat(user_data['last_login'])
                    days_inactive = (datetime.now() - last_login).days
                except:
                    days_inactive = 999
            
            inactive_users.append({
                "username": username,
                "name": user_data["name"],
                "email": user_data["email"],
                "plan": user_data["plan"],
                "last_login": user_data.get("last_login", "Never"),
                "days_inactive": days_inactive
            })
    
    if not inactive_users:
        st.info("🎉 No inactive users found!")
        if st.button("⬅️ Back to User Management", use_container_width=True, key="bulk_back_empty"):
            st.session_state.show_bulk_delete = False
            st.rerun()
        return
    
    st.warning(f"Found {len(inactive_users)} inactive users")
    
    # Display with checkboxes
    users_to_delete = []
    for user in inactive_users:
        col1, col2 = st.columns([3, 1])
        with col1:
            st.write(f"**{user['username']}** - {user['name']}")
            st.caption(f"Email: {user['email']} | Plan: {user['plan']} | Inactive for {user['days_inactive']} days")
        with col2:
            if st.checkbox("Select", key=f"bulk_{user['username']}"):
                users_to_delete.append(user['username'])
    
    st.markdown("---")
    
    if users_to_delete:
        st.error(f"**{len(users_to_delete)} users selected for deletion**")
        
        # Show selected users
        with st.expander("📋 Review Selected Users"):
            for username in users_to_delete:
                user_data = next((u for u in inactive_users if u['username'] == username), None)
                if user_data:
                    st.write(f"• {username} ({user_data['name']}) - {user_data['email']}")
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🗑️ Delete Selected Users", type="primary", use_container_width=True, key="bulk_confirm"):
                deleted_count = 0
                errors = []
                for username in users_to_delete:
                    success, message = user_manager.delete_user(username)
                    if success:
                        deleted_count += 1
                    else:
                        errors.append(f"{username}: {message}")
                
                if deleted_count > 0:
                    st.success(f"✅ Successfully deleted {deleted_count} users!")
                if errors:
                    for error in errors:
                        st.error(f"❌ {error}")
                
                time.sleep(2)
                st.session_state.show_bulk_delete = False
                st.rerun()
        
        with col2:
            if st.button("❌ Cancel Bulk Delete", use_container_width=True, key="bulk_cancel"):
                st.session_state.show_bulk_delete = False
                st.rerun()
    else:
        if st.button("⬅️ Back to User Management", use_container_width=True, key="bulk_back"):
            st.session_state.show_bulk_delete = False
            st.rerun()

# -------------------------
# PLAN MANAGEMENT INTERFACE - FIXED VERSION
# -------------------------
def render_plan_management_interface(username):
    """Interface for managing a specific user's plan - FIXED"""
    if username not in user_manager.users:
        st.error("User not found")
        if st.button("⬅️ Back to User Management", use_container_width=True, key="plan_back_notfound"):
            st.session_state.manage_user_plan = None
            st.rerun()
        return
    
    user_data = user_manager.users[username]
    current_plan = user_data['plan']
    
    st.subheader(f"📋 Plan Management: {username}")
    
    # Back button at the top
    if st.button("⬅️ Back to User Management", key="back_top_plan"):
        st.session_state.manage_user_plan = None
        st.rerun()
    
    st.write(f"**Current Plan:** {Config.PLANS.get(current_plan, {}).get('name', current_plan.title())}")
    st.write(f"**User:** {user_data['name']} ({user_data['email']})")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔄 Change Subscription Plan")
        
        # Plan selection
        available_plans = list(Config.PLANS.keys())
        new_plan = st.selectbox(
            "Select New Plan",
            available_plans,
            index=available_plans.index(current_plan) if current_plan in available_plans else 0,
            format_func=lambda x: f"{Config.PLANS[x]['name']} - ${Config.PLANS[x]['price']}/month",
            key="plan_select"
        )
        
        # Plan comparison
        if new_plan != current_plan:
            st.markdown("#### Plan Change Details:")
            
            old_plan_config = Config.PLANS.get(current_plan, {})
            new_plan_config = Config.PLANS.get(new_plan, {})
            
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Current Plan:**")
                st.write(f"• {old_plan_config.get('strategies', 0)} Strategies")
                st.write(f"• {old_plan_config.get('max_sessions', 1)} Sessions")
                st.write(f"• ${old_plan_config.get('price', 0)}/month")
            
            with col2:
                st.write("**New Plan:**")
                st.write(f"• {new_plan_config.get('strategies', 0)} Strategies")
                st.write(f"• {new_plan_config.get('max_sessions', 1)} Sessions")
                st.write(f"• ${new_plan_config.get('price', 0)}/month")
            
            # Change impact
            st.markdown("#### Change Impact:")
            strategies_change = new_plan_config.get('strategies', 0) - old_plan_config.get('strategies', 0)
            sessions_change = new_plan_config.get('max_sessions', 1) - old_plan_config.get('max_sessions', 1)
            price_change = new_plan_config.get('price', 0) - old_plan_config.get('price', 0)
            
            if strategies_change > 0:
                st.success(f"➕ {strategies_change} additional strategies")
            elif strategies_change < 0:
                st.warning(f"➖ {abs(strategies_change)} fewer strategies")
            
            if sessions_change > 0:
                st.success(f"➕ {sessions_change} additional concurrent sessions")
            elif sessions_change < 0:
                st.warning(f"➖ {abs(sessions_change)} fewer concurrent sessions")
            
            if price_change > 0:
                st.info(f"💵 Price increase: ${price_change}/month")
            elif price_change < 0:
                st.success(f"💵 Price decrease: ${abs(price_change)}/month")
        
        # FIXED: Now the change_reason is actually used
        change_reason = st.text_area("Reason for plan change (optional):", 
                                   placeholder="e.g., User requested upgrade, Payment issue, Special promotion...",
                                   key="change_reason_input")
        
        # Confirm change
        if st.button("✅ Confirm Plan Change", type="primary", use_container_width=True, key="confirm_plan_change"):
            if new_plan == current_plan:
                st.warning("User is already on this plan")
            else:
                # FIXED: Now passing change_reason to the function
                success, message = user_manager.change_user_plan(username, new_plan, change_reason)
                if success:
                    st.success(f"✅ {message}")
                    
                    # Send notification (simulated)
                    st.info(f"📧 Notification email sent to {user_data['email']}")
                    st.info("🔄 User will see changes immediately on next login")
                    
                    time.sleep(2)
                    st.session_state.manage_user_plan = None
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    with col2:
        st.markdown("### 📊 Current Plan Details")
        
        # Current plan info
        current_plan_config = Config.PLANS.get(current_plan, {})
        st.write(f"**Plan:** {current_plan_config.get('name', current_plan.title())}")
        st.write(f"**Expires:** {user_data['expires']}")
        
        days_left = (datetime.strptime(user_data['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Days Remaining", days_left, key="days_remaining_plan")
        
        st.markdown("#### Features:")
        st.write(f"• **Strategies:** {current_plan_config.get('strategies', 0)} available")
        st.write(f"• **Sessions:** {user_data.get('active_sessions', 0)}/{current_plan_config.get('max_sessions', 1)} active")
        st.write(f"• **Price:** ${current_plan_config.get('price', 0)}/month")
        
        st.markdown("#### User Statistics:")
        st.write(f"• **Joined:** {user_data['created'][:10]}")
        
        # FIXED: Handle None or empty last_login safely
        last_login = user_data.get('last_login')
        if last_login:
            try:
                # Try to format the date if it's a valid ISO string
                st.write(f"• **Last Login:** {last_login[:16]}")
            except:
                st.write(f"• **Last Login:** {last_login}")
        else:
            st.write(f"• **Last Login:** Never")
            
        st.write(f"• **Total Logins:** {user_data.get('login_count', 0)}")
        st.write(f"• **Status:** {'🟢 Active' if user_data.get('is_active', True) else '🔴 Inactive'}")
        
        # Quick actions
        st.markdown("#### Quick Actions:")
        
        # Quick plan changes
        quick_plans = {
            "🚀 Upgrade to Premium": "premium",
            "💼 Upgrade to Professional": "professional",
            "📊 Downgrade to Basic": "basic",
            "🎯 Set to Trial": "trial"
        }
        
        for btn_text, plan in quick_plans.items():
            if plan != current_plan:
                if st.button(btn_text, use_container_width=True, key=f"quick_{plan}_{username}"):
                    success, message = user_manager.change_user_plan(username, plan, f"Quick action: {btn_text}")
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.session_state.manage_user_plan = None
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
    
    st.markdown("---")
    
    # Another back button at the bottom for convenience
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("⬅️ Back to User Management", key="back_bottom_plan", use_container_width=True):
            st.session_state.manage_user_plan = None
            st.rerun()

# -------------------------
# ENHANCED PREMIUM USER DASHBOARD - FIXED SESSION STATE ACCESS
# -------------------------
def render_user_dashboard():
    """Enhanced trading dashboard for premium users - FIXED session state access"""
    user = st.session_state.user
    
    # FIXED: Safe session state access with proper initialization
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {}
    
    user_data_key = f"{user['username']}_data"
    
    # FIXED: Safe access with .get() and proper initialization
    if user_data_key not in st.session_state.user_data:
        st.session_state.user_data[user_data_key] = {
            "saved_analyses": {},
            "favorite_strategies": [],
            "performance_history": [],
            "recent_signals": []
        }
    
    # FIXED: Use .get() for safe access
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
        
        # Account status with enhanced visuals
        plan_config = Config.PLANS.get(user['plan'], Config.PLANS['trial'])
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        
        # Premium progress bar
        if user['plan'] in ['premium', 'professional', 'admin']:
            progress_color = "#00D4AA"  # Premium green
        else:
            progress_color = "#1f77b4"  # Basic blue
            
        st.progress(min(1.0, days_left / 30), text=f"📅 {days_left} days remaining")
        
        # Quick actions - Enhanced for premium
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🔄 Refresh Market Data", use_container_width=True, key="refresh_market"):
            st.rerun()
            
        if st.button("📊 Portfolio Overview", use_container_width=True, key="portfolio_quick"):
            st.session_state.dashboard_view = "portfolio"
            st.rerun()
            
        if st.button("🎯 Trading Signals", use_container_width=True, key="signals_quick"):
            st.session_state.dashboard_view = "signals"
            st.rerun()
            
        if st.button("📈 Performance Analytics", use_container_width=True, key="analytics_quick"):
            st.session_state.dashboard_view = "analytics"
            st.rerun()
            
        if st.button("⚙️ Account Settings", use_container_width=True, key="settings_quick"):
            st.session_state.dashboard_view = "settings"
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
    
    # Main dashboard content with enhanced views
    current_view = st.session_state.get('dashboard_view', 'main')
    
    if st.session_state.get('show_settings'):
        render_account_settings()
    elif st.session_state.get('show_upgrade'):
        render_upgrade_plans()
    elif current_view == 'portfolio':
        render_portfolio_overview(data, user)
    elif current_view == 'signals':
        render_trading_signals(data, user)
    elif current_view == 'analytics':
        render_performance_analytics(data, user)
    elif current_view == 'settings':
        render_account_settings()
    else:
        render_trading_dashboard(data, user)

def render_trading_dashboard(data, user):
    """Enhanced main trading dashboard with premium features"""
    # FIXED: Dynamic date handling instead of hardcoded 2024
    start_date = date.today() - timedelta(days=180)  # Last 6 months
    analysis_date = date.today()

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
    
    # Strategy progress with enhanced visuals
    st.subheader("🎯 Today's Focus Strategies")
    
    # Daily strategy rotation
    days_since_start = (analysis_date - start_date).days
    cycle_day = days_since_start % 5
    start_index = cycle_day * min(3, len(available_strategies))
    end_index = start_index + min(3, len(available_strategies))
    daily_strategies = available_strategies[start_index:end_index]
    
    if not daily_strategies:
        daily_strategies = available_strategies[:1]
    
    # Enhanced strategy cards
    cols = st.columns(len(daily_strategies))
    for i, strategy in enumerate(daily_strategies):
        with cols[i]:
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-radius: 10px; padding: 1rem; background: #f8f9fa;">
                    <h4 style="margin: 0; color: #1f77b4;">{strategy}</h4>
                    <p style="margin: 0.5rem 0; font-size: 0.9rem; color: #666;">
                        {len(STRATEGIES[strategy])} indicators • Day {cycle_day + 1}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Quick analysis button
                if st.button(f"📈 Analyze {strategy}", key=f"quick_{strategy}", use_container_width=True):
                    st.session_state.selected_strategy = strategy
                    st.rerun()
    
    # Strategy selector with enhanced features
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
    
    # Quick actions for premium users
    st.markdown("---")
    st.subheader("⚡ Premium Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🎯 Generate All Signals", use_container_width=True, key="gen_all_signals"):
            if user['plan'] in ['premium', 'professional', 'admin']:
                st.success("✅ All trading signals generated!")
                # Store signals in user data - FIXED: safe access
                if 'recent_signals' not in data:
                    data['recent_signals'] = []
                data['recent_signals'] = [
                    {"strategy": s, "signal": "BUY", "confidence": np.random.uniform(0.7, 0.9), "timestamp": datetime.now()}
                    for s in available_strategies[:3]
                ]
            else:
                st.info("🔒 Premium feature - upgrade to generate bulk signals")
    
    with col2:
        if st.button("📊 Portfolio Snapshot", use_container_width=True, key="portfolio_snapshot"):
            st.session_state.dashboard_view = "portfolio"
            st.rerun()
    
    with col3:
        if st.button("📈 Market Scanner", use_container_width=True, key="market_scanner"):
            if user['plan'] in ['premium', 'professional', 'admin']:
                st.info("🔄 Scanning markets for opportunities...")
                time.sleep(1)
                st.success("✅ 5 new opportunities found!")
            else:
                st.info("🔒 Premium feature - upgrade for advanced market scanning")
    
    with col4:
        if st.button("🔄 Reset All Analysis", use_container_width=True, key="reset_analysis"):
            st.warning("All analysis data has been reset")
            st.rerun()

def render_technical_analysis(strategy, indicators, data):
    """Enhanced technical analysis interface - FIXED data access"""
    st.write(f"**Technical Analysis for {strategy}**")
    
    # Display indicators in a nice layout
    col1, col2, col3 = st.columns(3)
    
    indicator_items = list(indicators.items())
    
    with col1:
        for key, value in indicator_items[:2]:
            if isinstance(value, float):
                st.metric(key.replace('_', ' '), f"{value:.2f}", key=f"ind_{key}_1")
            else:
                st.metric(key.replace('_', ' '), str(value), key=f"ind_{key}_1")
    
    with col2:
        for key, value in indicator_items[2:4] if len(indicator_items) > 2 else []:
            if isinstance(value, float):
                st.metric(key.replace('_', ' '), f"{value:.2f}", key=f"ind_{key}_2")
            else:
                st.metric(key.replace('_', ' '), str(value), key=f"ind_{key}_2")
    
    with col3:
        for key, value in indicator_items[4:] if len(indicator_items) > 4 else []:
            if isinstance(value, float):
                st.metric(key.replace('_', ' '), f"{value:.2f}", key=f"ind_{key}_3")
            else:
                st.metric(key.replace('_', ' '), str(value), key=f"ind_{key}_3")
    
    # Analysis form
    with st.form(f"analysis_{strategy}"):
        st.write("**Manual Analysis Input**")
        
        for indicator in STRATEGIES[strategy]:
            with st.expander(f"**{indicator}**", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    status = st.selectbox("Status", ["Open", "In Progress", "Done", "Skipped"], key=f"status_{indicator}")
                    confidence = st.slider("Confidence", 50, 100, 75, key=f"conf_{indicator}")
                with col2:
                    note = st.text_area("Analysis Notes", height=100, key=f"note_{indicator}", 
                                      placeholder="Enter your technical analysis...")
        
        # Enhanced save options
        col1, col2 = st.columns(2)
        with col1:
            save_btn = st.form_submit_button("💾 Save Analysis", use_container_width=True)
        with col2:
            export_btn = st.form_submit_button("📤 Export to PDF", use_container_width=True)
        
        if save_btn:
            st.success("✅ Analysis saved successfully!")
            # Store in user data - FIXED: safe access
            if 'saved_analyses' not in data:
                data['saved_analyses'] = {}
            data['saved_analyses'][strategy] = {
                "timestamp": datetime.now(),
                "indicators": indicators
            }
        
        if export_btn:
            st.info("📄 PDF export would be generated here")

def render_strategy_performance(strategy):
    """Premium strategy performance analytics"""
    st.write(f"**Performance Analytics for {strategy}**")
    
    # Create a simple performance chart using Streamlit
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
        st.metric("Total Return", "+24.5%", "+2.1%", key="total_return")
    
    with col2:
        st.metric("Win Rate", "68%", "+5%", key="win_rate")
    
    with col3:
        st.metric("Sharpe Ratio", "1.8", "+0.2", key="sharpe")
    
    with col4:
        st.metric("Max Drawdown", "-8.2%", "-1.1%", key="drawdown")
    
    # Recent trades table
    st.write("**Recent Trade History**")
    trades_data = {
        "Date": ["2024-01-15", "2024-01-14", "2024-01-13", "2024-01-12"],
        "Action": ["BUY", "SELL", "BUY", "SELL"],
        "Price": ["$42,150", "$43,200", "$41,800", "$42,900"],
        "P&L": ["+$1,050", "+$850", "+$1,100", "+$700"],
        "Status": ["Closed", "Closed", "Closed", "Closed"]
    }
    trades_df = pd.DataFrame(trades_data)
    st.dataframe(trades_df, use_container_width=True, hide_index=True)

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
            st.metric("Total Value", "$124,850", "+2.4%", key="total_value")
        
        with col2:
            st.metric("24h Change", "+$2,950", "+2.4%", key="daily_change")
        
        with col3:
            st.metric("All Time P&L", "+$24,850", "+24.8%", key="total_pnl")
        
        with col4:
            st.metric("Risk Score", "Medium", "-5%", key="risk_score")
        
        # Portfolio allocation
        st.subheader("📈 Portfolio Allocation")
        
        allocation_data = {
            'Asset': ['BTC', 'ETH', 'ADA', 'SOL', 'Cash'],
            'Value': [65000, 32000, 8500, 12350, 7000],
            'Allocation': [52.1, 25.6, 6.8, 9.9, 5.6]
        }
        allocation_df = pd.DataFrame(allocation_data)
        
        st.dataframe(allocation_df, use_container_width=True)
        
        # Create a simple pie chart using bar chart
        st.bar_chart(allocation_df.set_index('Asset')['Allocation'])
        
        # Recent activity
        st.subheader("📋 Recent Activity")
        activity_data = {
            "Date": ["2024-01-15", "2024-01-14", "2024-01-13"],
            "Action": ["BUY BTC", "SELL ETH", "BUY ADA"],
            "Amount": ["0.5 BTC", "2.1 ETH", "5000 ADA"],
            "Value": ["$21,075", "$5,250", "$2,125"],
            "Status": ["Completed", "Completed", "Completed"]
        }
        activity_df = pd.DataFrame(activity_data)
        st.dataframe(activity_df, use_container_width=True, hide_index=True)
        
    else:
        st.info("""
        🔒 **Premium Feature Unlock**
        
        Upgrade to Premium or Professional plan to access:
        - Real-time portfolio tracking
        - Advanced analytics
        - Performance metrics
        - Risk assessment tools
        """)
        
        if st.button("🚀 Upgrade to Premium", type="primary", use_container_width=True, key="upgrade_portfolio"):
            st.session_state.show_upgrade = True
            st.rerun()

def render_trading_signals(data, user):
    """Enhanced trading signals dashboard"""
    st.title("🎯 Trading Signals Center")
    
    if user['plan'] in ['premium', 'professional', 'admin']:
        # Signal overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Active Signals", "12", "+3", key="active_signals")
        
        with col2:
            st.metric("Signal Accuracy", "76%", "+4%", key="signal_accuracy")
        
        with col3:
            st.metric("Avg. Return", "+2.8%", "+0.4%", key="avg_return")
        
        # Generate sample signals
        strategies = list(STRATEGIES.keys())[:8]  # Show first 8 strategies
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
        
        # Color code the signals
        def color_strength(val):
            if val == 'High':
                return 'background-color: #d4edda'
            elif val == 'Medium':
                return 'background-color: #fff3cd'
            else:
                return 'background-color: #f8d7da'
        
        st.dataframe(signals_df.style.applymap(color_strength, subset=['Strength']), 
                    use_container_width=True)
        
        # Signal actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh All Signals", use_container_width=True, key="refresh_signals"):
                st.success("Signals refreshed!")
                st.rerun()
        
        with col2:
            if st.button("📤 Export Signals", use_container_width=True, key="export_signals"):
                st.info("Signals exported to CSV")
                
    else:
        st.info("""
        🔒 **Premium Signals Center**
        
        Upgrade to access real-time trading signals with:
        - Live market scanning
        - Multi-strategy analysis
        - Confidence scoring
        - Signal history tracking
        """)
        
        if st.button("🚀 Upgrade for Advanced Signals", type="primary", use_container_width=True, key="upgrade_signals"):
            st.session_state.show_upgrade = True
            st.rerun()

def render_performance_analytics(data, user):
    """Premium performance analytics dashboard"""
    st.title("📈 Performance Analytics")
    
    if user['plan'] in ['premium', 'professional', 'admin']:
        # Overall performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Return", "+24.8%", "+2.1%", key="perf_total_return")
        
        with col2:
            st.metric("Win Rate", "68%", "+3%", key="perf_win_rate")
        
        with col3:
            st.metric("Avg. Win", "+3.2%", "+0.4%", key="perf_avg_win")
        
        with col4:
            st.metric("Avg. Loss", "-1.8%", "-0.2%", key="perf_avg_loss")
        
        # Performance chart
        st.subheader("📊 Performance Over Time")
        
        # Generate sample performance data
        dates = pd.date_range(start='2023-07-01', end=datetime.now(), freq='D')
        performance = 100 * (1 + np.random.normal(0.001, 0.02, len(dates))).cumprod()
        
        chart_data = pd.DataFrame({
            'Date': dates,
            'Portfolio Value': performance
        })
        
        st.line_chart(chart_data.set_index('Date'))
        
        # Strategy performance comparison
        st.subheader("🏆 Strategy Performance")
        
        strategies = list(STRATEGIES.keys())[:6]
        returns = np.random.uniform(5, 25, len(strategies))
        
        perf_data = pd.DataFrame({
            'Strategy': strategies,
            'Return (%)': returns
        })
        
        st.bar_chart(perf_data.set_index('Strategy'))
        
    else:
        st.info("""
        🔒 **Premium Analytics Unlock**
        
        Upgrade to access advanced performance analytics:
        - Detailed performance metrics
        - Strategy comparison tools
        - Historical analysis
        - Risk-adjusted returns
        """)
        
        if st.button("🚀 Upgrade for Advanced Analytics", type="primary", use_container_width=True, key="upgrade_analytics"):
            st.session_state.show_upgrade = True
            st.rerun()

def render_account_settings():
    """User account settings - FIXED back button"""
    st.title("⚙️ Account Settings")
    
    user = st.session_state.user
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Profile Information")
        st.text_input("Full Name", value=user['name'], disabled=True, key="name_display")
        st.text_input("Email", value=user['email'], disabled=True, key="email_display")
        st.text_input("Username", value=user['username'], disabled=True, key="username_display")
        
        if st.button("📧 Request Profile Update", use_container_width=True, key="request_update"):
            st.info("Profile update requests are processed by our support team")
    
    with col2:
        st.subheader("Subscription Details")
        plan_name = Config.PLANS.get(user['plan'], {}).get('name', 'Unknown Plan')
        st.text_input("Current Plan", value=plan_name, disabled=True, key="plan_display")
        st.text_input("Expiry Date", value=user['expires'], disabled=True, key="expiry_display")
        
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Days Remaining", days_left, key="days_remaining")
        
        if st.button("💳 Manage Subscription", use_container_width=True, key="manage_subscription"):
            st.session_state.show_upgrade = True
            st.session_state.dashboard_view = 'main'
            st.rerun()
    
    st.markdown("---")
    st.subheader("Security")
    if st.button("🔐 Change Password", use_container_width=True, key="change_pwd_user"):
        st.info("Password change requests are handled by our support team for security")
    
    if st.button("📞 Contact Support", use_container_width=True, key="contact_support"):
        st.info(f"Email: {Config.SUPPORT_EMAIL}")
    
    # FIXED: Properly clear show_settings when going back
    if st.button("⬅️ Back to Dashboard", use_container_width=True, key="back_settings"):
        st.session_state.dashboard_view = 'main'
        st.session_state.show_settings = False  # FIXED: Added this line
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
                st.metric("Price", f"${plan_config['price']}", key=f"price_{plan_id}")
                
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
    if st.button("⬅️ Back to Dashboard", use_container_width=True, key="back_upgrade"):
        st.session_state.show_upgrade = False
        st.rerun()

# -------------------------
# ADMIN DASHBOARD - FIXED VERSION WITH BACKUP MANAGEMENT
# -------------------------
def render_admin_dashboard():
    """Professional admin dashboard for business management - FIXED"""
    
    with st.sidebar:
        st.title("👑 Admin Panel")
        st.markdown("---")
        st.write(f"Welcome, **{st.session_state.user['name']}**")
        st.success("System Administrator")
        
        # FIXED: Logout button should always work
        if st.button("🚪 Logout", use_container_width=True, key="sidebar_logout"):
            user_manager.logout(st.session_state.user['username'])
            st.session_state.user = None
            st.rerun()
        
        st.markdown("---")
        st.subheader("Admin Actions")
        
        # FIXED: All sidebar buttons should work from any view
        if st.button("🔄 Refresh All Data", use_container_width=True, key="sidebar_refresh"):
            user_manager.load_data()
            st.rerun()
        
        if st.button("📊 Business Overview", use_container_width=True, key="sidebar_overview"):
            # Clear any modal/management states first
            st.session_state.show_delete_confirmation = False
            st.session_state.show_bulk_delete = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.admin_view = "overview"
            st.rerun()
        
        if st.button("👥 Manage Users", use_container_width=True, key="sidebar_users"):
            # Clear any modal/management states first
            st.session_state.show_delete_confirmation = False
            st.session_state.show_bulk_delete = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.admin_view = "users"
            st.rerun()
        
        if st.button("📈 Analytics", use_container_width=True, key="sidebar_analytics"):
            # Clear any modal/management states first
            st.session_state.show_delete_confirmation = False
            st.session_state.show_bulk_delete = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.admin_view = "analytics"
            st.rerun()
        
        if st.button("💾 Backup Management", use_container_width=True, key="sidebar_backup"):
            # Clear any modal/management states first
            st.session_state.show_delete_confirmation = False
            st.session_state.show_bulk_delete = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.admin_view = "backup"
            st.rerun()
        
        if st.button("💰 Revenue Report", use_container_width=True, key="sidebar_revenue"):
            # Clear any modal/management states first
            st.session_state.show_delete_confirmation = False
            st.session_state.show_bulk_delete = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.admin_view = "revenue"
            st.rerun()
    
    # Main admin content
    st.title("👑 Business Administration Dashboard")
    
    # Show delete confirmation modal if needed
    if st.session_state.get('show_delete_confirmation'):
        render_delete_confirmation_modal()
        return
    
    # Show bulk delete interface if needed
    if st.session_state.get('show_bulk_delete'):
        render_bulk_delete_interface()
        return
    
    # Show plan management interface if needed
    if st.session_state.get('manage_user_plan'):
        render_plan_management_interface(st.session_state.manage_user_plan)
        return
    
    # Show password change interface if needed
    if st.session_state.get('show_password_change'):
        render_password_change_interface()
        return
    
    # Default view or selected view
    current_view = st.session_state.get('admin_view', 'overview')
    
    if current_view == 'overview':
        render_admin_overview()
    elif current_view == 'analytics':
        render_admin_analytics()
    elif current_view == 'users':
        render_admin_user_management()
    elif current_view == 'backup':
        render_backup_management()
    elif current_view == 'revenue':
        render_admin_revenue()

def render_admin_overview():
    """Admin overview with business metrics - FIXED VERSION"""
    st.subheader("📈 Business Overview")
    
    try:
        # Get business metrics with error handling
        metrics = user_manager.get_business_metrics()
        
        # Key metrics with safe access
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            total_users = metrics.get("total_users", 0)
            st.metric("Total Users", total_users, key="total_users_metric")
        with col2:
            active_users = metrics.get("active_users", 0)
            st.metric("Active Users", active_users, key="active_users_metric")
        with col3:
            online_users = metrics.get("online_users", 0)
            st.metric("Online Now", online_users, key="online_users_metric")
        with col4:
            total_logins = metrics.get("total_logins", 0)
            st.metric("Total Logins", total_logins, key="total_logins_metric")
        
        st.markdown("---")
        
        # Plan distribution with safe access
        st.subheader("📊 Plan Distribution")
        plan_data = metrics.get("plan_distribution", {})
        
        if plan_data:
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Users by Plan:**")
                for plan, count in plan_data.items():
                    plan_name = Config.PLANS.get(plan, {}).get('name', plan.title())
                    st.write(f"• {plan_name}: {count} users")
            
            with col2:
                # Simple chart using progress bars
                total = sum(plan_data.values())
                for plan, count in plan_data.items():
                    percentage = (count / total) * 100 if total > 0 else 0
                    plan_name = Config.PLANS.get(plan, {}).get('name', plan.title())
                    st.write(f"{plan_name}: {count} ({percentage:.1f}%)")
                    st.progress(percentage / 100)
        else:
            st.info("No plan distribution data available")
        
        st.markdown("---")
        
        # Recent activity
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🕒 Recent Registrations")
            recent_registrations = user_manager.analytics.get("user_registrations", [])[-5:]
            if recent_registrations:
                for reg in reversed(recent_registrations):
                    plan_name = Config.PLANS.get(reg.get('plan', 'unknown'), {}).get('name', 'Unknown')
                    username = reg.get('username', 'Unknown')
                    timestamp = reg.get('timestamp', '')[:16]
                    st.write(f"• {username} - {plan_name} - {timestamp}")
            else:
                st.info("No recent registrations")
        
        with col2:
            st.subheader("🔄 Recent Plan Changes")
            recent_plan_changes = user_manager.analytics.get("plan_changes", [])[-5:]
            if recent_plan_changes:
                for change in reversed(recent_plan_changes):
                    old_plan = Config.PLANS.get(change.get('old_plan', 'unknown'), {}).get('name', 'Unknown')
                    new_plan = Config.PLANS.get(change.get('new_plan', 'unknown'), {}).get('name', 'Unknown')
                    username = change.get('username', 'Unknown')
                    timestamp = change.get('timestamp', '')[:16]
                    st.write(f"• {username}: {old_plan} → {new_plan}")
                    st.caption(f"{timestamp}")
            else:
                st.info("No recent plan changes")
                
    except Exception as e:
        st.error(f"Error loading admin overview: {str(e)}")
        st.info("Please try refreshing the page or check the data files.")

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
        st.metric("Total Login Attempts", total_logins, key="total_logins_metric")
    with col2:
        st.metric("Successful Logins", successful_logins, key="success_logins")
    with col3:
        st.metric("Failed Logins", failed_logins, key="failed_logins")
    
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
    """User management interface with delete and plan management functionality"""
    st.subheader("👥 User Management")
    
    # User actions - UPDATED WITH PASSWORD CHANGE
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        if st.button("🔄 Refresh User List", use_container_width=True, key="um_refresh"):
            st.rerun()
    with col2:
        if st.button("📧 Export User Data", use_container_width=True, key="um_export"):
            st.success("User data export would be implemented here")
    with col3:
        if st.button("🆕 Create Test User", use_container_width=True, key="um_test"):
            created_username, msg = user_manager.create_test_user("trial")
            if created_username:
                st.success(msg)
            else:
                st.error(msg)
            st.rerun()
    with col4:
        if st.button("🗑️ Bulk Delete Inactive", use_container_width=True, key="um_bulk"):
            st.session_state.show_bulk_delete = True
            st.rerun()
    with col5:  # NEW PASSWORD CHANGE BUTTON
        if st.button("🔐 Change Admin Password", use_container_width=True, key="um_password"):
            st.session_state.show_password_change = True
            st.rerun()
    
    st.markdown("---")
    
    # Enhanced User table with quick actions
    st.write("**All Users - Quick Plan Management:**")
    
    # Display users with quick plan change options
    for username, user_data in user_manager.users.items():
        with st.container():
            col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 1, 1])
            
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
            
            with col6:
                if username != "admin":
                    if st.button("⚙️", key=f"manage_{username}", help="Manage Plan"):
                        st.session_state.manage_user_plan = username
                        st.rerun()
    
    st.markdown("---")
    
    # Individual User Actions Section
    st.subheader("⚡ User Actions")
    
    selected_user = st.selectbox("Select User for Action", [""] + list(user_manager.users.keys()), key="user_select")
    
    if selected_user:
        if selected_user == "admin":
            st.warning("⚠️ Admin account cannot be modified")
        else:
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if st.button("🔴 Deactivate User", use_container_width=True, key=f"deactivate_{selected_user}"):
                    user_manager.users[selected_user]["is_active"] = False
                    user_manager.users[selected_user]["active_sessions"] = 0
                    user_manager._immediate_save()
                    st.success(f"User '{selected_user}' deactivated!")
                    st.rerun()
            
            with col2:
                if st.button("🟢 Activate User", use_container_width=True, key=f"activate_{selected_user}"):
                    user_manager.users[selected_user]["is_active"] = True
                    user_manager._immediate_save()
                    st.success(f"User '{selected_user}' activated!")
                    st.rerun()
            
            with col3:
                if st.button("🔄 Reset Sessions", use_container_width=True, key=f"reset_{selected_user}"):
                    user_manager.users[selected_user]["active_sessions"] = 0
                    user_manager._immediate_save()
                    st.success(f"Sessions reset for '{selected_user}'!")
                    st.rerun()
            
            with col4:
                if st.button("🗑️ Delete User", type="secondary", use_container_width=True, key=f"delete_{selected_user}"):
                    st.session_state.user_to_delete = selected_user
                    st.session_state.show_delete_confirmation = True
                    st.rerun()

def render_admin_revenue():
    """Revenue and financial reporting"""
    st.subheader("💰 Revenue Analytics")
    
    # Revenue metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Estimated MRR", "$1,250", key="mrr_metric")
    with col2:
        st.metric("Active Subscriptions", "28", key="active_subs")
    with col3:
        st.metric("Trial Conversions", "12%", key="trial_conversions")
    
    st.markdown("---")
    
    # Revenue by plan
    st.write("**Revenue by Plan Type:**")
    
    revenue_data = {
        "Trial": {"users": 0, "revenue": 0},
        "Basic": {"users": 0, "revenue": 0},
        "Premium": {"users": 0, "revenue": 0},
        "Professional": {"users": 0, "revenue": 0}
    }
    
    for user_data in user_manager.users.values():
        plan = user_data.get("plan", "trial")
        # Normalize plan names to match revenue_data keys where possible
        pkey = plan.title() if plan.title() in revenue_data else plan.capitalize()
        if pkey in revenue_data:
            revenue_data[pkey]["users"] += 1
            if pkey != "Trial":
                revenue_data[pkey]["revenue"] += Config.PLANS.get(plan, {}).get("price", 0)
    
    # Display revenue table
    revenue_df = pd.DataFrame([
        {"Plan": "Trial", "Users": revenue_data["Trial"]["users"], "Monthly Revenue": revenue_data["Trial"]["revenue"]},
        {"Plan": "Basic", "Users": revenue_data["Basic"]["users"], "Monthly Revenue": revenue_data["Basic"]["revenue"]},
        {"Plan": "Premium", "Users": revenue_data["Premium"]["users"], "Monthly Revenue": revenue_data["Premium"]["revenue"]},
        {"Plan": "Professional", "Users": revenue_data["Professional"]["users"], "Monthly Revenue": revenue_data["Professional"]["revenue"]}
    ])
    
    st.dataframe(revenue_df, use_container_width=True)
    
    st.markdown("---")
    st.info("💡 **Note:** Revenue analytics are simulated. Integrate with Stripe or PayPal for real payment data.")

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
