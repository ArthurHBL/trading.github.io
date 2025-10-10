# app.py - COMPLETE FIXED VERSION WITH PERSISTENT DATABASE AND SMTP EMAIL VERIFICATION
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
from email.mime.application import MIMEApplication
import ssl

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
    if 'email_verification_pending' not in st.session_state:
        st.session_state.email_verification_pending = False
    if 'pending_verification_user' not in st.session_state:
        st.session_state.pending_verification_user = None
    if 'show_email_settings' not in st.session_state:
        st.session_state.show_email_settings = False

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
    
    # SMTP Configuration - UPDATE THESE WITH YOUR ACTUAL SMTP SETTINGS
    SMTP_SERVER = "smtp.gmail.com"  # Change to your SMTP server
    SMTP_PORT = 587  # 587 for TLS, 465 for SSL
    SMTP_USERNAME = "your-email@gmail.com"  # Change to your email
    SMTP_PASSWORD = "your-app-password"  # Change to your app password
    USE_TLS = True  # Set to False if using SSL
    
    # Email Templates
    EMAIL_TEMPLATES = {
        "welcome": {
            "subject": "Welcome to TradingAnalysis Pro - Verify Your Email",
            "template": """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                    .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                    .verification-code { background: #667eea; color: white; padding: 15px; border-radius: 5px; font-size: 24px; font-weight: bold; text-align: center; margin: 20px 0; }
                    .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to TradingAnalysis Pro! 🚀</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {name}!</h2>
                        <p>Thank you for registering with TradingAnalysis Pro. To complete your registration and start using our professional trading analysis platform, please verify your email address.</p>
                        
                        <div class="verification-code">
                            Your Verification Code: {verification_code}
                        </div>
                        
                        <p><strong>Instructions:</strong></p>
                        <ol>
                            <li>Return to the TradingAnalysis Pro application</li>
                            <li>Enter the verification code above when prompted</li>
                            <li>Start analyzing trading strategies immediately!</li>
                        </ol>
                        
                        <p><strong>Account Details:</strong></p>
                        <ul>
                            <li><strong>Username:</strong> {username}</li>
                            <li><strong>Plan:</strong> {plan_name}</li>
                            <li><strong>Expires:</strong> {expires_date}</li>
                        </ul>
                        
                        <p>If you didn't create this account, please ignore this email.</p>
                        
                        <p>Happy Trading!<br>The TradingAnalysis Pro Team</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2024 TradingAnalysis Inc. All rights reserved.</p>
                        <p>This is an automated message, please do not reply to this email.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        },
        "password_reset": {
            "subject": "TradingAnalysis Pro - Password Reset Request",
            "template": """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: linear-gradient(135deg, #ff6b6b 0%, #ee5a52 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                    .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                    .reset-code { background: #ff6b6b; color: white; padding: 15px; border-radius: 5px; font-size: 24px; font-weight: bold; text-align: center; margin: 20px 0; }
                    .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Password Reset Request 🔒</h1>
                    </div>
                    <div class="content">
                        <h2>Hello {name}!</h2>
                        <p>We received a request to reset your password for your TradingAnalysis Pro account.</p>
                        
                        <div class="reset-code">
                            Your Reset Code: {reset_code}
                        </div>
                        
                        <p><strong>Instructions:</strong></p>
                        <ol>
                            <li>Return to the TradingAnalysis Pro application</li>
                            <li>Enter the reset code above when prompted</li>
                            <li>Create your new secure password</li>
                        </ol>
                        
                        <p><strong>Security Note:</strong></p>
                        <ul>
                            <li>This code will expire in 1 hour</li>
                            <li>If you didn't request this reset, please ignore this email</li>
                            <li>For security, never share your verification codes</li>
                        </ul>
                        
                        <p>If you need assistance, contact our support team at {support_email}.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2024 TradingAnalysis Inc. All rights reserved.</p>
                        <p>This is an automated security message.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        },
        "plan_upgrade": {
            "subject": "TradingAnalysis Pro - Plan Upgrade Confirmation",
            "template": """
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body { font-family: Arial, sans-serif; line-height: 1.6; color: #333; }
                    .container { max-width: 600px; margin: 0 auto; padding: 20px; }
                    .header { background: linear-gradient(135deg, #00D4AA 0%, #009975 100%); color: white; padding: 30px; text-align: center; border-radius: 10px 10px 0 0; }
                    .content { background: #f9f9f9; padding: 30px; border-radius: 0 0 10px 10px; }
                    .feature-list { background: white; padding: 20px; border-radius: 5px; margin: 20px 0; }
                    .footer { text-align: center; margin-top: 20px; font-size: 12px; color: #666; }
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Plan Upgrade Successful! 🎉</h1>
                    </div>
                    <div class="content">
                        <h2>Congratulations, {name}!</h2>
                        <p>Your TradingAnalysis Pro account has been successfully upgraded to the <strong>{new_plan}</strong> plan.</p>
                        
                        <div class="feature-list">
                            <h3>🎯 New Features Available:</h3>
                            <ul>
                                <li><strong>{strategies_count} Trading Strategies</strong> - Full access to our complete strategy library</li>
                                <li><strong>{sessions_count} Concurrent Sessions</strong> - Use multiple devices simultaneously</li>
                                <li><strong>Priority Support</strong> - Faster response times</li>
                                <li><strong>Advanced Analytics</strong> - Deeper insights and metrics</li>
                            </ul>
                        </div>
                        
                        <p><strong>Account Summary:</strong></p>
                        <ul>
                            <li><strong>Username:</strong> {username}</li>
                            <li><strong>New Plan:</strong> {new_plan}</li>
                            <li><strong>Plan Expires:</strong> {expires_date}</li>
                            <li><strong>Upgrade Date:</strong> {upgrade_date}</li>
                        </ul>
                        
                        <p>You can start using all your new features immediately by logging into your account.</p>
                        
                        <p>Thank you for upgrading!<br>The TradingAnalysis Pro Team</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2024 TradingAnalysis Inc. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """
        }
    }

# -------------------------
# SMTP EMAIL SERVICE
# -------------------------
class EmailService:
    def __init__(self):
        self.smtp_server = Config.SMTP_SERVER
        self.smtp_port = Config.SMTP_PORT
        self.smtp_username = Config.SMTP_USERNAME
        self.smtp_password = Config.SMTP_PASSWORD
        self.use_tls = Config.USE_TLS
        self.test_mode = False  # Set to True to simulate emails without sending
    
    def test_connection(self):
        """Test SMTP connection"""
        try:
            if self.test_mode:
                return True, "Test mode enabled - emails will be simulated"
                
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.quit()
            return True, "SMTP connection successful"
        except Exception as e:
            return False, f"SMTP connection failed: {str(e)}"
    
    def send_email(self, to_email, subject, html_content, text_content=None):
        """Send email using SMTP"""
        try:
            if self.test_mode:
                # In test mode, just log the email instead of sending
                print(f"📧 TEST MODE - Would send email to: {to_email}")
                print(f"   Subject: {subject}")
                print(f"   Content: {text_content or html_content[:100]}...")
                return True, "Email sent successfully (test mode)"
            
            # Create message
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self.smtp_username
            msg['To'] = to_email
            
            # Create plain text version
            if text_content is None:
                # Create simple text version from HTML
                text_content = re.sub('<[^<]+?>', '', html_content)
            
            part1 = MIMEText(text_content, 'plain')
            part2 = MIMEText(html_content, 'html')
            
            msg.attach(part1)
            msg.attach(part2)
            
            # Connect to server and send
            server = smtplib.SMTP(self.smtp_server, self.smtp_port)
            if self.use_tls:
                server.starttls()
            server.login(self.smtp_username, self.smtp_password)
            server.send_message(msg)
            server.quit()
            
            print(f"✅ Email sent successfully to: {to_email}")
            return True, "Email sent successfully"
            
        except Exception as e:
            error_msg = f"Failed to send email: {str(e)}"
            print(f"❌ {error_msg}")
            return False, error_msg
    
    def send_verification_email(self, user_data, verification_code):
        """Send email verification code"""
        template = Config.EMAIL_TEMPLATES["welcome"]
        html_content = template["template"].format(
            name=user_data["name"],
            verification_code=verification_code,
            username=user_data["username"],
            plan_name=Config.PLANS.get(user_data["plan"], {}).get("name", "Trial"),
            expires_date=user_data["expires"]
        )
        
        return self.send_email(
            user_data["email"],
            template["subject"],
            html_content
        )
    
    def send_password_reset_email(self, user_data, reset_code):
        """Send password reset code"""
        template = Config.EMAIL_TEMPLATES["password_reset"]
        html_content = template["template"].format(
            name=user_data["name"],
            reset_code=reset_code,
            support_email=Config.SUPPORT_EMAIL
        )
        
        return self.send_email(
            user_data["email"],
            template["subject"],
            html_content
        )
    
    def send_plan_upgrade_email(self, user_data, old_plan, new_plan):
        """Send plan upgrade confirmation"""
        template = Config.EMAIL_TEMPLATES["plan_upgrade"]
        new_plan_config = Config.PLANS.get(new_plan, {})
        
        html_content = template["template"].format(
            name=user_data["name"],
            username=user_data["username"],
            old_plan=Config.PLANS.get(old_plan, {}).get("name", old_plan),
            new_plan=new_plan_config.get("name", new_plan),
            strategies_count=new_plan_config.get("strategies", 0),
            sessions_count=new_plan_config.get("max_sessions", 1),
            expires_date=user_data["expires"],
            upgrade_date=datetime.now().strftime("%Y-%m-%d")
        )
        
        return self.send_email(
            user_data["email"],
            template["subject"],
            html_content
        )

# Initialize email service
email_service = EmailService()

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
# SECURE USER MANAGEMENT WITH PERSISTENCE AND EMAIL VERIFICATION
# -------------------------
class UserManager:
    def __init__(self):
        self.users_file = "users.json"
        self.analytics_file = "analytics.json"
        self.verification_codes_file = "verification_codes.json"
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
                "password_resets": []
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
                    "password_resets": []
                }
                self.save_analytics()
        
        # Verification codes file
        if not os.path.exists(self.verification_codes_file):
            self.verification_codes = {}
            self.save_verification_codes()
        else:
            try:
                with open(self.verification_codes_file, 'r') as f:
                    self.verification_codes = json.load(f)
            except json.JSONDecodeError:
                backup_name = f"{self.verification_codes_file}.backup.{int(time.time())}"
                os.rename(self.verification_codes_file, backup_name)
                print(f"⚠️ Verification codes file corrupted. Backed up to {backup_name}")
                self.verification_codes = {}
                self.save_verification_codes()
    
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
                "password_resets": []
            }
            self.save_analytics()
        
        try:
            with open(self.verification_codes_file, 'r', encoding='utf-8') as f:
                self.verification_codes = json.load(f)
            print(f"✅ Loaded verification codes")
        except Exception as e:
            print(f"❌ Error loading verification codes: {e}")
            self.verification_codes = {}
            self.save_verification_codes()
    
    def save_verification_codes(self):
        """Save verification codes to file"""
        try:
            with open(self.verification_codes_file, 'w', encoding='utf-8') as f:
                json.dump(self.verification_codes, f, indent=2, ensure_ascii=False)
            return True
        except Exception as e:
            print(f"❌ Error saving verification codes: {e}")
            return False
    
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
            "email_verified": True  # Admin email is pre-verified
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
    
    def generate_verification_code(self, username, purpose="email_verification"):
        """Generate and store a verification code"""
        code = str(uuid.uuid4())[:8].upper()  # 8-character code
        expires = datetime.now() + timedelta(hours=1)  # 1 hour expiry
        
        self.verification_codes[code] = {
            "username": username,
            "purpose": purpose,
            "expires": expires.isoformat(),
            "used": False
        }
        
        self.save_verification_codes()
        return code
    
    def verify_code(self, code, username, purpose="email_verification"):
        """Verify a verification code"""
        if code not in self.verification_codes:
            return False, "Invalid verification code"
        
        code_data = self.verification_codes[code]
        
        # Check if code is expired
        expires = datetime.fromisoformat(code_data["expires"])
        if datetime.now() > expires:
            del self.verification_codes[code]
            self.save_verification_codes()
            return False, "Verification code has expired"
        
        # Check if code is already used
        if code_data["used"]:
            return False, "Verification code has already been used"
        
        # Check if code matches username and purpose
        if code_data["username"] != username or code_data["purpose"] != purpose:
            return False, "Invalid verification code"
        
        # Mark code as used
        self.verification_codes[code]["used"] = True
        self.save_verification_codes()
        
        return True, "Verification successful"
    
    def register_user(self, username, password, name, email, plan="trial"):
        """Register new user with email verification"""
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
        
        # Create user with email not verified
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
            "email_verified": False  # Email not verified yet
        }
        
        # Generate verification code
        verification_code = self.generate_verification_code(username, "email_verification")
        
        # Send verification email
        user_data = self.users[username]
        email_sent, email_message = email_service.send_verification_email(user_data, verification_code)
        
        if not email_sent:
            # Remove user if email sending failed
            del self.users[username]
            return False, f"Failed to send verification email: {email_message}"
        
        # Update analytics
        if 'user_registrations' not in self.analytics:
            self.analytics['user_registrations'] = []
        
        self.analytics["user_registrations"].append({
            "username": username,
            "plan": plan,
            "timestamp": datetime.now().isoformat(),
            "email_verification_sent": True
        })
        
        # Save both files
        users_saved = self.save_users()
        analytics_saved = self.save_analytics()
        
        if users_saved and analytics_saved:
            print(f"✅ Successfully registered user: {username}")
            return True, f"Account created successfully! Verification email sent to {email}. Please check your inbox."
        else:
            # Remove the user if save failed
            if username in self.users:
                del self.users[username]
            return False, "Error saving user data. Please try again."

    def verify_email(self, username, verification_code):
        """Verify user's email address"""
        if username not in self.users:
            return False, "User not found"
        
        success, message = self.verify_code(verification_code, username, "email_verification")
        
        if success:
            self.users[username]["email_verified"] = True
            
            # Update analytics
            if 'email_verifications' not in self.analytics:
                self.analytics['email_verifications'] = []
            
            self.analytics['email_verifications'].append({
                "username": username,
                "timestamp": datetime.now().isoformat()
            })
            
            if self.save_users() and self.save_analytics():
                return True, "Email verified successfully! You can now login."
            else:
                return False, "Error saving verification status"
        
        return False, message

    def resend_verification_email(self, username):
        """Resend verification email"""
        if username not in self.users:
            return False, "User not found"
        
        if self.users[username]["email_verified"]:
            return False, "Email is already verified"
        
        # Generate new verification code
        verification_code = self.generate_verification_code(username, "email_verification")
        
        # Send verification email
        user_data = self.users[username]
        email_sent, email_message = email_service.send_verification_email(user_data, verification_code)
        
        if email_sent:
            return True, f"Verification email resent to {user_data['email']}"
        else:
            return False, f"Failed to resend verification email: {email_message}"

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
            "email_verified": True  # Test users are auto-verified
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
        
        # Send upgrade email if upgrading to premium
        if new_plan == "premium" and old_plan != "premium":
            email_service.send_plan_upgrade_email(user_data, old_plan, new_plan)
        
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
        """Authenticate user with email verification check"""
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
        
        # Check if email is verified
        if not user.get("email_verified", False):
            return False, "Email not verified. Please check your inbox for verification email."
        
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
        verified_users = sum(1 for u in self.users.values() if u.get('email_verified', False))
        
        plan_counts = {}
        for user in self.users.values():
            plan = user.get('plan', 'unknown')
            plan_counts[plan] = plan_counts.get(plan, 0) + 1
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "online_users": online_users,
            "verified_users": verified_users,
            "plan_distribution": plan_counts,
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
                    "email_verified": user_data.get("email_verified", False)
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
                "email_verified": user_data.get("email_verified", False)
            })
        return users_list

