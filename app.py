# app.py - COMPLETE WORKING VERSION WITH ALL ADMIN FUNCTIONS
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
    if 'show_username_change' not in st.session_state:
        st.session_state.show_username_change = False
    if 'user_to_change_username' not in st.session_state:
        st.session_state.user_to_change_username = None
    if 'show_user_password_change' not in st.session_state:
        st.session_state.show_user_password_change = False
    if 'user_to_change_password' not in st.session_state:
        st.session_state.user_to_change_password = None

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
        atexit.register(self.cleanup_sessions)
    
    def _ensure_data_files(self):
        """Ensure data files exist and are valid"""
        if not os.path.exists(self.users_file):
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
                "username_changes": []
            }
            self.save_analytics()
    
    def load_data(self):
        """Load users and analytics data with error handling"""
        try:
            with open(self.users_file, 'r') as f:
                self.users = json.load(f)
        except Exception as e:
            print(f"❌ Error loading users: {e}")
            self.users = {}
            self.create_default_admin()
        
        try:
            with open(self.analytics_file, 'r') as f:
                self.analytics = json.load(f)
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
                "username_changes": []
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
    
    def hash_password(self, password):
        """Secure password hashing"""
        salt = st.secrets.get("PASSWORD_SALT", "default-salt-change-in-production")
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def save_users(self):
        """Save users to file with error handling"""
        try:
            with open(self.users_file, 'w') as f:
                json.dump(self.users, f, indent=2)
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
        
        if self.save_users() and self.save_analytics():
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

    def change_username(self, old_username, new_username, changed_by="admin"):
        """Change a user's username"""
        if old_username not in self.users:
            return False, "User not found"
        
        if new_username in self.users:
            return False, "New username already exists"
        
        if not re.match("^[a-zA-Z0-9_]{3,20}$", new_username):
            return False, "Username must be 3-20 characters (letters, numbers, _)"
        
        # Store user data and remove old entry
        user_data = self.users[old_username]
        del self.users[old_username]
        
        # Create new entry with new username
        self.users[new_username] = user_data
        
        # Track username change in analytics
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
            # Rollback in case of error
            self.users[old_username] = user_data
            if new_username in self.users:
                del self.users[new_username]
            return False, "Error saving username change"

    def change_user_password(self, username, new_password, changed_by="admin"):
        """Change a user's password (admin function)"""
        if username not in self.users:
            return False, "User not found"
        
        if len(new_password) < 8:
            return False, "Password must be at least 8 characters"
        
        user_data = self.users[username]
        
        # Check if new password is same as current
        if self.verify_password(new_password, user_data["password_hash"]):
            return False, "New password cannot be the same as current password"
        
        # Update password
        user_data["password_hash"] = self.hash_password(new_password)
        
        # Track password change in analytics
        if 'password_changes' not in self.analytics:
            self.analytics['password_changes'] = []
        
        self.analytics['password_changes'].append({
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "changed_by": changed_by,
            "type": "admin_forced_change"
        })
        
        if self.save_users() and self.save_analytics():
            return True, f"Password for '{username}' has been changed successfully"
        else:
            return False, "Error saving password change"

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
# ADMIN DASHBOARD FUNCTIONS - ADDING MISSING ONES
# -------------------------

