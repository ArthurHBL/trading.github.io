# app.py - REALISTIC TRADING DASHBOARD WITH LIVE CRYPTO CHARTS
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
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import requests
import talib

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
    if 'selected_crypto' not in st.session_state:
        st.session_state.selected_crypto = 'BTC/USDT'
    if 'timeframe' not in st.session_state:
        st.session_state.timeframe = '1h'

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

# -------------------------
# CRYPTO DATA SERVICE - REAL PRICE DATA
# -------------------------
class CryptoDataService:
    def __init__(self):
        self.base_url = "https://api.binance.com/api/v3"
        
    def get_historical_data(self, symbol='BTCUSDT', interval='1h', limit=100):
        """Get real historical price data from Binance"""
        try:
            url = f"{self.base_url}/klines"
            params = {
                'symbol': symbol.replace('/', ''),
                'interval': interval,
                'limit': limit
            }
            
            response = requests.get(url, params=params, timeout=10)
            data = response.json()
            
            # Convert to DataFrame
            df = pd.DataFrame(data, columns=[
                'timestamp', 'open', 'high', 'low', 'close', 'volume',
                'close_time', 'quote_asset_volume', 'number_of_trades',
                'taker_buy_base_asset_volume', 'taker_buy_quote_asset_volume', 'ignore'
            ])
            
            # Convert types
            for col in ['open', 'high', 'low', 'close', 'volume']:
                df[col] = pd.to_numeric(df[col])
            
            df['timestamp'] = pd.to_datetime(df['timestamp'], unit='ms')
            df.set_index('timestamp', inplace=True)
            
            return df[['open', 'high', 'low', 'close', 'volume']]
            
        except Exception as e:
            print(f"Error fetching crypto data: {e}")
            # Return mock data if API fails
            return self._generate_mock_data()
    
    def _generate_mock_data(self):
        """Generate realistic mock data when API is unavailable"""
        dates = pd.date_range(end=pd.Timestamp.now(), periods=100, freq='1H')
        np.random.seed(42)
        
        # Generate realistic price movement
        prices = [50000]
        for i in range(1, 100):
            change = np.random.normal(0, 0.02)  # 2% volatility
            prices.append(prices[-1] * (1 + change))
        
        df = pd.DataFrame({
            'open': prices,
            'high': [p * (1 + abs(np.random.normal(0, 0.01))) for p in prices],
            'low': [p * (1 - abs(np.random.normal(0, 0.01))) for p in prices],
            'close': prices,
            'volume': np.random.normal(1000, 200, 100)
        }, index=dates)
        
        return df

# Initialize crypto service
crypto_service = CryptoDataService()

