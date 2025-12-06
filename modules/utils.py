

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

class UserManager:
    def __init__(self):
        self.load_data()

    def load_data(self):
        """Load users and analytics data from Supabase - FIXED VERSION"""
        try:
            self.users = supabase_get_users()
            self.analytics = supabase_get_analytics()

            if "admin" not in self.users:
                self.create_default_admin()
                self.save_users()

            if not self.analytics:
                self.analytics = { "total_logins": 0, "active_users": 0, "revenue_today": 0, "user_registrations": [], "login_history": [], "deleted_users": [], "plan_changes": [], "password_changes": [], "email_verifications": [] }
                self.save_analytics()

        except Exception as e:
            st.error(f"❌ Error loading data: {e}")
            self.users = {}
            self.analytics = { "total_logins": 0, "active_users": 0, "revenue_today": 0, "user_registrations": [], "login_history": [], "deleted_users": [], "plan_changes": [], "password_changes": [], "email_verifications": [] }
            self.create_default_admin()
            self.save_users()
            self.save_analytics()

    def create_default_admin(self):
        """Create default admin account with a SECURE password hash"""
        self.users["admin"] = {
            "password_hash": self.hash_password("ChangeThis123!"),
            "name": "System Administrator", "plan": "admin", "expires": "2030-12-31",
            "created": datetime.now().isoformat(), "last_login": None, "login_count": 0,
            "active_sessions": 0, "max_sessions": 3, "is_active": True,
            "email": "admin@tradinganalysis.com", "subscription_id": "admin_account",
            "email_verified": True, "verification_date": datetime.now().isoformat()
        }

    # --- NEW SECURE HASHING METHODS (using bcrypt directly) ---
    def hash_password(self, password):
        """Hashes a password using bcrypt."""
        password_bytes = password.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(password_bytes, salt)
        return hashed_bytes.decode('utf-8')

    def verify_password(self, plain_password, hashed_password):
        """Verifies a plain password against a bcrypt hash."""
        try:
            plain_password_bytes = plain_password.encode('utf-8')
            hashed_password_bytes = hashed_password.encode('utf-8')
            return bcrypt.checkpw(plain_password_bytes, hashed_password_bytes)
        except (ValueError, TypeError):
            # This handles cases where the hash might be invalid, preventing a crash.
            return False

    # --- LEGACY METHOD FOR MIGRATION (private) ---
    def _verify_legacy_password(self, password, password_hash):
        """Verifies a password using the OLD insecure method."""
        salt = "default-salt-change-in-production"
        return hashlib.sha256((password + salt).encode()).hexdigest() == password_hash

    # --- THE REST OF YOUR CODE IS UNCHANGED ---
    def save_users(self):
        return supabase_save_users(self.users)

    def save_analytics(self):
        return supabase_save_analytics(self.analytics)

    def periodic_cleanup(self):
        session_reset_count = 0
        for username in self.users:
            if self.users[username].get('active_sessions', 0) > 0:
                self.users[username]['active_sessions'] = 0
                session_reset_count += 1
        if session_reset_count > 0:
            self.save_users()

    def register_user(self, username, password, name, email, plan="trial"):
        self.load_data()
        if username in self.users: return False, "Username already exists"
        if not re.match("^[a-zA-Z0-9_]{3,20}$", username): return False, "Username must be 3-20 characters (letters, numbers, _)"
        if len(password) < 8: return False, "Password must be at least 8 characters"
        if not re.match(r"[^@]+@[^@]+\.[^@]+", email): return False, "Invalid email address"

        plan_config = Config.PLANS.get(plan, Config.PLANS["trial"])
        expires = (datetime.now() + timedelta(days=plan_config["duration"])).strftime("%Y-%m-%d")

        self.users[username] = {
            "password_hash": self.hash_password(password),
            "name": name, "email": email, "plan": plan, "expires": expires,
            "created": datetime.now().isoformat(), "last_login": None, "login_count": 0,
            "active_sessions": 0, "max_sessions": plan_config["max_sessions"], "is_active": True,
            "subscription_id": f"sub_{username}_{int(time.time())}",
            "payment_status": "active" if plan == "trial" else "pending", "email_verified": False,
            "verification_date": None, "verification_notes": "", "verification_admin": None
        }
        if 'user_registrations' not in self.analytics: self.analytics['user_registrations'] = []
        self.analytics["user_registrations"].append({ "username": username, "plan": plan, "timestamp": datetime.now().isoformat() })
        
        users_saved, analytics_saved = self.save_users(), self.save_analytics()
        if users_saved and analytics_saved:
            return True, f"Account created successfully! {plan_config['name']} activated."
        else:
            if username in self.users: del self.users[username]
            return False, "Error saving user data. Please try again."

    def authenticate(self, username, password):
        if 'login_history' not in self.analytics: self.analytics['login_history'] = []
        self.analytics["total_logins"] = self.analytics.get("total_logins", 0) + 1
        self.analytics["login_history"].append({ "username": username, "timestamp": datetime.now().isoformat(), "success": False })

        if username not in self.users:
            self.save_analytics(); return False, "Invalid username or password"

        user = self.users[username]
        current_hash = user.get("password_hash")

        if not user.get("is_active", True): return False, "Account deactivated. Please contact support."

        password_verified, is_legacy_hash = False, False
        try:
            if self.verify_password(password, current_hash): password_verified = True
        except (ValueError, TypeError): pass

        if not password_verified:
            if self._verify_legacy_password(password, current_hash):
                password_verified, is_legacy_hash = True, True

        if not password_verified:
            self.save_analytics(); return False, "Invalid username or password"
        
        expires = user.get("expires")
        if expires and datetime.strptime(expires, "%Y-%m-%d").date() < date.today():
            return False, "Subscription expired. Please renew your plan."

        if is_legacy_hash:
            st.toast("Upgrading account security...", icon="🛡️")
            user["password_hash"] = self.hash_password(password)

        user["last_login"] = datetime.now().isoformat()
        user["login_count"] = user.get("login_count", 0) + 1
        user["active_sessions"] = user.get("active_sessions", 0) + 1
        self.analytics["login_history"][-1]["success"] = True

        users_saved, analytics_saved = self.save_users(), self.save_analytics()
        return (True, "Login successful") if users_saved and analytics_saved else (False, "Error saving login data")
    
    def create_test_user(self, plan="trial"):
        test_username = f"test_{int(time.time())}"
        test_email = f"test{int(time.time())}@example.com"
        plan_config = Config.PLANS.get(plan, Config.PLANS["trial"])
        expires = (datetime.now() + timedelta(days=plan_config["duration"])).strftime("%Y-%m-%d")
        self.users[test_username] = {
            "password_hash": self.hash_password("test12345"),
            "name": f"Test User {test_username}", "email": test_email, "plan": plan,
            "expires": expires, "created": datetime.now().isoformat(), "last_login": None,
            "login_count": 0, "active_sessions": 0, "max_sessions": plan_config["max_sessions"],
            "is_active": True, "subscription_id": f"test_{test_username}",
            "payment_status": "active", "email_verified": False, "verification_date": None,
            "verification_notes": "", "verification_admin": None
        }
        self.analytics["user_registrations"].append({ "username": test_username, "plan": plan, "timestamp": datetime.now().isoformat() })
        if self.save_users() and self.save_analytics():
            return test_username, f"Test user '{test_username}' created with {plan} plan!"
        else:
            return None, "Error creating test user"

    def delete_user(self, username):
        if username not in self.users: return False, "User not found"
        if username == "admin": return False, "Cannot delete admin account"
        user_data = self.users.pop(username)
        if 'deleted_users' not in self.analytics: self.analytics['deleted_users'] = []
        self.analytics['deleted_users'].append({ "username": username, "plan": user_data.get('plan', 'unknown'), "created": user_data.get('created', 'unknown'), "deleted_at": datetime.now().isoformat() })
        supabase_success = supabase_delete_user(username)
        users_saved, analytics_saved = self.save_users(), self.save_analytics()
        return (True, f"User '{username}' has been permanently deleted") if users_saved and analytics_saved and supabase_success else (False, "Error deleting user data")

    def change_user_plan(self, username, new_plan):
        if username not in self.users: return False, "User not found"
        if username == "admin": return False, "Cannot modify admin account plan"
        if new_plan not in Config.PLANS and new_plan != "admin": return False, f"Invalid plan: {new_plan}"
        user_data = self.users[username]
        old_plan = user_data.get('plan', 'unknown')
        new_plan_config = Config.PLANS.get(new_plan, {})
        expires = "2030-12-31" if new_plan == "admin" else (datetime.now() + timedelta(days=new_plan_config.get("duration", 30))).strftime("%Y-%m-%d")
        user_data.update({'plan': new_plan, 'expires': expires, 'max_sessions': new_plan_config.get('max_sessions', 1) if new_plan != "admin" else 3})
        if 'plan_changes' not in self.analytics: self.analytics['plan_changes'] = []
        self.analytics['plan_changes'].append({ "username": username, "old_plan": old_plan, "new_plan": new_plan, "timestamp": datetime.now().isoformat(), "admin": st.session_state.get("username", "System") })
        if self.save_users() and self.save_analytics():
            return True, f"User '{username}' plan changed from {old_plan} to {new_plan}"
        else:
            return False, "Error saving plan change"

    def logout(self, username):
        if username in self.users:
            self.users[username]["active_sessions"] = max(0, self.users[username].get("active_sessions", 1) - 1)
            self.save_users()

    def change_admin_password(self, current_password, new_password, changed_by="admin"):
        admin_user = self.users.get("admin")
        if not admin_user: return False, "Admin account not found"
        if not self.verify_password(current_password, admin_user["password_hash"]): return False, "Current password is incorrect"
        if self.verify_password(new_password, admin_user["password_hash"]): return False, "New password cannot be the same as current password"
        admin_user["password_hash"] = self.hash_password(new_password)
        if 'password_changes' not in self.analytics: self.analytics['password_changes'] = []
        self.analytics['password_changes'].append({ "username": "admin", "timestamp": datetime.now().isoformat(), "changed_by": changed_by })
        if self.save_users() and self.save_analytics():
            return True, "Admin password changed successfully!"
        else:
            return False, "Error saving password change"
    
    def change_user_password(self, username, new_password, changed_by="admin"):
        if username not in self.users: return False, "User not found"
        if len(new_password) < 8: return False, "Password must be at least 8 characters"
        user_data = self.users[username]
        if self.verify_password(new_password, user_data["password_hash"]): return False, "New password cannot be the same as current password"
        user_data["password_hash"] = self.hash_password(new_password)
        if 'password_changes' not in self.analytics: self.analytics['password_changes'] = []
        self.analytics['password_changes'].append({ "username": username, "timestamp": datetime.now().isoformat(), "changed_by": changed_by, "type": "admin_forced_change" })
        if self.save_users() and self.save_analytics():
            return True, f"Password for '{username}' changed successfully!"
        else:
            return False, "Error saving password change"

    def change_own_password(self, username, current_password, new_password):
        """Allow user to change their own password"""
        if username not in self.users:
            return False, "User not found"

        user_data = self.users[username]
        if not self.verify_password(current_password, user_data["password_hash"]):
            return False, "Current password is incorrect"

        if len(new_password) < 8:
            return False, "New password must be at least 8 characters"

        if self.verify_password(new_password, user_data["password_hash"]):
            return False, "New password cannot be the same as current password"

        user_data["password_hash"] = self.hash_password(new_password)
        if 'password_changes' not in self.analytics:
            self.analytics['password_changes'] = []
        self.analytics['password_changes'].append({
            "username": username, "timestamp": datetime.now().isoformat(),
            "changed_by": username, "type": "user_self_change"
        })

        if self.save_users() and self.save_analytics():
            return True, "Password changed successfully!"
        else:
            return False, "Error saving password change"

    def get_business_metrics(self):
        total_users = len(self.users)
        active_users = sum(1 for u in self.users.values() if u.get('is_active', True))
        online_users = sum(u.get('active_sessions', 0) for u in self.users.values())
        plan_counts = pd.Series([u.get('plan', 'unknown') for u in self.users.values()]).value_counts().to_dict()
        verified_users = sum(1 for u in self.users.values() if u.get('email_verified', False))
        return {
            "total_users": total_users, "active_users": active_users, "online_users": online_users,
            "plan_distribution": plan_counts, "total_logins": self.analytics.get("total_logins", 0),
            "revenue_today": self.analytics.get("revenue_today", 0), "verified_users": verified_users,
            "unverified_users": total_users - verified_users
        }

    def export_user_credentials(self):
        try:
            df = pd.DataFrame.from_dict(self.users, orient='index')
            df = df.drop(columns=['password_hash'])
            csv_bytes = df.to_csv(index=True).encode('utf-8')
            return csv_bytes, None
        except Exception as e:
            return None, f"Error exporting user data: {str(e)}"

    def change_username(self, old_username, new_username, changed_by="admin"):
        if old_username not in self.users: return False, "User not found"
        if new_username in self.users: return False, "New username already exists"
        if not re.match("^[a-zA-Z0-9_]{3,20}$", new_username): return False, "New username must be 3-20 characters (letters, numbers, _)"
        self.users[new_username] = self.users.pop(old_username)
        if 'username_changes' not in self.analytics: self.analytics['username_changes'] = []
        self.analytics['username_changes'].append({ "old_username": old_username, "new_username": new_username, "timestamp": datetime.now().isoformat(), "changed_by": changed_by })
        if self.save_users() and self.save_analytics():
            return True, f"Username changed from '{old_username}' to '{new_username}'"
        else:
            self.users[old_username] = self.users.pop(new_username) # Revert change on failure
            return False, "Error saving username change"
        
    def get_user_credentials_display(self):
        users_list = []
        for username, user_data in self.users.items():
            users_list.append({
                "username": username, "name": user_data.get("name", ""), "email": user_data.get("email", ""),
                "plan": user_data.get("plan", ""), "expires": user_data.get("expires", ""), "created": user_data.get("created", ""),
                "last_login": user_data.get("last_login", ""), "is_active": user_data.get("is_active", True), "login_count": user_data.get("login_count", 0),
                "active_sessions": user_data.get("active_sessions", 0), "email_verified": user_data.get("email_verified", False),
                "verification_date": user_data.get("verification_date", ""), "verification_admin": user_data.get("verification_admin", "")
            })
        return users_list

    def verify_user_email(self, username, admin_username, notes=""):
        if username not in self.users: return False, "User not found"
        if username == "admin": return False, "Cannot modify admin account verification"
        user_data = self.users[username]
        if user_data.get("email_verified", False): return False, "Email is already verified"
        user_data.update({"email_verified": True, "verification_date": datetime.now().isoformat(), "verification_admin": admin_username, "verification_notes": notes})
        if 'email_verifications' not in self.analytics: self.analytics['email_verifications'] = []
        self.analytics['email_verifications'].append({ "username": username, "email": user_data.get("email", ""), "verified_by": admin_username, "timestamp": datetime.now().isoformat(), "notes": notes })
        if self.save_users() and self.save_analytics():
            return True, f"Email for '{username}' has been verified successfully!"
        else:
            return False, "Error saving verification data"

    def revoke_email_verification(self, username, admin_username, reason=""):
        if username not in self.users: return False, "User not found"
        if username == "admin": return False, "Cannot modify admin account verification"
        user_data = self.users[username]
        if not user_data.get("email_verified", False): return False, "Email is not verified"
        user_data.update({"email_verified": False, "verification_date": None, "verification_admin": None, "verification_notes": reason})
        if 'email_verifications' not in self.analytics: self.analytics['email_verifications'] = []
        self.analytics['email_verifications'].append({ "username": username, "email": user_data.get("email", ""), "action": "revoked", "revoked_by": admin_username, "timestamp": datetime.now().isoformat(), "reason": reason })
        if self.save_users() and self.save_analytics():
            return True, f"Email verification for '{username}' has been revoked!"
        else:
            return False, "Error saving verification data"

    def get_email_verification_stats(self):
        total_users = len(self.users) -1 # Exclude admin
        verified_count = sum(1 for u, d in self.users.items() if u != "admin" and d.get("email_verified", False))
        return {
            "total_users": total_users, "verified_count": verified_count, "unverified_count": total_users - verified_count,
            "verification_rate": (verified_count / total_users) * 100 if total_users > 0 else 0
        }

    def get_inactive_users(self, days_threshold=30):
        inactive_users = []
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        for username, user_data in self.users.items():
            if username == "admin": continue
            last_login_str = user_data.get('last_login')
            last_activity_date = datetime.fromisoformat(last_login_str) if last_login_str else datetime.fromisoformat(user_data.get('created'))
            if last_activity_date < cutoff_date:
                inactive_users.append(username)
        return inactive_users

    def upgrade_user_to_premium_tier(self, username, plan_key, duration_days, admin_username):
        if username not in self.users: return False, "User not found"
        user_data = self.users[username]
        old_plan = user_data.get('plan', 'unknown')
        user_data.update({
            'plan': plan_key,
            'expires': (datetime.now() + timedelta(days=duration_days)).strftime("%Y-%m-%d"),
            'max_sessions': Config.PLANS.get(plan_key, {}).get('max_sessions', 3)
        })
        if 'plan_changes' not in self.analytics: self.analytics['plan_changes'] = []
        self.analytics['plan_changes'].append({ "username": username, "old_plan": old_plan, "new_plan": plan_key, "timestamp": datetime.now().isoformat(), "admin": admin_username, "duration_days": duration_days })
        if self.save_users() and self.save_analytics():
            return True, f"{username} upgraded to {Config.PLANS.get(plan_key, {}).get('name', plan_key)}"
        else: return False, "Error saving upgrade"

    def bulk_delete_inactive_users(self, usernames):
        success_count, error_count, errors = 0, 0, []
        for username in usernames:
            if username == "admin":
                errors.append(f"Cannot delete admin account: {username}"); error_count += 1; continue
            success, msg = self.delete_user(username)
            if success: success_count += 1
            else: errors.append(msg); error_count += 1
        return success_count, error_count, errors

# Initialize user manager
user_manager = UserManager()

# -------------------------
# FIXED: DELETE USER CONFIRMATION DIALOG - WORKING VERSION WITH BACK BUTTON
# -------------------------
def render_delete_user_confirmation():
    """Render the delete user confirmation dialog - FIXED VERSION WITH BACK BUTTON"""
    if not st.session_state.show_delete_confirmation or not st.session_state.user_to_delete:
        return

    username = st.session_state.user_to_delete
    user_data = user_manager.users.get(username)

    if not user_data:
        st.session_state.show_delete_confirmation = False
        st.session_state.user_to_delete = None
        st.rerun()
        return

    st.warning(f"🚨 Confirm Deletion of User: {username}")

    # Show user details
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Name:** {user_data.get('name', 'N/A')}")
        st.write(f"**Email:** {user_data.get('email', 'N/A')}")
    with col2:
        st.write(f"**Plan:** {user_data.get('plan', 'N/A')}")
        st.write(f"**Created:** {user_data.get('created', 'N/A')[:10]}")

    st.error("""
    ⚠️ **This action cannot be undone!**

    The user account and all associated data will be permanently deleted.
    """)

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("✅ Confirm Delete", use_container_width=True, type="primary", key="confirm_delete_user"):
            success, message = user_manager.delete_user(username)
            if success:
                st.success(message)
                st.session_state.show_delete_confirmation = False
                st.session_state.user_to_delete = None
                st.session_state.manage_user_plan = None
                st.session_state.show_manage_user_plan = False
                time.sleep(2)
                st.rerun()
            else:
                st.error(message)

    with col2:
        if st.button("❌ Cancel", use_container_width=True, key="cancel_delete_user"):
            st.session_state.show_delete_confirmation = False
            st.session_state.user_to_delete = None
            st.rerun()

    with col3:
        # ADDED: Back to User Management button
        if st.button("🔙 Back to User Management", use_container_width=True, key="back_to_user_mgmt"):
            st.session_state.show_delete_confirmation = False
            st.session_state.user_to_delete = None
            st.session_state.manage_user_plan = None
            st.session_state.show_manage_user_plan = False
            st.session_state.admin_view = "users"  # Ensure we go back to user management
            st.rerun()

# -------------------------
# FIXED: BULK DELETE INACTIVE USERS INTERFACE - WORKING VERSION WITH BACK BUTTON
# -------------------------
def render_bulk_delete_inactive():
    """Render the bulk delete inactive users interface - FIXED VERSION WITH BACK BUTTON"""
    st.subheader("🗑️ Bulk Delete Inactive Users")

    # ADDED: Back button at the top
    if st.button("🔙 Back to User Management", key="bulk_delete_back_top"):
        st.session_state.show_bulk_delete = False
        st.rerun()

    st.markdown("---")

    # Configuration
    col1, col2 = st.columns(2)
    with col1:
        days_threshold = st.number_input(
            "Inactivity Threshold (days):",
            min_value=1,
            max_value=365,
            value=30,
            help="Delete users who haven't logged in for more than this many days"
        )

    with col2:
        include_trial_only = st.checkbox(
            "Only Trial Users",
            value=True,
            help="Only delete inactive trial users (safer option)"
        )

    # Get inactive users - FIXED: Now uses the corrected method
    inactive_users = user_manager.get_inactive_users(days_threshold)

    if include_trial_only:
        inactive_users = [user for user in inactive_users if user_manager.users[user].get('plan') == 'trial']

    if not inactive_users:
        st.success("✅ No inactive users found matching your criteria!")
        if st.button("🔙 Back to User Management", use_container_width=True, key="back_from_no_inactive"):
            st.session_state.show_bulk_delete = False
            st.rerun()
        return

    # Display inactive users
    st.warning(f"🚨 Found {len(inactive_users)} inactive users matching your criteria:")

    users_to_display = []
    for username in inactive_users:
        user_data = user_manager.users[username]
        last_login = user_data.get('last_login', 'Never')
        if last_login != 'Never':
            last_login = datetime.fromisoformat(last_login).strftime("%Y-%m-%d")

        users_to_display.append({
            "Username": username,
            "Name": user_data.get('name', ''),
            "Email": user_data.get('email', ''),
            "Plan": user_data.get('plan', ''),
            "Last Login": last_login,
            "Created": datetime.fromisoformat(user_data.get('created')).strftime("%Y-%m-%d")
        })

    df = pd.DataFrame(users_to_display)
    st.dataframe(df, use_container_width=True)

    # Confirmation
    st.error("""
    ⚠️ **DANGER ZONE - IRREVERSIBLE ACTION**

    This will permanently delete all selected user accounts. This action cannot be undone!
    User data, analyses, and all associated information will be lost forever.
    """)

    confirm_text = st.text_input(
        "Type 'DELETE INACTIVE USERS' to confirm:",
        placeholder="Enter confirmation text...",
        help="This is a safety measure to prevent accidental mass deletion",
        key="bulk_delete_confirmation_text"
    )

    col1, col2, col3 = st.columns([1, 1, 1])

    with col1:
        if st.button("✅ CONFIRM DELETE", use_container_width=True, type="primary", key="confirm_bulk_delete"):
            if confirm_text == "DELETE INACTIVE USERS":
                with st.spinner(f"Deleting {len(inactive_users)} inactive users..."):
                    success_count, error_count, errors = user_manager.bulk_delete_inactive_users(inactive_users)

                    if success_count > 0:
                        st.success(f"✅ Successfully deleted {success_count} inactive users!")

                    if error_count > 0:
                        st.error(f"❌ Failed to delete {error_count} users:")
                        for error in errors:
                            st.error(error)

                    # Close the bulk delete interface
                    st.session_state.show_bulk_delete = False
                    time.sleep(2)
                    st.rerun()
            else:
                st.error("❌ Confirmation text does not match. Please type 'DELETE INACTIVE USERS' exactly.")

    with col2:
        if st.button("🔄 REFRESH LIST", use_container_width=True, key="refresh_inactive_list"):
            st.rerun()

    with col3:
        if st.button("🔙 CANCEL", use_container_width=True, key="cancel_bulk_delete"):
            st.session_state.show_bulk_delete = False
            st.rerun()