# Initialize user manager
user_manager = UserManager()

# -------------------------
# EMAIL VERIFICATION INTERFACE
# -------------------------
def render_email_verification():
    """Email verification interface for new users"""
    st.title("📧 Verify Your Email Address")
    st.markdown("---")
    
    if not st.session_state.pending_verification_user:
        st.error("No pending verification found. Please register again.")
        if st.button("⬅️ Back to Login"):
            st.session_state.email_verification_pending = False
            st.session_state.pending_verification_user = None
            st.rerun()
        return
    
    username = st.session_state.pending_verification_user
    user_data = user_manager.users.get(username, {})
    
    st.info(f"**Verification required for:** {user_data.get('name', username)}")
    st.write(f"**Email:** {user_data.get('email', 'N/A')}")
    st.write(f"**Username:** {username}")
    
    st.markdown("---")
    
    # Verification code input
    with st.form("email_verification_form"):
        st.subheader("Enter Verification Code")
        st.write("Check your email for the verification code we sent you.")
        
        verification_code = st.text_input(
            "Verification Code*",
            placeholder="Enter the 8-digit code from your email",
            help="The code is case-sensitive and expires in 1 hour"
        ).strip().upper()
        
        col1, col2 = st.columns(2)
        with col1:
            verify_submitted = st.form_submit_button("✅ Verify Email", use_container_width=True)
        with col2:
            resend_submitted = st.form_submit_button("🔄 Resend Code", use_container_width=True)
        
        if verify_submitted:
            if not verification_code:
                st.error("❌ Please enter the verification code")
            else:
                with st.spinner("Verifying..."):
                    success, message = user_manager.verify_email(username, verification_code)
                    if success:
                        st.success(f"✅ {message}")
                        st.balloons()
                        time.sleep(2)
                        st.session_state.email_verification_pending = False
                        st.session_state.pending_verification_user = None
                        st.rerun()
                    else:
                        st.error(f"❌ {message}")
        
        if resend_submitted:
            with st.spinner("Resending verification code..."):
                success, message = user_manager.resend_verification_email(username)
                if success:
                    st.success(f"✅ {message}")
                else:
                    st.error(f"❌ {message}")
    
    st.markdown("---")
    
    # Troubleshooting section
    with st.expander("❓ Having trouble receiving the email?"):
        st.markdown("""
        **Common issues and solutions:**
        
        1. **Check spam/junk folder** - Sometimes verification emails get filtered
        2. **Wait a few minutes** - Email delivery can take 1-5 minutes
        3. **Verify email address** - Make sure you entered the correct email: `{}`
        4. **Resend the code** - Use the 'Resend Code' button above
        5. **Contact support** - If problems persist, email: `{}`
        """.format(user_data.get('email', 'N/A'), Config.SUPPORT_EMAIL))
    
    if st.button("⬅️ Back to Login", key="back_from_verification"):
        st.session_state.email_verification_pending = False
        st.session_state.pending_verification_user = None
        st.rerun()

