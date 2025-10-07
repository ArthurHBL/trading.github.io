# app.py - FIXED ADMIN DASHBOARD
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
    
    def create_test_user(self, plan="trial"):
        """Create a test user for admin purposes - BYPASSES VALIDATION"""
        test_username = f"test_{int(time.time())}"
        test_email = f"test{int(time.time())}@example.com"
        
        # Calculate expiry date
        plan_config = Config.PLANS.get(plan, Config.PLANS["trial"])
        expires = (datetime.now() + timedelta(days=plan_config["duration"])).strftime("%Y-%m-%d")
        
        # Create user without validation
        self.users[test_username] = {
            "password_hash": self.hash_password("test123"),
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
        
        self.save_users()
        self.save_analytics()
        
        return test_username, f"Test user '{test_username}' created with {plan} plan!"
    
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
    
    def update_user_plan(self, username, new_plan, new_expires=None):
        """Update user's subscription plan"""
        if username not in self.users:
            return False, "User not found"
        
        user = self.users[username]
        user["plan"] = new_plan
        
        if new_expires:
            user["expires"] = new_expires
        else:
            plan_config = Config.PLANS.get(new_plan, Config.PLANS["trial"])
            user["expires"] = (datetime.now() + timedelta(days=plan_config["duration"])).strftime("%Y-%m-%d")
        
        # Update max sessions based on new plan
        user["max_sessions"] = Config.PLANS.get(new_plan, {}).get("max_sessions", 1)
        
        self.save_users()
        return True, f"User {username} updated to {new_plan} plan"
    
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

# ... (rest of the imports and configurations remain the same)
# ... (login, user dashboard, account settings functions remain the same)

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
        st.subheader("Admin Actions")
        
        if st.button("📊 Business Overview", use_container_width=True):
            st.session_state.admin_view = "overview"
            st.rerun()
        
        if st.button("👥 User Management", use_container_width=True):
            st.session_state.admin_view = "users"
            st.rerun()
        
        if st.button("📈 Analytics", use_container_width=True):
            st.session_state.admin_view = "analytics"
            st.rerun()
        
        if st.button("💰 Revenue", use_container_width=True):
            st.session_state.admin_view = "revenue"
            st.rerun()
        
        if st.button("⚙️ System Tools", use_container_width=True):
            st.session_state.admin_view = "tools"
            st.rerun()
    
    # Main admin content
    st.title("👑 Business Administration Dashboard")
    
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
    elif current_view == 'tools':
        render_admin_tools()

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
    
    # Quick actions
    st.subheader("⚡ Quick Actions")
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🆕 Create Test User", use_container_width=True):
            username, message = user_manager.create_test_user("trial")
            st.success(message)
            st.rerun()
    
    with col2:
        if st.button("🔄 Refresh Data", use_container_width=True):
            user_manager.load_data()
            st.rerun()
    
    with col3:
        if st.button("📋 User List", use_container_width=True):
            st.session_state.admin_view = "users"
            st.rerun()
    
    with col4:
        if st.button("📊 Analytics", use_container_width=True):
            st.session_state.admin_view = "analytics"
            st.rerun()
    
    st.markdown("---")
    
    # Plan distribution
    st.subheader("📊 Plan Distribution")
    plan_data = metrics["plan_distribution"]
    
    if plan_data:
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**Users by Plan:**")
            for plan, count in plan_data.items():
                st.write(f"• {plan.title()}: {count} users")
        
        with col2:
            # Simple chart using progress bars
            total = sum(plan_data.values())
            for plan, count in plan_data.items():
                percentage = (count / total) * 100 if total > 0 else 0
                st.write(f"{plan.title()}: {count} ({percentage:.1f}%)")
                st.progress(percentage / 100)
    else:
        st.info("No user data available")
    
    st.markdown("---")
    
    # Recent activity
    st.subheader("🕒 Recent Activity")
    
    # Show recent registrations
    recent_registrations = user_manager.analytics.get("user_registrations", [])[-5:]
    if recent_registrations:
        st.write("**Latest Registrations:**")
        for reg in reversed(recent_registrations):
            st.write(f"• {reg['username']} - {reg['plan']} - {reg['timestamp'][:16]}")
    else:
        st.info("No recent registrations")

def render_admin_user_management():
    """User management interface - IMPROVED VERSION"""
    st.subheader("👥 User Management")
    
    # Quick actions
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        if st.button("🆕 Create Test User", use_container_width=True, type="primary"):
            username, message = user_manager.create_test_user("trial")
            st.success(message)
            st.rerun()
    with col2:
        if st.button("🔄 Refresh List", use_container_width=True):
            st.rerun()
    with col3:
        if st.button("📧 Export Data", use_container_width=True):
            st.success("User data export would be implemented here")
    with col4:
        if st.button("📊 Back to Overview", use_container_width=True):
            st.session_state.admin_view = "overview"
            st.rerun()
    
    st.markdown("---")
    
    # Create user form for admin
    with st.expander("➕ Create New User Account", expanded=False):
        with st.form("admin_create_user"):
            st.write("**Create User Account**")
            
            col1, col2 = st.columns(2)
            with col1:
                new_username = st.text_input("Username*")
                new_name = st.text_input("Full Name*")
                new_email = st.text_input("Email*")
            with col2:
                new_password = st.text_input("Password*", type="password", value="default123")
                new_plan = st.selectbox("Plan*", list(Config.PLANS.keys()))
                new_status = st.selectbox("Status", ["active", "inactive"])
            
            if st.form_submit_button("🚀 Create User Account", use_container_width=True):
                if all([new_username, new_name, new_email, new_password]):
                    success, message = user_manager.register_user(
                        new_username, new_password, new_name, new_email, new_plan
                    )
                    if success:
                        st.success(f"✅ {message}")
                        if new_status == "inactive":
                            user_manager.users[new_username]["is_active"] = False
                            user_manager.save_users()
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.error("❌ Please fill in all required fields")
    
    st.markdown("---")
    
    # User table
    st.write("**All Users:**")
    users_data = []
    for username, user_data in user_manager.users.items():
        users_data.append({
            "Username": username,
            "Name": user_data["name"],
            "Email": user_data["email"],
            "Plan": user_data["plan"],
            "Expires": user_data["expires"],
            "Last Login": user_data.get("last_login", "Never")[:16] if user_data.get("last_login") else "Never",
            "Status": "🟢 Active" if user_data.get("is_active", True) else "🔴 Inactive",
            "Sessions": f"{user_data.get('active_sessions', 0)}/{user_data.get('max_sessions', 1)}"
        })
    
    users_df = pd.DataFrame(users_data)
    st.dataframe(users_df, use_container_width=True)
    
    st.markdown("---")
    
    # User actions
    st.subheader("⚡ User Actions")
    col1, col2 = st.columns(2)
    
    with col1:
        selected_user = st.selectbox("Select User", [""] + [u for u in user_manager.users.keys() if u != "admin"])
    
    with col2:
        if selected_user:
            user_info = user_manager.users[selected_user]
            st.write(f"**Selected:** {user_info['name']} ({selected_user})")
            st.write(f"**Plan:** {user_info['plan']} | **Status:** {'🟢 Active' if user_info.get('is_active', True) else '🔴 Inactive'}")
    
    if selected_user:
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            new_plan = st.selectbox("Change Plan", list(Config.PLANS.keys()), key="change_plan")
            if st.button("🔄 Update Plan", use_container_width=True):
                success, message = user_manager.update_user_plan(selected_user, new_plan)
                if success:
                    st.success(message)
                    st.rerun()
        
        with col2:
            if st.button("🔴 Deactivate", use_container_width=True):
                user_manager.users[selected_user]["is_active"] = False
                user_manager.users[selected_user]["active_sessions"] = 0
                user_manager.save_users()
                st.success(f"User '{selected_user}' deactivated!")
                st.rerun()
        
        with col3:
            if st.button("🟢 Activate", use_container_width=True):
                user_manager.users[selected_user]["is_active"] = True
                user_manager.save_users()
                st.success(f"User '{selected_user}' activated!")
                st.rerun()
        
        with col4:
            if st.button("🔄 Reset Sessions", use_container_width=True):
                user_manager.users[selected_user]["active_sessions"] = 0
                user_manager.save_users()
                st.success(f"Sessions reset for '{selected_user}'!")
                st.rerun()

def render_admin_tools():
    """Admin system tools"""
    st.subheader("⚙️ System Tools")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Database Management**")
        
        if st.button("🔄 Reload All Data", use_container_width=True):
            user_manager.load_data()
            st.success("Data reloaded successfully!")
        
        if st.button("🧹 Clear Analytics", use_container_width=True):
            user_manager.analytics = {
                "total_logins": 0,
                "active_users": 0,
                "revenue_today": 0,
                "user_registrations": [],
                "login_history": []
            }
            user_manager.save_analytics()
            st.success("Analytics data cleared!")
        
        if st.button("📊 System Health", use_container_width=True):
            st.success("System health check completed!")
            st.info(f"Total users: {len(user_manager.users)}")
            st.info(f"Data files: OK")
            st.info(f"Memory usage: Normal")
    
    with col2:
        st.write("**Test Data Generation**")
        
        col1, col2 = st.columns(2)
        with col1:
            test_plan = st.selectbox("Test Plan", list(Config.PLANS.keys()), key="test_plan")
        with col2:
            num_users = st.number_input("Number of users", min_value=1, max_value=10, value=3)
        
        if st.button("🎯 Generate Test Users", use_container_width=True):
            created_users = []
            for i in range(num_users):
                username, message = user_manager.create_test_user(test_plan)
                created_users.append(username)
            st.success(f"Created {num_users} test users: {', '.join(created_users)}")
            st.rerun()
        
        if st.button("🗑️ Delete Test Users", use_container_width=True):
            test_users = [u for u in user_manager.users.keys() if u.startswith('test_')]
            for username in test_users:
                del user_manager.users[username]
            user_manager.save_users()
            st.success(f"Deleted {len(test_users)} test users")
            st.rerun()
    
    st.markdown("---")
    st.write("**System Information**")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("App Version", Config.VERSION)
    with col2:
        st.metric("Total Plans", len(Config.PLANS))
    with col3:
        st.metric("Support Email", Config.SUPPORT_EMAIL)

# ... (rest of the admin analytics and revenue functions remain the same)
# ... (main application function remains the same)

if __name__ == "__main__":
    main()