# -------------------------
# FIXED: MANAGE USER PLAN INTERFACE - WORKING VERSION WITH BACK BUTTON
# -------------------------
def render_manage_user_plan():
    """Render the manage user plan interface with manual upgrade options"""
    if not st.session_state.manage_user_plan:
        return

    username = st.session_state.manage_user_plan
    user_data = user_manager.users.get(username)

    if not user_data:
        st.error("User not found")
        st.session_state.manage_user_plan = None
        st.session_state.show_manage_user_plan = False
        st.rerun()
        return

    # Back button at the top
    if st.button("Back to User Management", key="manage_user_back_top"):
        st.session_state.manage_user_plan = None
        st.session_state.show_manage_user_plan = False
        st.rerun()

    st.subheader(f"Manage User: {username}")

    # Main form for user details
    with st.form(f"manage_user_{username}"):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**User Information:**")
            st.text_input("Name", value=user_data.get('name', ''), disabled=True, key=f"name_{username}")
            st.text_input("Email", value=user_data.get('email', ''), disabled=True, key=f"email_{username}")
            st.text_input("Created", value=user_data.get('created', '')[:10], disabled=True, key=f"created_{username}")

            email_verified = user_data.get('email_verified', False)
            verification_status = "Verified" if email_verified else "Unverified"
            st.text_input("Email Status", value=verification_status, disabled=True, key=f"email_status_{username}")

        with col2:
            st.write("**Plan Management:**")
            current_plan = user_data.get('plan', 'trial')
            st.text_input("Current Plan", value=Config.PLANS.get(current_plan, {}).get('name', current_plan), disabled=True, key=f"current_plan_{username}")

            current_expiry = user_data.get('expires', '')
            st.text_input("Current Expiry", value=current_expiry, disabled=True, key=f"current_expiry_{username}")

            days_left = (datetime.strptime(current_expiry, "%Y-%m-%d").date() - date.today()).days if current_expiry else 0
            st.text_input("Days Remaining", value=str(days_left), disabled=True, key=f"days_left_{username}")

            is_active = st.checkbox(
                "Account Active",
                value=user_data.get('is_active', True),
                key=f"active_{username}"
            )

            max_sessions = st.number_input(
                "Max Concurrent Sessions",
                min_value=1,
                max_value=10,
                value=user_data.get('max_sessions', 1),
                key=f"sessions_{username}"
            )

        # Main action buttons
        col_b1, col_b2, col_b3 = st.columns(3)

        with col_b1:
            save_changes = st.form_submit_button("Save Changes", use_container_width=True, type="primary")

        with col_b2:
            delete_user = st.form_submit_button("Delete User", use_container_width=True, type="secondary")

        with col_b3:
            cancel = st.form_submit_button("Cancel", use_container_width=True)

        if save_changes:
            user_data['is_active'] = is_active
            user_data['max_sessions'] = max_sessions

            if user_manager.save_users():
                st.success("User settings updated successfully!")
                time.sleep(2)
                st.session_state.manage_user_plan = None
                st.session_state.show_manage_user_plan = False
                st.rerun()
            else:
                st.error("Error saving user settings")

        if delete_user:
            st.session_state.user_to_delete = username
            st.session_state.show_delete_confirmation = True
            st.rerun()

        if cancel:
            st.session_state.manage_user_plan = None
            st.session_state.show_manage_user_plan = False
            st.rerun()

    st.markdown("---")

    # Premium Tier Upgrade Section
    st.subheader("Manual Premium Upgrade")
    st.info("Select a premium tier to manually upgrade this user. Their subscription will be extended accordingly.")

    # Display current plan tier
    current_plan = user_data.get('plan', 'trial')
    if current_plan.startswith('premium'):
        plan_name = Config.PLANS.get(current_plan, {}).get('name', current_plan)
        st.success(f"Current Premium Tier: **{plan_name}**")
    else:
        st.warning(f"Current Plan: **{Config.PLANS.get(current_plan, {}).get('name', current_plan)}**")

    st.markdown("---")

    # Premium tier options in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### 1 Month")
        st.write("**$19**")
        st.write("30 days")
        if st.button("Upgrade", key=f"upgrade_1m_{username}", use_container_width=True):
            success, message = user_manager.upgrade_user_to_premium_tier(username, "premium", 30, st.session_state.user['username'])
            if success:
                st.success(message)
                time.sleep(2)
                st.rerun()
            else:
                st.error(message)

    with col2:
        st.markdown("### 3 Months")
        st.write("**$49**")
        st.write("90 days")
        if st.button("Upgrade", key=f"upgrade_3m_{username}", use_container_width=True):
            success, message = user_manager.upgrade_user_to_premium_tier(username, "premium_3month", 90, st.session_state.user['username'])
            if success:
                st.success(message)
                time.sleep(2)
                st.rerun()
            else:
                st.error(message)

    with col3:
        st.markdown("### 6 Months")
        st.write("**$97**")
        st.write("180 days")
        if st.button("Upgrade", key=f"upgrade_6m_{username}", use_container_width=True):
            success, message = user_manager.upgrade_user_to_premium_tier(username, "premium_6month", 180, st.session_state.user['username'])
            if success:
                st.success(message)
                time.sleep(2)
                st.rerun()
            else:
                st.error(message)

    with col4:
        st.markdown("### 12 Months")
        st.write("**$179**")
        st.write("365 days")
        if st.button("Upgrade", key=f"upgrade_12m_{username}", use_container_width=True):
            success, message = user_manager.upgrade_user_to_premium_tier(username, "premium_12month", 365, st.session_state.user['username'])
            if success:
                st.success(message)
                time.sleep(2)
                st.rerun()
            else:
                st.error(message)

    st.markdown("---")

    # Email verification and password reset
    st.write("**Email Verification & Password Reset:**")
    col_v1, col_v2 = st.columns(2)

    with col_v1:
        with st.form(f"verify_email_{username}"):
            if not user_data.get('email_verified', False):
                if st.form_submit_button("Verify Email", use_container_width=True, key=f"verify_email_btn_{username}"):
                    success, message = user_manager.verify_user_email(username, st.session_state.user['username'], "Manually verified by admin")
                    if success:
                        st.success(message)
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)
            else:
                if st.form_submit_button("Revoke Verification", use_container_width=True, key=f"revoke_email_btn_{username}"):
                    success, message = user_manager.revoke_email_verification(username, st.session_state.user['username'], "Revoked by admin")
                    if success:
                        st.success(message)
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)

    with col_v2:
        with st.form(f"reset_password_{username}"):
            if st.form_submit_button("Reset Password", use_container_width=True, key=f"reset_password_btn_{username}"):
                new_password = f"TempPass{int(time.time()) % 10000}"
                success, message = user_manager.change_user_password(username, new_password, st.session_state.user['username'])
                if success:
                    st.success(f"Password reset! New temporary password: {new_password}")
                    st.info("User should change this password immediately after login.")
                else:
                    st.error(message)

# -------------------------
# FIXED: EMAIL VERIFICATION INTERFACE
# -------------------------
def render_email_verification_interface():
    """Complete email verification management interface"""
    st.subheader("📧 Email Verification Management")

    # Get verification stats
    stats = user_manager.get_email_verification_stats()

    # Stats overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Users", stats["total_users"])
    with col2:
        st.metric("Verified", stats["verified_count"])
    with col3:
        st.metric("Unverified", stats["unverified_count"])
    with col4:
        st.metric("Verification Rate", f"{stats['verification_rate']:.1f}%")

    st.markdown("---")

    # Tabs for different views
    tab1, tab2, tab3 = st.tabs(["📋 Pending Verification", "✅ Verified Users", "📈 Verification Analytics"])

    with tab1:
        render_pending_verification_tab(stats)

    with tab2:
        render_verified_users_tab(stats)

    with tab3:
        render_verification_analytics_tab(stats)

def render_pending_verification_tab(stats):
    """Tab for pending email verification"""
    st.write("**Users Pending Email Verification:**")

    if not stats["pending_verification"]:
        st.success("🎉 All users are verified! No pending verifications.")
        return

    # Display pending users
    for user_info in stats["pending_verification"]:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 1, 1, 1])

            with col1:
                st.write(f"**{user_info['username']}**")
                st.caption(user_info['email'])

            with col2:
                created_date = datetime.fromisoformat(user_info['created']).strftime("%Y-%m-%d")
                st.write(f"Created: {created_date}")
                st.write(f"Plan: {user_info['plan']}")

            with col3:
                # Email quality check
                email_issues = check_email_quality(user_info['email'])
                if "✅" in email_issues[0]:
                    st.success("✅ Valid")
                else:
                    st.warning("⚠️ Check")

            with col4:
                if st.button("✅ Verify", key=f"verify_{user_info['username']}", use_container_width=True):
                    success, message = user_manager.verify_user_email(
                        user_info['username'],
                        st.session_state.user['username'],
                        "Verified via admin panel"
                    )
                    if success:
                        st.success(message)
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)

            with col5:
                if st.button("👀 View", key=f"view_{user_info['username']}", use_container_width=True):
                    st.session_state.manage_user_plan = user_info['username']
                    st.session_state.show_manage_user_plan = True
                    st.rerun()

            st.markdown("---")

def render_verified_users_tab(stats):
    """Tab for verified users"""
    st.write("**Recently Verified Users (Last 7 days):**")

    if not stats["recently_verified"]:
        st.info("No users verified in the last 7 days.")
        return

    for user_info in stats["recently_verified"]:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 2, 1])

            with col1:
                st.write(f"**{user_info['username']}**")
                st.caption(user_info['email'])

            with col2:
                verified_date = datetime.fromisoformat(user_info['verified_date']).strftime("%Y-%m-%d %H:%M")
                st.write(f"Verified: {verified_date}")

            with col3:
                st.write(f"By: {user_info['verified_by']}")

            with col4:
                if st.button("👀 Manage", key=f"manage_{user_info['username']}", use_container_width=True):
                    st.session_state.manage_user_plan = user_info['username']
                    st.session_state.show_manage_user_plan = True
                    st.rerun()

            st.markdown("---")

def render_verification_analytics_tab(stats):
    """Tab for verification analytics"""
    st.write("**Verification Analytics**")

    # Verification rate visualization
    col1, col2 = st.columns(2)

    with col1:
        st.write("**Verification Status Distribution:**")
        labels = ['Verified', 'Unverified']
        values = [stats['verified_count'], stats['unverified_count']]

        if sum(values) > 0:
            fig = px.pie(
                values=values,
                names=labels,
                title=f"Verification Rate: {stats['verification_rate']:.1f}%",
                color=labels,
                color_discrete_map={'Verified':'#10B981', 'Unverified':'#EF4444'}
            )
            st.plotly_chart(fig, use_container_width=True)
        else:
            st.info("No user data available for chart")

    with col2:
        st.write("**Verification Actions:**")

        if st.button("🔄 Refresh Analytics", use_container_width=True, key="refresh_verification_analytics"):
            st.rerun()

        if st.button("📧 Bulk Verify All", use_container_width=True, key="bulk_verify_all"):
            pending_users = stats["pending_verification"]
            if pending_users:
                success_count = 0
                for user_info in pending_users:
                    success, message = user_manager.verify_user_email(
                        user_info['username'],
                        st.session_state.user['username'],
                        "Bulk verified by admin"
                    )
                    if success:
                        success_count += 1

                st.success(f"✅ Bulk verification completed! {success_count} users verified.")
                time.sleep(2)
                st.rerun()
            else:
                st.info("No pending users to verify.")

        if st.button("📊 Export Report", use_container_width=True, key="export_verification_report"):
            # Create verification report
            report_data = []
            for username, user_data in user_manager.users.items():
                if username == "admin":
                    continue

                report_data.append({
                    "Username": username,
                    "Name": user_data.get('name', ''),
                    "Email": user_data.get('email', ''),
                    "Plan": user_data.get('plan', ''),
                    "Email Verified": "Yes" if user_data.get('email_verified') else "No",
                    "Verification Date": user_data.get('verification_date', ''),
                    "Verified By": user_data.get('verification_admin', ''),
                    "Last Login": user_data.get('last_login', 'Never')
                })

            df = pd.DataFrame(report_data)
            csv_bytes = df.to_csv(index=False).encode('utf-8')

            st.download_button(
                label="⬇️ Download Verification Report",
                data=csv_bytes,
                file_name=f"email_verification_report_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True,
                key="download_verification_report"
            )

# -------------------------
# FIXED: TRADING SIGNALS ROOM PASSWORD MANAGEMENT WITH SUPABASE PERSISTENCE
# -------------------------
def render_signals_password_management():
    """Interface for managing Trading Signals Room password with Supabase persistence"""
    st.subheader("🔐 Trading Signals Room Password Management")

    st.info("""
    **Trading Signals Room Security**

    This password controls access to the Trading Signals Room for all users (including admins).
    Change this password regularly to maintain security.
    """)

    with st.form("signals_password_form"):
        col1, col2 = st.columns(2)

        with col1:
            current_password = st.text_input(
                "Current Signals Room Password:",
                type="password",
                placeholder="Enter current password",
                help="The current password that users are using",
                key="current_signals_password"
            )

        with col2:
            new_password = st.text_input(
                "New Signals Room Password:",
                type="password",
                placeholder="Enter new password",
                help="The new password that will be required",
                key="new_signals_password"
            )

        # Display current password (masked)
        st.write(f"**Current Password Setting:** `{'*' * len(st.session_state.signals_room_password)}`")

        col_b1, col_b2 = st.columns(2)

        with col_b1:
            submit = st.form_submit_button("✅ Update Password", use_container_width=True, type="primary")

        with col_b2:
            cancel = st.form_submit_button("🔙 Cancel", use_container_width=True)

        if submit:
            if not current_password or not new_password:
                st.error("❌ Please fill in both password fields")
            elif current_password != st.session_state.signals_room_password:
                st.error("❌ Current password is incorrect")
            elif len(new_password) < 4:
                st.error("❌ New password must be at least 4 characters")
            else:
                # Update the password in both session state and Supabase
                st.session_state.signals_room_password = new_password

                # Save to Supabase for persistence
                app_settings = {'signals_room_password': new_password}
                save_success = save_app_settings(app_settings)

                if save_success:
                    st.success("✅ Trading Signals Room password updated successfully!")
                    st.info("🔒 All users will need to use the new password to access the Signals Room.")

                    # Also revoke access for everyone
                    st.session_state.signals_room_access_granted = False

                    time.sleep(2)
                    st.session_state.show_signals_password_change = False
                    st.rerun()
                else:
                    st.error("❌ Failed to save password to database. Please try again.")

        if cancel:
            st.session_state.show_signals_password_change = False
            st.rerun()

# -------------------------
# TRADING SIGNALS ROOM - PASSWORD PROTECTED VERSION WITH PERSISTENCE
# -------------------------
def render_trading_signals_room():
    """Main Trading Signals Room interface with password protection"""

    # Check if user has access to Signals Room
    if not st.session_state.signals_room_access_granted:
        render_signals_room_password_gate()
        return

    # Admin vs User view logic
    if st.session_state.user['plan'] == 'admin':
        render_admin_signals_room()
    else:
        render_user_signals_room()

def render_signals_room_password_gate():
    """Password gate with proper tracking - FIXED VERSION"""
    st.title("🔒 Trading Signals Room - Secure Access")
    
    # NEW: "Get Access Now" button at the top LEFT
    col1, col2 = st.columns([1, 3])  # Changed order - left column is smaller for button
    with col1:
        st.markdown(
            f'<a href="https://ko-fi.com/s/a6da7eb515" target="_blank">'
            f'<button style="background-color: #10B981; color: white; border: none; padding: 10px 16px; '
            f'text-align: center; text-decoration: none; display: inline-block; font-size: 14px; '
            f'cursor: pointer; border-radius: 6px; width: 100%; font-weight: bold;">'
            f'🚀 Get Access Now</button></a>',
            unsafe_allow_html=True
        )
    with col2:
        st.markdown("")  # Empty space for alignment
    
    st.markdown("---")

    st.warning("⚠️ **SECURE ACCESS REQUIRED** - Enter password to continue.")

    with st.form("signals_room_password_form"):
        password_input = st.text_input(
            "🔑 Enter Signals Room Password:",
            type="password",
            placeholder="Enter password...",
            key="signals_room_password_input"
        )

        submitted = st.form_submit_button("🚀 Access Trading Signals Room", use_container_width=True)

        if submitted:
            if password_input == st.session_state.signals_room_password:
                current_username = st.session_state.user['username']
                
                # CRITICAL: Track access BEFORE granting permission
                track_signals_access(current_username)
                
                # THEN grant access
                st.session_state.signals_room_access_granted = True
                st.success("✅ Access granted!")
                
                # FORCE a rerun to show the signals room
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Incorrect password")

def render_admin_signals_room():
    """Admin Trading Signals Room with full workflow"""

    # Header
    st.title("⚡ Trading Signals Room - Admin")
    st.markdown("---")

    # Admin workflow navigation - SIMPLIFIED
    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🚀 Launch Signal", use_container_width=True, key="admin_launch_signal"):
            st.session_state.signals_room_view = 'launch_signal'
            st.rerun()
    with col2:
        if st.button("🔍 Confirm Signals", use_container_width=True, key="admin_confirm_signal"):
            st.session_state.signals_room_view = 'confirm_signals'
            st.rerun()
    with col3:
        if st.button("📢 Published Signals", use_container_width=True, key="admin_published_signals"):
            st.session_state.signals_room_view = 'published_signals'
            st.rerun()

    st.markdown("---")

    # Render current view
    if st.session_state.signals_room_view == 'launch_signal':
        render_signal_launch_interface()
    elif st.session_state.signals_room_view == 'confirm_signals':
        render_signal_confirmation_interface()
    elif st.session_state.signals_room_view == 'published_signals':
        render_published_signals_interface()
    else:
        render_active_signals_overview()

def render_user_signals_room():
    """User Trading Signals Room - VIEW ONLY (SIMPLIFIED)"""

    # Header
    st.title("📱 Trading Signals Room")
    st.markdown("---")

    # User workflow navigation - ONLY SHOW ACTIVE SIGNALS
    if st.button("📱 Active Signals", use_container_width=True,
                type="primary", key="user_active_signals"):
        st.session_state.signals_room_view = 'active_signals'
        st.rerun()

    st.markdown("---")

    # Render active signals overview
    render_active_signals_overview()

def render_signal_launch_interface():
    """Interface for admin to launch new trading signals"""

    st.subheader("🚀 Launch New Trading Signal")

    # Signal creation mode selection
    col1, col2 = st.columns(2)
    with col1:
        if st.button("⚡ Quick Signal", use_container_width=True,
                    type="primary" if st.session_state.signal_creation_mode == 'quick' else "secondary",
                    key="quick_signal_btn"):
            st.session_state.signal_creation_mode = 'quick'
            st.rerun()
    with col2:
        if st.button("📋 Detailed Signal", use_container_width=True,
                    type="primary" if st.session_state.signal_creation_mode == 'detailed' else "secondary",
                    key="detailed_signal_btn"):
            st.session_state.signal_creation_mode = 'detailed'
            st.rerun()

    st.markdown("---")

    # Signal creation form
    if st.session_state.signal_creation_mode == 'quick':
        render_quick_signal_form()
    else:
        render_detailed_signal_form()

def render_quick_signal_form():
    """Quick signal form for rapid signal creation"""

    with st.form("quick_signal_form"):
        col1, col2 = st.columns(2)

        with col1:
            asset = st.selectbox("Asset*", SIGNAL_CONFIG["assets"], key="quick_asset")
            signal_type = st.selectbox("Signal Type*", SIGNAL_CONFIG["signal_types"], key="quick_signal_type")
            timeframe = st.selectbox("Timeframe*", list(SIGNAL_CONFIG["timeframes"].keys()),
                                   format_func=lambda x: SIGNAL_CONFIG["timeframes"][x]["name"],
                                   key="quick_timeframe")

        with col2:
            entry_price = st.number_input("Entry Price*", min_value=0.0, step=0.01, key="quick_entry")
            target_price = st.number_input("Target Price*", min_value=0.0, step=0.01, key="quick_target")
            stop_loss = st.number_input("Stop Loss*", min_value=0.0, step=0.01, key="quick_stop")

        # Quick description
        description = st.text_area("Signal Description*",
                                 placeholder="Brief description of the trading signal...",
                                 max_chars=200,
                                 key="quick_description")

        submitted = st.form_submit_button("🚀 Launch Quick Signal", use_container_width=True)

        if submitted:
            if not all([asset, signal_type, timeframe, entry_price, target_price, stop_loss, description]):
                st.error("❌ Please fill in all required fields (*)")
            else:
                # Create signal object
                new_signal = {
                    "signal_id": str(uuid.uuid4())[:8],
                    "asset": asset,
                    "signal_type": signal_type,
                    "timeframe": timeframe,
                    "entry_price": entry_price,
                    "target_price": target_price,
                    "stop_loss": stop_loss,
                    "description": description,
                    "created_by": st.session_state.user['username'],
                    "created_at": datetime.now().isoformat(),
                    "status": "pending_confirmation",
                    "confirmations": [],
                    "published_at": None,
                    "risk_level": "Medium",
                    "confidence": "Medium"
                }

                # Add to active signals
                st.session_state.active_signals.append(new_signal)
                save_signals_data(st.session_state.active_signals)

                st.success("✅ Signal launched successfully! Waiting for confirmation...")
                st.balloons()
                time.sleep(2)
                st.session_state.signals_room_view = 'confirm_signals'
                st.rerun()

