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
import cv2

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
    # NEW: Image upload states
    if 'uploaded_images' not in st.session_state:
        st.session_state.uploaded_images = {}
    if 'current_image_uploads' not in st.session_state:
        st.session_state.current_image_uploads = {}

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
# IMAGE MANAGEMENT SYSTEM
# -------------------------
class ImageManager:
    def __init__(self):
        self.images_dir = "uploaded_images"
        self._ensure_images_directory()
    
    def _ensure_images_directory(self):
        """Create images directory if it doesn't exist"""
        if not os.path.exists(self.images_dir):
            os.makedirs(self.images_dir)
            print(f"✅ Created images directory: {self.images_dir}")
    
    def save_uploaded_image(self, uploaded_file, strategy_name, indicator_name, analysis_date, username):
        """Save uploaded image and return file path"""
        try:
            # Create user-specific directory
            user_dir = os.path.join(self.images_dir, username)
            if not os.path.exists(user_dir):
                os.makedirs(user_dir)
            
            # Create strategy directory
            strategy_dir = os.path.join(user_dir, strategy_name)
            if not os.path.exists(strategy_dir):
                os.makedirs(strategy_dir)
            
            # Create date directory
            date_dir = os.path.join(strategy_dir, analysis_date.strftime("%Y-%m-%d"))
            if not os.path.exists(date_dir):
                os.makedirs(date_dir)
            
            # Generate unique filename
            file_extension = os.path.splitext(uploaded_file.name)[1].lower()
            unique_id = str(uuid.uuid4())[:8]
            filename = f"{indicator_name}_{unique_id}{file_extension}"
            file_path = os.path.join(date_dir, filename)
            
            # Save the file
            with open(file_path, "wb") as f:
                f.write(uploaded_file.getbuffer())
            
            print(f"✅ Saved image: {file_path}")
            return file_path
            
        except Exception as e:
            print(f"❌ Error saving image: {e}")
            return None
    
    def get_image_paths(self, strategy_name, indicator_name, analysis_date, username):
        """Get all image paths for a specific indicator"""
        try:
            base_path = os.path.join(self.images_dir, username, strategy_name, analysis_date.strftime("%Y-%m-%d"))
            if not os.path.exists(base_path):
                return []
            
            # Find all images for this indicator
            image_files = []
            for file in os.listdir(base_path):
                if file.startswith(indicator_name + "_") and file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    image_files.append(os.path.join(base_path, file))
            
            return sorted(image_files)
        except Exception as e:
            print(f"❌ Error getting image paths: {e}")
            return []
    
    def delete_image(self, image_path):
        """Delete a specific image file"""
        try:
            if os.path.exists(image_path):
                os.remove(image_path)
                print(f"✅ Deleted image: {image_path}")
                return True
            return False
        except Exception as e:
            print(f"❌ Error deleting image: {e}")
            return False
    
    def get_image_bytes(self, image_path):
        """Get image bytes for display"""
        try:
            with open(image_path, "rb") as f:
                return f.read()
        except Exception as e:
            print(f"❌ Error reading image: {e}")
            return None
    
    def display_image(self, image_path, caption=None, width=300):
        """Display image in Streamlit"""
        try:
            image_bytes = self.get_image_bytes(image_path)
            if image_bytes:
                st.image(image_bytes, caption=caption, width=width)
                return True
            return False
        except Exception as e:
            st.error(f"Error displaying image: {e}")
            return False

