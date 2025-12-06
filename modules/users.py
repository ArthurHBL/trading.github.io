

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