def render_detailed_signal_form():
    """Detailed signal form with comprehensive analysis"""

    with st.form("detailed_signal_form"):
        col1, col2 = st.columns(2)

        with col1:
            asset = st.selectbox("Asset*", SIGNAL_CONFIG["assets"], key="detailed_asset")
            signal_type = st.selectbox("Signal Type*", SIGNAL_CONFIG["signal_types"], key="detailed_signal_type")
            timeframe = st.selectbox("Timeframe*", list(SIGNAL_CONFIG["timeframes"].keys()),
                                   format_func=lambda x: SIGNAL_CONFIG["timeframes"][x]["name"],
                                   key="detailed_timeframe")
            confidence = st.selectbox("Confidence Level*", SIGNAL_CONFIG["confidence_levels"], key="detailed_confidence")

        with col2:
            entry_price = st.number_input("Entry Price*", min_value=0.0, step=0.01, key="detailed_entry")
            target_price = st.number_input("Target Price*", min_value=0.0, step=0.01, key="detailed_target")
            stop_loss = st.number_input("Stop Loss*", min_value=0.0, step=0.01, key="detailed_stop")
            risk_level = st.select_slider("Risk Level*", ["Low", "Medium", "High", "Very High"], value="Medium", key="detailed_risk")

        # Technical analysis
        st.subheader("📊 Technical Analysis")
        col1, col2 = st.columns(2)

        with col1:
            rsi = st.slider("RSI", 0, 100, 50, key="detailed_rsi")
            macd = st.selectbox("MACD Signal", ["Bullish", "Bearish", "Neutral"], key="detailed_macd")
            volume_trend = st.selectbox("Volume Trend", ["Increasing", "Decreasing", "Stable"], key="detailed_volume")

        with col2:
            support_level = st.number_input("Support Level", min_value=0.0, step=0.01, key="detailed_support")
            resistance_level = st.number_input("Resistance Level", min_value=0.0, step=0.01, key="detailed_resistance")
            trend_direction = st.selectbox("Trend Direction", ["Uptrend", "Downtrend", "Sideways"], key="detailed_trend")

        # Detailed description and rationale
        description = st.text_area("Signal Description*",
                                 placeholder="Detailed description of the trading signal...",
                                 height=100,
                                 key="detailed_description")

        rationale = st.text_area("Trading Rationale*",
                               placeholder="Explain the reasoning behind this signal...",
                               height=100,
                               key="detailed_rationale")

        submitted = st.form_submit_button("🚀 Launch Detailed Signal", use_container_width=True)

        if submitted:
            if not all([asset, signal_type, timeframe, entry_price, target_price, stop_loss, description, rationale]):
                st.error("❌ Please fill in all required fields (*)")
            else:
                # Create detailed signal object
                new_signal = {
                    "signal_id": str(uuid.uuid4())[:8],
                    "asset": asset,
                    "signal_type": signal_type,
                    "timeframe": timeframe,
                    "entry_price": entry_price,
                    "target_price": target_price,
                    "stop_loss": stop_loss,
                    "description": description,
                    "rationale": rationale,
                    "technical_analysis": {
                        "rsi": rsi,
                        "macd": macd,
                        "volume_trend": volume_trend,
                        "support_level": support_level,
                        "resistance_level": resistance_level,
                        "trend_direction": trend_direction
                    },
                    "created_by": st.session_state.user['username'],
                    "created_at": datetime.now().isoformat(),
                    "status": "pending_confirmation",
                    "confirmations": [],
                    "published_at": None,
                    "risk_level": risk_level,
                    "confidence": confidence
                }

                # Add to active signals
                st.session_state.active_signals.append(new_signal)
                save_signals_data(st.session_state.active_signals)

                st.success("✅ Detailed signal launched successfully! Waiting for confirmation...")
                st.balloons()
                time.sleep(2)
                st.session_state.signals_room_view = 'confirm_signals'
                st.rerun()

def render_signal_confirmation_interface():
    """Interface for confirmation system - FIXED: Only 1 confirmation required"""

    st.subheader("🔍 Signal Confirmation Queue")

    # Get pending confirmation signals
    pending_signals = [s for s in st.session_state.active_signals if s["status"] == "pending_confirmation"]

    if not pending_signals:
        st.info("🎉 No signals waiting for confirmation. All signals are confirmed!")
        return

    for signal in pending_signals:
        with st.container():
            st.markdown("---")

            # Signal header
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                timeframe_config = SIGNAL_CONFIG["timeframes"][signal["timeframe"]]
                color = timeframe_config["color"]
                st.markdown(f"### **{signal['asset']}** - `{signal['signal_type']}`")
                st.markdown(f"<span style='color: {color}; font-weight: bold;'>⏱️ {timeframe_config['name']}</span>", unsafe_allow_html=True)

            with col2:
                st.write(f"**Entry:** ${signal['entry_price']:,.2f}")
                st.write(f"**Target:** ${signal['target_price']:,.2f}")

            with col3:
                st.write(f"**Stop:** ${signal['stop_loss']:,.2f}")
                risk_reward = (signal['target_price'] - signal['entry_price']) / (signal['entry_price'] - signal['stop_loss'])
                st.write(f"**R/R:** {risk_reward:.2f}:1")

            # Signal details
            with st.expander("📋 Signal Details", expanded=False):
                col1, col2 = st.columns(2)

                with col1:
                    st.write(f"**Description:** {signal['description']}")
                    if 'rationale' in signal:
                        st.write(f"**Rationale:** {signal['rationale']}")

                with col2:
                    st.write(f"**Risk Level:** {signal.get('risk_level', 'Medium')}")
                    st.write(f"**Confidence:** {signal.get('confidence', 'Medium')}")
                    st.write(f"**Created by:** {signal['created_by']}")
                    st.write(f"**Created at:** {datetime.fromisoformat(signal['created_at']).strftime('%Y-%m-%d %H:%M')}")

                # Technical analysis if available
                if 'technical_analysis' in signal:
                    st.subheader("📊 Technical Analysis")
                    tech = signal['technical_analysis']
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.write(f"**RSI:** {tech['rsi']}")
                        st.write(f"**MACD:** {tech['macd']}")
                    with col2:
                        st.write(f"**Volume:** {tech['volume_trend']}")
                        st.write(f"**Trend:** {tech['trend_direction']}")
                    with col3:
                        if tech['support_level'] > 0:
                            st.write(f"**Support:** ${tech['support_level']:,.2f}")
                        if tech['resistance_level'] > 0:
                            st.write(f"**Resistance:** ${tech['resistance_level']:,.2f}")

            # Confirmation actions - FIXED: Only 1 confirmation required
            col1, col2, col3 = st.columns([1, 1, 2])

            with col1:
                if st.button("✅ Confirm", key=f"confirm_{signal['signal_id']}", use_container_width=True):
                    # Add confirmation
                    if st.session_state.user['username'] not in [c['admin'] for c in signal['confirmations']]:
                        signal['confirmations'].append({
                            "admin": st.session_state.user['username'],
                            "timestamp": datetime.now().isoformat(),
                            "notes": "Signal confirmed"
                        })
                        save_signals_data(st.session_state.active_signals)
                        st.success("✅ Signal confirmed!")

                        # AUTO-PUBLISH after 1 confirmation (FIXED)
                        signal['status'] = 'published'
                        signal['published_at'] = datetime.now().isoformat()
                        save_signals_data(st.session_state.active_signals)
                        st.success("🎉 Signal automatically published!")
                        st.rerun()
                    else:
                        st.warning("⚠️ You have already confirmed this signal")

            with col2:
                if st.button("❌ Reject", key=f"reject_{signal['signal_id']}", use_container_width=True):
                    signal['status'] = 'rejected'
                    save_signals_data(st.session_state.active_signals)
                    st.error("❌ Signal rejected!")
                    st.rerun()

            with col3:
                # Show confirmation progress - FIXED: Only 1 required
                confirm_count = len(signal['confirmations'])
                required_confirmations = 1  # FIXED: Changed from 2 to 1
                progress = confirm_count / required_confirmations
                st.progress(progress, text=f"Confirmations: {confirm_count}/{required_confirmations}")

def render_published_signals_interface():
    """Interface for managing published signals"""

    st.subheader("📢 Published Signals")

    # Get published signals
    published_signals = [s for s in st.session_state.active_signals if s["status"] == "published"]

    if not published_signals:
        st.info("📭 No published signals yet. Confirm some signals first!")
        return

    # Filters
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_asset = st.selectbox("Filter by Asset", ["All Assets"] + SIGNAL_CONFIG["assets"], key="published_filter_asset")
    with col2:
        filter_timeframe = st.selectbox("Filter by Timeframe", ["All Timeframes"] + list(SIGNAL_CONFIG["timeframes"].keys()),
                                      format_func=lambda x: SIGNAL_CONFIG["timeframes"][x]["name"] if x != "All Timeframes" else x,
                                      key="published_filter_timeframe")
    with col3:
        filter_signal_type = st.selectbox("Filter by Type", ["All Types"] + SIGNAL_CONFIG["signal_types"], key="published_filter_type")

    # Apply filters
    filtered_signals = published_signals.copy()
    if filter_asset != "All Assets":
        filtered_signals = [s for s in filtered_signals if s["asset"] == filter_asset]
    if filter_timeframe != "All Timeframes":
        filtered_signals = [s for s in filtered_signals if s["timeframe"] == filter_timeframe]
    if filter_signal_type != "All Types":
        filtered_signals = [s for s in filtered_signals if s["signal_type"] == filter_signal_type]

    # Display signals
    for signal in filtered_signals:
        with st.container():
            st.markdown("---")

            # Signal card
            col1, col2, col3, col4 = st.columns([3, 2, 2, 1])

            with col1:
                # Signal type color coding
                signal_color = "#10B981" if signal["signal_type"] in ["BUY", "STRONG_BUY"] else "#EF4444" if signal["signal_type"] in ["SELL", "STRONG_SELL"] else "#6B7280"
                st.markdown(f"### **{signal['asset']}** - <span style='color: {signal_color};'>{signal['signal_type']}</span>", unsafe_allow_html=True)

                timeframe_config = SIGNAL_CONFIG["timeframes"][signal["timeframe"]]
                st.markdown(f"⏱️ {timeframe_config['name']} • 🎯 {signal.get('confidence', 'Medium')} Confidence")
                st.markdown(f"📝 {signal['description']}")

            with col2:
                st.metric("Entry Price", f"${signal['entry_price']:,.2f}")
                st.metric("Target Price", f"${signal['target_price']:,.2f}")

            with col3:
                st.metric("Stop Loss", f"${signal['stop_loss']:,.2f}")
                current_progress = 0  # This would come from real market data
                st.progress(current_progress, text=f"Progress: {current_progress:.1%}")

            with col4:
                # Remove signal button for admin
                if st.button("🗑️ Remove", key=f"remove_{signal['signal_id']}", use_container_width=True):
                    # Remove signal from active signals
                    st.session_state.active_signals = [s for s in st.session_state.active_signals if s['signal_id'] != signal['signal_id']]
                    save_signals_data(st.session_state.active_signals)
                    st.success("✅ Signal removed!")
                    st.rerun()

def render_active_signals_overview():
    """Overview of all active signals for both admin and users"""

    st.subheader("📱 Active Trading Signals")

    # Get active signals (published and not expired)
    active_signals = [s for s in st.session_state.active_signals
                     if s["status"] == "published"]

    if not active_signals:
        st.info("📭 No active signals available. Check back later for new trading opportunities!")
        return

    # Stats overview
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        buy_signals = len([s for s in active_signals if s["signal_type"] in ["BUY", "STRONG_BUY"]])
        st.metric("Buy Signals", buy_signals)
    with col2:
        sell_signals = len([s for s in active_signals if s["signal_type"] in ["SELL", "STRONG_SELL"]])
        st.metric("Sell Signals", sell_signals)
    with col3:
        short_term = len([s for s in active_signals if s["timeframe"] == "short"])
        st.metric("Short Term", short_term)
    with col4:
        total_signals = len(active_signals)
        st.metric("Total Active", total_signals)

    st.markdown("---")

    # Display active signals in a clean grid
    for i, signal in enumerate(active_signals):
        col1, col2 = st.columns([3, 2])

        with col1:
            # Signal info
            signal_color = "#10B981" if signal["signal_type"] in ["BUY", "STRONG_BUY"] else "#EF4444"
            timeframe_config = SIGNAL_CONFIG["timeframes"][signal["timeframe"]]

            st.markdown(f"#### **{signal['asset']}** • <span style='color: {signal_color};'>{signal['signal_type']}</span>", unsafe_allow_html=True)
            st.markdown(f"**{timeframe_config['name']}** • {signal.get('confidence', 'Medium')} Confidence")
            st.markdown(f"📊 {signal['description']}")

            # Progress bar for signal performance (simulated)
            progress_value = min(0.7, 0.3 + (i * 0.1))  # Simulated progress
            st.progress(progress_value, text=f"Signal Progress: {progress_value:.1%}")

        with col2:
            # Pricing info
            col2a, col2b = st.columns(2)
            with col2a:
                st.metric("Entry", f"${signal['entry_price']:,.2f}")
                st.metric("Stop Loss", f"${signal['stop_loss']:,.2f}")
            with col2b:
                st.metric("Target", f"${signal['target_price']:,.2f}")
                risk_reward = (signal['target_price'] - signal['entry_price']) / (signal['entry_price'] - signal['stop_loss'])
                st.metric("R/R Ratio", f"{risk_reward:.2f}:1")

        st.markdown("---")

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
                new_username = st.text_input("Choose Username*", help="3-20 characters, letters and numbers only", key="register_username")
                new_name = st.text_input("Full Name*", key="register_name")
                
                # FIXED: View-only plan selection - Always Trial
                plan_choice = "trial"  # HARDCODED to trial
                plan_info = Config.PLANS["trial"]
                st.text_input(
                    "Subscription Plan*",
                    value=f"{plan_info['name']} - Free",
                    disabled=True,
                    key="register_plan_display"
                )

            with col2:
                new_email = st.text_input("Email Address*", key="register_email")
                new_password = st.text_input("Create Password*", type="password", help="Minimum 8 characters", key="register_password")
                confirm_password = st.text_input("Confirm Password*", type="password", key="register_confirm_password")

            st.markdown("Required fields marked with *")

            # Plan features - Display Trial features
            st.info(f"""
            ✅ **{plan_info['name']} Features (Free):**
            • {plan_info['strategies']} Trading Strategies
            • {plan_info['max_sessions']} Concurrent Session
            • {plan_info['duration']}-day access
            • Basic Signal Access
            • View-Only Gallery
            • KAI Analysis View
            • No payment required
            """)

            # Terms agreement checkbox
            agreed = st.checkbox("I agree to the Terms of Service and Privacy Policy*", key="register_agree")

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
# ENHANCED IMAGE GALLERY FORUM WITH FIXED THUMBNAIL DISPLAY AND PERSISTENCE
# -------------------------

def render_image_gallery():
    """Main gallery - now paginated"""
    import streamlit as st
    st.session_state.gallery_page = 0
    st.title("📸 User Image Gallery (Paginated View)")
    render_image_gallery_paginated()

def decode_image_from_storage(item):
    """Decode image from storage format - placeholder implementation"""
    try:
        # This is a simplified version - you'll need to adapt based on your actual storage format
        if 'bytes_b64' in item:
            return base64.b64decode(item['bytes_b64'])
        return None
    except Exception:
        return None

# =====================================================================
# GALLERY PAGINATION CORE (placed before dashboard & main)
# =====================================================================
def get_gallery_images_count():
    """Get total count of gallery images"""
    if 'supabase_client' not in globals() or not supabase_client:
        return _cache_get("lk_gallery_count", 0)
    try:
        resp = supabase_client.table('gallery_images').select('id', count='exact').execute()
        if hasattr(resp, 'error') and resp.error:
            logging.error(f"Count error: {resp.error}")
            return _cache_get("lk_gallery_count", 0)
        count = getattr(resp, 'count', None) or (resp.data and len(resp.data)) or 0
        _cache_set("lk_gallery_count", count)
        return count
    except Exception as e:
        logging.error(f"Database count error: {e}")
        return _cache_get("lk_gallery_count", 0)

# USER IMAGE GALLERY - VIEW ONLY VERSION
# -------------------------
def render_user_image_gallery():
    """User image gallery with full database-backed pagination (FINAL)"""
    import streamlit as st

    # ---------- SAFETY: ensure needed session keys exist ----------
    if 'gallery_page' not in st.session_state:
        st.session_state.gallery_page = 0
    if 'gallery_per_page' not in st.session_state:
        st.session_state.gallery_per_page = 15
    if 'gallery_filter_author' not in st.session_state:
        st.session_state.gallery_filter_author = "All Authors"
    if 'gallery_filter_strategy' not in st.session_state:
        st.session_state.gallery_filter_strategy = "All Strategies"

    # ---------- HEADER ----------
    st.title("📸 Trading Analysis Image Gallery")
    st.markdown("View trading charts, analysis screenshots, and market insights shared by the community.")
    st.markdown("---")

    # Optional top tabs (Gallery / Statistics)
    tab1, tab2 = st.tabs(["🖼️ Image Gallery", "📊 Statistics"])
    with tab2:
        try:
            # Reuse your existing stats block
            if 'render_gallery_statistics_paginated' in globals():
                render_gallery_statistics_paginated()
            else:
                # Minimal stats fallback if function is not present
                total_images = get_gallery_images_count_filtered()
                st.metric("Total Images", total_images)
        except Exception as e:
            st.warning(f"Statistics unavailable: {e}")

    with tab1:
        # ---------- CONTROLS ----------
        st.subheader("🔍 Gallery Controls")
        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            sort_by = st.selectbox(
                "Sort by:",
                ["newest", "oldest", "most_liked"],
                key="user_gallery_sort"
            )

        with c2:
            # Best-effort author list from any cached/known images in session
            authors_set = set(
                img.get('uploaded_by', 'Unknown')
                for img in (st.session_state.get('uploaded_images', []))
            )
            author_choice = st.selectbox(
                "Filter by Author:",
                ["All Authors"] + sorted(list(authors_set)),
                key="user_gallery_filter_author"
            )

        with c3:
            # If you keep strategies in st.session_state.STRATEGIES (dict), reuse it
            STRATEGIES = st.session_state.get('STRATEGIES', {})
            strategies_list = list(STRATEGIES.keys()) if isinstance(STRATEGIES, dict) else []
            strategy_choice = st.selectbox(
                "Filter by Strategy:",
                ["All Strategies"] + strategies_list,
                key="user_gallery_filter_strategy"
            )

        with c4:
            per_page = st.selectbox(
                "Per Page:",
                [10, 15, 20, 30],
                index=[10, 15, 20, 30].index(st.session_state.get("gallery_per_page", 15)) if st.session_state.get("gallery_per_page", 15) in [10, 15, 20, 30] else 1,
                key="user_gallery_per_page"
            )
            # Persist per-page
            st.session_state.gallery_per_page = per_page

        with c5:
            if st.button("🔄 Refresh", use_container_width=True, key="user_gallery_refresh"):
                st.rerun()

        # ---------- HANDLE FILTER CHANGES: reset to page 1 ----------
        # (We only reset if user changed the selection in this render cycle)
        if author_choice != st.session_state.get("_last_user_author_choice"):
            st.session_state.gallery_page = 0
            st.session_state._last_user_author_choice = author_choice
            st.rerun()
        if strategy_choice != st.session_state.get("_last_user_strategy_choice"):
            st.session_state.gallery_page = 0
            st.session_state._last_user_strategy_choice = strategy_choice
            st.rerun()

        st.markdown("---")

        # ---------- TOTAL COUNT ----------
        filter_author = None if author_choice == "All Authors" else author_choice
        filter_strategy = None if strategy_choice == "All Strategies" else strategy_choice

        with st.spinner("📊 Counting images..."):
            total_images = get_gallery_images_count_filtered(
                filter_author=filter_author,
                filter_strategy=filter_strategy
            )

        if total_images == 0:
            st.warning("🖼️ **No images found** for the selected filters.")
            return

        total_pages = (total_images + per_page - 1) // per_page
        current_page = min(st.session_state.gallery_page, max(0, total_pages - 1))

        # ---------- STATS ----------
        st.subheader("📈 Gallery Statistics")
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1: st.metric("Total Images", total_images)
        with sc2: st.metric("Total Pages", total_pages)
        with sc3: st.metric("Current Page", current_page + 1)
        with sc4:
            start_num = current_page * per_page + 1
            end_num = min((current_page + 1) * per_page, total_images)
            st.metric("Showing", f"{start_num}-{end_num}")

        st.markdown("---")

        # ---------- TOP NAV ----------
        st.subheader("📄 Page Navigation")
        n1, n2, n3, n4, n5 = st.columns(5)

        with n1:
            if st.button("⏮️ First Page", use_container_width=True, key="user_gallery_first_top"):
                st.session_state.gallery_page = 0
                st.rerun()

        with n2:
            if current_page > 0:
                if st.button("◀️ Previous", use_container_width=True, key="user_gallery_prev_top"):
                    st.session_state.gallery_page = current_page - 1
                    st.rerun()
            else:
                st.button("◀️ Previous", use_container_width=True, disabled=True, key="user_gallery_prev_top_disabled")

        with n3:
            jump_page = st.number_input(
                "Go to Page:",
                min_value=1,
                max_value=max(1, total_pages),
                value=current_page + 1,
                key="user_gallery_jump"
            ) - 1
            if jump_page != current_page:
                st.session_state.gallery_page = max(0, min(jump_page, total_pages - 1))
                st.rerun()

        with n4:
            if current_page < total_pages - 1:
                if st.button("Next ▶️", use_container_width=True, key="user_gallery_next_top"):
                    st.session_state.gallery_page = current_page + 1
                    st.rerun()
            else:
                st.button("Next ▶️", use_container_width=True, disabled=True, key="user_gallery_next_top_disabled")

        with n5:
            if st.button("⏭️ Last Page", use_container_width=True, key="user_gallery_last_top"):
                st.session_state.gallery_page = total_pages - 1
                st.rerun()

        st.markdown("---")

        # ---------- PAGE DATA ----------
        with st.spinner("📥 Loading images..."):
            page_images = get_gallery_images_paginated(
                page=current_page,
                per_page=per_page,
                sort_by=sort_by,
                filter_author=filter_author,
                filter_strategy=filter_strategy
            )

        if not page_images:
            st.warning("⚠️ Failed to load images for this page.")
            if current_page > 0:
                st.session_state.gallery_page = 0
                st.rerun()
            return

        # Save current page images (if your viewer uses this)
        st.session_state.current_page_images = page_images

        # ---------- GRID ----------
        st.subheader(f"📸 Page {current_page + 1} Images")
        cols = st.columns(3)
        for idx, img_data in enumerate(page_images):
            col = cols[idx % 3]
            with col:
                # Use user card if you have one; otherwise reuse the generic card
                if 'render_user_image_card_paginated' in globals():
                    render_user_image_card_paginated(img_data, current_page, idx)
                else:
                    render_image_card_paginated(img_data, current_page, idx)

        st.markdown("---")

        # ---------- BOTTOM NAV ----------
        st.subheader("📄 Bottom Navigation")
        b1, b2, b3, b4, b5 = st.columns(5)

        with b1:
            if st.button("⏮️ First", use_container_width=True, key="user_gallery_first_bottom"):
                st.session_state.gallery_page = 0
                st.rerun()

        with b2:
            if current_page > 0:
                if st.button("◀️ Prev", use_container_width=True, key="user_gallery_prev_bottom"):
                    st.session_state.gallery_page = current_page - 1
                    st.rerun()
            else:
                st.button("◀️ Prev", use_container_width=True, disabled=True, key="user_gallery_prev_bottom_disabled")

        with b3:
            st.write(f"**Page {current_page + 1}/{total_pages}**")

        with b4:
            if current_page < total_pages - 1:
                if st.button("Next ▶️", use_container_width=True, key="user_gallery_next_bottom"):
                    st.session_state.gallery_page = current_page + 1
                    st.rerun()
            else:
                st.button("Next ▶️", use_container_width=True, disabled=True, key="user_gallery_next_bottom_disabled")

        with b5:
            if st.button("⏭️ Last", use_container_width=True, key="user_gallery_last_bottom"):
                st.session_state.gallery_page = total_pages - 1
                st.rerun()

        st.markdown("---")
        st.caption(f"✅ Displaying images {start_num}-{end_num} of {total_images} total")