# Initialize image manager
image_manager = ImageManager()

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
# SECURE USER MANAGEMENT WITH PERSISTENCE
# -------------------------
class UserManager:
    def __init__(self):
        self.users_file = "users.json"
        self.analytics_file = "analytics.json"
        self._ensure_data_files()
        self.load_data()
    
    def _ensure_data_files(self):
        """Ensure data files exist and are valid"""
        if not os.path.exists(self.users_file):
            self.users = {}
            self.create_default_admin()
            self.save_users()
        else:
            try:
                with open(self.users_file, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError:
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
            try:
                with open(self.analytics_file, 'r') as f:
                    json.load(f)
            except json.JSONDecodeError:
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
            "email_verified": True,
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
            if os.path.exists(self.users_file):
                backup_file = f"{self.users_file}.backup"
                shutil.copy2(self.users_file, backup_file)
            
            with open(self.users_file, 'w', encoding='utf-8') as f:
                json.dump(self.users, f, indent=2, ensure_ascii=False)
            print(f"✅ Saved {len(self.users)} users to {self.users_file}")
            return True
        except Exception as e:
            print(f"❌ Error saving users: {e}")
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
    
    def register_user(self, username, password, name, email, plan="trial"):
        """Register new user with proper validation and persistence"""
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
            "email_verified": False,
            "verification_date": None,
            "verification_notes": "",
            "verification_admin": None
        }
        
        if 'user_registrations' not in self.analytics:
            self.analytics['user_registrations'] = []
        
        self.analytics["user_registrations"].append({
            "username": username,
            "plan": plan,
            "timestamp": datetime.now().isoformat()
        })
        
        users_saved = self.save_users()
        analytics_saved = self.save_analytics()
        
        if users_saved and analytics_saved:
            print(f"✅ Successfully registered user: {username}")
            return True, f"Account created successfully! {plan_config['name']} activated."
        else:
            if username in self.users:
                del self.users[username]
            return False, "Error saving user data. Please try again."

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

# Initialize user manager
user_manager = UserManager()

