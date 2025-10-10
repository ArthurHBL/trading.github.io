# app.py - COMPLETE FIXED VERSION WITH PERSISTENT DATABASE AND EMAIL VERIFICATION
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
import smtplib
from email.mime.text import MimeText
from email.mime.multipart import MimeMultipart
import random
import string

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
    if 'pending_verification' not in st.session_state:
        st.session_state.pending_verification = {}
    if 'show_verification_sent' not in st.session_state:
        st.session_state.show_verification_sent = False
    if 'verification_code_input' not in st.session_state:
        st.session_state.verification_code_input = ""

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
    
    # SMTP Configuration for Email Verification
    SMTP_SERVER = "smtp.gmail.com"  # Change to your SMTP server
    SMTP_PORT = 587
    SMTP_USERNAME = "your-email@gmail.com"  # Change to your email
    SMTP_PASSWORD = "your-app-password"  # Change to your app password
    FROM_EMAIL = "your-email@gmail.com"  # Change to your email
    FROM_NAME = "TradingAnalysis Pro"

# -------------------------
# EMAIL VERIFICATION SYSTEM
# -------------------------
class EmailVerification:
    def __init__(self):
        self.verification_codes = {}
        self.code_expiry_minutes = 30
    
    def generate_verification_code(self):
        """Generate a 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=6))
    
    def send_verification_email(self, to_email, username, verification_code):
        """Send verification email using SMTP"""
        try:
            # Create message
            msg = MimeMultipart()
            msg['From'] = f"{Config.FROM_NAME} <{Config.FROM_EMAIL}>"
            msg['To'] = to_email
            msg['Subject'] = "Verify Your TradingAnalysis Pro Account"
            
            # Email body
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="text-align: center; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); padding: 20px; border-radius: 10px 10px 0 0; color: white;">
                        <h1 style="margin: 0;">🔐 Verify Your Account</h1>
                    </div>
                    
                    <div style="padding: 30px;">
                        <h2 style="color: #667eea;">Welcome to TradingAnalysis Pro!</h2>
                        
                        <p>Hello <strong>{username}</strong>,</p>
                        
                        <p>Thank you for registering with TradingAnalysis Pro. To complete your account setup and start using our professional trading analysis tools, please verify your email address using the code below:</p>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <div style="font-size: 32px; font-weight: bold; letter-spacing: 5px; color: #667eea; background: #f8f9fa; padding: 20px; border-radius: 10px; border: 2px dashed #667eea;">
                                {verification_code}
                            </div>
                        </div>
                        
                        <p><strong>Verification Code:</strong> {verification_code}</p>
                        
                        <div style="background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                            <strong>⚠️ Important:</strong> 
                            <ul>
                                <li>This code will expire in {self.code_expiry_minutes} minutes</li>
                                <li>Do not share this code with anyone</li>
                                <li>If you didn't create this account, please ignore this email</li>
                            </ul>
                        </div>
                        
                        <p>Enter this code in the verification form to activate your account and get started with your trading analysis.</p>
                        
                        <div style="margin-top: 30px; padding-top: 20px; border-top: 1px solid #eee;">
                            <p style="font-size: 12px; color: #666;">
                                If you're having trouble with the verification code, you can:<br>
                                • Reply to this email for support<br>
                                • Visit our help center<br>
                                • Contact support at {Config.SUPPORT_EMAIL}
                            </p>
                        </div>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 15px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; color: #666;">
                        <p>&copy; 2024 {Config.BUSINESS_NAME}. All rights reserved.<br>
                        This email was sent to {to_email}</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MimeText(body, 'html'))
            
            # Send email
            with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
                server.send_message(msg)
            
            print(f"✅ Verification email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send verification email to {to_email}: {str(e)}")
            return False
    
    def send_welcome_email(self, to_email, username, plan_name):
        """Send welcome email after successful verification"""
        try:
            msg = MimeMultipart()
            msg['From'] = f"{Config.FROM_NAME} <{Config.FROM_EMAIL}>"
            msg['To'] = to_email
            msg['Subject'] = f"Welcome to TradingAnalysis Pro - {plan_name} Activated!"
            
            body = f"""
            <html>
            <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
                <div style="max-width: 600px; margin: 0 auto; padding: 20px; border: 1px solid #ddd; border-radius: 10px;">
                    <div style="text-align: center; background: linear-gradient(135deg, #28a745 0%, #20c997 100%); padding: 20px; border-radius: 10px 10px 0 0; color: white;">
                        <h1 style="margin: 0;">🎉 Welcome to TradingAnalysis Pro!</h1>
                    </div>
                    
                    <div style="padding: 30px;">
                        <h2 style="color: #28a745;">Your Account is Ready!</h2>
                        
                        <p>Hello <strong>{username}</strong>,</p>
                        
                        <p>Congratulations! Your TradingAnalysis Pro account has been successfully verified and your <strong>{plan_name}</strong> is now active.</p>
                        
                        <div style="background: #d4edda; padding: 20px; border-radius: 10px; border-left: 4px solid #28a745;">
                            <h3 style="color: #155724; margin-top: 0;">What's Next?</h3>
                            <ul style="color: #155724;">
                                <li>Access your personalized trading dashboard</li>
                                <li>Explore our 15 professional trading strategies</li>
                                <li>Start analyzing with our 5-day cycle system</li>
                                <li>Save and export your analysis notes</li>
                            </ul>
                        </div>
                        
                        <div style="text-align: center; margin: 30px 0;">
                            <a href="#" style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 15px 30px; text-decoration: none; border-radius: 25px; font-weight: bold; display: inline-block;">
                                🚀 Launch Your Dashboard
                            </a>
                        </div>
                        
                        <div style="background: #fff3cd; padding: 15px; border-radius: 5px; border-left: 4px solid #ffc107;">
                            <strong>💡 Pro Tip:</strong> Make sure to complete your daily strategy analysis to get the most out of our 5-day cycle system!
                        </div>
                        
                        <p>If you have any questions or need assistance, our support team is here to help at {Config.SUPPORT_EMAIL}.</p>
                        
                        <p>Happy trading!<br>
                        <strong>The {Config.BUSINESS_NAME} Team</strong></p>
                    </div>
                    
                    <div style="background: #f8f9fa; padding: 15px; text-align: center; border-radius: 0 0 10px 10px; font-size: 12px; color: #666;">
                        <p>&copy; 2024 {Config.BUSINESS_NAME}. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg.attach(MimeText(body, 'html'))
            
            with smtplib.SMTP(Config.SMTP_SERVER, Config.SMTP_PORT) as server:
                server.starttls()
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
                server.send_message(msg)
            
            print(f"✅ Welcome email sent to {to_email}")
            return True
            
        except Exception as e:
            print(f"❌ Failed to send welcome email to {to_email}: {str(e)}")
            return False
    
    def store_verification_code(self, username, email, verification_code):
        """Store verification code with expiry"""
        expiry_time = datetime.now() + timedelta(minutes=self.code_expiry_minutes)
        self.verification_codes[username] = {
            'code': verification_code,
            'email': email,
            'expires': expiry_time.isoformat(),
            'attempts': 0
        }
    
    def verify_code(self, username, code):
        """Verify the code and check expiry"""
        if username not in self.verification_codes:
            return False, "No pending verification found"
        
        verification_data = self.verification_codes[username]
        
        # Check expiry
        expiry_time = datetime.fromisoformat(verification_data['expires'])
        if datetime.now() > expiry_time:
            del self.verification_codes[username]
            return False, "Verification code has expired"
        
        # Check attempts
        if verification_data['attempts'] >= 3:
            del self.verification_codes[username]
            return False, "Too many failed attempts. Please request a new code"
        
        # Verify code
        if verification_data['code'] == code:
            del self.verification_codes[username]
            return True, "Email verified successfully"
        else:
            verification_data['attempts'] += 1
            return False, f"Invalid code. {3 - verification_data['attempts']} attempts remaining"
    
    def cleanup_expired_codes(self):
        """Clean up expired verification codes"""
        current_time = datetime.now()
        expired_users = []
        
        for username, data in self.verification_codes.items():
            if current_time > datetime.fromisoformat(data['expires']):
                expired_users.append(username)
        
        for username in expired_users:
            del self.verification_codes[username]
        
        if expired_users:
            print(f"🧹 Cleaned up {len(expired_users)} expired verification codes")