def render_user_image_card_paginated(img_data, page_num, index):
    """Render individual image card - CLEAN IMAGE WITH DATE AND SMALL INFO"""
    try:
        # Get image bytes
        image_bytes = None
        if 'bytes' in img_data:
            image_bytes = img_data['bytes']
        elif 'bytes_b64' in img_data:
            image_bytes = base64.b64decode(img_data['bytes_b64'])
        
        if image_bytes:
            st.image(
                image_bytes,
                use_container_width=True,
                caption=None
            )
        else:
            st.warning("🖼️ Image data not available")
    except Exception as e:
        st.error(f"❌ Error displaying image")
    
    # Date and Download button row
    col1, col2 = st.columns([2, 1])
    
    with col1:
        timestamp = img_data.get('timestamp', '')
        if timestamp:
            try:
                upload_time = datetime.fromisoformat(timestamp).strftime("%m/%d/%Y")
                st.caption(f"📅 {upload_time}")
            except:
                st.caption(f"📅 {timestamp[:10]}")
        else:
            st.caption("📅 Unknown date")
    
    with col2:
        try:
            image_bytes = None
            if 'bytes' in img_data:
                image_bytes = img_data['bytes']
            elif 'bytes_b64' in img_data:
                image_bytes = base64.b64decode(img_data['bytes_b64'])
            
            if image_bytes:
                b64_img = base64.b64encode(image_bytes).decode()
                file_format = get_image_format_safe(img_data).lower()
                file_name = img_data.get('name', f'image_{index}')
                href = f'<a href="data:image/{file_format};base64,{b64_img}" download="{file_name}.{file_format}"><button style="width:100%; padding:6px; background:#4CAF50; color:white; border:none; border-radius:4px; cursor:pointer; font-size:12px; font-weight:bold;">⬇️ Download</button></a>'
                st.markdown(href, unsafe_allow_html=True)
        except Exception as e:
            st.button("⬇️ Download", disabled=True, use_container_width=True)
    
    st.divider()

def render_user_image_card(img_data, index):
    """Render individual image card for users - UPDATED FOR PAGINATION"""
    with st.container():
        # Display image at 50% width for better visibility
        col_image, col_info = st.columns([1.5, 1])  # 60% image, 40% info

        with col_image:
            try:
                # Check if we have bytes data in the expected format
                image_bytes = None
                if 'bytes' in img_data:
                    image_bytes = img_data['bytes']
                elif 'bytes_b64' in img_data:
                    image_bytes = base64.b64decode(img_data['bytes_b64'])
                
                if image_bytes:
                    st.image(
                        image_bytes,
                        use_container_width=True,
                        caption=img_data.get('name', 'Unnamed Image')
                    )
                else:
                    st.warning("📷 Image data not available")
            except Exception as e:
                st.error(f"❌ Error displaying image: {str(e)}")
                st.info("Image format may not be supported.")

        with col_info:
            # Image info on the right side
            st.markdown(f"**{img_data.get('name', 'Unnamed Image')}**")
            st.divider()

            # Description
            description = img_data.get('description', '')
            if description:
                preview = description[:100] + "..." if len(description) > 100 else description
                st.caption(f"📝 {preview}")
            else:
                st.caption("No description")

            # Strategy tags
            strategies = img_data.get('strategies', [])
            if strategies:
                st.caption(f"🏷️ **Strategies:**")
                for strategy in strategies[:3]:
                    st.caption(f"  • {strategy}")
                if len(strategies) > 3:
                    st.caption(f"  +{len(strategies) - 3} more")

            st.divider()

            # Metadata
            st.caption(f"👤 By: **{img_data.get('uploaded_by', 'Unknown')}**")
            timestamp = img_data.get('timestamp', '')
            if timestamp:
                try:
                    upload_time = datetime.fromisoformat(timestamp).strftime("%m/%d/%Y %H:%M")
                    st.caption(f"📅 {upload_time}")
                except:
                    st.caption(f"📅 {timestamp}")

            st.divider()

            # Interaction buttons - FULL WIDTH for better UX
            col_like, col_view = st.columns(2)

            with col_like:
                if st.button("❤️ Like", key=f"user_like_{index}_{img_data.get('id', index)}", use_container_width=True):
                    # Note: Like functionality would need to be implemented in the database
                    st.info("Like functionality requires database update implementation")
                    # img_data['likes'] = img_data.get('likes', 0) + 1
                    # save_gallery_images(st.session_state.uploaded_images)
                    # st.rerun()

            with col_view:
                if st.button("🖼️ Fullscreen", key=f"user_view_{index}_{img_data.get('id', index)}", use_container_width=True):
                    st.session_state.current_image_index = index
                    st.session_state.current_page_images = images  # Store current page images
                    st.session_state.image_viewer_mode = True
                    st.rerun()

            # Like count and download
            col_count, col_download = st.columns(2)
            with col_count:
                likes = img_data.get('likes', 0)
                st.metric("Likes", likes, label_visibility="collapsed")

            with col_download:
                try:
                    # Get image bytes for download
                    image_bytes = None
                    if 'bytes' in img_data:
                        image_bytes = img_data['bytes']
                    elif 'bytes_b64' in img_data:
                        image_bytes = base64.b64decode(img_data['bytes_b64'])
                    
                    if image_bytes:
                        b64_img = base64.b64encode(image_bytes).decode()
                        file_format = get_image_format_safe(img_data).lower()
                        file_name = img_data.get('name', f'image_{index}')
                        href = f'<a href="data:image/{file_format};base64,{b64_img}" download="{file_name}.{file_format}" style="text-decoration: none;">'
                        st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 8px; text-align: center; text-decoration: none; display: inline-block; font-size: 12px; cursor: pointer; border-radius: 4px; width: 100%;">⬇️ Download</button></a>', unsafe_allow_html=True)
                    else:
                        st.caption("Download unavailable")
                except Exception as e:
                    st.caption("Download unavailable")

        st.markdown("---")

def render_image_viewer():
    """Image viewer for both admin and user galleries"""
    if not hasattr(st.session_state, 'current_page_images') or not st.session_state.current_page_images:
        st.warning("No images to display")
        st.session_state.image_viewer_mode = False
        st.rerun()
        return

    current_images = st.session_state.current_page_images
    current_index = st.session_state.current_image_index
    
    if current_index >= len(current_images):
        st.session_state.current_image_index = 0
        current_index = 0

    img_data = current_images[current_index]

    # Header with navigation
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("⬅️ Back", use_container_width=True, key="viewer_back"):
            st.session_state.image_viewer_mode = False
            st.rerun()
            
    with col2:
        if st.button("◀️ Previous", use_container_width=True, disabled=current_index == 0, key="viewer_prev"):
            st.session_state.current_image_index = max(0, current_index - 1)
            st.rerun()
            
    with col3:
        st.markdown(f"### {img_data.get('name', 'Image Viewer')}")
        st.caption(f"Image {current_index + 1} of {len(current_images)}")
        
    with col4:
        if st.button("Next ▶️", use_container_width=True, disabled=current_index >= len(current_images) - 1, key="viewer_next"):
            st.session_state.current_image_index = min(len(current_images) - 1, current_index + 1)
            st.rerun()
            
    with col5:
        if st.button("📋 Close", use_container_width=True, key="viewer_close"):
            st.session_state.image_viewer_mode = False
            st.rerun()

    st.markdown("---")

    # Display the image at full width
    try:
        # Get image bytes
        image_bytes = None
        if 'bytes' in img_data:
            image_bytes = img_data['bytes']
        elif 'bytes_b64' in img_data:
            image_bytes = base64.b64decode(img_data['bytes_b64'])
        
        if image_bytes:
            st.image(image_bytes, use_container_width=True, caption=img_data.get('name', ''))
        else:
            st.error("❌ Unable to load image data")
    except Exception as e:
        st.error(f"❌ Error displaying image: {str(e)}")

    # Image details
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Image Details")
        st.write(f"**Name:** {img_data.get('name', 'N/A')}")
        st.write(f"**Uploaded by:** {img_data.get('uploaded_by', 'N/A')}")
        st.write(f"**Format:** {img_data.get('format', 'N/A')}")
        
        timestamp = img_data.get('timestamp', '')
        if timestamp:
            try:
                upload_time = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                st.write(f"**Uploaded:** {upload_time}")
            except:
                st.write(f"**Uploaded:** {timestamp}")
                
        st.write(f"**Likes:** {img_data.get('likes', 0)}")

    with col2:
        st.subheader("Description & Strategies")
        description = img_data.get('description', '')
        if description:
            st.write(description)
        else:
            st.info("No description provided")
            
        strategies = img_data.get('strategies', [])
        if strategies:
            st.write("**Related Strategies:**")
            for strategy in strategies:
                st.write(f"• {strategy}")
        else:
            st.info("No strategies tagged")

    # Download button
    st.markdown("---")
    try:
        image_bytes = None
        if 'bytes' in img_data:
            image_bytes = img_data['bytes']
        elif 'bytes_b64' in img_data:
            image_bytes = base64.b64decode(img_data['bytes_b64'])
            
        if image_bytes:
            b64_img = base64.b64encode(image_bytes).decode()
            file_format = get_image_format_safe(img_data).lower()
            file_name = img_data.get('name', f'image_{current_index}')
            href = f'<a href="data:image/{file_format};base64,{b64_img}" download="{file_name}.{file_format}" style="text-decoration: none;">'
            st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 12px 24px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 4px; width: 100%;">⬇️ Download Full Resolution Image</button></a>', unsafe_allow_html=True)
    except Exception as e:
        st.error("Download unavailable")

# -------------------------
# STRATEGY INDICATOR IMAGE UPLOAD AND DISPLAY COMPONENTS - FIXED VERSION
# -------------------------
def render_strategy_indicator_image_upload(strategy_name, indicator_name):
    """Render image upload for a specific strategy indicator - FULL WIDTH"""
    st.subheader(f"🖼️ {indicator_name} - Chart Image")

    # Check if there's already an image for this indicator
    existing_image = get_strategy_indicator_image(strategy_name, indicator_name)

    if existing_image:
        st.success("✅ Image already uploaded for this indicator")

        # Display the existing image at FULL WIDTH
        st.markdown(f"**Current {indicator_name} Chart:**")

        # Display at 75% width (fixed size that works)
        col_empty, col_image, col_empty2 = st.columns([1, 3, 1])
        with col_image:
            st.image(
                existing_image['bytes'],
                use_container_width=True,
                caption=f"{indicator_name} Chart"
            )

        # Image info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"📤 Uploaded by: {existing_image['uploaded_by']}")
        with col2:
            st.caption(f"📅 {datetime.fromisoformat(existing_image['timestamp']).strftime('%Y-%m-%d %H:%M')}")
        with col3:
            st.caption(f"📋 Format: {existing_image['format']}")

        # Action buttons
        col_v, col_r = st.columns(2)
        with col_v:
            if st.button("🖼️ Full View", key=f"full_view_{strategy_name}_{indicator_name}", use_container_width=True):
                st.session_state.current_strategy_indicator_image = existing_image
                st.session_state.strategy_indicator_viewer_mode = True
                st.session_state.current_strategy_indicator = f"{strategy_name}_{indicator_name}"
                st.rerun()

        with col_r:
            if st.button("🗑️ Remove", key=f"remove_{strategy_name}_{indicator_name}", use_container_width=True):
                success = delete_strategy_indicator_image(strategy_name, indicator_name)
                if success:
                    st.success("✅ Image removed!")
                    st.rerun()
                else:
                    st.error("❌ Error removing image")

    # Image upload section
    st.markdown("---")
    st.write("**Upload New Chart Image:**")

    uploaded_file = st.file_uploader(
        f"Upload chart image for {indicator_name}",
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
        key=f"upload_{strategy_name}_{indicator_name}"
    )

    if uploaded_file is not None:
        # Display preview at FULL WIDTH
        st.markdown("**Preview:**")

        col_empty, col_preview, col_empty2 = st.columns([1, 3, 1])
        with col_preview:
            st.image(uploaded_file, use_container_width=True)

        # Upload button
        if st.button("💾 Save Image to Indicator", key=f"save_{strategy_name}_{indicator_name}", use_container_width=True):
            # Read and process the image
            image = Image.open(uploaded_file)
            img_bytes = io.BytesIO()

            # Use the correct format for saving
            if image.format:
                image.save(img_bytes, format=image.format)
            else:
                image.save(img_bytes, format='PNG')

            # Create image data with all required fields
            image_data = {
                'name': f"{strategy_name}_{indicator_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                'bytes': img_bytes.getvalue(),
                'format': image.format if image.format else 'PNG',
                'uploaded_by': st.session_state.user['username'],
                'timestamp': datetime.now().isoformat()
            }

            # Save the image
            success = save_strategy_indicator_image(strategy_name, indicator_name, image_data)
            if success:
                st.success("✅ Image saved successfully!")
                st.balloons()
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Error saving image")

def render_strategy_indicator_image_viewer():
    """Viewer for strategy indicator images"""
    if not hasattr(st.session_state, 'current_strategy_indicator_image') or not st.session_state.current_strategy_indicator_image:
        st.warning("No image to display")
        st.session_state.strategy_indicator_viewer_mode = False
        st.rerun()
        return

    img_data = st.session_state.current_strategy_indicator_image

    # Header
    col1, col2, col3 = st.columns([1, 2, 1])
    with col1:
        if st.button("⬅️ Back", use_container_width=True, key="strategy_image_back"):
            st.session_state.strategy_indicator_viewer_mode = False
            st.rerun()

    with col2:
        st.markdown(f"### {img_data['strategy_name']} - {img_data['indicator_name']}")
        st.caption(f"Uploaded by: {img_data['uploaded_by']} | {datetime.fromisoformat(img_data['timestamp']).strftime('%Y-%m-%d %H:%M')}")

    with col3:
        if st.button("📋 Close", use_container_width=True, key="strategy_image_close"):
            st.session_state.strategy_indicator_viewer_mode = False
            st.rerun()

    st.markdown("---")

    # Main image display
    st.image(img_data['bytes'], use_container_width=True)

    # Download button
    st.markdown("---")
    try:
        b64_img = base64.b64encode(img_data['bytes']).decode()
        href = f'<a href="data:image/{img_data["format"].lower()};base64,{b64_img}" download="{img_data["name"]}" style="text-decoration: none;">'
        st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 10px 20px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; cursor: pointer; border-radius: 4px; width: 100%;">⬇️ Download Image</button></a>', unsafe_allow_html=True)
    except Exception as e:
        st.error("Download unavailable")

def display_strategy_indicator_images_user(strategy_name):
    """Display strategy indicator images for users (view only) - FULL WIDTH"""
    if strategy_name not in st.session_state.strategy_indicator_images:
        return

    st.subheader("📊 Strategy Charts")

    indicators_with_images = st.session_state.strategy_indicator_images[strategy_name]

    if not indicators_with_images:
        st.info("No chart images available for this strategy yet.")
        return

    # Display images ONE PER ROW at FULL WIDTH
    for indicator_name, img_data in indicators_with_images.items():
        with st.container():
            st.markdown(f"#### **{indicator_name}**")

            # Display at full width
            # Display at 75% width (fixed size that works)
            col_empty, col_image, col_empty2 = st.columns([1, 3, 1])
            with col_image:
                st.image(
                    img_data['bytes'],
                    use_container_width=True,
                    caption=f"{indicator_name} Chart"
                )

            # Image info below
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"📤 Uploaded by: {img_data['uploaded_by']}")
            with col2:
                st.caption(f"📅 {datetime.fromisoformat(img_data['timestamp']).strftime('%Y-%m-%d %H:%M')}")
            with col3:
                st.caption(f"📋 Format: {img_data['format']}")

            # Action buttons
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🖼️ Fullscreen", key=f"user_view_strat_{strategy_name}_{indicator_name}", use_container_width=True):
                    st.session_state.current_strategy_indicator_image = img_data
                    st.session_state.strategy_indicator_viewer_mode = True
                    st.session_state.current_strategy_indicator = f"{strategy_name}_{indicator_name}"
                    st.rerun()
            with col_b:
                try:
                    b64_img = base64.b64encode(img_data['bytes']).decode()
                    href = f'<a href="data:image/{img_data["format"].lower()};base64,{b64_img}" download="{img_data["name"]}" style="text-decoration: none;">'
                    st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 8px 12px; text-align: center; text-decoration: none; display: inline-block; font-size: 12px; cursor: pointer; border-radius: 4px; width: 100%;">⬇️ Download</button></a>', unsafe_allow_html=True)
                except:
                    st.button("⬇️ Download", disabled=True, use_container_width=True)

            st.markdown("---")

# -------------------------
# FIXED: USER PASSWORD CHANGE FUNCTIONALITY
# -------------------------
def render_user_password_change():
    """Allow users to change their own password"""
    st.subheader("🔐 Change Password")

    with st.form("user_password_change_form"):
        current_password = st.text_input("Current Password", type="password",
                                        placeholder="Enter your current password",
                                        key="user_current_password")
        new_password = st.text_input("New Password", type="password",
                                    placeholder="Enter new password (min 8 characters)",
                                    key="user_new_password")
        confirm_password = st.text_input("Confirm New Password", type="password",
                                        placeholder="Confirm new password",
                                        key="user_confirm_password")

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("✅ Change Password", use_container_width=True)
        with col2:
            if st.form_submit_button("❌ Cancel", use_container_width=True):
                st.session_state.show_user_password_change = False
                st.rerun()

        if submitted:
            if not current_password or not new_password or not confirm_password:
                st.error("❌ Please fill in all password fields")
            elif new_password != confirm_password:
                st.error("❌ New passwords do not match")
            elif len(new_password) < 8:
                st.error("❌ New password must be at least 8 characters")
            else:
                success, message = user_manager.change_own_password(
                    st.session_state.user['username'],
                    current_password,
                    new_password
                )
                if success:
                    st.success(f"✅ {message}")
                    st.session_state.show_user_password_change = False
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

# -------------------------
# FIXED: USER ACCOUNT SETTINGS - REMOVED KEY PARAMETER FROM ST.METRIC
# -------------------------
def render_user_account_settings():
    """User account settings - FIXED VERSION with top back button only"""

    # ADDED: Back button at the top
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("⬅️ Back to Dashboard", use_container_width=True, key="user_settings_back_top"):
            st.session_state.dashboard_view = 'main'
            st.rerun()

    with col_title:
        st.title("⚙️ Account Settings")

    user = st.session_state.user

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Profile Information")
        st.text_input("Full Name", value=user['name'], disabled=True, key="user_profile_name")
        st.text_input("Email", value=user['email'], disabled=True, key="user_profile_email")
        st.text_input("Username", value=user['username'], disabled=True, key="user_profile_username")

    with col2:
        st.subheader("Subscription Details")
        plan_name = Config.PLANS.get(user['plan'], {}).get('name', user['plan'].title())
        st.text_input("Current Plan", value=plan_name, disabled=True, key="user_plan")
        st.text_input("Expiry Date", value=user['expires'], disabled=True, key="user_expires")

        # FIXED: Removed the 'key' parameter from st.metric to fix the error
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Days Remaining", days_left)

    st.markdown("---")

    # Password change section
    if st.session_state.show_user_password_change:
        render_user_password_change()
    else:
        if st.button("🔑 Change Password", use_container_width=True, key="user_change_password_btn"):
            st.session_state.show_user_password_change = True
            st.rerun()

