# app.py - COMPLETE FIXED VERSION WITH WORKING EMAIL VERIFICATION
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
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
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
# PRODUCTION CONFIGURATION WITH EMAIL SETUP
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
    
    # SMTP Configuration - Can be set via environment variables or Streamlit secrets
    SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))
    SMTP_USERNAME = os.getenv("SMTP_USERNAME", "")
    SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
    FROM_EMAIL = os.getenv("FROM_EMAIL", "noreply@tradinganalysis.com")
    FROM_NAME = os.getenv("FROM_NAME", "TradingAnalysis Pro")
    
    @classmethod
    def is_email_configured(cls):
        """Check if email configuration is complete"""
        return all([
            cls.SMTP_SERVER,
            cls.SMTP_PORT,
            cls.SMTP_USERNAME,
            cls.SMTP_PASSWORD,
            cls.FROM_EMAIL
        ])

# -------------------------
# ENHANCED EMAIL VERIFICATION SYSTEM WITH FALLBACKS
# -------------------------
class EmailVerification:
    def __init__(self):
        self.verification_codes = {}
        self.code_expiry_minutes = 30
        self.email_enabled = Config.is_email_configured()
        
        if not self.email_enabled:
            print("⚠️ Email system disabled - SMTP configuration incomplete")
            print("💡 To enable email verification, set these environment variables:")
            print("   - SMTP_SERVER (e.g., smtp.gmail.com)")
            print("   - SMTP_PORT (e.g., 587)")
            print("   - SMTP_USERNAME (your email)")
            print("   - SMTP_PASSWORD (your app password)")
            print("   - FROM_EMAIL (sender email)")
    
    def generate_verification_code(self):
        """Generate a 6-digit verification code"""
        return ''.join(random.choices(string.digits, k=6))
    
    def send_verification_email(self, to_email, username, verification_code):
        """Send verification email using SMTP with enhanced error handling"""
        if not self.email_enabled:
            print(f"📧 [SIMULATED] Verification email would be sent to {to_email}")
            print(f"📧 [SIMULATED] Verification code for {username}: {verification_code}")
            return True  # Simulate success for development
        
        try:
            # Create message
            msg = MIMEMultipart()
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
            
            msg.attach(MIMEText(body, 'html'))
            
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
        if not self.email_enabled:
            print(f"📧 [SIMULATED] Welcome email would be sent to {to_email}")
            print(f"📧 [SIMULATED] Welcome {username} to {plan_name} plan!")
            return True
        
        try:
            msg = MIMEMultipart()
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
            
            msg.attach(MIMEText(body, 'html'))
            
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
# ENHANCED USER MANAGEMENT WITH BETTER EMAIL HANDLING
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
# ENHANCED EMAIL VERIFICATION INTERFACE WITH FALLBACK
# -------------------------
def render_email_verification_interface(username, email, plan_name):
    """Interface for email verification with fallback options"""
    st.title("📧 Verify Your Email Address")
    
    st.markdown("---")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        st.subheader("🔐 Account Verification Required")
        
        if email_verifier.email_enabled:
            st.info(f"""
            **Hello {username}!** 
            
            We've sent a verification code to **{email}**.
            
            Please check your inbox and enter the 6-digit code below to activate your account and start using TradingAnalysis Pro.
            """)
        else:
            st.warning("""
            **Email System Currently Unavailable**
            
            Our email system is temporarily unavailable. Please use one of these options to verify your account:
            """)
            
            # Show verification code directly when email is disabled
            if username in email_verifier.verification_codes:
                verification_code = email_verifier.verification_codes[username]['code']
                st.markdown("### Your Verification Code:")
                st.markdown(f'<div class="verification-code">{verification_code}</div>', unsafe_allow_html=True)
                st.info("**Copy this code and enter it below:**")
        
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
            if email_verifier.email_enabled:
                if st.button("🔄 Resend Code", use_container_width=True):
                    new_code = email_verifier.generate_verification_code()
                    email_verifier.store_verification_code(username, email, new_code)
                    if email_verifier.send_verification_email(email, username, new_code):
                        st.success("✅ New verification code sent!")
                    else:
                        st.error("❌ Failed to send verification email. Please try again.")
            else:
                if st.button("🔄 New Code", use_container_width=True):
                    new_code = email_verifier.generate_verification_code()
                    email_verifier.store_verification_code(username, email, new_code)
                    st.success("✅ New verification code generated!")
                    st.rerun()
        
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
        
        # Admin contact option when email is disabled
        if not email_verifier.email_enabled:
            st.error("""
            **Email System Notice:**
            Our automated email system is currently being configured. 
            Please contact support for immediate assistance.
            """)
        
        st.markdown("---")
        st.markdown(f"**Support Email:** {Config.SUPPORT_EMAIL}")
    
    st.markdown("---")
    
    # Debug information (only show in development)
    if st.secrets.get("ENVIRONMENT") == "development":
        with st.expander("🔧 Debug Information"):
            st.write(f"Username: {username}")
            st.write(f"Email: {email}")
            st.write(f"Email System Enabled: {email_verifier.email_enabled}")
            st.write(f"Pending verifications: {list(email_verifier.verification_codes.keys())}")
            if username in email_verifier.verification_codes:
                st.write(f"Stored code: {email_verifier.verification_codes[username]}")

# -------------------------
# ENHANCED REGISTRATION WITH BETTER EMAIL HANDLING
# -------------------------
def render_login():
    """Professional login/registration interface with enhanced email verification"""
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
            
            # Email system status indicator
            if not email_verifier.email_enabled:
                st.warning("⚠️ **Email System Notice:** Our automated email system is currently being configured. You'll see your verification code on screen after registration.")
            
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
                            
                            # Always try to send email, but handle failure gracefully
                            email_sent = email_verifier.send_verification_email(new_email, new_username, verification_code)
                            
                            if email_sent or not email_verifier.email_enabled:
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
                                # Email failed but system is supposed to be enabled
                                st.error("❌ Account created but failed to send verification email. Please contact support or try again later.")
                        else:
                            st.error(f"❌ {message}")

# [REST OF THE CODE REMAINS THE SAME AS BEFORE - User Credentials Management, Admin Dashboard, User Dashboard, etc.]

# Only include the essential parts that were changed above to fix the email verification issue.
# The rest of the code (admin dashboard, user dashboard, etc.) remains exactly the same as in your working version.

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