# -------------------------
# ENHANCED STRATEGY NOTES WITH IMAGE UPLOAD
# -------------------------
def render_admin_strategy_notes(strategy_data, daily_strategies, cycle_day, analysis_date, selected_strategy):
    """Detailed strategy notes interface with image upload capability"""
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
    
    # Notes Form - ADMIN VERSION WITH IMAGE UPLOAD
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
        
        # Indicator analysis in columns - WITH IMAGE UPLOAD
        indicators = STRATEGIES[selected_strategy]
        col_objs = st.columns(3)
        
        for i, indicator in enumerate(indicators):
            col = col_objs[i % 3]
            key_note = f"note__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"
            key_status = f"status__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"
            key_image = f"image__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"
            
            existing = existing_data.get(indicator, {})
            default_note = existing.get("note", "")
            default_status = existing.get("status", "Open")
            
            with col.expander(f"**{indicator}** - ADMIN EDIT", expanded=False):
                # Text analysis
                st.text_area(
                    f"Analysis Notes", 
                    value=default_note, 
                    key=key_note, 
                    height=120,
                    placeholder=f"Enter analysis for {indicator}..."
                )
                
                # Status selector
                st.selectbox(
                    "Status", 
                    ["Open", "In Progress", "Done", "Skipped"], 
                    index=["Open", "In Progress", "Done", "Skipped"].index(default_status) if default_status in ["Open", "In Progress", "Done", "Skipped"] else 0,
                    key=key_status
                )
                
                # Image upload section
                st.markdown("---")
                st.subheader("🖼️ Upload Images")
                
                uploaded_files = st.file_uploader(
                    f"Upload images for {indicator}",
                    type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
                    accept_multiple_files=True,
                    key=key_image
                )
                
                if uploaded_files:
                    st.success(f"✅ {len(uploaded_files)} image(s) ready for upload")
                    for uploaded_file in uploaded_files:
                        st.write(f"• {uploaded_file.name} ({uploaded_file.size} bytes)")
                
                # Display existing images for this indicator
                existing_images = image_manager.get_image_paths(
                    selected_strategy, indicator, analysis_date, st.session_state.user['username']
                )
                
                if existing_images:
                    st.markdown("**Existing Images:**")
                    for img_path in existing_images:
                        col_img1, col_img2 = st.columns([3, 1])
                        with col_img1:
                            if image_manager.display_image(img_path, width=200):
                                st.caption(os.path.basename(img_path))
                        with col_img2:
                            if st.button("🗑️", key=f"delete_{os.path.basename(img_path)}"):
                                if image_manager.delete_image(img_path):
                                    st.success("Image deleted!")
                                    time.sleep(1)
                                    st.rerun()
        
        # Save button
        submitted = st.form_submit_button("💾 Save All Signals & Images (Admin)", use_container_width=True)
        if submitted:
            if selected_strategy not in strategy_data:
                strategy_data[selected_strategy] = {}
            
            # Save text data
            for indicator in indicators:
                key_note = f"note__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"
                key_status = f"status__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"
                key_image = f"image__{sanitize_key(selected_strategy)}__{sanitize_key(indicator)}"
                
                # Get uploaded files for this indicator
                uploaded_files = st.session_state.get(key_image, [])
                
                # Save images
                image_paths = []
                for uploaded_file in uploaded_files:
                    saved_path = image_manager.save_uploaded_image(
                        uploaded_file, selected_strategy, indicator, 
                        analysis_date, st.session_state.user['username']
                    )
                    if saved_path:
                        image_paths.append(saved_path)
                
                # Save text data
                strategy_data[selected_strategy][indicator] = {
                    "note": st.session_state.get(key_note, ""),
                    "status": st.session_state.get(key_status, "Open"),
                    "momentum": strategy_type,
                    "strategy_tag": strategy_tag,
                    "analysis_date": analysis_date.strftime("%Y-%m-%d"),
                    "last_modified": datetime.utcnow().isoformat() + "Z",
                    "modified_by": "admin",
                    "image_paths": image_paths  # Store image paths in the data
                }
            
            save_data(strategy_data)
            st.success("✅ All signals and images saved successfully! (Admin Mode)")
    
    # Display saved analyses with images
    st.markdown("---")
    st.subheader("📜 Saved Signals with Images - ADMIN VIEW")
    
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
                        # Display note
                        st.write("**Analysis Notes:**")
                        st.write(meta.get("note", "") or "_No notes yet_")
                        
                        # Display images
                        image_paths = meta.get("image_paths", [])
                        if image_paths:
                            st.markdown("---")
                            st.write("**Attached Images:**")
                            cols = st.columns(min(3, len(image_paths)))
                            for idx, img_path in enumerate(image_paths):
                                with cols[idx % 3]:
                                    if image_manager.display_image(img_path, width=200):
                                        st.caption(os.path.basename(img_path))
                                        if st.button("🗑️ Delete", key=f"delete_saved_{os.path.basename(img_path)}"):
                                            if image_manager.delete_image(img_path):
                                                # Remove from data
                                                if 'image_paths' in strategy_data[strat][ind_name]:
                                                    strategy_data[strat][ind_name]['image_paths'].remove(img_path)
                                                save_data(strategy_data)
                                                st.success("Image deleted!")
                                                time.sleep(1)
                                                st.rerun()
                        else:
                            st.info("No images attached to this indicator.")
                        
                        st.caption(f"Last updated: {meta.get('last_modified', 'N/A')}")
            st.markdown("---")

def render_user_strategy_notes(strategy_data, daily_strategies, cycle_day, analysis_date, selected_strategy):
    """Detailed strategy notes interface - READ ONLY FOR USERS WITH IMAGES"""
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
    
    # Indicator analysis in columns - READ ONLY WITH IMAGES
    st.subheader("📊 Indicator Analysis")
    
    indicators = STRATEGIES[selected_strategy]
    col_objs = st.columns(3)
    
    for i, indicator in enumerate(indicators):
        col = col_objs[i % 3]
        existing = existing_data.get(indicator, {})
        note = existing.get("note", "")
        status = existing.get("status", "Open")
        image_paths = existing.get("image_paths", [])
        
        with col.expander(f"**{indicator}** - {status}", expanded=False):
            # Display note
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
            
            # Display images if any
            if image_paths:
                st.markdown("**Attached Images:**")
                for img_path in image_paths:
                    if image_manager.display_image(img_path, width=150):
                        st.caption(os.path.basename(img_path))
            
            st.caption(f"Status: {status}")
            if existing.get("last_modified"):
                st.caption(f"Last updated: {existing['last_modified'][:16]}")