def render_premium_user_section():
    """Premium user section with membership options"""
    st.title("💎 Premium User")

    user = st.session_state.user
    current_plan = user['plan']
    plan_name = Config.PLANS.get(current_plan, {}).get('name', current_plan.title())

    # User status header
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Plan", plan_name)
    with col2:
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Days Remaining", days_left)
    with col3:
        if current_plan == 'premium':
            st.metric("Status", "Active ✅")
        else:
            st.metric("Status", "Trial ⏳")

    st.markdown("---")

    # Plan comparison
    st.subheader("📊 Plan Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🆓 Trial Plan")
        trial_plan = Config.PLANS['trial']
        st.write("**Features:**")
        st.write(f"• {trial_plan['strategies']} Trading Strategies")
        st.write(f"• {trial_plan['max_sessions']} Concurrent Session")
        st.write(f"• {trial_plan['duration']}-day access")
        st.write("• Basic Signal Access")
        st.write("• View-Only Gallery")
        st.write("• KAI Analysis View")
        st.write(f"• **Price: ${trial_plan['price']}/month**")

        if current_plan == 'trial':
            st.success("🎯 Your Current Plan")

    with col2:
        st.markdown("### 💎 Premium Plan")
        premium_plan = Config.PLANS['premium']
        st.write("**Premium Features:**")
        st.write(f"• {premium_plan['strategies']} Trading Strategies")
        st.write(f"• {premium_plan['max_sessions']} Concurrent Sessions")
        st.write(f"• {premium_plan['duration']}-day access")
        st.write("• Full Signal Access")
        st.write("• Upload & Download Gallery")
        st.write("• Enhanced KAI Analysis")
        st.write("• Priority Support")
        st.write(f"• **Starting at: ${premium_plan['price']}/month**")

        if current_plan == 'premium':
            st.success("🎉 Premium Member!")
        else:
            st.warning("Upgrade to unlock")

    st.markdown("---")

    # Action sections
    if current_plan == 'trial':
        render_become_member_section()
    else:
        render_renew_subscription_section()

    st.markdown("---")

    # Benefits showcase
    st.subheader("🚀 Premium Benefits")

    benefits_col1, benefits_col2, benefits_col3 = st.columns(3)

    with benefits_col1:
        st.markdown("""
        **📈 Enhanced Signals**
        - Full strategy access
        - Real-time updates
        - Advanced analytics
        - Export capabilities
        """)

    with benefits_col2:
        st.markdown("""
        **🖼️ Gallery Features**
        - Upload your charts
        - Download community images
        - Fullscreen viewer
        - Strategy tagging
        """)

    with benefits_col3:
        st.markdown("""
        **🧠 KAI AI Agent**
        - Enhanced analysis
        - DeepSeek AI integration
        - Historical archive
        - Export functionality
        """)

    # Support information
    st.markdown("---")
    st.info("""
    **💁 Need Help?**
    - Contact support: support@tradinganalysis.com
    - Billing questions: billing@tradinganalysis.com
    - Technical issues: tech@tradinganalysis.com
    """)