# -------------------------
# EMAIL SETTINGS INTERFACE (ADMIN)
# -------------------------
def render_email_settings():
    """Admin interface for email/SMTP settings"""
    st.subheader("📧 Email & SMTP Configuration")
    
    # Back button
    if st.button("⬅️ Back to Admin Dashboard", key="back_email_settings"):
        st.session_state.show_email_settings = False
        st.rerun()
    
    st.markdown("---")
    
    # SMTP Configuration Form
    with st.form("smtp_config_form"):
        st.subheader("SMTP Server Settings")
        
        col1, col2 = st.columns(2)
        with col1:
            smtp_server = st.text_input(
                "SMTP Server*",
                value=Config.SMTP_SERVER,
                placeholder="smtp.gmail.com"
            )
            smtp_username = st.text_input(
                "SMTP Username/Email*",
                value=Config.SMTP_USERNAME,
                placeholder="your-email@gmail.com"
            )
        with col2:
            smtp_port = st.number_input(
                "SMTP Port*",
                value=Config.SMTP_PORT,
                min_value=1,
                max_value=65535
            )
            smtp_password = st.text_input(
                "SMTP Password*",
                type="password",
                value=Config.SMTP_PASSWORD,
                placeholder="Your app password"
            )
        
        use_tls = st.checkbox("Use TLS (recommended)", value=Config.USE_TLS)
        test_mode = st.checkbox("Test Mode (simulate emails without sending)", value=email_service.test_mode)
        
        col1, col2 = st.columns(2)
        with col1:
            test_connection = st.form_submit_button("🔍 Test SMTP Connection", use_container_width=True)
        with col2:
            save_config = st.form_submit_button("💾 Save SMTP Settings", use_container_width=True)
        
        if test_connection:
            # Update service with current form values for testing
            temp_service = EmailService()
            temp_service.smtp_server = smtp_server
            temp_service.smtp_port = smtp_port
            temp_service.smtp_username = smtp_username
            temp_service.smtp_password = smtp_password
            temp_service.use_tls = use_tls
            temp_service.test_mode = test_mode
            
            success, message = temp_service.test_connection()
            if success:
                st.success(f"✅ {message}")
            else:
                st.error(f"❌ {message}")
        
        if save_config:
            # In a real application, you would save these to a config file
            st.warning("⚠️ SMTP configuration changes require application restart to take effect.")
            st.info("""
            **To update SMTP settings permanently:**
            1. Update the SMTP configuration in the Config class
            2. Restart the application
            3. Test the connection
            """)
    
    st.markdown("---")
    
    # Email Statistics
    st.subheader("📊 Email Statistics")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        total_verifications = len(user_manager.analytics.get("email_verifications", []))
        st.metric("Email Verifications", total_verifications)
    with col2:
        verified_users = sum(1 for u in user_manager.users.values() if u.get('email_verified', False))
        st.metric("Verified Users", verified_users)
    with col3:
        pending_verifications = sum(1 for u in user_manager.users.values() if not u.get('email_verified', False) and u.get('is_active', True))
        st.metric("Pending Verifications", pending_verifications)
    
    # Recent email activity
    st.markdown("#### Recent Email Activity")
    recent_verifications = user_manager.analytics.get("email_verifications", [])[-10:]
    if recent_verifications:
        for verification in reversed(recent_verifications):
            st.write(f"• {verification['username']} - {verification['timestamp'][:16]}")
    else:
        st.info("No email verification activity yet")
    
    st.markdown("---")
    
    # Manual email sending (admin tool)
    st.subheader("🛠️ Manual Email Tool")
    
    with st.form("manual_email_form"):
        st.write("Send a custom email to any user")
        
        user_emails = {user['email']: user['username'] for user in user_manager.users.values() if user.get('email')}
        selected_email = st.selectbox("Recipient Email", [""] + list(user_emails.keys()))
        
        subject = st.text_input("Subject", placeholder="Email subject...")
        message = st.text_area("Message", height=150, placeholder="Email content...")
        
        if st.form_submit_button("📤 Send Manual Email", use_container_width=True):
            if not all([selected_email, subject, message]):
                st.error("❌ Please fill all fields")
            else:
                # Create simple HTML email
                html_content = f"""
                <!DOCTYPE html>
                <html>
                <body>
                    <h2>{subject}</h2>
                    <p>{message.replace(chr(10), '<br>')}</p>
                    <hr>
                    <p><em>Sent from {Config.APP_NAME} Admin Panel</em></p>
                </body>
                </html>
                """
                
                success, msg = email_service.send_email(selected_email, subject, html_content, message)
                if success:
                    st.success(f"✅ Email sent to {selected_email}")
                else:
                    st.error(f"❌ {msg}")