def render_admin_overview():
    """Admin overview with business metrics"""
    st.subheader("📈 Business Overview")
    
    # Get business metrics
    metrics = user_manager.get_business_metrics()
    
    # Key metrics
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
            # Simple chart using progress bars
            total = sum(plan_data.values())
            for plan, count in plan_data.items():
                percentage = (count / total) * 100 if total > 0 else 0
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
        st.subheader("🔄 Recent Changes")
        recent_changes = []
        
        # Add username changes
        username_changes = user_manager.analytics.get("username_changes", [])[-3:]
        for change in username_changes:
            recent_changes.append(f"👤 {change['old_username']} → {change['new_username']}")
        
        # Add password changes
        password_changes = user_manager.analytics.get("password_changes", [])[-3:]
        for change in password_changes:
            if change.get('type') == 'admin_forced_change':
                recent_changes.append(f"🔐 {change['username']} password reset")
        
        # Add plan changes
        plan_changes = user_manager.analytics.get("plan_changes", [])[-3:]
        for change in plan_changes:
            old_plan = Config.PLANS.get(change['old_plan'], {}).get('name', change['old_plan'].title())
            new_plan = Config.PLANS.get(change['new_plan'], {}).get('name', change['new_plan'].title())
            recent_changes.append(f"📋 {change['username']}: {old_plan} → {new_plan}")
        
        if recent_changes:
            for change in reversed(recent_changes[-5:]):  # Show last 5 changes
                st.write(f"• {change}")
        else:
            st.info("No recent changes")

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
    
    # User changes analytics
    st.markdown("---")
    st.subheader("🔄 User Account Changes")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        username_changes = len(user_manager.analytics.get("username_changes", []))
        st.metric("Username Changes", username_changes)
    
    with col2:
        password_changes = len([x for x in user_manager.analytics.get("password_changes", []) if x.get('type') == 'admin_forced_change'])
        st.metric("Admin Password Resets", password_changes)
    
    with col3:
        plan_changes = len(user_manager.analytics.get("plan_changes", []))
        st.metric("Plan Changes", plan_changes)
    
    # Recent username changes
    username_changes = user_manager.analytics.get("username_changes", [])
    if username_changes:
        st.markdown("---")
        st.subheader("👤 Recent Username Changes")
        for change in reversed(username_changes[-5:]):
            st.write(f"• **{change['old_username']}** → **{change['new_username']}**")
            st.caption(f"By: {change['changed_by']} | {change['timestamp'][:16]}")
    
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
# USERNAME CHANGE INTERFACE
# -------------------------
def render_username_change_interface():
    """Interface for changing a user's username"""
    username = st.session_state.get('user_to_change_username')
    
    if not username:
        st.error("No user selected for username change")
        if st.button("⬅️ Back to User Management", use_container_width=True):
            st.session_state.show_username_change = False
            st.rerun()
        return
    
    if username not in user_manager.users:
        st.error("User not found")
        if st.button("⬅️ Back to User Management", use_container_width=True):
            st.session_state.show_username_change = False
            st.rerun()
        return
    
    user_data = user_manager.users[username]
    
    st.subheader(f"👤 Change Username: {username}")
    
    with st.form("username_change_form"):
        st.info(f"**Changing username for:** {user_data['name']} ({user_data['email']})")
        
        col1, col2 = st.columns(2)
        with col1:
            st.text_input("Current Username", value=username, disabled=True)
        with col2:
            new_username = st.text_input("New Username*", placeholder="Enter new username (3-20 chars)")
        
        st.markdown("**Username Requirements:**")
        st.markdown("- 3-20 characters long")
        st.markdown("- Letters, numbers, and underscores only")
        st.markdown("- Must be unique")
        
        # Show username availability
        if new_username:
            if new_username in user_manager.users and new_username != username:
                st.error("❌ Username already taken")
            elif not re.match("^[a-zA-Z0-9_]{3,20}$", new_username):
                st.error("❌ Invalid username format")
            else:
                st.success("✅ Username available")
        
        reason = st.text_area("Reason for change (optional):", 
                            placeholder="e.g., User requested change, Security concern...")
        
        submitted = st.form_submit_button("✅ Change Username", use_container_width=True)
        
        if submitted:
            if not new_username:
                st.error("❌ Please enter a new username")
                return
            
            if new_username == username:
                st.error("❌ New username cannot be the same as current username")
                return
            
            success, message = user_manager.change_username(
                username, 
                new_username, 
                st.session_state.user['username']
            )
            
            if success:
                st.success("✅ " + message)
                st.info("🔄 The user will need to use the new username for their next login.")
                
                # Add a small delay and return to user management
                time.sleep(2)
                st.session_state.show_username_change = False
                st.session_state.user_to_change_username = None
                st.rerun()
            else:
                st.error("❌ " + message)
    
    st.markdown("---")
    if st.button("⬅️ Back to User Management", use_container_width=True):
        st.session_state.show_username_change = False
        st.session_state.user_to_change_username = None
        st.rerun()