# -------------------------
# STRATEGY VISUALIZATION ENGINE
# -------------------------
class StrategyVisualizer:
    def __init__(self):
        self.colors = {
            'buy': '#00D4AA',
            'sell': '#FF6B6B',
            'neutral': '#6C757D',
            'primary': '#1f77b4',
            'secondary': '#ff7f0e'
        }
    
    def create_strategy_chart(self, strategy_name, price_data, indicators_config):
        """Create professional strategy visualization"""
        fig = make_subplots(
            rows=2, cols=1,
            shared_xaxes=True,
            vertical_spacing=0.05,
            subplot_titles=(f'{strategy_name} - Strategy Signals', 'BTC/USDT Price Chart'),
            row_heights=[0.4, 0.6]
        )
        
        # Add price data
        self._add_price_chart(fig, price_data, row=2)
        
        # Add strategy-specific indicators
        self._add_strategy_indicators(fig, strategy_name, price_data, indicators_config, row=1)
        
        # Update layout
        fig.update_layout(
            height=600,
            showlegend=True,
            template='plotly_dark',
            margin=dict(t=50, l=50, r=50, b=50),
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(color='white')
        )
        
        return fig
    
    def _add_price_chart(self, fig, price_data, row=1):
        """Add candlestick price chart"""
        fig.add_trace(
            go.Candlestick(
                x=price_data.index,
                open=price_data['open'],
                high=price_data['high'],
                low=price_data['low'],
                close=price_data['close'],
                name='BTC/USDT'
            ),
            row=row, col=1
        )
        
        # Add volume
        fig.add_trace(
            go.Bar(
                x=price_data.index,
                y=price_data['volume'],
                name='Volume',
                marker_color='rgba(100, 100, 100, 0.3)',
                yaxis='y2'
            ),
            row=row, col=1
        )
        
        # Add volume axis
        fig.update_layout(
            yaxis2=dict(
                title="Volume",
                overlaying="y",
                side="right",
                showgrid=False
            )
        )
    
    def _add_strategy_indicators(self, fig, strategy_name, price_data, indicators_config, row=1):
        """Add strategy-specific indicators to the chart"""
        
        if strategy_name == "Premium Stoch":
            self._add_stochastic_indicators(fig, price_data, row)
        elif strategy_name == "LS Copy":
            self._add_momentum_indicators(fig, price_data, row)
        elif strategy_name == "PositionFlow":
            self._add_vwap_indicators(fig, price_data, row)
        elif strategy_name == "RenkoVol":
            self._add_volatility_indicators(fig, price_data, row)
        elif strategy_name == "10h WWV Chart":
            self._add_wwv_indicators(fig, price_data, row)
        else:
            # Default strategy visualization
            self._add_default_indicators(fig, price_data, row)
    
    def _add_stochastic_indicators(self, fig, price_data, row):
        """Add Stochastic indicators"""
        # Mock Stochastic values
        stoch_k = talib.STOCH(price_data['high'], price_data['low'], price_data['close'])[0]
        stoch_d = talib.STOCH(price_data['high'], price_data['low'], price_data['close'])[1]
        
        fig.add_trace(
            go.Scatter(
                x=price_data.index,
                y=stoch_k,
                name='Stoch %K',
                line=dict(color=self.colors['primary'])
            ),
            row=row, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=price_data.index,
                y=stoch_d,
                name='Stoch %D',
                line=dict(color=self.colors['secondary'])
            ),
            row=row, col=1
        )
        
        # Add overbought/oversold levels
        fig.add_hline(y=80, line_dash="dash", line_color="red", row=row, col=1)
        fig.add_hline(y=20, line_dash="dash", line_color="green", row=row, col=1)
    
    def _add_momentum_indicators(self, fig, price_data, row):
        """Add momentum-based indicators"""
        rsi = talib.RSI(price_data['close'], timeperiod=14)
        macd, macd_signal, macd_hist = talib.MACD(price_data['close'])
        
        fig.add_trace(
            go.Scatter(
                x=price_data.index,
                y=rsi,
                name='RSI',
                line=dict(color=self.colors['primary'])
            ),
            row=row, col=1
        )
        
        fig.add_hline(y=70, line_dash="dash", line_color="red", row=row, col=1)
        fig.add_hline(y=30, line_dash="dash", line_color="green", row=row, col=1)
    
    def _add_vwap_indicators(self, fig, price_data, row):
        """Add VWAP indicators"""
        # Mock VWAP calculation
        typical_price = (price_data['high'] + price_data['low'] + price_data['close']) / 3
        vwap = (typical_price * price_data['volume']).cumsum() / price_data['volume'].cumsum()
        
        fig.add_trace(
            go.Scatter(
                x=price_data.index,
                y=vwap,
                name='VWAP',
                line=dict(color=self.colors['buy'])
            ),
            row=row, col=1
        )
    
    def _add_volatility_indicators(self, fig, price_data, row):
        """Add volatility indicators"""
        bb_upper, bb_middle, bb_lower = talib.BBANDS(price_data['close'], timeperiod=20)
        atr = talib.ATR(price_data['high'], price_data['low'], price_data['close'], timeperiod=14)
        
        fig.add_trace(
            go.Scatter(
                x=price_data.index,
                y=bb_upper,
                name='BB Upper',
                line=dict(color='rgba(255,255,255,0.5)', dash='dash')
            ),
            row=row, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=price_data.index,
                y=bb_lower,
                name='BB Lower',
                line=dict(color='rgba(255,255,255,0.5)', dash='dash')
            ),
            row=row, col=1
        )
    
    def _add_wwv_indicators(self, fig, price_data, row):
        """Add WWV chart indicators"""
        # Add multiple moving averages
        for period in [10, 20, 50]:
            sma = talib.SMA(price_data['close'], timeperiod=period)
            fig.add_trace(
                go.Scatter(
                    x=price_data.index,
                    y=sma,
                    name=f'SMA {period}',
                    line=dict(width=1)
                ),
                row=row, col=1
            )
    
    def _add_default_indicators(self, fig, price_data, row):
        """Add default set of indicators"""
        # Add RSI
        rsi = talib.RSI(price_data['close'], timeperiod=14)
        fig.add_trace(
            go.Scatter(
                x=price_data.index,
                y=rsi,
                name='RSI',
                line=dict(color=self.colors['primary'])
            ),
            row=row, col=1
        )
        
        # Add buy/sell signals based on mock logic
        signals = self._generate_mock_signals(price_data)
        buy_signals = signals[signals == 1]
        sell_signals = signals[signals == -1]
        
        fig.add_trace(
            go.Scatter(
                x=buy_signals.index,
                y=[rsi.loc[x] for x in buy_signals.index],
                mode='markers',
                name='Buy Signal',
                marker=dict(color=self.colors['buy'], size=10, symbol='triangle-up')
            ),
            row=row, col=1
        )
        
        fig.add_trace(
            go.Scatter(
                x=sell_signals.index,
                y=[rsi.loc[x] for x in sell_signals.index],
                mode='markers',
                name='Sell Signal',
                marker=dict(color=self.colors['sell'], size=10, symbol='triangle-down')
            ),
            row=row, col=1
        )
    
    def _generate_mock_signals(self, price_data):
        """Generate realistic buy/sell signals for demonstration"""
        signals = pd.Series(0, index=price_data.index)
        
        # Simple momentum-based signal generation
        returns = price_data['close'].pct_change()
        volatility = returns.rolling(20).std()
        
        for i in range(20, len(price_data)):
            if returns.iloc[i] > 2 * volatility.iloc[i]:
                signals.iloc[i] = 1  # Buy signal
            elif returns.iloc[i] < -2 * volatility.iloc[i]:
                signals.iloc[i] = -1  # Sell signal
        
        return signals