# -------------------------
# ENHANCED PREMIUM SIGNAL DASHBOARD WITH IMAGE SUPPORT
# -------------------------
def render_premium_signal_dashboard():
    """Premium signal dashboard where admin can edit signals with image uploads"""
    
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
            "📝 Edit Signals & Images": "notes", 
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
        st.success(f"👑 Welcome back, **{user['name']}**! You're in **Admin Signal Mode** with full editing and image upload access.")
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
            images_count = 0
            
            if strategy in strategy_data:
                # Check if all indicators have notes for today
                today_indicators = [ind for ind, meta in strategy_data[strategy].items() 
                                  if meta.get("analysis_date") == analysis_date.strftime("%Y-%m-%d")]
                if len(today_indicators) == len(STRATEGIES[strategy]):
                    strategy_completed = True
                
                # Count images for this strategy
                for ind, meta in strategy_data[strategy].items():
                    if meta.get("analysis_date") == analysis_date.strftime("%Y-%m-%d"):
                        images_count += len(meta.get("image_paths", []))
            
            if strategy_completed:
                if images_count > 0:
                    st.success(f"✅ {strategy} ({images_count} 📷)")
                else:
                    st.success(f"✅ {strategy}")
            elif strategy == selected_strategy:
                if images_count > 0:
                    st.info(f"📝 {strategy} (current) ({images_count} 📷)")
                else:
                    st.info(f"📝 {strategy} (current)")
            else:
                if images_count > 0:
                    st.warning(f"🕓 {strategy} ({images_count} 📷)")
                else:
                    st.warning(f"🕓 {strategy}")
    
    st.markdown("---")
    
    # Quick image upload section
    st.subheader("🖼️ Quick Image Upload")
    
    with st.form("quick_image_upload"):
        quick_indicator = st.selectbox("Select Indicator:", STRATEGIES[selected_strategy])
        quick_images = st.file_uploader(
            "Upload images for quick analysis",
            type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
            accept_multiple_files=True,
            key="quick_upload"
        )
        
        if st.form_submit_button("🚀 Upload Images Quickly", use_container_width=True):
            if quick_images:
                uploaded_count = 0
                for uploaded_file in quick_images:
                    saved_path = image_manager.save_uploaded_image(
                        uploaded_file, selected_strategy, quick_indicator,
                        analysis_date, user['username']
                    )
                    if saved_path:
                        uploaded_count += 1
                
                if uploaded_count > 0:
                    # Update strategy data
                    if selected_strategy not in strategy_data:
                        strategy_data[selected_strategy] = {}
                    
                    if quick_indicator not in strategy_data[selected_strategy]:
                        strategy_data[selected_strategy][quick_indicator] = {}
                    
                    # Get existing image paths
                    existing_paths = strategy_data[selected_strategy][quick_indicator].get("image_paths", [])
                    new_paths = image_manager.get_image_paths(selected_strategy, quick_indicator, analysis_date, user['username'])
                    
                    strategy_data[selected_strategy][quick_indicator].update({
                        "image_paths": new_paths,
                        "analysis_date": analysis_date.strftime("%Y-%m-%d"),
                        "last_modified": datetime.utcnow().isoformat() + "Z",
                        "modified_by": "admin"
                    })
                    
                    save_data(strategy_data)
                    st.success(f"✅ {uploaded_count} image(s) uploaded successfully!")
                else:
                    st.error("❌ Failed to upload images")
            else:
                st.warning("⚠️ Please select at least one image to upload")
    
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
    if st.button("📝 Open Detailed Analysis & Image Editor", use_container_width=True):
        st.session_state.dashboard_view = 'notes'
        st.rerun()
    
    # Recent activity with image preview
    if data.get('saved_analyses'):
        st.markdown("---")
        st.subheader("📜 Recent Analyses")
        for strategy, analysis in list(data['saved_analyses'].items())[-3:]:
            with st.expander(f"{strategy} - {analysis['timestamp'].strftime('%H:%M')}"):
                st.write(f"**Tag:** {analysis['tag']} | **Type:** {analysis['type']}")
                st.write(analysis.get('note', 'No notes'))