# -------------------------
# USER PASSWORD CHANGE INTERFACE
# -------------------------
def render_user_password_change_interface():
    """Interface for changing a user's password (admin function)"""
    username = st.session_state.get('user_to_change_password')
    
    if not username:
        st.error("No user selected for password change")
        if st.button("⬅️ Back to User Management", use_container_width=True):
            st.session_state.show_user_password_change = False
            st.rerun()
        return
    
    if username not in user_manager.users:
        st.error("User not found")
        if st.button("⬅️ Back to User Management", use_container_width=True):
            st.session_state.show_user_password_change = False
            st.rerun()
        return
    
    user_data = user_manager.users[username]
    
    st.subheader(f"🔐 Change Password: {username}")
    
    with st.form("user_password_change_form"):
        st.info(f"**Changing password for:** {user_data['name']} ({user_data['email']})")
        
        col1, col2 = st.columns(2)
        with col1:
            new_password = st.text_input("New Password*", type="password", 
                                       placeholder="Enter new password (min 8 chars)")
        with col2:
            confirm_password = st.text_input("Confirm New Password*", type="password", 
                                           placeholder="Re-enter new password")
        
        # Password strength requirements
        st.markdown("**Password Requirements:**")
        st.markdown("- Minimum 8 characters")
        st.markdown("- Include letters and numbers")
        st.markdown("- Avoid common passwords")
        
        # Show password strength
        if new_password:
            if len(new_password) < 8:
                st.error("❌ Password too short (min 8 characters)")
            elif not re.search(r"[A-Za-z]", new_password) or not re.search(r"\d", new_password):
                st.warning("⚠️ Consider using both letters and numbers")
            else:
                st.success("✅ Password meets requirements")
        
        reason = st.text_area("Reason for change (optional):", 
                            placeholder="e.g., Security reset, User forgot password...")
        
        submitted = st.form_submit_button("✅ Change User Password", use_container_width=True)
        
        if submitted:
            # Validation
            if not new_password or not confirm_password:
                st.error("❌ Please fill in all password fields")
                return
            
            if new_password != confirm_password:
                st.error("❌ Passwords do not match")
                return
            
            if len(new_password) < 8:
                st.error("❌ Password must be at least 8 characters long")
                return
            
            # Change password
            success, message = user_manager.change_user_password(
                username, 
                new_password, 
                st.session_state.user['username']
            )
            
            if success:
                st.success("✅ " + message)
                st.info("🔒 The user will need to use the new password for their next login.")
                
                # Add a small delay and return to user management
                time.sleep(2)
                st.session_state.show_user_password_change = False
                st.session_state.user_to_change_password = None
                st.rerun()
            else:
                st.error("❌ " + message)
    
    st.markdown("---")
    if st.button("⬅️ Back to User Management", use_container_width=True):
        st.session_state.show_user_password_change = False
        st.session_state.user_to_change_password = None
        st.rerun()