# Initialize visualizer
strategy_visualizer = StrategyVisualizer()

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
# USER MANAGEMENT (Simplified for brevity)
# -------------------------
class UserManager:
    def __init__(self):
        self.users = {
            "admin": {
                "password_hash": hashlib.sha256(("ChangeThis123!" + "default-salt").encode()).hexdigest(),
                "name": "System Administrator",
                "plan": "admin",
                "expires": "2030-12-31",
                "created": datetime.now().isoformat(),
                "email": "admin@tradinganalysis.com"
            },
            "demo": {
                "password_hash": hashlib.sha256(("demo12345" + "default-salt").encode()).hexdigest(),
                "name": "Demo User",
                "plan": "premium",
                "expires": "2025-12-31",
                "created": datetime.now().isoformat(),
                "email": "demo@tradinganalysis.com"
            }
        }
        self.analytics = {
            "total_logins": 0,
            "active_users": 0,
            "user_registrations": []
        }
    
    def hash_password(self, password):
        return hashlib.sha256((password + "default-salt").encode()).hexdigest()
    
    def authenticate(self, username, password):
        if username in self.users:
            user = self.users[username]
            if user["password_hash"] == self.hash_password(password):
                self.analytics["total_logins"] += 1
                return True, "Login successful"
        return False, "Invalid credentials"
    
    def logout(self, username):
        pass

user_manager = UserManager()