# -------------------------
# ENHANCED USER DASHBOARD WITH IMAGE VIEWING
# -------------------------
def render_user_dashboard():
    """User dashboard - READ ONLY for regular users with image viewing"""
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
    
    # Clean sidebar with 5-day cycle system - READ ONLY
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
        
        # 5-Day Cycle System
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
    
    # Main dashboard content - READ ONLY for users
    current_view = st.session_state.get('dashboard_view', 'main')
    
    if current_view == 'notes':
        render_user_strategy_notes(strategy_data, daily_strategies, cycle_day, analysis_date, selected_strategy)
    elif current_view == 'settings':
        render_user_account_settings()
    else:
        render_user_trading_dashboard(data, user, daily_strategies, cycle_day, analysis_date, selected_strategy)

def render_user_trading_dashboard(data, user, daily_strategies, cycle_day, analysis_date, selected_strategy):
    """User trading dashboard - READ ONLY WITH IMAGE VIEWING"""
    st.title("📊 Trading Signal Dashboard")
    
    # Welcome message
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if user['plan'] == 'premium':
            st.success(f"🎉 Welcome back, **{user['name']}**! You're viewing Premium Signals with image support.")
        else:
            st.info(f"👋 Welcome, **{user['name']}**! You have access to {Config.PLANS[user['plan']]['strategies']} strategies.")
    with col2:
        st.metric("Cycle Day", f"Day {cycle_day}/5")
    with col3:
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Plan Days", days_left)
    
    st.markdown("---")
    
    # Progress indicators for today's strategies - WITH IMAGE COUNTS
    st.subheader("📋 Today's Strategy Progress")
    cols = st.columns(3)
    
    strategy_data = load_data()
    for i, strategy in enumerate(daily_strategies):
        with cols[i]:
            strategy_completed = False
            images_count = 0
            
            if strategy in strategy_data:
                # Check if all indicators have notes for today
                today_indicators = [ind for ind, meta in strategy_data[strategy].items() 
                                  if meta.get("analysis_date") == analysis_date.strftime("%Y-%m-%d")]
                if len(today_indicators) == len(STRATEGIES[strategy]):
                    strategy_completed = True
                
                # Count images for this strategy
                for ind, meta in strategy_data[strategy].items():
                    if meta.get("analysis_date") == analysis_date.strftime("%Y-%m-%d"):
                        images_count += len(meta.get("image_paths", []))
            
            if strategy_completed:
                if images_count > 0:
                    st.success(f"✅ {strategy} ({images_count} 📷)")
                else:
                    st.success(f"✅ {strategy}")
            elif strategy == selected_strategy:
                if images_count > 0:
                    st.info(f"📊 {strategy} (viewing) ({images_count} 📷)")
                else:
                    st.info(f"📊 {strategy} (viewing)")
            else:
                if images_count > 0:
                    st.warning(f"🕓 {strategy} ({images_count} 📷)")
                else:
                    st.warning(f"🕓 {strategy}")
    
    st.markdown("---")
    
    # Selected strategy analysis - READ ONLY WITH IMAGES
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
        
        # Quick image preview
        total_images = 0
        for indicator, meta in existing_data.items():
            if meta.get("analysis_date") == analysis_date.strftime("%Y-%m-%d"):
                total_images += len(meta.get("image_paths", []))
        
        if total_images > 0:
            st.info(f"📷 This strategy has {total_images} attached image(s). View details for full access.")
        
    else:
        st.warning("No signal data available for this strategy yet.")
    
    st.markdown("---")
    
    # Detailed view button - LEADS TO READ-ONLY DETAILED VIEW WITH IMAGES
    if st.button("📋 View Detailed Analysis & Images", use_container_width=True):
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