# -------------------------
# USER CREDENTIALS MANAGEMENT INTERFACE
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
        
        col1, col2 = st.columns(2)
        
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
            st.write(f"**Email Verified:** {'✅ Yes' if user_data.get('email_verified', False) else '❌ No'}")
            st.write(f"**Expires:** {user_data.get('expires', 'N/A')}")

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
# ADMIN DASHBOARD - COMPLETE VERSION WITH EMAIL SETTINGS
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
            st.session_state.show_email_settings = False
            st.session_state.admin_view = "analytics"
            st.rerun()
        
        if st.button("👥 Manage Users", use_container_width=True, key="sidebar_users"):
            # Clear any modal/management states first
            st.session_state.show_delete_confirmation = False
            st.session_state.show_bulk_delete = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.show_user_credentials = False
            st.session_state.show_email_settings = False
            st.session_state.admin_view = "users"
            st.rerun()
        
        if st.button("🔐 User Credentials", use_container_width=True, key="sidebar_credentials"):
            # Clear any modal/management states first
            st.session_state.show_delete_confirmation = False
            st.session_state.show_bulk_delete = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.show_user_credentials = True
            st.session_state.show_email_settings = False
            st.rerun()
        
        if st.button("📧 Email Settings", use_container_width=True, key="sidebar_email"):
            # Clear any modal/management states first
            st.session_state.show_delete_confirmation = False
            st.session_state.show_bulk_delete = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.show_user_credentials = False
            st.session_state.show_email_settings = True
            st.rerun()
        
        if st.button("🗑️ Bulk Delete", use_container_width=True, key="sidebar_bulk_delete"):
            # Clear any modal/management states first
            st.session_state.show_delete_confirmation = False
            st.session_state.manage_user_plan = None
            st.session_state.show_password_change = False
            st.session_state.show_user_credentials = False
            st.session_state.show_email_settings = False
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
            st.session_state.show_email_settings = False
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
    
    # Show email settings interface if needed
    if st.session_state.get('show_email_settings'):
        render_email_settings()
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
        st.metric("Verified Users", metrics["verified_users"])
    
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
                verification_status = "✅" if reg.get('email_verification_sent') else "❌"
                st.write(f"• {reg['username']} - {plan_name} {verification_status}")
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
    
    col1, col2, col3 = st.columns(3)
    with col1:
        total_verifications = len(user_manager.analytics.get("email_verifications", []))
        st.metric("Total Verifications", total_verifications)
    with col2:
        verified_users = sum(1 for u in user_manager.users.values() if u.get('email_verified', False))
        st.metric("Verified Users", verified_users)
    with col3:
        pending_verifications = sum(1 for u in user_manager.users.values() if not u.get('email_verified', False) and u.get('is_active', True))
        st.metric("Pending Verifications", pending_verifications)
    
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
    
    # User actions - UPDATED WITH EMAIL SETTINGS
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        if st.button("🔄 Refresh User List", use_container_width=True, key="um_refresh"):
            st.rerun()
    with col2:
        if st.button("🔐 User Credentials", use_container_width=True, key="um_credentials"):
            st.session_state.show_user_credentials = True
            st.rerun()
    with col3:
        if st.button("📧 Email Settings", use_container_width=True, key="um_email"):
            st.session_state.show_email_settings = True
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
                st.caption("✅ Verified" if user_data.get('email_verified') else "❌ Unverified")
            
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
    
    # Show email verification interface if pending
    if st.session_state.email_verification_pending:
        render_email_verification()
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
                            st.success(f"✅ {message}")
                            # Set verification pending state
                            st.session_state.email_verification_pending = True
                            st.session_state.pending_verification_user = new_username
                            st.rerun()
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
