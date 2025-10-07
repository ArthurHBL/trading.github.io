# app.py - COMPLETE VERSION WITH PERSISTENT DATA AND PASSWORD CHANGE
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
# SECURE USER MANAGEMENT WITH PERSISTENCE
# -------------------------
class UserManager:
    def __init__(self):
        self.users_file = "users.json"
        self.analytics_file = "analytics.json"
        self._ensure_data_files()
        self.load_data()
        atexit.register(self.cleanup_sessions)  # Clean up on app exit
    
    def _ensure_data_files(self):
        """Ensure data files exist and are valid"""
        # Create users file if it doesn't exist
        if not os.path.exists(self.users_file):
            self.users = {}
            self.create_default_admin()
            self.save_users()
        
        # Create analytics file if it doesn't exist
        if not os.path.exists(self.analytics_file):
            self.analytics = {
                "total_logins": 0,
                "active_users": 0,
                "revenue_today": 0,
                "user_registrations": [],
                "login_history": [],
                "deleted_users": [],
                "plan_changes": [],
                "password_changes": []
            }
            self.save_analytics()
    
    def load_data(self):
        """Load users and analytics data with error handling"""
        try:
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
            print(f"✅ Loaded {len(self.users)} users from {self.users_file}")
        except Exception as e:
            print(f"❌ Error loading users: {e}")
            self.users = {}
            self.create_default_admin()
        
        try:
            with open(self.analytics_file, 'r') as f:
                self.analytics = json.load(f)
            print(f"✅ Loaded analytics data from {self.analytics_file}")
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
                "password_changes": []
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
        print("✅ Created default admin account")
    
    def hash_password(self, password):
        """Secure password hashing"""
        salt = st.secrets.get("PASSWORD_SALT", "default-salt-change-in-production")
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def save_users(self):
        """Save users to file with error handling"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
            print(f"✅ Saved {len(self.users)} users to {self.users_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving users: {e}")
            return False
    
    def save_analytics(self):
        """Save analytics data with error handling"""
        try:
            with open(self.analytics_file, 'w') as f:
                json.dump(self.analytics, f, indent=2)
            return True
        except Exception as e:
            print(f"❌ Error saving analytics: {e}")
            return False
    
    def cleanup_sessions(self):
        """Reset all active sessions (called on app exit)"""
        for username in self.users:
            self.users[username]["active_sessions"] = 0
        self.save_users()
        print("✅ Cleaned up all active sessions")
    
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
        
        if self.save_users() and self.save_analytics():
            return True, f"Account created successfully! {plan_config['name']} activated."
        else:
            return False, "Error saving user data. Please try again."

    def create_test_user(self, plan="trial"):
        """Create a test user for admin purposes"""
        test_username = f"test_{int(time.time())}"
        test_email = f"test{int(time.time())}@example.com"
        
        # Calculate expiry date
        plan_config = Config.PLANS.get(plan, Config.PLANS["trial"])
        expires = (datetime.now() + timedelta(days=plan_config["duration"])).strftime("%Y-%m-%d")
        
        # Create user without going through register_user validations
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
        
        # Update analytics
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
        # Validation checks
        if username not in self.users:
            return False, "User not found"
        
        if username == "admin":
            return False, "Cannot delete admin account"
        
        # Check if user has active sessions
        user_data = self.users[username]
        if user_data.get('active_sessions', 0) > 0:
            return False, "User has active sessions. Reset sessions first."
        
        # Store user info for analytics before deletion
        user_plan = user_data.get('plan', 'unknown')
        user_created = user_data.get('created', 'unknown')
        
        # Delete the user
        del self.users[username]
        
        # Update analytics
        if 'deleted_users' not in self.analytics:
            self.analytics['deleted_users'] = []
        
        self.analytics['deleted_users'].append({
            "username": username,
            "plan": user_plan,
            "created": user_created,
            "deleted_at": datetime.now().isoformat()
        })
        
        if self.save_users() and self.save_analytics():
            # Log the deletion
            print(f"User {username} deleted at {datetime.now()}")
            return True, f"User '{username}' has been permanently deleted"
        else:
            return False, "Error deleting user data"

    def change_user_plan(self, username, new_plan):
        """Change a user's subscription plan"""
        # Validation checks
        if username not in self.users:
            return False, "User not found"
        
        if username == "admin":
            return False, "Cannot modify admin account plan"
        
        if new_plan not in Config.PLANS and new_plan != "admin":
            return False, f"Invalid plan: {new_plan}"
        
        user_data = self.users[username]
        old_plan = user_data.get('plan', 'unknown')
        
        # Store old plan info for analytics
        old_plan_config = Config.PLANS.get(old_plan, {})
        new_plan_config = Config.PLANS.get(new_plan, {})
        
        # Calculate new expiry date
        if new_plan != "admin":
            expires = (datetime.now() + timedelta(days=new_plan_config["duration"])).strftime("%Y-%m-%d")
        else:
            expires = "2030-12-31"  # Admin account
        
        # Update user data
        user_data['plan'] = new_plan
        user_data['expires'] = expires
        user_data['max_sessions'] = new_plan_config.get('max_sessions', 1) if new_plan != "admin" else 3
        
        # Update analytics
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
        
        # Verify current password
        if not self.verify_password(current_password, admin_user["password_hash"]):
            return False, "Current password is incorrect"
        
        # Check if new password is same as old
        if self.verify_password(new_password, admin_user["password_hash"]):
            return False, "New password cannot be the same as current password"
        
        # Update password
        admin_user["password_hash"] = self.hash_password(new_password)
        
        # Update analytics
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
                                           placeholder="Enter current admin password")
        with col2:
            new_password = st.text_input("New Password*", type="password", 
                                       placeholder="Enter new password (min 8 chars)")
        
        confirm_password = st.text_input("Confirm New Password*", type="password", 
                                       placeholder="Re-enter new password")
        
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
    if st.button("⬅️ Back to User Management", use_container_width=True):
        st.session_state.show_password_change = False
        st.rerun()