# Initialize email verification system
email_verifier = EmailVerification()

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
# SECURE USER MANAGEMENT WITH PERSISTENCE & EMAIL VERIFICATION
# -------------------------
class UserManager:
    def __init__(self):
        self.users_file = "users.json"
        self.analytics_file = "analytics.json"
        self._ensure_data_files()
        self.load_data()
        # REMOVED: atexit.register(self.cleanup_sessions) - This was causing issues
    
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
                "email_verifications": [],
                "test_users_created": []
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
                    "email_verifications": [],
                    "test_users_created": []
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
                "email_verifications": [],
                "test_users_created": []
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
            "email_verified": True,  # Admin doesn't need email verification
            "is_test_user": False
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
    
    def register_user(self, username, password, name, email, plan="trial", is_test_user=False):
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
        
        # For test users and admin, skip email verification
        email_verified = is_test_user or username == "admin"
        
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
            "email_verified": email_verified,
            "is_test_user": is_test_user
        }
        
        # Update analytics
        if 'user_registrations' not in self.analytics:
            self.analytics['user_registrations'] = []
        
        self.analytics["user_registrations"].append({
            "username": username,
            "plan": plan,
            "timestamp": datetime.now().isoformat(),
            "is_test_user": is_test_user,
            "email_verified": email_verified
        })
        
        # Save both files
        users_saved = self.save_users()
        analytics_saved = self.save_analytics()
        
        if users_saved and analytics_saved:
            print(f"✅ Successfully registered user: {username} (Test: {is_test_user}, Verified: {email_verified})")
            
            if is_test_user:
                return True, f"Test account created successfully! {plan_config['name']} activated."
            else:
                return True, f"Account created successfully! Please check your email for verification."
        else:
            # Remove the user if save failed
            if username in self.users:
                del self.users[username]
            return False, "Error saving user data. Please try again."

    def create_test_user(self, plan="trial"):
        """Create a test user for admin purposes (no email verification needed)"""
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
            "email_verified": True,  # Test users don't need email verification
            "is_test_user": True
        }
        
        self.analytics["user_registrations"].append({
            "username": test_username,
            "plan": plan,
            "timestamp": datetime.now().isoformat(),
            "is_test_user": True,
            "email_verified": True
        })
        
        # Track test user creation
        if 'test_users_created' not in self.analytics:
            self.analytics['test_users_created'] = []
        
        self.analytics['test_users_created'].append({
            "username": test_username,
            "created_by": "admin",
            "timestamp": datetime.now().isoformat()
        })
        
        if self.save_users() and self.save_analytics():
            return test_username, f"Test user '{test_username}' created with {plan} plan! (No email verification needed)"
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
        is_test_user = user_data.get('is_test_user', False)
        
        del self.users[username]
        
        if 'deleted_users' not in self.analytics:
            self.analytics['deleted_users'] = []
        
        self.analytics['deleted_users'].append({
            "username": username,
            "plan": user_plan,
            "created": user_created,
            "deleted_at": datetime.now().isoformat(),
            "was_test_user": is_test_user
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
        """Authenticate user WITH email verification check"""
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
        
        # Check email verification (skip for admin and test users)
        if not user.get("email_verified", False) and not user.get("is_test_user", False) and username != "admin":
            return False, "Email not verified. Please check your email for verification instructions."
        
        expires = user.get("expires")
        if expires and datetime.strptime(expires, "%Y-%m-%d").date() < date.today():
            return False, "Subscription expired. Please renew your plan."
        
        # REMOVED: Session blocking check - users can always login regardless of active sessions
        
        user["last_login"] = datetime.now().isoformat()
        user["login_count"] = user.get("login_count", 0) + 1
        user["active_sessions"] += 1  # Still track sessions but don't block login
        
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
        verified_counts = {"verified": 0, "unverified": 0, "test_users": 0}
        
        for user in self.users.values():
            plan = user.get('plan', 'unknown')
            plan_counts[plan] = plan_counts.get(plan, 0) + 1
            
            if user.get('is_test_user', False):
                verified_counts["test_users"] += 1
            elif user.get('email_verified', False):
                verified_counts["verified"] += 1
            else:
                verified_counts["unverified"] += 1
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "online_users": online_users,
            "plan_distribution": plan_counts,
            "verification_status": verified_counts,
            "total_logins": self.analytics.get("total_logins", 0),
            "revenue_today": self.analytics.get("revenue_today", 0)
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
                    "email_verified": user_data.get("email_verified", False),
                    "is_test_user": user_data.get("is_test_user", False)
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
                "email_verified": user_data.get("email_verified", False),
                "is_test_user": user_data.get("is_test_user", False)
            })
        return users_list

    # NEW FUNCTION: Manually verify user email (admin function)
    def manually_verify_email(self, username, verified_by="admin"):
        """Manually verify a user's email address (admin function)"""
        if username not in self.users:
            return False, "User not found"
        
        if username == "admin":
            return False, "Admin account is already verified"
        
        user_data = self.users[username]
        
        if user_data.get('email_verified', False):
            return False, "User email is already verified"
        
        user_data['email_verified'] = True
        
        # Update analytics
        if 'email_verifications' not in self.analytics:
            self.analytics['email_verifications'] = []
        
        self.analytics['email_verifications'].append({
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "verified_by": verified_by,
            "method": "manual_admin"
        })
        
        if self.save_users() and self.save_analytics():
            return True, f"Email for '{username}' manually verified by admin"
        else:
            return False, "Error saving verification status"