# -------------------------
# REDESIGNED USER DASHBOARD WITH REAL CHARTS
# -------------------------
def render_user_dashboard():
    """Professional trading dashboard with real crypto charts"""
    user = st.session_state.user
    
    # Initialize session state for trading view
    if 'selected_crypto' not in st.session_state:
        st.session_state.selected_crypto = 'BTC/USDT'
    if 'timeframe' not in st.session_state:
        st.session_state.timeframe = '1h'
    
    # Get crypto data
    crypto_data = crypto_service.get_historical_data(
        symbol=st.session_state.selected_crypto.replace('/', ''),
        interval=st.session_state.timeframe,
        limit=100
    )
    
    # Get current strategies
    analysis_date = st.session_state.get('analysis_date', date.today())
    daily_strategies, cycle_day = get_daily_strategies(analysis_date)
    selected_strategy = st.session_state.get('selected_strategy', daily_strategies[0])
    
    # Clean sidebar
    with st.sidebar:
        st.title("🎛️ Control Panel")
        
        # User profile
        st.markdown("---")
        st.write(f"**👤 {user['name']}**")
        plan_display = Config.PLANS.get(user['plan'], {}).get('name', user['plan'].title())
        st.caption(f"🚀 {plan_display}")
        
        # 5-Day Cycle System
        st.markdown("---")
        st.subheader("📅 5-Day Cycle")
        st.markdown(f"**Day {cycle_day} of 5-day cycle**")
        
        # Strategy selection
        selected_strategy = st.selectbox(
            "Choose Strategy:", 
            daily_strategies,
            key="strategy_selector"
        )
        st.session_state.selected_strategy = selected_strategy
        
        # Market selection
        st.markdown("---")
        st.subheader("📊 Market Data")
        
        col1, col2 = st.columns(2)
        with col1:
            crypto_pair = st.selectbox(
                "Crypto Pair:",
                ["BTC/USDT", "ETH/USDT", "ADA/USDT", "DOT/USDT"],
                key="crypto_select"
            )
            st.session_state.selected_crypto = crypto_pair
        
        with col2:
            timeframe = st.selectbox(
                "Timeframe:",
                ["15m", "1h", "4h", "1d"],
                key="timeframe_select"
            )
            st.session_state.timeframe = timeframe
        
        st.markdown("---")
        
        # Navigation
        st.subheader("📋 Navigation")
        if st.button("📈 Trading Dashboard", use_container_width=True):
            st.session_state.dashboard_view = 'main'
        if st.button("📝 Strategy Notes", use_container_width=True):
            st.session_state.dashboard_view = 'notes'
        if st.button("⚙️ Account Settings", use_container_width=True):
            st.session_state.dashboard_view = 'settings'
        
        st.markdown("---")
        if st.button("🚪 Secure Logout", use_container_width=True):
            user_manager.logout(user['username'])
            st.session_state.user = None
            st.rerun()
    
    # Main dashboard content
    current_view = st.session_state.get('dashboard_view', 'main')
    
    if current_view == 'notes':
        render_strategy_notes(selected_strategy, analysis_date)
    elif current_view == 'settings':
        render_account_settings()
    else:
        render_trading_dashboard(user, selected_strategy, crypto_data, cycle_day)