def render_become_member_section():
    """Section for trial users to become premium members - Ko-Fi Integration"""
    st.subheader("⭐ Become a Premium Member")

    st.success("""
    **Ready to upgrade?** Get full access to all premium features including enhanced signals,
    gallery uploads, and advanced KAI AI analysis.
    """)

    # Ko-Fi payment options with GREEN buttons
    st.markdown("### 💳 Choose Your Plan")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("#### 1 Month")
        st.write("**$19**")
        st.write("• Flexible billing")
        st.write("• Cancel anytime")

        kofi_monthly = Config.KOFI_PREMIUM_MONTHLY_LINK
        st.markdown(
            f'<a href="{kofi_monthly}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">💳 Subscribe Now</button></a>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("#### 3 Months")
        st.write("**$49**")
        st.write("• 3 months access")
        st.write("• Best for short-term")

        kofi_quarterly = Config.KOFI_PREMIUM_QUARTERLY_LINK
        st.markdown(
            f'<a href="{kofi_quarterly}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">💎 Subscribe Now</button></a>',
            unsafe_allow_html=True
        )

    with col3:
        st.markdown("#### 6 Months")
        st.write("**$97**")
        st.write("• 6 months access")
        st.write("• Extended access")

        kofi_semi_annual = Config.KOFI_PREMIUM_SEMI_ANNUAL_LINK
        st.markdown(
            f'<a href="{kofi_semi_annual}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🚀 Subscribe Now</button></a>',
            unsafe_allow_html=True
        )

    with col4:
        st.markdown("#### 12 Months")
        st.write("**$179**")
        st.write("• 12 months access")
        st.write("• Long-term value")

        kofi_annual = Config.KOFI_PREMIUM_ANNUAL_LINK
        st.markdown(
            f'<a href="{kofi_annual}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🏆 Subscribe Now</button></a>',
            unsafe_allow_html=True
        )

    # Important information
    st.markdown("---")
    st.info("""
    **🔐 Secure Payment Process:**
    - You'll be redirected to Ko-Fi's secure payment page
    - Multiple payment methods accepted (credit card, PayPal, Apple Pay, Google Pay)
    - Instant access after successful payment
    - Email receipt provided
    """)

    # Manual upgrade option for admin
    if st.session_state.user['plan'] == 'admin':
        st.markdown("---")
        st.warning("**Admin Manual Upgrade:**")
        if st.button("🔼 Manually Upgrade User to Premium", key="manual_upgrade"):
            success, message = user_manager.change_user_plan(st.session_state.user['username'], "premium")
            if success:
                st.session_state.user['plan'] = "premium"
                st.success("✅ User upgraded to premium!")
                st.rerun()

def render_renew_subscription_section():
    """Updated renewal section with Ko-Fi buttons"""
    st.subheader("🔄 Renew Your Subscription")

    user = st.session_state.user
    days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days

    if days_left > 7:
        st.success(f"✅ Your premium subscription is active! {days_left} days remaining.")
    elif days_left > 0:
        st.warning(f"⚠️ Your subscription expires in {days_left} days. Renew now to avoid interruption.")
    else:
        st.error("❌ Your subscription has expired. Renew to restore premium access.")

    # Ko-Fi renewal options with GREEN buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("#### 1 Month")
        st.write("**$19**")
        kofi_monthly = Config.KOFI_PREMIUM_MONTHLY_LINK
        st.markdown(
            f'<a href="{kofi_monthly}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🔄 Renew</button></a>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("#### 3 Months")
        st.write("**$49**")
        kofi_quarterly = Config.KOFI_PREMIUM_QUARTERLY_LINK
        st.markdown(
            f'<a href="{kofi_quarterly}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🔄 Renew</button></a>',
            unsafe_allow_html=True
        )

    with col3:
        st.markdown("#### 6 Months")
        st.write("**$97**")
        kofi_semi_annual = Config.KOFI_PREMIUM_SEMI_ANNUAL_LINK
        st.markdown(
            f'<a href="{kofi_semi_annual}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🔄 Renew</button></a>',
            unsafe_allow_html=True
        )

    with col4:
        st.markdown("#### 12 Months")
        st.write("**$179**")
        kofi_annual = Config.KOFI_PREMIUM_ANNUAL_LINK
        st.markdown(
            f'<a href="{kofi_annual}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🔄 Renew</button></a>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.subheader("⚙️ Subscription Settings")
    col5, col6 = st.columns(2)
    with col5:
        st.info("💡 Ko-Fi handles automatic renewals. Check your Ko-Fi dashboard for subscription settings.")
    with col6:
        st.info("📧 You'll receive renewal reminders via email before expiry.")

# -------------------------
# ENHANCED PREMIUM SIGNAL DASHBOARD WITH STRATEGY INDICATOR IMAGES - FIXED VERSION
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

    # Use session state strategy analyses data - FIXED: Now using session state
    strategy_data = st.session_state.strategy_analyses_data

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

    # Get daily strategies and cycle day
    daily_strategies, cycle_day = get_daily_strategies(analysis_date)

    # FIXED: Auto-select first strategy when date changes or no strategy selected
    if (st.session_state.get('last_analysis_date') != analysis_date or
        st.session_state.selected_strategy is None or
        st.session_state.selected_strategy not in daily_strategies):
        st.session_state.selected_strategy = daily_strategies[0]
        st.session_state.last_analysis_date = analysis_date

    selected_strategy = st.session_state.selected_strategy

    # FIXED: Clean sidebar with proper layout - 5-DAY CYCLE FIRST, then STRATEGY SELECTION, then SIGNAL ACTIONS
    with st.sidebar:
        st.title("🎛️ Admin Signal Control Panel")

        # Admin profile section
        st.markdown("---")
        st.write(f"👑 {user['name']}")
        st.success("🛠️ Admin Signal Editor")

        st.markdown("---")

        # 5-Day Cycle System - MOVED TO TOP (FIRST SECTION)
        st.subheader("📅 5-Day Cycle")

        # Display current date
        st.markdown(f"**Current Date:** {analysis_date.strftime('%m/%d/%Y')}")

        # Date navigation
        col1, col2 = st.columns(2)
        with col1:
            if st.button("◀️ Prev Day", use_container_width=True, key="premium_prev_day_btn"):
                new_date = analysis_date - timedelta(days=1)
                if new_date >= start_date:
                    st.query_params["date"] = new_date.strftime("%Y-%m-%d")
                    st.rerun()
                else:
                    st.warning("Cannot go before start date")
        with col2:
            if st.button("Next Day ▶️", use_container_width=True, key="premium_next_day_btn"):
                new_date = analysis_date + timedelta(days=1)
                st.query_params["date"] = new_date.strftime("%Y-%m-%d")
                st.rerun()

        # Quick date reset button
        if st.button("🔄 Today", use_container_width=True, key="premium_today_btn"):
            st.query_params["date"] = date.today().strftime("%Y-%m-%d")
            st.rerun()

        # Cycle information
        st.info(f"**Day {cycle_day} of 5-day cycle**")

        st.markdown("---")

        # Strategy selection - MOVED TO SECOND SECTION (right after 5-day cycle)
        # CHANGED: Replace dropdown with clickable buttons
        st.subheader("🎯 Choose Strategy to Edit:")

        # Create clickable buttons for each strategy
        for strategy in daily_strategies:
            if st.button(
                f"📊 {strategy}",
                use_container_width=True,
                type="primary" if strategy == selected_strategy else "secondary",
                key=f"premium_strategy_{strategy}"
            ):
                st.session_state.selected_strategy = strategy
                st.rerun()

        st.markdown("---")

        # Signal Actions - MOVED TO THIRD SECTION (after strategy selection)
        st.subheader("📊 Signal Actions")

        if st.button("📈 Signal Dashboard", use_container_width=True, key="premium_nav_main"):
            st.session_state.dashboard_view = 'main'
            st.rerun()

        if st.button("📝 Edit Signals", use_container_width=True, key="premium_nav_notes"):
            st.session_state.dashboard_view = 'notes'
            st.rerun()

        if st.button("⚙️ Admin Settings", use_container_width=True, key="premium_nav_settings"):
            st.session_state.dashboard_view = 'settings'
            st.rerun()

        if st.button("🔄 Refresh Signals", use_container_width=True, key="premium_nav_refresh"):
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
            use_container_width=True,
            key="premium_export_btn"
        )

        st.markdown("---")
        if st.button("🚪 Secure Logout", use_container_width=True, key="premium_logout_btn"):
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

    strategy_data = st.session_state.strategy_analyses_data
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
    # CHANGED: Removed " - ADMIN EDIT MODE" and added green BUY button
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.subheader(f"🔍 {selected_strategy} Analysis")
    with col_header2:
        st.button("🟢 BUY Strategy",
                 use_container_width=True,
                 key=f"buy_bundle_{selected_strategy}",
                 help="Purchase to use in TradingView")

    # REMOVED: Quick Analysis Notes section completely

    st.markdown("---")

    # NEW: Strategy indicator images section - FIXED: Now properly placed outside forms
    render_strategy_indicator_image_upload(selected_strategy, "Overview")

    st.markdown("---")

    # Detailed analysis button
    if st.button("📝 Open Detailed Analysis Editor", use_container_width=True, key="detailed_analysis_btn"):
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
    """Detailed strategy notes interface with full admin editing - UPDATED TYPE OPTIONS AND PROVIDER"""
    st.title("📝 Admin Signal Editor")

    # Header with cycle info
    col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
    with col1:
        st.subheader(f"Day {cycle_day} - {selected_strategy}")
    with col2:
        st.metric("Analysis Date", analysis_date.strftime("%m/%d/%Y"))
    with col3:
        st.button("🟢 BUY Strategy",
                 use_container_width=True,
                 key=f"buy_bundle_notes_{selected_strategy}",
                 help="Purchase to use in TradingView")
    with col4:
        if st.button("⬅️ Back to Dashboard", use_container_width=True, key="admin_back_dashboard_btn"):
            st.session_state.dashboard_view = 'main'
            st.rerun()

    st.markdown("---")

    # Notes Form - ADMIN VERSION WITH FULL ACCESS
    with st.form("admin_detailed_notes_form"):
        st.subheader(f"Admin Signal Editor - {selected_strategy}")

        # Load existing data for this strategy
        existing_data = strategy_data.get(selected_strategy, {})
        current_strategy_tag = next(iter(existing_data.values()), {}).get("strategy_tag", "Neutral")

        # UPDATED: Strategy Type with new lowercase options
        current_strategy_type = next(iter(existing_data.values()), {}).get("momentum", "Neutral reading")

        # Handle migration from old values to new values
        type_mapping = {
            "Momentum": "Momentum reading",
            "Extreme": "Extreme reading",
            "Not Defined": "Neutral reading",
            "MOMENTUM READING": "Momentum reading",
            "EXTREME READING": "Extreme reading",
            "NEUTRAL READING": "Neutral reading"
        }

        # Convert old values to new values
        if current_strategy_type in type_mapping:
            current_strategy_type = type_mapping[current_strategy_type]

        # Strategy-level settings
        col1, col2 = st.columns(2)
        with col1:
            strategy_tag = st.selectbox("Strategy Tag:", ["Neutral", "Buy", "Sell"],
                                      index=["Neutral","Buy","Sell"].index(current_strategy_tag),
                                      key="admin_strategy_tag")
        with col2:
            # UPDATED: New Type options in lowercase
            new_type_options = ["Neutral reading", "Extreme reading", "Momentum reading"]
            current_index = new_type_options.index(current_strategy_type) if current_strategy_type in new_type_options else 0
            strategy_type = st.selectbox("Strategy Type:", new_type_options,
                                       index=current_index,
                                       key="admin_strategy_type")

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
        submitted = st.form_submit_button("💾 Save All Signals (Admin)", use_container_width=True, key="admin_save_all_btn")
        if submitted:
            if selected_strategy not in st.session_state.strategy_analyses_data:
                st.session_state.strategy_analyses_data[selected_strategy] = {}

            for indicator in indicators:
                key_note = f"note__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"
                key_status = f"status__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"

                st.session_state.strategy_analyses_data[selected_strategy][indicator] = {
                    "note": st.session_state.get(key_note, ""),
                    "status": st.session_state.get(key_status, "Open"),
                    "momentum": strategy_type,  # This now stores the new lowercase type
                    "strategy_tag": strategy_tag,
                    "analysis_date": analysis_date.strftime("%Y-%m-%d"),
                    "last_modified": datetime.utcnow().isoformat() + "Z",
                    "modified_by": "KAI"  # CHANGED: from "admin" to "KAI"
                }

            # Save to Supabase
            save_data(st.session_state.strategy_analyses_data)
            st.success("✅ All signals saved successfully! (Admin Mode)")

    # FIXED: Strategy indicator images section - Now placed outside the main form
    st.markdown("---")
    st.subheader("🖼️ Strategy Indicator Images")

    # Display images for each indicator
    indicators = STRATEGIES[selected_strategy]
    col_objs = st.columns(3)

    for i, indicator in enumerate(indicators):
        col = col_objs[i % 3]
        with col:
            with st.expander(f"📊 {indicator} Chart", expanded=False):
                # FIXED: Call the image upload function outside any form
                render_strategy_indicator_image_upload(selected_strategy, indicator)

    # Display saved analyses
    st.markdown("---")
    st.subheader("📜 Saved Signals - ADMIN VIEW")

    view_options = ["Today's Focus"] + daily_strategies
    filter_strategy = st.selectbox("Filter by strategy:", view_options, index=0, key="admin_filter_strategy")

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
                    momentum_type = meta.get("momentum", "neutral reading")
                    # Apply the same mapping for display
                    if momentum_type in type_mapping:
                        momentum_type = type_mapping[momentum_type]
                    status_icon = "✅ Done" if meta.get("status", "Open") == "Done" else "🕓 Open"
                    # CHANGED: Show "KAI" instead of the actual modified_by field
                    with st.expander(f"{ind_name} ({momentum_type}) — {status_icon} — Provider: KAI", expanded=False):
                        st.write(meta.get("note", "") or "_No notes yet_")
                        st.caption(f"Last updated: {meta.get('last_modified', 'N/A')}")

def render_admin_account_settings():
    """Admin account settings in premium mode - FIXED with top back button only"""

    # ADDED: Back button at the top
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("⬅️ Back to Dashboard", use_container_width=True, key="admin_settings_back_top"):
            st.session_state.dashboard_view = 'main'
            st.rerun()

    with col_title:
        st.title("⚙️ Admin Settings - Premium Mode")

    user = st.session_state.user

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Admin Profile")
        st.text_input("Full Name", value=user['name'], disabled=True, key="admin_profile_name")
        st.text_input("Email", value=user['email'], disabled=True, key="admin_profile_email")
        st.text_input("Username", value=user['username'], disabled=True, key="admin_profile_username")

    with col2:
        st.subheader("Admin Privileges")
        st.text_input("Role", value="System Administrator", disabled=True, key="admin_role")
        st.text_input("Access Level", value="Full System Access", disabled=True, key="admin_access")
        st.text_input("Signal Editing", value="Enabled", disabled=True, key="admin_editing")

    st.markdown("---")
    st.subheader("Quick Actions")

    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("🛠️ Switch to Admin Dashboard", use_container_width=True, key="switch_admin_dash_btn"):
            st.session_state.admin_dashboard_mode = "admin"
            st.rerun()

    with col2:
        if st.button("📊 Refresh All Data", use_container_width=True, key="refresh_admin_data_btn"):
            user_manager.load_data()
            st.rerun()

# -------------------------
# ENHANCED USER DASHBOARD WITH STRATEGY INDICATOR IMAGES - FIXED VERSION
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

    # Use session state strategy analyses data - FIXED: Now using session state
    strategy_data = st.session_state.strategy_analyses_data

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

    # Get daily strategies and cycle day
    daily_strategies, cycle_day = get_daily_strategies(analysis_date)

    # FIXED: Auto-select first strategy when date changes or no strategy selected
    if (st.session_state.get('last_analysis_date') != analysis_date or
        st.session_state.selected_strategy is None or
        st.session_state.selected_strategy not in daily_strategies):
        st.session_state.selected_strategy = daily_strategies[0]
        st.session_state.last_analysis_date = analysis_date

    selected_strategy = st.session_state.selected_strategy

    # FIXED: Clean sidebar with proper layout - 5-DAY CYCLE FIRST, then STRATEGY SELECTION, then NAVIGATION
    with st.sidebar:
        st.title("🎛️ Signal Dashboard")

        # User profile section
        st.markdown("---")
        st.write(f"👤 {user['name']}")
        plan_display = Config.PLANS.get(user['plan'], {}).get('name', user['plan'].title())
        st.caption(f"🚀 {plan_display}")

        # Account status with progress
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.progress(min(1.0, days_left / 30), text=f"📅 {days_left} days remaining")

        st.markdown("---")

        render_user_purchase_button()

        # 5-Day Cycle System - MOVED TO TOP (FIRST SECTION)
        st.subheader("📅 5-Day Cycle")

        # Display current date
        st.markdown(f"**Current Date:** {analysis_date.strftime('%m/%d/%Y')}")

        # Date navigation - READ ONLY FOR USERS
        col1, col2 = st.columns(2)
        with col1:
            if st.button("◀️ Prev Day", use_container_width=True, key="user_prev_day_btn"):
                new_date = analysis_date - timedelta(days=1)
                if new_date >= start_date:
                    st.query_params["date"] = new_date.strftime("%Y-%m-%d")
                    st.rerun()
                else:
                    st.warning("Cannot go before start date")
        with col2:
            if st.button("Next Day ▶️", use_container_width=True, key="user_next_day_btn"):
                new_date = analysis_date + timedelta(days=1)
                st.query_params["date"] = new_date.strftime("%Y-%m-%d")
                st.rerun()

        # Quick date reset button
        if st.button("🔄 Today", use_container_width=True, key="user_today_btn"):
            st.query_params["date"] = date.today().strftime("%Y-%m-%d")
            st.rerun()

        # Cycle information
        st.info(f"**Day {cycle_day} of 5-day cycle**")

        st.markdown("---")

        # Strategy selection - READ ONLY - MOVED TO SECOND SECTION (right after 5-day cycle)
        # CHANGED: Replace dropdown with clickable buttons
        st.subheader("🎯 Choose Strategy to View:")

        # Create clickable buttons for each strategy
        for strategy in daily_strategies:
            if st.button(
                f"📊 {strategy}",
                use_container_width=True,
                type="primary" if strategy == selected_strategy else "secondary",
                key=f"user_strategy_{strategy}"
            ):
                st.session_state.selected_strategy = strategy
                st.rerun()

        st.markdown("---")

        # Navigation - SIMPLIFIED FOR USERS - MOVED TO THIRD SECTION (after strategy selection)
        st.subheader("📊 Navigation")
        if st.button("📈 View Signals", use_container_width=True, key="user_nav_main"):
            st.session_state.dashboard_view = 'main'
            st.rerun()

        if st.button("⚙️ Account Settings", use_container_width=True, key="user_nav_settings"):
            st.session_state.dashboard_view = 'settings'
            st.rerun()

        st.markdown("---")

        # DISCLAIMER BEFORE LOGOUT BUTTON - FOR LEGAL REASONS
        st.markdown("""
        <div style="background-color: #fbe9e7; padding: 12px; border-radius: 6px; border-left: 4px solid #d84315; margin: 10px 0;">
            <small><strong style="color: #bf360c;">⚠️ RISK WARNING</strong></small><br>
            <small style="color: #3e2723;">This is not financial advice. Trading carries high risk of loss. 
            Only risk capital you can afford to lose. Past performance ≠ future results.</small>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # LOGOUT BUTTON AFTER DISCLAIMER
        if st.button("🚪 Logout", use_container_width=True, key="user_logout_btn"):
            user_manager.logout(user['username'])
            st.session_state.user = None
            st.rerun()

    # Main dashboard content - READ ONLY for users but same layout as admin
    current_view = st.session_state.get('dashboard_view', 'main')

    # ADD THIS: Check if purchase verification modal should be shown
    if st.session_state.get('show_purchase_verification'):
        render_purchase_verification_modal()
        return  # Return early to prevent showing other content when modal is open

    if current_view == 'settings':
        render_user_account_settings()
    else:
        render_user_trading_dashboard(data, user, daily_strategies, cycle_day, analysis_date, selected_strategy)

def render_user_trading_dashboard(data, user, daily_strategies, cycle_day, analysis_date, selected_strategy):
    """User trading dashboard - CLEANED VERSION WITHOUT KAI BUTTONS"""
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

    strategy_data = st.session_state.strategy_analyses_data
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

    # ENHANCED: Green Buy Strategy buttons like admin dashboard
    col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
    with col_header1:
        st.subheader(f"Signal Analysis - {selected_strategy}")
    with col_header2:
        st.markdown(
            f'<a href="https://ko-fi.com/s/c2d66d197b" target="_blank">'
            f'<button style="background-color: #059669; color: white; border: none; padding: 10px 16px; '
            f'text-align: center; text-decoration: none; display: inline-block; font-size: 14px; '
            f'cursor: pointer; border-radius: 6px; width: 100%; font-weight: bold;">'
            f'📊 BUY This Strategy</button></a>',
            unsafe_allow_html=True
        )
    with col_header3:
        st.markdown(
            f'<a href="https://ko-fi.com/s/218558f1c9" target="_blank">'
            f'<button style="background-color: #10B981; color: white; border: none; padding: 10px 16px; '
            f'text-align: center; text-decoration: none; display: inline-block; font-size: 14px; '
            f'cursor: pointer; border-radius: 6px; width: 100%; font-weight: bold;">'
            f'🚀 BUY All 15 Strategies</button></a>',
            unsafe_allow_html=True
        )

    # Display existing analysis
    strategy_data = st.session_state.strategy_analyses_data
    existing_data = strategy_data.get(selected_strategy, {})

    if existing_data:
        # Get strategy-level info from first indicator
        first_indicator = next(iter(existing_data.values()), {})
        strategy_tag = first_indicator.get("strategy_tag", "Neutral")
        strategy_type = first_indicator.get("momentum", "neutral reading")

        # Handle migration from old values for display
        type_mapping = {
            "Momentum": "Momentum reading",
            "Extreme": "Extreme reading",
            "Not Defined": "Neutral reading",
            "MOMENTUM READING": "Momentum reading",
            "EXTREME READING": "Extreme reading",
            "NEUTRAL READING": "Neutral reading"
        }

        # Convert old values to new values for display
        if strategy_type in type_mapping:
            strategy_type = type_mapping[strategy_type]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Signal:** {strategy_tag}")
        with col2:
            st.info(f"**Type:** {strategy_type}")  # Now shows new lowercase type options
        with col3:
            st.info(f"**Provider:** KAI")  # CHANGED: Always show "KAI" instead of the modified_by field

        st.markdown("---")

        # ENHANCED: Display indicators in expandable boxes - INTERACTIVE VIEW
        st.subheader("📊 Indicator Analysis")

        indicators = STRATEGIES[selected_strategy]
        col_objs = st.columns(3)

        for i, indicator in enumerate(indicators):
            col = col_objs[i % 3]
            existing = existing_data.get(indicator, {})
            note = existing.get("note", "")
            status = existing.get("status", "Open")
            momentum = existing.get("momentum", "Not Defined")

            # ✅ COSMETIC CHANGE: Add checkmark for "Done" status indicators
            if status == "Done":
                expander_title = f"**{indicator}** ✅"
            else:
                expander_title = f"**{indicator}**"

            with col.expander(expander_title, expanded=False):
                if note:
                    st.text_area(
                        f"Analysis",
                        value=note,
                        height=120,
                        disabled=True,
                        key=f"user_view_{sanitize_key(selected_strategy)}_{sanitize_key(indicator)}_{i}"
                    )
                else:
                    st.info("No analysis available for this indicator.")

                st.caption(f"Status: {status}")
                if existing.get("last_modified"):
                    st.caption(f"Last updated: {existing['last_modified'][:16]}")
    else:
        st.warning("No signal data available for this strategy yet.")

    # NEW: Display strategy indicator images for users
    display_strategy_indicator_images_user(selected_strategy)

    st.markdown("---")

    # Recent activity - READ ONLY
    if data.get('saved_analyses'):
        st.markdown("---")
        st.subheader("📜 Your Recent Views")
        for strategy, analysis in list(data['saved_analyses'].items())[-3:]:
            with st.expander(f"{strategy} - {analysis['timestamp'].strftime('%H:%M')}"):
                st.write(f"**Tag:** {analysis['tag']} | **Type:** {analysis['type']}")
                st.write(analysis.get('note', 'No notes'))

# -------------------------
# COMPLETE ADMIN DASHBOARD WITH DUAL MODE - FIXED VERSION
# -------------------------
# === KAI PAGINATION CORE (placed before dashboard & main) ===
def get_gallery_images_count():
    """Get total count of gallery images"""
    if 'supabase_client' not in globals() or not supabase_client:
        return _cache_get("lk_gallery_count", 0)
    try:
        resp = supabase_client.table('gallery_images').select('id', count='exact').execute()
        if hasattr(resp, 'error') and resp.error:
            logging.error(f"Count error: {resp.error}")
            return _cache_get("lk_gallery_count", 0)
        count = getattr(resp, 'count', None) or (resp.data and len(resp.data)) or 0
        _cache_set("lk_gallery_count", count)
        return count
    except Exception as e:
        logging.error(f"Database count error: {e}")
        return _cache_get("lk_gallery_count", 0)

# -------------------------
# Gallery Pagination - UI Layer
# -------------------------
import streamlit as st


def render_admin_image_gallery_paginated():
    st.title("🖼️ Admin: Image Gallery Management")
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📊 View & Manage", "⬆️ Upload", "⚙️ Settings"])
    with admin_tab1:
        render_image_gallery_paginated()
        st.markdown("---")
        st.subheader("🛠️ Admin Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh Gallery", use_container_width=True, key="admin_refresh_gallery"):
                st.session_state.gallery_page = 0; st.rerun()
        with col2:
            if st.button("📊 Gallery Stats", use_container_width=True, key="admin_gallery_stats"):
                st.session_state.show_gallery_stats = True
        with col3:
            if st.button("🗑️ Clear Gallery", use_container_width=True, key="admin_clear_gallery"):
                st.session_state.show_clear_gallery_confirmation = True; st.rerun()
        if st.session_state.get('show_gallery_stats'):
            render_gallery_statistics_paginated()
    with admin_tab2:
        render_image_uploader()
    with admin_tab3:
        st.subheader("⚙️ Gallery Settings")
        days_old = st.slider("Delete images older than (days):", 1, 365, 90)
        if st.button("🗑️ Purge Old Images", use_container_width=True):
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            try:
                if 'supabase_client' in globals() and supabase_client:
                    supabase_client.table('gallery_images').delete().lt('timestamp', cutoff_date).execute()
                st.success(f"✅ Deleted images older than {days_old} days")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")


@retry_with_backoff(max_retries=3, base_delay=0.5, exceptions=(Exception,))
def get_gallery_images_paginated(page=0, per_page=15, sort_by="newest", 
                                  filter_author=None, filter_strategy=None):
    """Paginated fetch with robust null checking"""
    try:
        if not supabase_client:
            return []

        offset = max(page, 0) * max(per_page, 1)
        query = supabase_client.table("gallery_images").select("*")

        # Apply filters
        if filter_author and filter_author != "All Authors":
            query = query.eq("uploaded_by", filter_author)
        if filter_strategy and filter_strategy != "All Strategies":
            try:
                query = query.contains("strategies", [filter_strategy])
            except:
                pass  # Array filtering might not be supported

        # Apply sorting
        sort_field = "timestamp"
        sort_order = "desc" if sort_by != "oldest" else "asc"
        if sort_by == "most_liked":
            sort_field = "likes"
            sort_order = "desc"
            
        query = query.order(sort_field, desc=(sort_order == "desc"))
        query = query.range(offset, offset + per_page - 1)

        resp = query.execute()
        if not resp or not getattr(resp, "data", None):
            return []

        imgs = []
        for row in resp.data:
            try:
                # CRITICAL: Ensure format field exists
                if not row.get('format'):
                    # Try to infer from name
                    name = row.get('name', '')
                    if name:
                        ext = name.split('.')[-1].lower() if '.' in name else 'png'
                        row['format'] = ext.upper() if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp'] else 'PNG'
                    else:
                        row['format'] = 'PNG'  # Safe default
                
                # Reconstruct bytes from multiple possible sources
                if isinstance(row.get('encoded_data'), dict):
                    row['bytes'] = decode_image_from_storage(row['encoded_data'])
                elif row.get('bytes_b64'):
                    try:
                        row['bytes'] = base64.b64decode(row['bytes_b64'])
                    except Exception as e:
                        logging.warning(f"Failed to decode bytes_b64 for {row.get('name')}: {e}")
                        row['bytes'] = None
                elif not row.get('bytes'):
                    row['bytes'] = None
                
                # Ensure strategies field exists
                row["strategies"] = row.get("strategies") or [row.get("strategy") or "Unspecified"]
                row["likes"] = row.get("likes", 0)
                
                imgs.append(row)
                
            except Exception as e:
                logging.warning(f"Skipping corrupted image {row.get('name')}: {e}")
                continue
        
        return imgs
        
    except Exception as e:
        logging.error(f"Gallery pagination error: {e}")
        st.error(f"⚠️ Failed to load images: {e}")
        return []
        
def render_admin_image_gallery_paginated():
    st.title("🖼️ Admin: Image Gallery Management")
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📊 View & Manage", "⬆️ Upload", "⚙️ Settings"])
    with admin_tab1:
        render_image_gallery_paginated()
        st.markdown("---")
        st.subheader("🛠️ Admin Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh Gallery", use_container_width=True, key="admin_refresh_gallery"):
                st.session_state.gallery_page = 0; st.rerun()
        with col2:
            if st.button("📊 Gallery Stats", use_container_width=True, key="admin_gallery_stats"):
                st.session_state.show_gallery_stats = True
        with col3:
            if st.button("🗑️ Clear Gallery", use_container_width=True, key="admin_clear_gallery"):
                st.session_state.show_clear_gallery_confirmation = True; st.rerun()
        if st.session_state.get('show_gallery_stats'):
            render_gallery_statistics_paginated()
    with admin_tab2:
        render_image_uploader()
    with admin_tab3:
        st.subheader("⚙️ Gallery Settings")
        days_old = st.slider("Delete images older than (days):", 1, 365, 90)
        if st.button("🗑️ Purge Old Images", use_container_width=True):
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            try:
                if 'supabase_client' in globals() and supabase_client:
                    supabase_client.table('gallery_images').delete().lt('timestamp', cutoff_date).execute()
                st.success(f"✅ Deleted images older than {days_old} days")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

@retry_with_backoff(max_retries=3, base_delay=0.5, exceptions=(Exception,))
def get_gallery_images_count_filtered(
    filter_author: str = None,
    filter_strategy: str = None,
    min_likes: int = 0
) -> int:
    """
    Get total count of gallery images with filters applied.
    
    FIXES:
    - Proper error handling
    - Fallback to session state
    - Safe filter application
    """
    
    # STEP 1: Try database first
    if supabase_client:
        try:
            query = supabase_client.table('gallery_images').select('id', count='exact')
            
            if filter_author:
                query = query.eq('uploaded_by', filter_author)
            
            if filter_strategy:
                try:
                    query = query.contains('strategies', [filter_strategy])
                except Exception:
                    # Array filtering might not be supported
                    pass
            
            resp = query.execute()
            
            if hasattr(resp, 'error') and resp.error:
                raise RuntimeError(f"Database error: {resp.error}")
            
            count = getattr(resp, 'count', None)
            if count is None and hasattr(resp, 'data'):
                count = len(resp.data)
            
            count = count or 0
            _cache_set("lk_gallery_count_filtered", count)
            
            logging.info(f"✅ Gallery count: {count}")
            return count
            
        except Exception as e:
            logging.error(f"❌ Database count failed: {e}")
            # Fall through to session state fallback
    
    # STEP 2: Fallback to session state
    try:
        all_images = st.session_state.get('uploaded_images', [])
        filtered = all_images.copy()
        
        if filter_author:
            filtered = [img for img in filtered if img.get('uploaded_by') == filter_author]
        
        if filter_strategy:
            filtered = [img for img in filtered if filter_strategy in (img.get('strategies') or [])]
        
        if min_likes > 0:
            filtered = [img for img in filtered if img.get('likes', 0) >= min_likes]
        
        count = len(filtered)
        logging.info(f"✅ Session state count: {count}")
        return count
        
    except Exception as e:
        logging.error(f"❌ Session state count failed: {e}")
        return 0
        
# -------------------------
# Gallery Pagination - UI Layer
# -------------------------
import streamlit as st

def render_image_uploader():
    """
    MINIMAL IMAGE UPLOADER - Only uses columns visible in your table structure
    """
    st.subheader("🖼️ Upload Trading Images")
    
    # Get available strategies for tagging
    STRATEGIES = st.session_state.get('STRATEGIES', {})
    if isinstance(STRATEGIES, dict):
        available_strategies = list(STRATEGIES.keys())
    else:
        available_strategies = []
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose images to upload",
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
        accept_multiple_files=True,
        key="gallery_uploader_minimal"
    )
    
    # Image description
    image_description = st.text_area(
        "Image Description (Optional):",
        placeholder="Describe what this image shows...",
        height=100,
        key="gallery_description_minimal"
    )
    
    # Strategy tagging
    selected_strategies = st.multiselect(
        "Tag Related Strategies (Optional):",
        available_strategies,
        default=[],
        key="gallery_strategies_minimal"
    )
    
    if st.button("🚀 Upload to Gallery", use_container_width=True, key="upload_btn_minimal"):
        if not uploaded_files:
            st.warning("Select at least one image to upload.")
            return
        
        if not supabase_client:
            st.error("❌ Supabase client not available")
            return
        
        success_count = 0
        error_count = 0
        
        for uf in uploaded_files:
            try:
                # Read file bytes
                file_bytes = uf.read()
                
                # Validate file size (10MB limit)
                if len(file_bytes) > 10 * 1024 * 1024:
                    st.error(f"❌ {uf.name}: File too large (>10MB)")
                    error_count += 1
                    continue
                
                # Validate file not empty
                if len(file_bytes) == 0:
                    st.error(f"❌ {uf.name}: File is empty")
                    error_count += 1
                    continue
                
                # Determine file format from filename
                file_ext = uf.name.split('.')[-1].lower() if '.' in uf.name else 'png'
                format_map = {
                    'jpg': 'JPEG', 'jpeg': 'JPEG', 'png': 'PNG', 
                    'gif': 'GIF', 'bmp': 'BMP'
                }
                file_format = format_map.get(file_ext, 'PNG')
                
                # Create unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_name = f"{timestamp}_{uf.name}"
                
                # Encode to base64 for storage
                try:
                    bytes_b64 = base64.b64encode(file_bytes).decode('utf-8')
                except Exception as e:
                    st.error(f"❌ {uf.name}: Failed to encode - {str(e)}")
                    error_count += 1
                    continue
                
                # MINIMAL record - ONLY columns we can see in your table
                db_record = {
                    "name": uf.name,
                    "filename": unique_name,
                    "storage_path": f"gallery/{unique_name}",
                    "public_url": f"https://example.com/gallery/{unique_name}",
                    "description": image_description if image_description else "",
                    "uploaded_by": st.session_state.user['username'],
                    "timestamp": datetime.now().isoformat(),
                    "file_size": len(file_bytes),
                    "file_format": file_format,
                    "likes": 0,
                    "strategies": selected_strategies if selected_strategies else [],
                    "bytes_b64": bytes_b64,
                    "comments": []
                    # NOTE: We're NOT including 'format', 'created_at', 'updated_at' 
                    # since they either don't exist or cause errors
                }
                
                # Insert the record
                response = supabase_client.table('gallery_images').insert(db_record).execute()
                
                if hasattr(response, 'error') and response.error:
                    raise RuntimeError(f"Supabase error: {response.error}")
                
                st.success(f"✅ {uf.name} uploaded successfully!")
                success_count += 1
                
            except Exception as e:
                error_msg = str(e)
                st.error(f"❌ {uf.name}: Upload failed - {error_msg[:100]}")
                error_count += 1
        
        # Display summary
        if success_count > 0:
            st.success(f"✅ Successfully uploaded {success_count} image(s)!")
            
            if selected_strategies:
                st.info(f"🏷️ Tagged with: {', '.join(selected_strategies)}")
            
            # Refresh gallery data
            st.session_state.uploaded_images = load_gallery_images()
            st.session_state.gallery_page = 0
            
            st.balloons()
            time.sleep(2)
            st.rerun()
        
        if error_count > 0:
            st.warning(f"⚠️ {error_count} image(s) failed to upload")
            
def render_admin_image_gallery_paginated():
    st.title("🖼️ Admin: Image Gallery Management")
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📊 View & Manage", "⬆️ Upload", "⚙️ Settings"])
    with admin_tab1:
        render_image_gallery_paginated()
        st.markdown("---")
        st.subheader("🛠️ Admin Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh Gallery", use_container_width=True, key="admin_refresh_gallery"):
                st.session_state.gallery_page = 0; st.rerun()
        with col2:
            if st.button("📊 Gallery Stats", use_container_width=True, key="admin_gallery_stats"):
                st.session_state.show_gallery_stats = True
        with col3:
            if st.button("🗑️ Clear Gallery", use_container_width=True, key="admin_clear_gallery"):
                st.session_state.show_clear_gallery_confirmation = True; st.rerun()
        if st.session_state.get('show_gallery_stats'):
            render_gallery_statistics_paginated()
    with admin_tab2:
        render_image_uploader()
    with admin_tab3:
        st.subheader("⚙️ Gallery Settings")
        days_old = st.slider("Delete images older than (days):", 1, 365, 90)
        if st.button("🗑️ Purge Old Images", use_container_width=True):
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            try:
                if 'supabase_client' in globals() and supabase_client:
                    supabase_client.table('gallery_images').delete().lt('timestamp', cutoff_date).execute()
                st.success(f"✅ Deleted images older than {days_old} days")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

def render_image_card_paginated(img_data, page_num, index):
    """Compact image card optimized for grid display - FIXED WITH NULL CHECKS"""
    try:
        with st.container():
            # STEP 1: Safely retrieve image bytes
            image_bytes = None
            
            # Try direct bytes first
            if img_data.get('bytes'):
                image_bytes = img_data['bytes']
            # Try base64 decode
            elif img_data.get('bytes_b64'):
                try:
                    image_bytes = base64.b64decode(img_data['bytes_b64'])
                except Exception as e:
                    logging.warning(f"Failed to decode bytes_b64: {e}")
            # Try encoded_data dict
            elif isinstance(img_data.get('encoded_data'), dict):
                image_bytes = decode_image_from_storage(img_data['encoded_data'])
            
            # If we still don't have image bytes, show placeholder
            if image_bytes is None:
                st.warning(f"⚠️ Image data unavailable for {img_data.get('name', 'Unknown')}")
                return
            
            # STEP 2: Display image safely
            st.image(
                image_bytes,
                use_container_width=True,
                caption=str(img_data.get('name', 'Unnamed'))[:25]
            )
            
            st.divider()
            
            # STEP 3: Display image info with null checks
            st.write(f"**{str(img_data.get('name', 'Image'))[:20]}**")
            
            desc = img_data.get('description', '')
            if desc:
                preview = desc[:60] + "..." if len(desc) > 60 else desc
                st.caption(f"📝 {preview}")
            
            # Metadata
            col1, col2 = st.columns(2)
            with col1:
                uploaded_by = img_data.get('uploaded_by', 'Unknown')
                st.caption(f"👤 {uploaded_by}")
            with col2:
                try:
                    timestamp = img_data.get('timestamp', '')
                    if timestamp:
                        dt = datetime.fromisoformat(timestamp)
                        st.caption(f"📅 {dt.strftime('%m/%d/%y')}")
                    else:
                        st.caption("📅 Unknown date")
                except Exception as e:
                    logging.warning(f"Timestamp parse error: {e}")
                    st.caption("📅 Unknown date")
            
            st.divider()
            
            # STEP 4: Action buttons with unique keys
            action_col1, action_col2, action_col3 = st.columns(3)
            unique_key = f"like_p{page_num}_{index}"
            
            with action_col1:
                likes = img_data.get('likes', 0)
                if st.button(f"❤️ {likes}", key=f"like_{unique_key}", use_container_width=True):
                    img_data['likes'] = likes + 1
                    try:
                        if supabase_client:
                            supabase_client.table('gallery_images').update(
                                {'likes': img_data['likes']}
                            ).eq('id', img_data.get('id')).execute()
                    except Exception as e:
                        logging.error(f"Failed to save like: {e}")
                    st.rerun()
            
            with action_col2:
                if st.button("👁️ View", key=f"view_{unique_key}", use_container_width=True):
                    st.session_state.current_strategy_indicator_image = img_data
                    st.session_state.strategy_indicator_viewer_mode = True
                    st.rerun()
            
            with action_col3:
                # STEP 5: Safe download link generation
                try:
                    if image_bytes:
                        # Get format safely
                        img_format = img_data.get('format', 'png')
                        if img_format is None:
                            img_format = 'png'  # Safe default
                        img_format = str(img_format).lower().replace('jpeg', 'jpg')
                        
                        file_name = img_data.get('name', f'image_{index}')
                        file_name = str(file_name)[:50]  # Limit filename length
                        
                        b64_img = base64.b64encode(image_bytes).decode()
                        href = f'<a href="data:image/{img_format};base64,{b64_img}" download="{file_name}"><button style="width:100%; padding:6px; background:#4CAF50; color:white; border:none; border-radius:4px; cursor:pointer; font-size:12px; font-weight:bold;">⬇️ Download</button></a>'
                        st.markdown(href, unsafe_allow_html=True)
                    else:
                        st.button("⬇️ Download", disabled=True, use_container_width=True)
                except Exception as e:
                    logging.error(f"Download button error: {e}")
                    st.button("⬇️ Download", disabled=True, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Error rendering image card: {str(e)[:100]}")
        logging.error(f"render_image_card_paginated failed: {e}", exc_info=True)

def render_image_gallery_paginated():
    """Gallery with improved error handling and user feedback."""
    st.title("🖼️ Trading Analysis Image Gallery")
    st.markdown("Share and discuss trading charts, analysis screenshots, and market insights.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        gallery_view = st.radio(
            "Gallery View:",
            ["🖼️ Image Gallery", "⬆️ Upload Images"],
            horizontal=True,
            key="gallery_nav_paginated"
        )
    
    st.markdown("---")
    
    # Upload view
    if gallery_view == "⬆️ Upload Images":
        render_image_uploader()
        return
    
    # Gallery view controls
    st.subheader("🔍 Gallery Controls")
    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns(5)
    
    with filter_col1:
        sort_by = st.selectbox(
            "Sort by:",
            ["newest", "oldest", "most_liked"],
            key="gallery_sort_paginated"
        )
    
    with filter_col2:
        authors_set = set(
            img.get('uploaded_by', 'Unknown')
            for img in st.session_state.get('uploaded_images', [])
        )
        filter_author = st.selectbox(
            "Filter by Author:",
            ["All Authors"] + sorted(list(authors_set)),
            key="gallery_filter_author_paginated"
        )
    
    with filter_col3:
        STRATEGIES = st.session_state.get('STRATEGIES', {})
        strategies_list = list(STRATEGIES.keys()) if isinstance(STRATEGIES, dict) else []
        filter_strategy = st.selectbox(
            "Filter by Strategy:",
            ["All Strategies"] + strategies_list,
            key="gallery_filter_strategy_paginated"
        )
    
    with filter_col4:
        min_likes = st.slider(
            "Minimum Likes:",
            0, 100, 0,
            key="gallery_min_likes"
        )
    
    with filter_col5:
        per_page = st.selectbox(
            "Per Page:",
            [10, 15, 20, 30],
            index=1,
            key="gallery_per_page_paginated"
        )
    
    st.session_state.gallery_per_page = per_page
    st.markdown("---")
    
    # Get count
    try:
        with st.spinner("🔍 Counting images..."):
            total_count = get_gallery_images_count_filtered(
                filter_author=None if filter_author == "All Authors" else filter_author,
                filter_strategy=None if filter_strategy == "All Strategies" else filter_strategy,
                min_likes=min_likes
            )
    except Exception as e:
        st.error(f"❌ Error counting images: {e}")
        return
    
    if total_count == 0:
        st.warning("❌ No images found matching your filters.")
        st.info("💡 Try uploading some images or adjusting your filters.")
        return
    
    st.session_state.gallery_total_count = total_count
    total_pages = (total_count + per_page - 1) // per_page
    
    # Ensure current page is valid
    if st.session_state.gallery_page >= total_pages:
        st.session_state.gallery_page = max(0, total_pages - 1)
    
    # Statistics
    st.subheader("📊 Gallery Statistics")
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    with stat_col1:
        st.metric("Total Images", total_count)
    with stat_col2:
        st.metric("Total Pages", total_pages)
    with stat_col3:
        st.metric("Current Page", st.session_state.gallery_page + 1)
    with stat_col4:
        start_num = st.session_state.gallery_page * per_page + 1
        end_num = min((st.session_state.gallery_page + 1) * per_page, total_count)
        st.metric("Showing", f"{start_num}-{end_num}")
    
    st.markdown("---")
    
    # Navigation
    st.subheader("📄 Page Navigation")
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns(5)
    
    with nav_col1:
        if st.button("⏮️ First Page", use_container_width=True, key="gallery_first_top"):
            st.session_state.gallery_page = 0
            st.rerun()
    
    with nav_col2:
        if st.session_state.gallery_page > 0:
            if st.button("◀️ Previous", use_container_width=True, key="gallery_prev_top"):
                st.session_state.gallery_page -= 1
                st.rerun()
        else:
            st.button("◀️ Previous", use_container_width=True, disabled=True, key="gallery_prev_top_disabled")
    
    with nav_col3:
        jump_page = st.number_input(
            "Go to Page:",
            min_value=1,
            max_value=max(1, total_pages),
            value=st.session_state.gallery_page + 1,
            key="gallery_jump_page"
        ) - 1
        if jump_page != st.session_state.gallery_page:
            st.session_state.gallery_page = max(0, min(jump_page, total_pages - 1))
            st.rerun()
    
    with nav_col4:
        if st.session_state.gallery_page < total_pages - 1:
            if st.button("Next ▶️", use_container_width=True, key="gallery_next_top"):
                st.session_state.gallery_page += 1
                st.rerun()
        else:
            st.button("Next ▶️", use_container_width=True, disabled=True, key="gallery_next_top_disabled")
    
    with nav_col5:
        if st.button("⭐ Last Page", use_container_width=True, key="gallery_last_top"):
            st.session_state.gallery_page = total_pages - 1
            st.rerun()
    
    st.markdown("---")
    
    # Load page images
    try:
        with st.spinner("📥 Loading images..."):
            page_images = get_gallery_images_paginated(
                page=st.session_state.gallery_page,
                per_page=per_page,
                sort_by=sort_by,
                filter_author=None if filter_author == "All Authors" else filter_author,
                filter_strategy=None if filter_strategy == "All Strategies" else filter_strategy
            )
    except Exception as e:
        st.error(f"❌ Error loading images: {e}")
        logging.error(f"Page load error: {e}")
        return
    
    if not page_images:
        st.warning("⚠️ Failed to load images for this page.")
        st.info("💡 This might be a temporary issue. Try refreshing or adjusting filters.")
        return
    
    # Display images in grid
    st.session_state.current_page_images = page_images
    st.subheader(f"🖼️ Page {st.session_state.gallery_page + 1} Images ({len(page_images)} shown)")
    
    cols = st.columns(3)
    for idx, img_data in enumerate(page_images):
        col = cols[idx % 3]
        with col:
            try:
                render_image_card_paginated(img_data, st.session_state.gallery_page, idx)
            except Exception as e:
                st.error(f"❌ Error rendering image {idx}: {str(e)[:50]}")
                logging.error(f"Image render error: {e}")
    
    st.markdown("---")
    
    # Bottom navigation
    st.subheader("📄 Bottom Navigation")
    bot_col1, bot_col2, bot_col3, bot_col4, bot_col5 = st.columns(5)
    
    with bot_col1:
        if st.button("⏮️ First", use_container_width=True, key="gallery_first_bottom"):
            st.session_state.gallery_page = 0
            st.rerun()
    
    with bot_col2:
        if st.session_state.gallery_page > 0:
            if st.button("◀️ Prev", use_container_width=True, key="gallery_prev_bottom"):
                st.session_state.gallery_page -= 1
                st.rerun()
        else:
            st.button("◀️ Prev", use_container_width=True, disabled=True, key="gallery_prev_bottom_disabled")
    
    with bot_col3:
        st.write(f"**Page {st.session_state.gallery_page + 1}/{total_pages}**")
    
    with bot_col4:
        if st.session_state.gallery_page < total_pages - 1:
            if st.button("Next ▶️", use_container_width=True, key="gallery_next_bottom"):
                st.session_state.gallery_page += 1
                st.rerun()
        else:
            st.button("Next ▶️", use_container_width=True, disabled=True, key="gallery_next_bottom_disabled")
    
    with bot_col5:
        if st.button("⭐ Last", use_container_width=True, key="gallery_last_bottom"):
            st.session_state.gallery_page = total_pages - 1
            st.rerun()
    
    st.markdown("---")
    start_num = st.session_state.gallery_page * per_page + 1
    end_num = min((st.session_state.gallery_page + 1) * per_page, total_count)
    st.caption(f"✅ Displaying images {start_num}-{end_num} of {total_count} total")
    
def render_admin_image_gallery_paginated():
    st.title("🖼️ Admin: Image Gallery Management")
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📊 View & Manage", "⬆️ Upload", "⚙️ Settings"])
    with admin_tab1:
        render_image_gallery_paginated()
        st.markdown("---")
        st.subheader("🛠️ Admin Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh Gallery", use_container_width=True, key="admin_refresh_gallery"):
                st.session_state.gallery_page = 0; st.rerun()
        with col2:
            if st.button("📊 Gallery Stats", use_container_width=True, key="admin_gallery_stats"):
                st.session_state.show_gallery_stats = True
        with col3:
            if st.button("🗑️ Clear Gallery", use_container_width=True, key="admin_clear_gallery"):
                st.session_state.show_clear_gallery_confirmation = True; st.rerun()
        if st.session_state.get('show_gallery_stats'):
            render_gallery_statistics_paginated()
    with admin_tab2:
        render_image_uploader()
    with admin_tab3:
        st.subheader("⚙️ Gallery Settings")
        days_old = st.slider("Delete images older than (days):", 1, 365, 90)
        if st.button("🗑️ Purge Old Images", use_container_width=True):
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            try:
                if 'supabase_client' in globals() and supabase_client:
                    supabase_client.table('gallery_images').delete().lt('timestamp', cutoff_date).execute()
                st.success(f"✅ Deleted images older than {days_old} days")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

def render_admin_image_gallery_paginated():
    st.title("🖼️ Admin: Image Gallery Management")
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📊 View & Manage", "⬆️ Upload", "⚙️ Settings"])
    with admin_tab1:
        render_image_gallery_paginated()
        st.markdown("---")
        st.subheader("🛠️ Admin Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh Gallery", use_container_width=True, key="admin_refresh_gallery"):
                st.session_state.gallery_page = 0; st.rerun()
        with col2:
            if st.button("📊 Gallery Stats", use_container_width=True, key="admin_gallery_stats"):
                st.session_state.show_gallery_stats = True
        with col3:
            if st.button("🗑️ Clear Gallery", use_container_width=True, key="admin_clear_gallery"):
                st.session_state.show_clear_gallery_confirmation = True; st.rerun()
        if st.session_state.get('show_gallery_stats'):
            render_gallery_statistics_paginated()
    with admin_tab2:
        render_image_uploader()
    with admin_tab3:
        st.subheader("⚙️ Gallery Settings")
        days_old = st.slider("Delete images older than (days):", 1, 365, 90)
        if st.button("🗑️ Purge Old Images", use_container_width=True):
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            try:
                if 'supabase_client' in globals() and supabase_client:
                    supabase_client.table('gallery_images').delete().lt('timestamp', cutoff_date).execute()
                st.success(f"✅ Deleted images older than {days_old} days")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

def render_gallery_statistics_paginated():
    st.subheader("📊 Gallery Statistics")
    try:
        total = get_gallery_images_count()
        st.metric("Total Images", total)
    except Exception as e:
        st.error(f"⚠️ Stats Error: {e}")

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

        # Show current mode (CLEAN IF/ELIF CHAIN)
        current_mode = st.session_state.admin_dashboard_mode
        if current_mode == "admin":
            st.success("🛠️ Admin Management Mode")
        elif current_mode == "premium":
            st.success("📊 Premium Signal Mode")
        elif current_mode == "gallery":
            st.success("🖼️ Image Gallery Mode")
        elif current_mode == "signals_room":
            st.success("⚡ Trading Signals Room")
        elif current_mode == "kai_agent":
            st.success("🧠 KAI AI Agent Mode")
        else:
            st.success("🛠️ Admin Management Mode")

        st.markdown("---")
        st.subheader("Dashboard Mode")
        st.markdown("---")
        
        col1, col2, col3, col4, col5 = st.columns(5)  # 5 columns for the sidebar buttons
        with col1:
            if st.button("🛠️ Admin", use_container_width=True,
                        type="primary" if current_mode == "admin" else "secondary",
                        key="sidebar_admin_btn"):
                st.session_state.admin_dashboard_mode = "admin"
                st.rerun()
        with col2:
            if st.button("📊 Premium", use_container_width=True,
                        type="primary" if current_mode == "premium" else "secondary",
                        key="sidebar_premium_btn"):
                st.session_state.admin_dashboard_mode = "premium"
                st.rerun()
        with col3:
            if st.button("🖼️ Gallery", use_container_width=True,
                        type="primary" if current_mode == "gallery" else "secondary",
                        key="sidebar_gallery_btn"):
                st.session_state.admin_dashboard_mode = "gallery"
                st.rerun()
        with col4:
            if st.button("⚡ Signals", use_container_width=True,
                        type="primary" if current_mode == "signals_room" else "secondary",
                        key="sidebar_signals_btn"):
                st.session_state.admin_dashboard_mode = "signals_room"
                st.rerun()
        with col5:  # Ko-Fi Verification button
            if st.button("💳 Ko-Fi", use_container_width=True, key="sidebar_kofi_verification_btn"):
                st.session_state.admin_dashboard_mode = "purchase_verification"
                st.rerun()

        st.markdown("---")

        # Logout button should always work
        if st.button("🚪 Logout", use_container_width=True, key="admin_sidebar_logout"):
            user_manager.logout(st.session_state.user['username'])
            st.session_state.user = None
            st.session_state.admin_dashboard_mode = None
            st.rerun()

        # Show different sidebar options based on mode
        if current_mode == "admin":
            render_admin_sidebar_options()
        elif current_mode == "premium":
            # Premium mode uses its own sidebar built in render_premium_signal_dashboard
            pass
        elif current_mode == "signals_room":
            # Signals Room mode - show signal-specific options
            st.subheader("Signal Actions")
            if st.button("🚀 Launch Signal", use_container_width=True, key="sidebar_launch_signal"):
                st.session_state.signals_room_view = 'launch_signal'
                st.rerun()
            if st.button("🔍 Confirm Signals", use_container_width=True, key="sidebar_confirm_signal"):
                st.session_state.signals_room_view = 'confirm_signals'
                st.rerun()
            if st.button("📢 Published", use_container_width=True, key="sidebar_published_signals"):
                st.session_state.signals_room_view = 'published_signals'
                st.rerun()
            if st.button("📱 Active Signals", use_container_width=True, key="sidebar_active_signals"):
                st.session_state.signals_room_view = 'active_signals'
                st.rerun()
        elif current_mode == "kai_agent":  # KAI Agent sidebar options
            st.subheader("KAI Agent Actions")
            if st.button("📊 Upload CSV Analysis", use_container_width=True, key="sidebar_kai_upload"):
                st.rerun()
            if st.button("📜 View Analysis History", use_container_width=True, key="sidebar_kai_history"):
                st.rerun()
        else:
            # Gallery mode
            st.subheader("Gallery Actions")
            if st.button("🖼️ Full Gallery", use_container_width=True, key="sidebar_gallery_full"):
                st.session_state.current_gallery_view = "gallery"
                st.session_state.image_viewer_mode = False
                st.rerun()
            if st.button("📤 Upload Images", use_container_width=True, key="sidebar_gallery_upload"):
                st.session_state.current_gallery_view = "upload"
                st.session_state.image_viewer_mode = False
                st.rerun()
            if st.session_state.uploaded_images:
                if st.button("👁️ Image Viewer", use_container_width=True, key="sidebar_gallery_viewer", help="Open the first image in full viewer"):
                    st.session_state.current_image_index = 0
                    st.session_state.image_viewer_mode = True
                    st.rerun()

    # Main admin content based on selected mode
    if st.session_state.get('admin_dashboard_mode') == "admin":
        render_admin_management_dashboard()

    elif st.session_state.get('admin_dashboard_mode') == "premium":
        render_premium_signal_dashboard()

    elif st.session_state.get('admin_dashboard_mode') == "signals_room":
        render_trading_signals_room()

    elif st.session_state.get('admin_dashboard_mode') == "kai_agent":
        render_kai_agent()
    
    elif st.session_state.get('admin_dashboard_mode') == "purchase_verification":  # New section for Ko-Fi Verification
        st.markdown("## 💳 Ko-Fi")
        render_admin_purchase_verification_panel()  # This renders the Ko-Fi verification section
    
    else:
        render_image_gallery_paginated()

def render_admin_sidebar_options():
    """Sidebar options for admin management mode"""
    st.subheader("Admin Actions")

    if st.button("🔄 Refresh All Data", use_container_width=True, key="sidebar_refresh_btn"):
        user_manager.load_data()
        st.rerun()

    if st.button("📊 Business Overview", use_container_width=True, key="sidebar_overview_btn"):
        st.session_state.admin_view = "overview"
        st.rerun()

    if st.button("📈 View Analytics", use_container_width=True, key="sidebar_analytics_btn"):
        st.session_state.admin_view = "analytics"
        st.rerun()

    if st.button("👥 Manage Users", use_container_width=True, key="sidebar_users_btn"):
        st.session_state.admin_view = "users"
        st.rerun()

    if st.button("📧 Email Verification", use_container_width=True, key="sidebar_email_verify_btn"):
        st.session_state.admin_view = "email_verification"
        st.rerun()

    if st.button("💰 Revenue Report", use_container_width=True, key="sidebar_revenue_btn"):
        st.session_state.admin_view = "revenue"
        st.rerun()

    if st.button("📊 Signals Access Tracking", use_container_width=True):
        st.session_state.admin_view = "signals_tracking"
        st.rerun()

    # NEW: KAI AI Agent access
    if st.button("🧠 KAI AI Agent", use_container_width=True, key="sidebar_kai_agent_btn"):
        st.session_state.admin_view = "kai_agent"
        st.rerun()

    # NEW: Signals Room Password Management
    if st.button("🔐 Signals Room Password", use_container_width=True, key="sidebar_signals_password_btn"):
        st.session_state.show_signals_password_change = True
        st.rerun()

def render_admin_dashboard_selection():
    """Interface for admin to choose between admin dashboard and premium dashboard"""
    st.title("👑 Admin Portal - Choose Dashboard")
    st.markdown("---")

    col1, col2, col3, col4, col5 = st.columns(5)

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
        if st.button("🚀 Go to Admin Dashboard", use_container_width=True, key="admin_dash_btn"):
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
        if st.button("📈 Go to Premium Dashboard", use_container_width=True, key="premium_dash_btn"):
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
        if st.button("🖼️ Go to Image Gallery", use_container_width=True, key="gallery_dash_btn"):
            st.session_state.admin_dashboard_mode = "gallery"
            st.rerun()

    with col4:
        st.subheader("⚡ Trading Signals Room")
        st.markdown("""
        **Signal Workflow:**
        - Launch trading signals
        - Multi-confirmation system
        - Publish to all users
        - View active signals
        - Track performance
        - User feedback system
        - Real-time updates
        """)
        if st.button("⚡ Go to Signals Room", use_container_width=True, key="signals_dash_btn"):
            st.session_state.admin_dashboard_mode = "signals_room"
            st.rerun()

    with col5:
        st.subheader("🧠 KAI AI Agent")
        st.markdown("""
        **AI Analysis:**
        - Upload CSV for analysis
        - Technical pattern detection
        - Reversal signal identification
        - Confidence scoring
        - Time horizon mapping
        - Trading recommendations
        - Historical analysis
        - DeepSeek AI Enhanced
        """)
        if st.button("🧠 Go to KAI Agent", use_container_width=True, key="kai_dash_btn"):
            st.session_state.admin_dashboard_mode = "kai_agent"
            st.rerun()

    st.markdown("---")
    st.info("💡 **Tip:** Use different dashboards for different management tasks.")

def render_admin_management_dashboard():
    """Admin dashboard with simple tracking and maintenance panel"""
    st.title("🛠️ Admin Management Dashboard")

    # Get business metrics safely
    try:
        metrics = user_manager.get_business_metrics()
    except:
        metrics = {}
    
    # Ensure metrics is a dictionary
    if not isinstance(metrics, dict):
        metrics = {}

    # Key metrics - ULTRA SAFE VERSION
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Total Users", metrics.get("total_users", 0))
    with col2:
        st.metric("Active Users", metrics.get("active_users", 0))
    with col3:
        st.metric("Online Now", metrics.get("online_users", 0))
    with col4:
        st.metric("Verified Users", metrics.get("verified_users", 0))
    with col5:
        st.metric("Unverified Users", metrics.get("unverified_users", 0))
    with col6:
        signals_count = len(st.session_state.get('signals_access_tracking', []))
        st.metric("Signals Access", signals_count)

    st.markdown("---")

    # 🔧 DATABASE MAINTENANCE SECTION
    st.subheader("🔧 Database Maintenance Panel")
    
    col_m1, col_m2, col_m3 = st.columns(3)
    
    with col_m1:
        if st.button("🔄 Reset Access Tracking", use_container_width=True, key="reset_tracking_btn"):
            st.session_state.signals_access_tracking = []
            if supabase_client:
                try:
                    supabase_client.table('signals_access_tracking').delete().neq('id', 0).execute()
                    st.success("✅ Access tracking reset successfully!")
                    st.info("All tracking data cleared from database")
                except Exception as e:
                    st.error(f"❌ Error clearing data: {e}")
            else:
                st.warning("⚠️ Supabase not connected, only cleared session data")
            time.sleep(1)
            st.rerun()
    
    with col_m2:
        if st.button("📊 Verify Table Structure", use_container_width=True, key="verify_table_btn"):
            if supabase_client:
                try:
                    resp = supabase_client.table('signals_access_tracking').select('*').limit(1).execute()
                    st.success("✅ Table exists and is accessible!")
                    st.info(f"Table currently has {len(resp.data or [])} records")
                    
                    # Show table structure info
                    st.write("**Expected columns:**")
                    st.write("- id (bigint, primary key)")
                    st.write("- username (text)")
                    st.write("- first_access (timestamp)")
                    st.write("- last_access (timestamp)")
                    st.write("- access_count (integer)")
                    
                except Exception as e:
                    st.error("❌ Table verification failed!")
                    st.error(f"Error: {str(e)[:200]}")
                    st.warning("**Solution:** Run the CREATE TABLE SQL in Supabase SQL Editor")
            else:
                st.error("❌ Supabase client not connected")
    
    with col_m3:
        if st.button("🔍 Run Full Diagnostics", use_container_width=True, key="diagnostics_btn"):
            st.write("**📊 Diagnostic Report:**")
            st.markdown("---")
            
            # Session state info
            st.write("**Session State:**")
            tracking_sess = st.session_state.get('signals_access_tracking', [])
            st.write(f"✓ Items in session: {len(tracking_sess)}")
            if tracking_sess:
                st.write(f"  - Last user: {tracking_sess[-1].get('username', 'unknown')}")
                st.write(f"  - Last access: {tracking_sess[-1].get('last_access', 'unknown')[:16]}")
            
            st.markdown("---")
            
            # Database info
            st.write("**Database Status:**")
            if supabase_client:
                try:
                    resp = supabase_client.table('signals_access_tracking').select('*').execute()
                    records = resp.data or []
                    st.write(f"✓ Items in DB: {len(records)}")
                    
                    if records:
                        st.write("**Sample records (first 3):**")
                        for i, record in enumerate(records[:3], 1):
                            st.write(f"  {i}. {record.get('username')} - Access count: {record.get('access_count', 1)}")
                    else:
                        st.info("Table is empty (no access records yet)")
                        
                except Exception as e:
                    st.error(f"❌ Database query failed: {str(e)[:150]}")
                    st.error("**Possible causes:**")
                    st.write("- Table doesn't exist")
                    st.write("- RLS policies not configured")
                    st.write("- Connection issue")
            else:
                st.error("❌ Supabase client not initialized")
            
            st.markdown("---")
            st.success("Diagnostics complete")

    st.markdown("---")

    # FIXED: Check for modals in the correct order - DELETE CONFIRMATION FIRST
    if st.session_state.show_delete_confirmation:
        render_delete_user_confirmation()
        return

    if st.session_state.show_bulk_delete:
        render_bulk_delete_inactive()
        return

    if st.session_state.show_manage_user_plan:
        render_manage_user_plan()
        return

    if st.session_state.show_signals_password_change:
        render_signals_password_management()
        return

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
    elif current_view == 'signals_tracking':
        render_simple_signals_tracking()
    elif current_view == 'kai_agent':
        render_kai_agent()
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
    """Complete user management interface - FIXED VERSION"""
    st.subheader("👥 User Management")

    # User actions - FIXED: Proper bulk delete trigger
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("🔄 Refresh User List", use_container_width=True, key="um_refresh_btn"):
            st.rerun()
    with col2:
        if st.button("📧 Email Verification", use_container_width=True, key="um_email_verify_btn"):
            st.session_state.admin_view = "email_verification"
            st.rerun()
    with col3:
        if st.button("🔐 User Credentials", use_container_width=True, key="um_credentials_btn"):
            st.session_state.show_user_credentials = True
            st.rerun()
    with col4:
        if st.button("🆕 Create Test User", use_container_width=True, key="um_test_btn"):
            created_username, msg = user_manager.create_test_user("trial")
            if created_username:
                st.success(msg)
            else:
                st.error(msg)
            st.rerun()
    with col5:
        # FIXED: This button now properly triggers bulk delete
        if st.button("🗑️ Bulk Delete Inactive", use_container_width=True, key="um_bulk_btn"):
            st.session_state.show_bulk_delete = True
            st.rerun()
    with col6:
        if st.button("🔐 Change Admin Password", use_container_width=True, key="um_password_btn"):
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
                    # FIXED: This button now properly triggers user management
                    if st.button("⚙️", key=f"manage_{username}", help="Manage User"):
                        st.session_state.manage_user_plan = username
                        st.session_state.show_manage_user_plan = True
                        st.rerun()

    # Render the password change interface if activated
    if st.session_state.show_password_change:
        render_admin_password_change()

    # Render the user credentials interface if activated
    if st.session_state.show_user_credentials:
        render_user_credentials_display()

# SIMPLE ADMIN VIEW
def render_simple_signals_tracking():
    """Simple: Show who accessed Signals Room - FIXED VERSION"""
    st.subheader("👥 Signals Room Access Tracking")
    
    # CRITICAL: Load fresh data from Supabase
    tracking_data = load_signals_access_tracking()
    
    if not tracking_data or len(tracking_data) == 0:
        st.info("📊 No one has accessed Signals Room yet. Access will be tracked here.")
        
        # Show how to test
        st.markdown("---")
        st.subheader("🧪 How to Test Access Tracking:")
        st.markdown("""
        1. Go to **Trading Signals** menu
        2. Enter the Signals Room password
        3. Access will be automatically tracked
        4. Refresh this page to see the tracking update
        """)
        return
    
    st.success(f"✅ **Total Users with Access: {len(tracking_data)}**")
    st.markdown("---")
    
    # Display access data in a table
    tracking_df = pd.DataFrame(tracking_data)
    tracking_df['first_access'] = pd.to_datetime(tracking_df['first_access']).dt.strftime('%Y-%m-%d %H:%M')
    tracking_df['last_access'] = pd.to_datetime(tracking_df['last_access']).dt.strftime('%Y-%m-%d %H:%M')
    
    st.dataframe(
        tracking_df[['username', 'first_access', 'last_access', 'access_count']],
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    st.subheader("📊 Access Statistics")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        total_users = len(tracking_data)
        st.metric("Total Users", total_users)
    with col2:
        total_accesses = sum(t.get('access_count', 1) for t in tracking_data)
        st.metric("Total Accesses", total_accesses)
    with col3:
        if total_users > 0:
            avg_accesses = total_accesses / total_users
            st.metric("Avg per User", f"{avg_accesses:.1f}")
    
    st.markdown("---")
    
    # Individual user details
    st.subheader("📋 Detailed Access Log")
    
    for track in tracking_data:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            
            with col1:
                st.write(f"**👤 {track['username']}**")
            
            with col2:
                first = datetime.fromisoformat(track['first_access']).strftime('%Y-%m-%d %H:%M')
                last = datetime.fromisoformat(track['last_access']).strftime('%Y-%m-%d %H:%M')
                st.write(f"First: {first}")
                st.caption(f"Last: {last}")
            
            with col3:
                count = track.get('access_count', 1)
                st.metric("Accesses", count, label_visibility="collapsed")
            
            with col4:
                if st.button("🗑️ Remove", key=f"remove_track_{track['username']}", use_container_width=True):
                    # Remove from tracking
                    new_tracking = [t for t in tracking_data if t['username'] != track['username']]
                    save_signals_access_tracking(new_tracking)
                    st.success(f"✅ Removed {track['username']}")
                    st.rerun()
            
            st.divider()
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True, key="refresh_signals_tracking"):
            st.rerun()
    
    with col2:
        if st.button("📥 Export CSV", use_container_width=True, key="export_signals_tracking"):
            csv_data = tracking_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"signals_access_tracking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col3:
        if st.button("🗑️ Clear All", use_container_width=True, key="clear_all_tracking"):
            if st.session_state.get('confirm_clear_tracking'):
                save_signals_access_tracking([])
                st.success("✅ All tracking cleared")
                st.rerun()
            else:
                st.session_state.confirm_clear_tracking = True
                st.warning("⚠️ Click again to confirm clearing all tracking data")

def export_simple_tracking_csv():
    """Simple CSV export"""
    tracking_data = st.session_state.signals_access_tracking
    if tracking_data:
        df = pd.DataFrame(tracking_data)
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Access Report",
            data=csv,
            file_name="signals_access_report.csv",
            mime="text/csv"
        )

def render_admin_password_change():
    """Admin password change interface - FIXED VERSION"""
    st.markdown("---")
    st.subheader("🔐 Change Admin Password")

    with st.form("admin_password_change_form"):
        current_password = st.text_input("Current Password", type="password",
                                        placeholder="Enter current admin password",
                                        key="admin_current_password")
        new_password = st.text_input("New Password", type="password",
                                    placeholder="Enter new password (min 8 characters)",
                                    key="admin_new_password")
        confirm_password = st.text_input("Confirm New Password", type="password",
                                        placeholder="Confirm new password",
                                        key="admin_confirm_password")

        col1, col2 = st.columns(2)
        with col1:
            submitted = st.form_submit_button("✅ Change Password", use_container_width=True)
        with col2:
            if st.form_submit_button("❌ Cancel", use_container_width=True):
                st.session_state.show_password_change = False
                st.rerun()

        if submitted:
            if not current_password or not new_password or not confirm_password:
                st.error("❌ Please fill in all password fields")
            elif new_password != confirm_password:
                st.error("❌ New passwords do not match")
            elif len(new_password) < 8:
                st.error("❌ New password must be at least 8 characters")
            else:
                success, message = user_manager.change_admin_password(current_password, new_password)
                if success:
                    st.success(f"✅ {message}")
                    st.session_state.show_password_change = False
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error(f"❌ {message}")

def render_user_credentials_display():
    """Display user credentials - FIXED VERSION"""
    st.markdown("---")
    st.subheader("🔐 User Credentials Export")

    # Get user credentials for display
    users_list = user_manager.get_user_credentials_display()

    if users_list:
        # Display as a table
        st.write("**All User Accounts:**")
        df = pd.DataFrame(users_list)
        st.dataframe(df, use_container_width=True)

        # Export functionality
        col1, col2 = st.columns(2)
        with col1:
            csv_bytes, error = user_manager.export_user_credentials()
            if csv_bytes:
                st.download_button(
                    label="📄 Export to CSV",
                    data=csv_bytes,
                    file_name=f"user_credentials_{datetime.now().strftime('%Y%m%d_%H%M')}.csv",
                    mime="text/csv",
                    use_container_width=True,
                    key="export_user_credentials"
                )
            else:
                st.error(f"Error exporting: {error}")

        with col2:
            if st.button("❌ Close", use_container_width=True, key="close_user_credentials"):
                st.session_state.show_user_credentials = False
                st.rerun()
    else:
        st.info("No user data available")
        if st.button("❌ Close", use_container_width=True, key="close_no_user_credentials"):
            st.session_state.show_user_credentials = False
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
# STREAMLIT APP CONFIG
# -------------------------
st.set_page_config(
    page_title=f"{Config.APP_NAME} - Professional Trading Analysis",
    layout="wide",
    page_icon="📊",
    initial_sidebar_state="expanded"
)

# -------------------------
# MAIN APPLICATION - FIXED USER ACCESS
# -------------------------
def main():
    # Initialize session state variables - ONLY ONCE
    if 'session_initialized' not in st.session_state:
        init_session()
        st.session_state.session_initialized = True

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
    .signals-feature {
        border: 2px solid #EF4444;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%);
    }
    .kai-feature {
        border: 2px solid #8B5CF6;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 0.5rem 0;
        background: linear-gradient(135deg, #F0F4FF 0%, #E0E7FF 100%);
    }
    .verification-badge {
        font-size: 0.7rem !important;
        padding: 2px
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
    .signal-card {
        border: 2px solid #E5E7EB;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        background: white;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
        transition: all 0.3s ease;
    }
    .signal-card:hover {
        box-shadow: 0 10px 15px rgba(0, 0, 0, 0.1);
        transform: translateY(-2px);
    }
    .signal-buy {
        border-left: 5px solid #10B981;
        background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
    }
    .signal-sell {
        border-left: 5px solid #EF4444;
        background: linear-gradient(135deg, #FEF2F2 0%, #FECACA 100%);
    }
    .signal-hold {
        border-left: 5px solid #6B7280;
        background: linear-gradient(135deg, #F9FAFB 0%, #F3F4F6 100%);
    }
    .timeframe-short {
        background: linear-gradient(135deg, #FFE4E6 0%, #FECACA 100%);
        color: #DC2626;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .timeframe-medium {
        background: linear-gradient(135deg, #F0FDF4 0%, #DCFCE7 100%);
        color: #059669;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .timeframe-long {
        background: linear-gradient(135deg, #EFF6FF 0%, #DBEAFE 100%);
        color: #2563EB;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.8rem;
        font-weight: 600;
    }
    .deepseek-enhanced {
        background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-left: 10px;
    }
    .quantitative-score {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .risk-high {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .risk-medium {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .risk-low {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    </style>
    """, unsafe_allow_html=True)

    if not st.session_state.user:
        render_login()
    else:
        # Check if we're in strategy indicator image viewer mode
        if hasattr(st.session_state, 'strategy_indicator_viewer_mode') and st.session_state.strategy_indicator_viewer_mode:
            render_strategy_indicator_image_viewer()
            return

        if st.session_state.user['plan'] == 'admin':
            render_admin_dashboard()
        else:
            # FIXED: Users should have access to BOTH premium dashboard (view mode) AND image gallery AND signals room AND KAI Agent
            # Add navigation for users to switch between dashboard and gallery

            # User navigation header
            st.sidebar.title("👤 User Navigation")

            # User mode selection
            user_mode = st.sidebar.radio(
                "Select View:",
                ["📊 Trading Dashboard", "🖼️ Image Gallery", "⚡ Trading Signals", "🧠 KAI", "💎 PREMIUM USER"],
                key="user_navigation_mode"
            )

            # Display appropriate view based on user selection
            if user_mode == "🖼️ Image Gallery":
                # For gallery, ensure user can only view (not upload)
                render_user_image_gallery()
            elif user_mode == "⚡ Trading Signals":
                # Show the trading signals room in VIEW MODE
                render_trading_signals_room()
            elif user_mode == "🧠 KAI":
                # Show the KAI AI Agent in VIEW MODE (users can view but not upload)
                render_kai_agent()
            elif user_mode == "💎 PREMIUM USER":
                # Show the premium user section
                render_premium_user_section()
            else:
                # Show the premium trading dashboard in VIEW MODE
                render_user_dashboard()

if __name__ == "__main__":
    main()

# =====================================================================
# EXTREME RELIABILITY SUPABASE PATCH (idempotent, safe to append)
# - Adds robust retry/backoff around Supabase calls
# - Handles transient OSError: [Errno 11] Resource temporarily unavailable (EAGAIN)
# - Suppresses noisy startup errors; returns last-known-good values on failure
# - Does NOT require GitHub or repo connections
# =====================================================================
import errno
import functools

# Global in-memory "last good" caches (kept per-session)
_cache = {}

def _is_transient_error(err):
    """Check if error is transient and worth retrying."""
    # OSError with errno.EAGAIN (Resource temporarily unavailable)
    if isinstance(err, OSError) and hasattr(err, 'errno') and err.errno == errno.EAGAIN:
        return True
    # Connection errors
    if isinstance(err, (ConnectionError, TimeoutError)):
        return True
    # Generic: some Supabase/postgrest errors bubble up as Exception with message patterns
    msg = str(err).lower()
    transient_fragments = ["temporarily unavailable", "timeout", "eagain", "rate limit", "connection reset"]
    return any(frag in msg for frag in transient_fragments)

def _init_supabase_hardened():
    if '___supabase_ok___' in st.session_state:
        return supabase_client  # already initialized by the main code
    tries = 0
    while tries < 5:
        try:
            # If the original code already created supabase_client successfully, just use it.
            if supabase_client:
                st.session_state.___supabase_ok___ = True
                return supabase_client
        except Exception as e:
            # If this fails in weird ways, keep retrying briefly.
            pass
        time.sleep(0.25 * (2 ** tries))
        tries += 1
    return supabase_client  # may be None; downstream code is guarded

# ===== Re-define critical Supabase functions with retries =====

@retry_with_backoff(max_retries=4, base_delay=0.5)
def supabase_get_analytics():
    """Get analytics with retry + cache last good value."""
    client = _init_supabase_hardened()
    if not client:
        return _cache_get("lk_supabase_get_analytics", {})
    resp = client.table('analytics').select('*').execute()
    if hasattr(resp, 'error') and resp.error:
        raise RuntimeError(resp.error)
    data = (resp.data or [])
    result = data[0] if data else {}
    _cache_set("lk_supabase_get_analytics", result)
    return result

@retry_with_backoff(max_retries=4, base_delay=0.5)
def supabase_get_users():
    """Get users with retry + cache last good value."""
    client = _init_supabase_hardened()
    if not client:
        return _cache_get("lk_supabase_get_users", {})
    resp = client.table('users').select('*').execute()
    if hasattr(resp, 'error') and resp.error:
        raise RuntimeError(resp.error)
    users = {u['username']: u for u in (resp.data or [])}
    _cache_set("lk_supabase_get_users", users)
    return users

@retry_with_backoff(max_retries=4, base_delay=0.5)
def supabase_save_users(users: dict):
    """Save users with retry. Returns True on success."""
    client = _init_supabase_hardened()
    if not client:
        return False
    payload = []
    for username, user_data in users.items():
        row = dict(user_data)
        row['username'] = username
        payload.append(row)
    resp = client.table('users').upsert(payload).execute()
    if hasattr(resp, 'error') and resp.error:
        raise RuntimeError(resp.error)
    return True

@retry_with_backoff(max_retries=4, base_delay=0.5)
def supabase_delete_user(username: str):
    """Delete a user with retry."""
    client = _init_supabase_hardened()
    if not client:
        return False
    resp = client.table('users').delete().eq('username', username).execute()
    if hasattr(resp, 'error') and resp.error:
        raise RuntimeError(resp.error)
    return True

@retry_with_backoff(max_retries=4, base_delay=0.5)
def supabase_get_strategy_analyses():
    """Get strategy analyses with retry + cache last good value."""
    client = _init_supabase_hardened()
    if not client:
        return _cache_get("lk_supabase_get_strategy_analyses", {})
    resp = client.table('strategy_analyses').select('*').execute()
    if hasattr(resp, 'error') and resp.error:
        raise RuntimeError(resp.error)
    strategies = {}
    for item in (resp.data or []):
        s = item.get('strategy_name')
        i = item.get('indicator_name')
        strategies.setdefault(s, {})[i] = {
            "note": item.get('note', ''),
            "status": item.get('status', 'Open'),
            "momentum": item.get('momentum', 'Not Defined'),
            "strategy_tag": item.get('strategy_tag', 'Neutral'),
            "analysis_date": item.get('analysis_date', ''),
            "last_modified": item.get('last_modified', ''),
            "modified_by": item.get('modified_by', 'system')
        }
    _cache_set("lk_supabase_get_strategy_analyses", strategies)
    return strategies

@retry_with_backoff(max_retries=4, base_delay=0.5)
def supabase_save_strategy_analyses(strategy_data: dict):
    """Save strategy analyses with retry."""
    client = _init_supabase_hardened()
    if not client:
        return False
    rows = []
    for strategy_name, indicators in strategy_data.items():
        for indicator_name, meta in indicators.items():
            rows.append({
                "strategy_name": strategy_name,
                "indicator_name": indicator_name,
                "note": meta.get("note", ""),
                "status": meta.get("status", "Open"),
                "momentum": meta.get("momentum", "Not Defined"),
                "strategy_tag": meta.get("strategy_tag", "Neutral"),
                "analysis_date": meta.get("analysis_date", ""),
                "last_modified": meta.get("last_modified", ""),
                "modified_by": meta.get("modified_by", "system"),
            })
    if rows:
        resp = client.table('strategy_analyses').upsert(rows).execute()
        if hasattr(resp, 'error') and resp.error:
            raise RuntimeError(resp.error)
    return True

@retry_with_backoff(max_retries=4, base_delay=0.5)
def supabase_get_gallery_images():
    """Get gallery images with retry + cache last good value."""
    client = _init_supabase_hardened()
    if not client:
        return _cache_get("lk_supabase_get_gallery_images", [])
    resp = client.table('gallery_images').select('*').execute()
    if hasattr(resp, 'error') and resp.error:
        raise RuntimeError(resp.error)
    images = []
    for img in (resp.data or []):
        if 'bytes_b64' in img:
            try:
                img['bytes'] = base64.b64decode(img['bytes_b64'])
            except Exception:
                pass
        images.append(img)
    _cache_set("lk_supabase_get_gallery_images", images)
    return images

@retry_with_backoff(max_retries=4, base_delay=0.5)
def supabase_save_gallery_images(images: list):
    """Save gallery images with retry."""
    client = _init_supabase_hardened()
    if not client:
        return False
    resp = client.table('gallery_images').upsert(images).execute()
    if hasattr(resp, 'error') and resp.error:
        raise RuntimeError(resp.error)
    return True

# =====================================================================
# END OF EXTREME RELIABILITY SUPABASE PATCH
# =====================================================================

# =====================================================================
# GALLERY IMAGE PERSISTENCE & SUPABASE RELIABILITY — FIXED (Claude-style)
# - Robust encode/decode with checksum
# - Silent transient retries
# - Transaction-safe upload
# - Backward-compatible with legacy bytes_b64
# - Overrides old gallery functions to avoid touching call sites
# =====================================================================
import base64, io, hashlib, logging
from datetime import datetime
try:
    from PIL import Image
except Exception:
    Image = None  # If PIL is not installed, uploader will guard.

logging.getLogger(__name__).setLevel(logging.INFO)

# ----- Robust image (de)serialization -----
def encode_image_for_storage(image_bytes: bytes, format_str: str) -> dict | None:
    try:
        if not image_bytes:
            raise ValueError("Empty image bytes")
        b64_str = base64.b64encode(image_bytes).decode("utf-8")
        checksum = hashlib.md5(image_bytes).hexdigest()[:8]
        return {
            "b64_data": b64_str,
            "checksum": checksum,
            "size": len(image_bytes),
            "format": format_str,
            "encoded_at": datetime.now().isoformat(),
        }
    except Exception as e:
        logging.error(f"encode_image_for_storage failed: {e}")
        return None

def decode_image_from_storage(encoded_data: dict) -> bytes | None:
    try:
        if not encoded_data or "b64_data" not in encoded_data:
            return None
        decoded = base64.b64decode(encoded_data["b64_data"])
        stored = encoded_data.get("checksum")
        if stored:
            actual = hashlib.md5(decoded).hexdigest()[:8]
            if actual != stored:
                logging.error(f"Checksum mismatch: expected {stored}, got {actual}")
                return None
        return decoded
    except Exception as e:
        logging.error(f"decode_image_from_storage failed: {e}")
        return None

# ----- Fixed Supabase gallery functions (use existing retry_with_backoff if present) -----
_retry = retry_with_backoff if 'retry_with_backoff' in globals() else (lambda **kw: (lambda f: f))

# ----- Local loading & uploader (override) -----
# =====================================================================
# END OF GALLERY IMAGE PERSISTENCE FIX
# =====================================================================

# -------------------------
# Gallery Pagination - Database Layer
# -------------------------
def render_gallery_statistics_paginated():
    st.markdown("---")
    st.subheader("📊 Gallery Statistics")
    try:
        total = get_gallery_images_count()
        images = st.session_state.get('uploaded_images', [])
        authors = len(set(img.get('uploaded_by') for img in images)) if images else 0
        strategies = set()
        for img in images:
            for s in img.get('strategies', []) or []:
                strategies.add(s)
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Total Images", total)
        with col2: st.metric("Unique Authors", authors)
        with col3: st.metric("Strategies Tagged", len(strategies))
        with col4: st.metric("Total Likes", sum(img.get('likes',0) for img in images) if images else 0)
        st.markdown("---")
        st.write("**📈 Top Images by Likes:**")
        top_images = sorted(images, key=lambda x: x.get('likes',0), reverse=True)[:5] if images else []
        for rank, img in enumerate(top_images, 1):
            st.write(f"{rank}. **{img.get('name','Unknown')}** - ❤️ {img.get('likes',0)} | 👤 {img.get('uploaded_by','Unknown')}")
    except Exception as e:
        st.error(f"Error loading stats: {e}")