# Initialize user manager
user_manager = UserManager()

# -------------------------
# EMAIL VERIFICATION INTERFACE
# -------------------------
def render_email_verification_interface(username, email, plan_name):
    """Interface for email verification"""
    st.title("📧 Verify Your Email Address")
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔐 Account Verification Required")
        st.info(f"""
        **Hello {username}!** 
        
        We've sent a verification code to **{email}**.
        
        Please check your inbox and enter the 6-digit code below to activate your account and start using TradingAnalysis Pro.
        """)
        
        # Verification code input
        st.markdown("### Enter Verification Code")
        verification_code = st.text_input(
            "6-Digit Verification Code:",
            placeholder="Enter the code from your email",
            max_chars=6,
            key="verification_code_input"
        )
        
        col1, col2, col3 = st.columns([1, 1, 2])
        
        with col1:
            if st.button("✅ Verify Code", use_container_width=True):
                if not verification_code or len(verification_code) != 6:
                    st.error("❌ Please enter a valid 6-digit code")
                else:
                    success, message = email_verifier.verify_code(username, verification_code)
                    if success:
                        # Mark user as verified
                        user_manager.users[username]['email_verified'] = True
                        user_manager.save_users()
                        
                        # Send welcome email
                        email_verifier.send_welcome_email(email, username, plan_name)
                        
                        # Update analytics
                        if 'email_verifications' not in user_manager.analytics:
                            user_manager.analytics['email_verifications'] = []
                        
                        user_manager.analytics['email_verifications'].append({
                            "username": username,
                            "timestamp": datetime.now().isoformat(),
                            "method": "email_code"
                        })
                        user_manager.save_analytics()
                        
                        st.success("🎉 " + message)
                        st.balloons()
                        st.info("📧 Welcome email sent! You can now login to your account.")
                        
                        time.sleep(3)
                        st.session_state.show_verification_sent = False
                        st.rerun()
                    else:
                        st.error("❌ " + message)
        
        with col2:
            if st.button("🔄 Resend Code", use_container_width=True):
                new_code = email_verifier.generate_verification_code()
                email_verifier.store_verification_code(username, email, new_code)
                if email_verifier.send_verification_email(email, username, new_code):
                    st.success("✅ New verification code sent!")
                else:
                    st.error("❌ Failed to send verification email. Please try again.")
        
        with col3:
            st.markdown("")
    
    with col2:
        st.markdown("### 💡 Need Help?")
        st.info("""
        **Didn't receive the email?**
        - Check your spam folder
        - Verify your email address is correct
        - Wait a few minutes and try again
        - Contact support if issues persist
        """)
        
        st.markdown("---")
        st.markdown(f"**Support Email:** {Config.SUPPORT_EMAIL}")
    
    st.markdown("---")
    
    # Debug information (only show in development)
    if st.secrets.get("ENVIRONMENT") == "development":
        with st.expander("🔧 Debug Information"):
            st.write(f"Username: {username}")
            st.write(f"Email: {email}")
            st.write(f"Pending verifications: {list(email_verifier.verification_codes.keys())}")
            if username in email_verifier.verification_codes:
                st.write(f"Stored code: {email_verifier.verification_codes[username]}")