# -------------------------
# OTHER REQUIRED FUNCTIONS (simplified for brevity)
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
                    st.write(f"• Image Upload & Viewing Support")  # NEW FEATURE
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
        st.text_input("Image Upload", value="Enabled", disabled=True)
    
    st.markdown("---")
    st.subheader("Image Management")
    
    # Image storage info
    total_size = 0
    image_count = 0
    
    if os.path.exists(image_manager.images_dir):
        for root, dirs, files in os.walk(image_manager.images_dir):
            for file in files:
                if file.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    image_count += 1
                    file_path = os.path.join(root, file)
                    total_size += os.path.getsize(file_path)
    
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Total Images", image_count)
    with col2:
        st.metric("Storage Used", f"{total_size / (1024*1024):.2f} MB")
    
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
    
    # Image access info for users
    st.subheader("Image Access")
    if user['plan'] == 'premium':
        st.success("✅ You have full access to view all uploaded images and charts")
    else:
        st.info("ℹ️ Upgrade to Premium for full image viewing capabilities")
    
    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        st.session_state.dashboard_view = 'main'
        st.rerun()

# -------------------------
# ADMIN DASHBOARD COMPONENTS (simplified)
# -------------------------
def render_admin_dashboard_selection():
    """Interface for admin to choose between admin dashboard and premium dashboard"""
    st.title("👑 Admin Portal - Choose Dashboard")
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("🛠️ Admin Management Dashboard")
        st.markdown("""
        **Full System Control:**
        - User management & analytics
        - Email verification
        - Plan management
        - Business metrics
        - System configuration
        """)
        if st.button("🚀 Go to Admin Dashboard", use_container_width=True, key="admin_dash"):
            st.session_state.admin_dashboard_mode = "admin"
            st.rerun()
    
    with col2:
        st.subheader("📊 Premium Signal Dashboard")
        st.markdown("""
        **Signal & Image Management:**
        - Edit trading signals & strategies
        - Upload and manage images
        - Update market analysis
        - Manage 5-day cycle
        - Image organization
        """)
        if st.button("📈 Go to Premium Dashboard", use_container_width=True, key="premium_dash"):
            st.session_state.admin_dashboard_mode = "premium"
            st.rerun()

def render_admin_management_dashboard():
    """Simplified admin management dashboard"""
    st.title("🛠️ Admin Management Dashboard")
    st.info("Admin management features would be implemented here")
    
    if st.button("📊 Switch to Signal Dashboard", use_container_width=True):
        st.session_state.admin_dashboard_mode = "premium"
        st.rerun()

def render_admin_dashboard():
    """Professional admin dashboard with dual mode selection"""
    
    if st.session_state.get('admin_dashboard_mode') is None:
        render_admin_dashboard_selection()
        return
    
    with st.sidebar:
        st.title("👑 Admin Panel")
        st.markdown("---")
        st.write(f"Welcome, **{st.session_state.user['name']}**")
        
        current_mode = st.session_state.admin_dashboard_mode
        if current_mode == "admin":
            st.success("🛠️ Admin Management Mode")
        else:
            st.success("📊 Premium Signal Mode")
        
        st.markdown("---")
        st.subheader("Dashboard Mode")
        col1, col2 = st.columns(2)
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
        
        st.markdown("---")
        
        if st.button("🚪 Logout", use_container_width=True, key="sidebar_logout"):
            user_manager.logout(st.session_state.user['username'])
            st.session_state.user = None
            st.session_state.admin_dashboard_mode = None
            st.rerun()
    
    if st.session_state.get('admin_dashboard_mode') == "admin":
        render_admin_management_dashboard()
    else:
        render_premium_signal_dashboard()

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
    .image-upload-section {
        border: 2px dashed #4CAF50;
        border-radius: 10px;
        padding: 1rem;
        background: #f9fff9;
        margin: 1rem 0;
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