# -------------------------
# AUTHENTICATION COMPONENTS
# -------------------------
def render_login():
    """Professional login/registration interface"""
    st.title(f"🔐 Welcome to {Config.APP_NAME}")
    st.markdown("---")
    
    # Display current user count for debugging
    user_count = len(user_manager.users)
    st.sidebar.info(f"📊 Total users in system: {user_count}")
    
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
# DELETE CONFIRMATION MODAL
# -------------------------
def render_delete_confirmation_modal():
    """Modal for confirming user deletion"""
    user_to_delete = st.session_state.get('user_to_delete')
    
    if not user_to_delete:
        return
    
    # Create overlay effect
    st.markdown("""
        <style>
        .delete-modal {
            position: fixed;
            top: 50%;
            left: 50%;
            transform: translate(-50%, -50%);
            background: white;
            padding: 2rem;
            border-radius: 10px;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
            z-index: 1000;
            border: 2px solid #ff6b6b;
            min-width: 500px;
        }
        .modal-backdrop {
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            z-index: 999;
        }
        </style>
    """, unsafe_allow_html=True)
    
    # Backdrop
    st.markdown('<div class="modal-backdrop"></div>', unsafe_allow_html=True)
    
    # Modal content
    with st.container():
        st.markdown(f'<div class="delete-modal">', unsafe_allow_html=True)
        
        st.error("🚨 **Confirm User Deletion**")
        st.warning(f"**User to delete:** {user_to_delete}")
        
        user_data = user_manager.users[user_to_delete]
        st.write(f"**Name:** {user_data['name']}")
        st.write(f"**Email:** {user_data['email']}")
        st.write(f"**Plan:** {user_data['plan']}")
        st.write(f"**Status:** {'Active' if user_data.get('is_active', True) else 'Inactive'}")
        
        st.markdown("---")
        st.error("**This action cannot be undone!**")
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("✅ Confirm Delete", type="primary", use_container_width=True):
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
            if st.button("❌ Cancel", use_container_width=True):
                st.session_state.show_delete_confirmation = False
                st.session_state.user_to_delete = None
                st.rerun()
        
        with col3:
            st.markdown("")
        
        st.markdown('</div>', unsafe_allow_html=True)

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
        if st.button("⬅️ Back to User Management", use_container_width=True):
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
            if st.button("🗑️ Delete Selected Users", type="primary", use_container_width=True):
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
            if st.button("❌ Cancel Bulk Delete", use_container_width=True):
                st.session_state.show_bulk_delete = False
                st.rerun()
    else:
        if st.button("⬅️ Back to User Management", use_container_width=True):
            st.session_state.show_bulk_delete = False
            st.rerun()

# -------------------------
# PLAN MANAGEMENT INTERFACE - FIXED VERSION
# -------------------------
def render_plan_management_interface(username):
    """Interface for managing a specific user's plan"""
    if username not in user_manager.users:
        st.error("User not found")
        if st.button("⬅️ Back to User Management", use_container_width=True):
            st.session_state.manage_user_plan = None
            st.rerun()
        return
    
    user_data = user_manager.users[username]
    current_plan = user_data['plan']
    
    st.subheader(f"📋 Plan Management: {username}")
    
    # ADDED: Back button at the top
    if st.button("⬅️ Back to User Management", key="back_top"):
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
            format_func=lambda x: f"{Config.PLANS[x]['name']} - ${Config.PLANS[x]['price']}/month"
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
                st.info(f"