# -------------------------
# NEW: USER CREDENTIALS MANAGEMENT INTERFACE
# -------------------------
def render_user_credentials_interface():
    """Interface for viewing and managing user credentials"""
    st.subheader("🔐 User Credentials Management")
    
    # Back button
    if st.button("⬅️ Back to User Management", key="back_credentials"):
        st.session_state.show_user_credentials = False
        st.rerun()
    
    # Export all credentials
    st.markdown("### 📊 Export All User Data")
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button("📥 Download User Credentials CSV", use_container_width=True):
            csv_bytes, error = user_manager.export_user_credentials()
            if csv_bytes:
                st.download_button(
                    label="⬇️ Download CSV File",
                    data=csv_bytes,
                    file_name=f"user_credentials_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                    mime="text/csv",
                    use_container_width=True
                )
            else:
                st.error(f"❌ {error}")
    
    with col2:
        st.info("This export contains all user account details including usernames, emails, and subscription information.")
    
    st.markdown("---")
    
    # Display all users in a table
    st.markdown("### 👥 All User Accounts")
    users_display = user_manager.get_user_credentials_display()
    
    if users_display:
        df = pd.DataFrame(users_display)
        st.dataframe(df, use_container_width=True)
    else:
        st.info("No users found.")
    
    st.markdown("---")
    
    # Individual user management
    st.markdown("### ⚙️ Manage Individual User")
    
    col1, col2 = st.columns(2)
    
    with col1:
        selected_user = st.selectbox(
            "Select User to Manage:",
            [""] + [user["username"] for user in users_display],
            key="user_cred_select"
        )
    
    if selected_user:
        user_data = user_manager.users[selected_user]
        
        st.markdown(f"#### Managing: **{selected_user}**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.markdown("**Change Username**")
            new_username = st.text_input("New Username:", value=selected_user, key=f"new_username_{selected_user}")
            
            if st.button("🔄 Change Username", key=f"change_username_{selected_user}"):
                if new_username != selected_user:
                    success, message = user_manager.change_username(selected_user, new_username, st.session_state.user['username'])
                    if success:
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
                else:
                    st.warning("New username must be different from current username")
        
        with col2:
            st.markdown("**Change Password**")
            new_password = st.text_input("New Password:", type="password", key=f"new_password_{selected_user}")
            confirm_password = st.text_input("Confirm Password:", type="password", key=f"confirm_password_{selected_user}")
            
            if st.button("🔑 Change Password", key=f"change_password_{selected_user}"):
                if not new_password:
                    st.error("❌ Please enter a new password")
                elif new_password != confirm_password:
                    st.error("❌ Passwords do not match")
                elif len(new_password) < 8:
                    st.error("❌ Password must be at least 8 characters")
                else:
                    success, message = user_manager.change_user_password(selected_user, new_password, st.session_state.user['username'])
                    if success:
                        st.success(f"✅ {message}")
                    else:
                        st.error(f"❌ {message}")
        
        with col3:
            st.markdown("**Email Verification**")
            if user_data.get('email_verified', False):
                st.success("✅ Email Verified")
            else:
                st.error("❌ Email Not Verified")
                if st.button("✅ Manually Verify", key=f"verify_{selected_user}"):
                    success, message = user_manager.manually_verify_email(selected_user, st.session_state.user['username'])
                    if success:
                        st.success(f"✅ {message}")
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        # User details
        st.markdown("#### 📋 User Details")
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.write(f"**Name:** {user_data.get('name', 'N/A')}")
            st.write(f"**Email:** {user_data.get('email', 'N/A')}")
            st.write(f"**Plan:** {user_data.get('plan', 'N/A')}")
        
        with col2:
            st.write(f"**Created:** {user_data.get('created', 'N/A')[:10]}")
            st.write(f"**Last Login:** {user_data.get('last_login', 'Never')[:19]}")
            st.write(f"**Login Count:** {user_data.get('login_count', 0)}")
        
        with col3:
            st.write(f"**Active Sessions:** {user_data.get('active_sessions', 0)}")
            st.write(f"**Status:** {'🟢 Active' if user_data.get('is_active', True) else '🔴 Inactive'}")
            st.write(f"**Expires:** {user_data.get('expires', 'N/A')}")
            st.write(f"**Test User:** {'✅ Yes' if user_data.get('is_test_user', False) else '❌ No'}")

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
    
    # Back button at the top
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
                st.info(f"💵 Price increase: ${price_change}/month")
            elif price_change < 0:
                st.success(f"💵 Price decrease: ${abs(price_change)}/month")
        
        # Change reason (optional)
        change_reason = st.text_area("Reason for plan change (optional):", 
                                   placeholder="e.g., User requested upgrade, Payment issue, Special promotion...")
        
        # Confirm change
        if st.button("✅ Confirm Plan Change", type="primary", use_container_width=True):
            if new_plan == current_plan:
                st.warning("User is already on this plan")
            else:
                success, message = user_manager.change_user_plan(username, new_plan)
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
        st.metric("Days Remaining", days_left)
        
        st.markdown("#### Features:")
        st.write(f"• **Strategies:** {current_plan_config.get('strategies', 0)} available")
        st.write(f"• **Sessions:** {user_data.get('active_sessions', 0)}/{current_plan_config.get('max_sessions', 1)} active")
        st.write(f"• **Price:** ${current_plan_config.get('price', 0)}/month")
        
        st.markdown("#### User Statistics:")
        st.write(f"• **Joined:** {user_data['created'][:10]}")
        
        # Handle None or empty last_login safely
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
        st.write(f"• **Email Verified:** {'✅ Yes' if user_data.get('email_verified', False) else '❌ No'}")
        st.write(f"• **Test User:** {'✅ Yes' if user_data.get('is_test_user', False) else '❌ No'}")
        
        # Quick actions
        st.markdown("#### Quick Actions:")
        
        # Quick plan changes
        quick_plans = {
            "🚀 Upgrade to Premium": "premium",
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
    
    # Another back button at the bottom for convenience
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("⬅️ Back to User Management", key="back_bottom", use_container_width=True):
            st.session_state.manage_user_plan = None
            st.rerun()

# -------------------------
# ADMIN DASHBOARD - COMPLETE VERSION
# -------------------------
def render_admin_dashboard():
    """Professional admin dashboard for business management"""
    
    # Always render the sidebar first, regardless of current view
    with st.sidebar:
        st.title("👑 Admin Panel")
        st.markdown("---")
        st.write(f"Welcome, **{st.session_state.user['name']}**")
        st.success("System Administrator")
        
        # Logout button should always work
        if st.button("🚪 Logout", use_container_width=True, key="sidebar_logout"):
            user_manager.logout(st.session_state.user['username'])
            st.session_state.user = None
            st.rerun()
        
        st.markdown("---")
        st.subheader("Admin Actions")
        
        # All sidebar buttons should work from any view
        if st.button("🔄 Refresh All Data", use_container_width=True, key="sidebar_refresh"):
            user_manager.load_data()
            st.rerun()
        
        if st.button("📊 View Analytics", use_container_width=True, key="sidebar_analytics"):
            # Clear any modal/management states first
            st.session_state.show_delete_confirmation = False
            st.session_state.show_bulk_delete = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.show_user_credentials = False
            st.session_state.admin_view = "analytics"
            st.rerun()
        
        if st.button("👥 Manage Users", use_container_width=True, key="sidebar_users"):
            # Clear any modal/management states first
            st.session_state.show_delete_confirmation = False
            st.session_state.show_bulk_delete = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.show_user_credentials = False
            st.session_state.admin_view = "users"
            st.rerun()
        
        if st.button("🔐 User Credentials", use_container_width=True, key="sidebar_credentials"):
            # Clear any modal/management states first
            st.session_state.show_delete_confirmation = False
            st.session_state.show_bulk_delete = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.show_user_credentials = True
            st.rerun()
        
        if st.button("🗑️ Bulk Delete", use_container_width=True, key="sidebar_bulk_delete"):
            # Clear any modal/management states first
            st.session_state.show_delete_confirmation = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.show_user_credentials = False
            st.session_state.admin_view = "users"
            st.session_state.show_bulk_delete = True
            st.rerun()
        
        if st.button("💰 Revenue Report", use_container_width=True, key="sidebar_revenue"):
            # Clear any modal/management states first
            st.session_state.show_delete_confirmation = False
            st.session_state.show_bulk_delete = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.show_user_credentials = False
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
    
    # Show user credentials interface if needed
    if st.session_state.get('show_user_credentials'):
        render_user_credentials_interface()
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
    
    # Email verification status
    st.subheader("📧 Email Verification Status")
    verification_data = metrics["verification_status"]
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Verified Users", verification_data["verified"])
    with col2:
        st.metric("Unverified Users", verification_data["unverified"])
    with col3:
        st.metric("Test Users", verification_data["test_users"])
    
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
                verified_status = "✅" if reg.get('email_verified') or reg.get('is_test_user') else "❌"
                test_status = "🧪" if reg.get('is_test_user') else ""
                st.write(f"• {reg['username']} - {plan_name} {verified_status}{test_status} - {reg['timestamp'][:16]}")
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
    
    email_verifications = user_manager.analytics.get("email_verifications", [])
    if email_verifications:
        manual_verifications = [v for v in email_verifications if v.get('method') == 'manual_admin']
        email_verifications_count = len(email_verifications) - len(manual_verifications)
        
        col1, col2 = st.columns(2)
        with col1:
            st.metric("Total Verifications", len(email_verifications))
        with col2:
            st.metric("Manual Admin Verifications", len(manual_verifications))
    else:
        st.info("No email verification data available")
    
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
    
    # User actions - UPDATED WITH USER CREDENTIALS
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("🔄 Refresh User List", use_container_width=True, key="um_refresh"):
            st.rerun()
    with col2:
        if st.button("🔐 User Credentials", use_container_width=True, key="um_credentials"):
            st.session_state.show_user_credentials = True
            st.rerun()
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
    with col5:
        if st.button("🔐 Change Admin Password", use_container_width=True, key="um_password"):
            st.session_state.show_password_change = True
            st.rerun()
    with col6:
        # Export credentials button
        csv_bytes, error = user_manager.export_user_credentials()
        if csv_bytes:
            st.download_button(
                label="📥 Export Users",
                data=csv_bytes,
                file_name=f"user_credentials_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    st.markdown("---")
    
    # Enhanced User table with quick actions
    st.write("**All Users - Quick Plan Management:**")
    
    # Display users with quick plan change options
    for username, user_data in user_manager.users.items():
        with st.container():
            col1, col2, col3, col4, col5, col6, col7 = st.columns([2, 2, 2, 2, 1, 1, 1])
            
            with col1:
                st.write(f"**{username}**")
                st.caption(user_data['name'])
                if user_data.get('is_test_user', False):
                    st.caption("🧪 Test User")
            
            with col2:
                st.write(user_data['email'])
            
            with col3:
                current_plan = user_data['plan']
                plan_display = Config.PLANS.get(current_plan, {}).get('name', current_plan.title())
                st.write(f"`{plan_display}`")
            
            with col4:
                expires = user_data['expires']
                days_left = (datetime.strptime(expires, "%Y-%m-%d").date() - date.today()).days
                email_status = "✅" if user_data.get('email_verified', False) else "❌"
                st.write(f"Expires: {expires} {email_status}")
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
                if username != "admin" and not user_data.get('email_verified', False):
                    if st.button("✅", key=f"verify_{username}", help="Verify Email"):
                        success, message = user_manager.manually_verify_email(username, st.session_state.user['username'])
                        if success:
                            st.success(message)
                            time.sleep(1)
                            st.rerun()
                        else:
                            st.error(message)
            
            with col7:
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
# AUTHENTICATION COMPONENTS WITH EMAIL VERIFICATION
# -------------------------
def render_login():
    """Professional login/registration interface with email verification"""
    st.title(f"🔐 Welcome to {Config.APP_NAME}")
    st.markdown("---")
    
    # Check if we need to show email verification interface
    if st.session_state.get('show_verification_sent'):
        pending_user = st.session_state.get('pending_verification', {})
        if pending_user:
            render_email_verification_interface(
                pending_user.get('username'), 
                pending_user.get('email'),
                pending_user.get('plan_name')
            )
        return
    
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
                            # Generate and send verification code
                            verification_code = email_verifier.generate_verification_code()
                            email_verifier.store_verification_code(new_username, new_email, verification_code)
                            
                            if email_verifier.send_verification_email(new_email, new_username, verification_code):
                                st.success(f"✅ {message}")
                                st.balloons()
                                
                                # Store pending verification and show verification interface
                                st.session_state.pending_verification = {
                                    'username': new_username,
                                    'email': new_email,
                                    'plan_name': Config.PLANS[plan_choice]['name']
                                }
                                st.session_state.show_verification_sent = True
                                st.rerun()
                            else:
                                st.error("❌ Account created but failed to send verification email. Please contact support.")
                        else:
                            st.error(f"❌ {message}")

# -------------------------
# REDESIGNED USER DASHBOARD WITH 5-DAY CYCLE
# -------------------------
def render_user_dashboard():
    """Redesigned trading dashboard with 5-day cycle system"""
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
    
    # Clean sidebar with 5-day cycle system
    with st.sidebar:
        st.title("🎛️ Control Panel")
        
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
        start_date = date(2025, 8, 9)
        analysis_date = st.date_input(
            "Analysis Date:",
            value=st.session_state.get('analysis_date', date.today()),
            min_value=start_date,
            key="analysis_date_selector"
        )
        st.session_state.analysis_date = analysis_date
        
        daily_strategies, cycle_day = get_daily_strategies(analysis_date)
        st.info(f"**Day {cycle_day} of 5-day cycle**")
        
        # Today's focus strategies
        st.markdown("**Today's Focus:**")
        for strategy in daily_strategies:
            st.write(f"• {strategy}")
        
        st.markdown("---")
        
        # Strategy selection
        selected_strategy = st.selectbox(
            "Choose Strategy:", 
            daily_strategies,
            key="strategy_selector"
        )
        
        st.markdown("---")
        
        # Navigation
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
            st.rerun()
    
    # Main dashboard content
    current_view = st.session_state.get('dashboard_view', 'main')
    
    if st.session_state.get('show_settings'):
        render_account_settings()
    elif st.session_state.get('show_upgrade'):
        render_upgrade_plans()
    elif current_view == 'notes':
        render_strategy_notes(strategy_data, daily_strategies, cycle_day, analysis_date, selected_strategy)
    elif current_view == 'settings':
        render_account_settings()
    else:
        render_trading_dashboard(data, user, daily_strategies, cycle_day, analysis_date, selected_strategy)

def render_trading_dashboard(data, user, daily_strategies, cycle_day, analysis_date, selected_strategy):
    """Clean trading dashboard with 5-day cycle"""
    st.title("📊 Professional Trading Analysis")
    
    # Welcome and cycle info
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        if user['plan'] == 'premium':
            st.success(f"🎉 Welcome back, **{user['name']}**! You're using our **Premium Plan** with full access.")
        else:
            st.info(f"👋 Welcome, **{user['name']}**! You have access to {Config.PLANS[user['plan']]['strategies']} strategies.")
    with col2:
        st.metric("Cycle Day", f"Day {cycle_day}/5")
    with col3:
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Plan Days", days_left)
    
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
    
    # Selected strategy analysis
    st.subheader(f"🔍 {selected_strategy} Analysis")
    
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
    if st.button("📝 Open Detailed Analysis", use_container_width=True):
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

def render_strategy_notes(strategy_data, daily_strategies, cycle_day, analysis_date, selected_strategy):
    """Detailed strategy notes interface with 5-day cycle"""
    st.title("📝 Strategy Analysis Notes")
    
    # Header with cycle info
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
        
        # Indicator analysis in columns
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
        
        # Save button
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
                    "last_modified": datetime.utcnow().isoformat() + "Z"
                }
            
            save_data(strategy_data)
            st.success("✅ All notes saved successfully!")
    
    # Display saved analyses
    st.markdown("---")
    st.subheader("📜 Saved Analyses")
    
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
                st.info("No saved notes for this strategy.")
                continue
            
            strategy_tag = next(iter(inds.values())).get("strategy_tag", "Neutral")
            st.markdown(f"**Strategy Tag:** {color_map.get(strategy_tag, strategy_tag)}")
            st.markdown("---")
            
            for ind_name, meta in inds.items():
                if meta.get("analysis_date") == analysis_date.strftime("%Y-%m-%d"):
                    momentum_type = meta.get("momentum", "Not Defined")
                    status_icon = "✅ Done" if meta.get("status", "Open") == "Done" else "🕓 Open"
                    with st.expander(f"{ind_name} ({momentum_type}) — {status_icon}", expanded=False):
                        st.write(meta.get("note", "") or "_No notes yet_")
                        st.caption(f"Last updated: {meta.get('last_modified', 'N/A')}")
            st.markdown("---")

def render_account_settings():
    """Clean account settings interface"""
    st.title("⚙️ Account Settings")
    
    user = st.session_state.user
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Profile Information")
        st.text_input("Full Name", value=user['name'], disabled=True)
        st.text_input("Email", value=user['email'], disabled=True)
        st.text_input("Username", value=user['username'], disabled=True)
        
        if st.button("📧 Request Profile Update", use_container_width=True):
            st.info("Profile update requests are processed by our support team")
    
    with col2:
        st.subheader("Subscription Details")
        plan_name = Config.PLANS.get(user['plan'], {}).get('name', 'Unknown Plan')
        st.text_input("Current Plan", value=plan_name, disabled=True)
        st.text_input("Expiry Date", value=user['expires'], disabled=True)
        
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Days Remaining", days_left)
        
        if st.button("💳 Manage Subscription", use_container_width=True):
            st.session_state.show_upgrade = True
            st.rerun()
    
    st.markdown("---")
    st.subheader("Security")
    if st.button("🔐 Change Password", use_container_width=True):
        st.info("Password change requests are handled by our support team for security")
    
    if st.button("📞 Contact Support", use_container_width=True):
        st.info(f"Email: {Config.SUPPORT_EMAIL}")
    
    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        st.session_state.dashboard_view = 'main'
        st.rerun()

def render_upgrade_plans():
    """Clean plan upgrade interface"""
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
                    if st.button(f"Upgrade to {plan_config['name']}", key=f"upgrade_{plan_id}", use_container_width=True):
                        st.info("🔒 Secure payment processing would be implemented here")
                        st.success(f"Upgrade to {plan_config['name']} selected!")
    
    st.markdown("---")
    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        st.session_state.show_upgrade = False
        st.rerun()

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
    
    # Clean up expired verification codes periodically
    email_verifier.cleanup_expired_codes()
    
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
    .verification-code {
        font-family: 'Courier New', monospace;
        font-size: 1.5rem;
        font-weight: bold;
        letter-spacing: 0.5rem;
        text-align: center;
        background: #f8f9fa;
        padding: 1rem;
        border-radius: 10px;
        border: 2px dashed #667eea;
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