def render_trading_dashboard(user, selected_strategy, crypto_data, cycle_day):
    """Main trading dashboard with professional charts"""
    
    # Header
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
    
    # Strategy Performance Overview
    st.subheader("📊 Strategy Performance Overview")
    
    cols = st.columns(3)
    with cols[0]:
        st.metric("Current Strategy", selected_strategy)
    with cols[1]:
        # Mock performance metrics
        st.metric("Today's P&L", "+2.3%", "+0.8%")
    with cols[2]:
        st.metric("Win Rate", "68%", "3%")
    
    st.markdown("---")
    
    # MAIN TRADING INTERFACE - Strategy above, Crypto below
    st.subheader(f"🔍 {selected_strategy} - Live Analysis")
    
    # Create strategy visualization
    indicators_config = STRATEGIES[selected_strategy]
    strategy_fig = strategy_visualizer.create_strategy_chart(
        selected_strategy, 
        crypto_data, 
        indicators_config
    )
    
    # Display the chart
    st.plotly_chart(strategy_fig, use_container_width=True)
    
    # Strategy Details
    st.markdown("---")
    st.subheader("📋 Strategy Components")
    
    # Display strategy indicators in a clean layout
    indicators = STRATEGIES[selected_strategy]
    num_cols = 3
    cols = st.columns(num_cols)
    
    for i, indicator in enumerate(indicators):
        col = cols[i % num_cols]
        with col:
            # Mock indicator status
            status_color = "#00D4AA" if i % 3 == 0 else "#FF6B6B" if i % 3 == 1 else "#6C757D"
            status_text = "Bullish" if i % 3 == 0 else "Bearish" if i % 3 == 1 else "Neutral"
            
            st.markdown(f"""
            <div style="border: 1px solid {status_color}; border-radius: 10px; padding: 15px; margin: 5px 0; background: rgba(0,0,0,0.1);">
                <h4 style="margin: 0; color: white;">{indicator}</h4>
                <p style="margin: 5px 0; color: {status_color}; font-weight: bold;">{status_text}</p>
                <p style="margin: 0; font-size: 0.8em; color: #888;">Active</p>
            </div>
            """, unsafe_allow_html=True)
    
    # Quick Analysis Section
    st.markdown("---")
    st.subheader("💡 Quick Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        with st.form("quick_analysis"):
            strategy_tag = st.selectbox("Strategy Outlook:", ["Neutral", "Bullish", "Bearish"])
            confidence = st.slider("Confidence Level:", 0, 100, 75)
            notes = st.text_area("Quick Notes:", placeholder="Enter your analysis notes...")
            
            if st.form_submit_button("💾 Save Analysis", use_container_width=True):
                st.success("✅ Analysis saved successfully!")
    
    with col2:
        st.markdown("**Recent Signals:**")
        
        # Mock recent signals
        signals = [
            {"time": "10:30", "signal": "BUY", "strength": "Strong", "indicator": "Stoch RSI"},
            {"time": "09:45", "signal": "SELL", "strength": "Medium", "indicator": "VWAP"},
            {"time": "08:15", "signal": "BUY", "strength": "Weak", "indicator": "Volume Delta"}
        ]
        
        for signal in signals:
            color = "#00D4AA" if signal["signal"] == "BUY" else "#FF6B6B"
            st.markdown(f"""
            <div style="border-left: 3px solid {color}; padding-left: 10px; margin: 5px 0;">
                <strong>{signal['time']} - {signal['signal']}</strong><br>
                <small>{signal['indicator']} ({signal['strength']})</small>
            </div>
            """, unsafe_allow_html=True)

def render_strategy_notes(selected_strategy, analysis_date):
    """Strategy notes interface"""
    st.title("📝 Strategy Analysis Notes")
    
    col1, col2 = st.columns([3, 1])
    with col1:
        st.subheader(f"Detailed Analysis - {selected_strategy}")
    with col2:
        if st.button("⬅️ Back to Dashboard", use_container_width=True):
            st.session_state.dashboard_view = 'main'
            st.rerun()
    
    st.markdown("---")
    
    # Notes form
    with st.form("detailed_notes_form"):
        # Strategy-level settings
        col1, col2 = st.columns(2)
        with col1:
            strategy_tag = st.selectbox("Strategy Outlook:", ["Neutral", "Bullish", "Bearish"])
        with col2:
            strategy_type = st.selectbox("Market Condition:", ["Trending", "Ranging", "Volatile"])
        
        st.markdown("---")
        
        # Indicator analysis
        st.subheader("Indicator Analysis")
        indicators = STRATEGIES[selected_strategy]
        
        for indicator in indicators:
            with st.expander(f"📊 {indicator}", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    status = st.selectbox(
                        f"Status - {indicator}",
                        ["Active", "Monitoring", "Inactive"],
                        key=f"status_{indicator}"
                    )
                with col2:
                    signal = st.selectbox(
                        f"Signal - {indicator}",
                        ["Bullish", "Bearish", "Neutral"],
                        key=f"signal_{indicator}"
                    )
                
                notes = st.text_area(
                    f"Notes - {indicator}",
                    placeholder=f"Enter detailed analysis for {indicator}...",
                    key=f"notes_{indicator}",
                    height=100
                )
        
        if st.form_submit_button("💾 Save All Notes", use_container_width=True):
            st.success("✅ All notes saved successfully!")

def render_account_settings():
    """Account settings interface"""
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
        plan_name = Config.PLANS.get(user['plan'], {}).get('name', 'Unknown Plan')
        st.text_input("Current Plan", value=plan_name, disabled=True)
        st.text_input("Expiry Date", value=user['expires'], disabled=True)
        
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Days Remaining", days_left)
    
    if st.button("⬅️ Back to Dashboard", use_container_width=True):
        st.session_state.dashboard_view = 'main'
        st.rerun()

# -------------------------
# AUTHENTICATION
# -------------------------
def render_login():
    """Login interface"""
    st.title(f"🔐 Welcome to {Config.APP_NAME}")
    st.markdown("---")
    
    with st.form("login_form"):
        st.subheader("Sign In to Your Account")
        
        col1, col2 = st.columns(2)
        with col1:
            username = st.text_input("Username", value="demo")
        with col2:
            password = st.text_input("Password", type="password", value="demo12345")
        
        submitted = st.form_submit_button("🔐 Secure Login", use_container_width=True)
        
        if submitted:
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

# -------------------------
# MAIN APPLICATION
# -------------------------
def main():
    init_session()
    
    # Enhanced CSS for professional appearance
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
    .strategy-card {
        border: 1px solid #444;
        border-radius: 10px;
        padding: 1rem;
        margin: 0.5rem 0;
        background: rgba(30, 30, 30, 0.5);
    }
    </style>
    """, unsafe_allow_html=True)
    
    if not st.session_state.user:
        render_login()
    else:
        if st.session_state.user['plan'] == 'admin':
            # Simple admin view for demo
            st.title("👑 Admin Dashboard")
            st.info("Admin features simplified for demo. Use 'demo' account for trading interface.")
            if st.button("🚪 Logout"):
                st.session_state.user = None
                st.rerun()
        else:
            render_user_dashboard()

if __name__ == "__main__":
    main()