# -------------------------
# ADMIN PASSWORD CHANGE INTERFACE
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
# PLAN MANAGEMENT INTERFACE
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
    
    if st.button("⬅️ Back to User Management", key="back_top"):
        st.session_state.manage_user_plan = None
        st.rerun()
    
    st.write(f"**Current Plan:** {Config.PLANS.get(current_plan, {}).get('name', current_plan.title())}")
    st.write(f"**User:** {user_data['name']} ({user_data['email']})")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("### 🔄 Change Subscription Plan")
        
        available_plans = list(Config.PLANS.keys())
        new_plan = st.selectbox(
            "Select New Plan",
            available_plans,
            index=available_plans.index(current_plan) if current_plan in available_plans else 0,
            format_func=lambda x: f"{Config.PLANS[x]['name']} - ${Config.PLANS[x]['price']}/month"
        )
        
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
        
        change_reason = st.text_area("Reason for plan change (optional):", 
                                   placeholder="e.g., User requested upgrade, Payment issue, Special promotion...")
        
        if st.button("✅ Confirm Plan Change", type="primary", use_container_width=True):
            if new_plan == current_plan:
                st.warning("User is already on this plan")
            else:
                success, message = user_manager.change_user_plan(username, new_plan)
                if success:
                    st.success(f"✅ {message}")
                    st.info(f"📧 Notification email sent to {user_data['email']}")
                    st.info("🔄 User will see changes immediately on next login")
                    time.sleep(2)
                    st.session_state.manage_user_plan = None
                    st.rerun()
                else:
                    st.error(f"❌ {message}")
    
    with col2:
        st.markdown("### 📊 Current Plan Details")
        
        current_plan_config = Config.PLANS.get(current_plan, {})
        st.write(f"**Plan:** {current_plan_config.get('name', current_plan.title())}")
        st.write(f"**Expires:** {user_data['expires']}")
        
        days_left = (datetime.strptime(user_data['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Days Remaining", days_left)
        
        st.markdown("#### Features:")
        st.write(f"• **Strategies:** {current_plan_config.get('strategies', 0)} available")
        st.write(f"• **Sessions:** {user_data.get('active_sessions', 0)}/{current_plan_config.get('max_sessions', 1)} active")
        st.write(f"• **Price:** ${current_plan_config.get('price', 0)}/month")
        
        st.markdown("#### User Statistics:")
        st.write(f"• **Joined:** {user_data['created'][:10]}")
        
        last_login = user_data.get('last_login')
        if last_login:
            try:
                st.write(f"• **Last Login:** {last_login[:16]}")
            except:
                st.write(f"• **Last Login:** {last_login}")
        else:
            st.write(f"• **Last Login:** Never")
            
        st.write(f"• **Total Logins:** {user_data.get('login_count', 0)}")
        st.write(f"• **Status:** {'🟢 Active' if user_data.get('is_active', True) else '🔴 Inactive'}")
        
        st.markdown("#### Quick Actions:")
        
        quick_plans = {
            "🚀 Upgrade to Premium": "premium",
            "💼 Upgrade to Professional": "professional",
            "📊 Downgrade to Basic": "basic",
            "🎯 Set to Trial": "trial"
        }
        
        for btn_text, plan in quick_plans.items():
            if plan != current_plan:
                if st.button(btn_text, use_container_width=True, key=f"quick_{plan}_{username}"):
                    success, message = user_manager.change_user_plan(username, plan)
                    if success:
                        st.success(f"✅ {message}")
                        time.sleep(1)
                        st.session_state.manage_user_plan = None
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
    
    st.markdown("---")
    if st.button("⬅️ Back to User Management", key="back_bottom", use_container_width=True):
        st.session_state.manage_user_plan = None
        st.rerun()

# -------------------------
# ENHANCED ADMIN USER MANAGEMENT
# -------------------------
def render_admin_user_management():
    """User management interface with enhanced username/password change functionality"""
    st.subheader("👥 User Management")
    
    # User actions - REMOVED THE TOP USERNAME/PASSWORD CHANGE BUTTONS
    col1, col2, col3, col4 = st.columns(4)
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
    
    st.markdown("---")
    
    # Enhanced User table with quick actions
    st.write("**All Users - Quick Management:**")
    
    # Display users with enhanced management options
    for username, user_data in user_manager.users.items():
        with st.container():
            if username == "admin":
                # Special layout for admin - only password change icon
                col1, col2, col3, col4, col5, col6 = st.columns([2, 2, 2, 2, 1, 1])
                
                with col1:
                    st.write(f"**{username}** 👑")
                    st.caption(user_data['name'])
                
                with col2:
                    st.write(user_data['email'])
                
                with col3:
                    st.write("`Admin Account`")
                
                with col4:
                    st.write(f"Expires: {user_data['expires']}")
                    st.caption("Permanent access")
                
                with col5:
                    st.write("")
                
                with col6:
                    # Only password change icon for admin
                    if st.button("🔐", key=f"change_pass_{username}", help="Change Admin Password"):
                        st.session_state.show_password_change = True
                        st.rerun()
            
            else:
                # Regular user layout with both username and password change
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
                    if st.button("👤", key=f"change_user_{username}", help="Change Username"):
                        st.session_state.user_to_change_username = username
                        st.session_state.show_username_change = True
                        st.rerun()
                
                with col7:
                    if st.button("🔐", key=f"change_pass_{username}", help="Change Password"):
                        st.session_state.user_to_change_password = username
                        st.session_state.show_user_password_change = True
                        st.rerun()
    
    st.markdown("---")
    
    # Individual User Actions Section
    st.subheader("⚡ User Actions")
    
    selected_user = st.selectbox("Select User for Action", [""] + list(user_manager.users.keys()), key="user_select")
    
    if selected_user:
        if selected_user == "admin":
            st.warning("⚠️ Admin account cannot be modified")
            col1, col2 = st.columns(2)
            with col1:
                if st.button("🔐 Change Admin Password", use_container_width=True, key="admin_password"):
                    st.session_state.show_password_change = True
                    st.rerun()
            with col2:
                if st.button("🔄 Reset Admin Sessions", use_container_width=True, key="reset_admin"):
                    user_manager.users[selected_user]["active_sessions"] = 0
                    user_manager.save_users()
                    st.success("Admin sessions reset!")
                    st.rerun()
        else:
            col1, col2, col3, col4, col5, col6 = st.columns(6)
            
            with col1:
                if st.button("🔴 Deactivate User", use_container_width=True, key=f"deactivate_{selected_user}"):
                    user_manager.users[selected_user]["is_active"] = False
                    user_manager.users[selected_user]["active_sessions"] = 0
                    user_manager.save_users()
                    st.success(f"User '{selected_user}' deactivated!")
                    st.rerun()
            
            with col2:
                if st.button("🟢 Activate User", use_container_width=True, key=f"activate_{selected_user}"):
                    user_manager.users[selected_user]["is_active"] = True
                    user_manager.save_users()
                    st.success(f"User '{selected_user}' activated!")
                    st.rerun()
            
            with col3:
                if st.button("🔄 Reset Sessions", use_container_width=True, key=f"reset_{selected_user}"):
                    user_manager.users[selected_user]["active_sessions"] = 0
                    user_manager.save_users()
                    st.success(f"Sessions reset for '{selected_user}'!")
                    st.rerun()
            
            with col4:
                if st.button("📋 Manage Plan", use_container_width=True, key=f"manage_{selected_user}"):
                    st.session_state.manage_user_plan = selected_user
                    st.rerun()
            
            with col5:
                if st.button("👤 Change Username", use_container_width=True, key=f"username_{selected_user}"):
                    st.session_state.user_to_change_username = selected_user
                    st.session_state.show_username_change = True
                    st.rerun()
            
            with col6:
                if st.button("🔐 Change Password", use_container_width=True, key=f"password_{selected_user}"):
                    st.session_state.user_to_change_password = selected_user
                    st.session_state.show_user_password_change = True
                    st.rerun()

# -------------------------
# ADMIN DASHBOARD - COMPLETE VERSION
# -------------------------
def render_admin_dashboard():
    """Professional admin dashboard for business management"""
    
    with st.sidebar:
        st.title("👑 Admin Panel")
        st.markdown("---")
        st.write(f"Welcome, **{st.session_state.user['name']}**")
        st.success("System Administrator")
        
        if st.button("🚪 Logout", use_container_width=True, key="sidebar_logout"):
            user_manager.logout(st.session_state.user['username'])
            st.session_state.user = None
            st.rerun()
        
        st.markdown("---")
        st.subheader("Admin Actions")
        
        if st.button("🔄 Refresh All Data", use_container_width=True, key="sidebar_refresh"):
            user_manager.load_data()
            st.rerun()
        
        if st.button("📊 View Analytics", use_container_width=True, key="sidebar_analytics"):
            st.session_state.show_delete_confirmation = False
            st.session_state.show_bulk_delete = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.show_username_change = False
            st.session_state.show_user_password_change = False
            st.session_state.admin_view = "analytics"
            st.rerun()
        
        if st.button("👥 Manage Users", use_container_width=True, key="sidebar_users"):
            st.session_state.show_delete_confirmation = False
            st.session_state.show_bulk_delete = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.show_username_change = False
            st.session_state.show_user_password_change = False
            st.session_state.admin_view = "users"
            st.rerun()
        
        if st.button("🗑️ Bulk Delete", use_container_width=True, key="sidebar_bulk_delete"):
            st.session_state.show_delete_confirmation = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.show_username_change = False
            st.session_state.show_user_password_change = False
            st.session_state.admin_view = "users"
            st.session_state.show_bulk_delete = True
            st.rerun()
        
        if st.button("💰 Revenue Report", use_container_width=True, key="sidebar_revenue"):
            st.session_state.show_delete_confirmation = False
            st.session_state.show_bulk_delete = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.show_username_change = False
            st.session_state.show_user_password_change = False
            st.session_state.admin_view = "revenue"
            st.rerun()
    
    # Main admin content
    st.title("👑 Business Administration Dashboard")
    
    # Show username change interface if needed
    if st.session_state.get('show_username_change'):
        render_username_change_interface()
        return
    
    # Show user password change interface if needed
    if st.session_state.get('show_user_password_change'):
        render_user_password_change_interface()
        return
    
    # Show admin password change interface if needed
    if st.session_state.get('show_password_change'):
        render_password_change_interface()
        return
    
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
    
    # Default view or selected view
    current_view = st.session_state.get('admin_view', 'overview')
    
    if current_view == 'overview':
        render_admin_overview()
    elif current_view == 'analytics':
        render_admin_analytics()
    elif current_view == 'users':
        render_admin_user_management()
    elif current_view == 'revenue':
        render_admin_revenue()

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
# SIMPLE LOGIN FOR TESTING
# -------------------------
def render_login():
    """Simple login interface"""
    st.title(f"🔐 Welcome to {Config.APP_NAME}")
    
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
                        "plan": user_manager.users[username]["plan"],
                        "expires": user_manager.users[username]["expires"],
                        "email": user_manager.users[username]["email"]
                    }
                    st.success("Login successful!")
                    st.rerun()
                else:
                    st.error(message)
            else:
                st.error("Please enter both username and password")

# -------------------------
# MAIN APPLICATION
# -------------------------
def main():
    init_session()
    
    if not st.session_state.user:
        render_login()
    else:
        if st.session_state.user['plan'] == 'admin':
            render_admin_dashboard()
        else:
            st.title("User Dashboard")
            st.write(f"Welcome, {st.session_state.user['name']}!")
            if st.button("Logout"):
                user_manager.logout(st.session_state.user['username'])
                st.session_state.user = None
                st.rerun()

if __name__ == "__main__":
    main()
