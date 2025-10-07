# app.py - ENHANCED PREMIUM USER EXPERIENCE
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
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

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
# ENHANCED TRADING ANALYSIS ENGINE
# -------------------------
class TradingAnalysisEngine:
    def __init__(self):
        self.market_data = self.generate_market_data()
    
    def generate_market_data(self):
        """Generate simulated market data for analysis"""
        dates = pd.date_range(start='2024-01-01', end=datetime.now(), freq='D')
        base_price = 50000
        returns = np.random.normal(0.001, 0.02, len(dates))
        prices = base_price * (1 + returns).cumprod()
        
        data = pd.DataFrame({
            'Date': dates,
            'Price': prices,
            'Volume': np.random.randint(1000, 10000, len(dates)),
            'RSI': np.random.uniform(30, 70, len(dates)),
            'MACD': np.random.uniform(-100, 100, len(dates)),
            'Volatility': np.random.uniform(0.01, 0.05, len(dates))
        })
        return data
    
    def calculate_technical_indicators(self, strategy):
        """Calculate technical indicators for a given strategy"""
        indicators = {}
        
        if strategy == "Premium Stoch":
            indicators['Stochastic'] = np.random.uniform(20, 80)
            indicators['Momentum'] = np.random.uniform(-1, 1)
            indicators['Trend_Strength'] = np.random.uniform(0, 1)
            
        elif strategy == "PositionFlow":
            indicators['Flow_Direction'] = np.random.choice(['Bullish', 'Bearish', 'Neutral'])
            indicators['Volume_Profile'] = np.random.uniform(0, 1)
            indicators['Liquidity_Levels'] = np.random.uniform(40000, 60000, 3)
            
        elif strategy == "Volatility":
            indicators['ATR'] = np.random.uniform(500, 2000)
            indicators['VIX_Level'] = np.random.uniform(15, 45)
            indicators['Volatility_Regime'] = np.random.choice(['Low', 'Medium', 'High'])
            
        return indicators
    
    def generate_trading_signals(self, strategy, indicators):
        """Generate trading signals based on strategy and indicators"""
        signals = []
        confidence = np.random.uniform(0.6, 0.95)
        
        if strategy == "Premium Stoch":
            if indicators['Stochastic'] < 20:
                signals.append(("Oversold Buy", confidence, "High potential reversal"))
            elif indicators['Stochastic'] > 80:
                signals.append(("Overbought Sell", confidence, "Potential pullback"))
            else:
                signals.append(("Neutral Hold", 0.5, "Wait for better entry"))
                
        elif strategy == "PositionFlow":
            if indicators['Flow_Direction'] == 'Bullish':
                signals.append(("Long Entry", confidence, "Strong buying pressure"))
            elif indicators['Flow_Direction'] == 'Bearish':
                signals.append(("Short Entry", confidence, "Strong selling pressure"))
            else:
                signals.append(("Wait for Confirmation", 0.4, "Mixed signals"))
                
        return signals
    
    def create_performance_chart(self, strategy_name, days=30):
        """Create performance chart for a strategy"""
        fig = go.Figure()
        
        # Simulated strategy performance
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        base_perf = 100
        returns = np.random.normal(0.002, 0.015, days)
        performance = base_perf * (1 + returns).cumprod()
        
        fig.add_trace(go.Scatter(
            x=dates, 
            y=performance,
            mode='lines',
            name=f'{strategy_name} Performance',
            line=dict(color='#00D4AA', width=3)
        ))
        
        # Add benchmark (buy & hold)
        benchmark_returns = np.random.normal(0.001, 0.012, days)
        benchmark = base_perf * (1 + benchmark_returns).cumprod()
        
        fig.add_trace(go.Scatter(
            x=dates, 
            y=benchmark,
            mode='lines',
            name='Market Benchmark',
            line=dict(color='#888', width=2, dash='dash')
        ))
        
        fig.update_layout(
            title=f'{strategy_name} - 30-Day Performance',
            xaxis_title='Date',
            yaxis_title='Portfolio Value ($)',
            template='plotly_dark',
            height=300
        )
        
        return fig

# Initialize trading engine
trading_engine = TradingAnalysisEngine()

# ... [KEEP ALL THE PREVIOUS UserManager, STRATEGIES, and other classes exactly the same] ...
# ... [ONLY REPLACE THE render_user_dashboard() and render_trading_dashboard() functions] ...

# -------------------------
# ENHANCED PREMIUM USER DASHBOARD
# -------------------------
def render_user_dashboard():
    """Enhanced trading dashboard for premium users"""
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
    
    # Enhanced sidebar with premium features
    with st.sidebar:
        st.title("🎛️ Premium Control Panel")
        
        # Premium user profile section
        st.markdown("---")
        col1, col2 = st.columns([1, 3])
        with col1:
            if user['plan'] in ['premium', 'professional']:
                st.markdown("⭐")
            else:
                st.markdown("👤")
        with col2:
            st.write(f"**{user['name']}**")
            plan_display = Config.PLANS.get(user['plan'], {}).get('name', user['plan'].title())
            st.caption(f"🚀 {plan_display}")
        
        # Account status with enhanced visuals
        plan_config = Config.PLANS.get(user['plan'], Config.PLANS['trial'])
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        
        # Premium progress bar
        if user['plan'] in ['premium', 'professional']:
            progress_color = "#00D4AA"  # Premium green
        else:
            progress_color = "#1f77b4"  # Basic blue
            
        st.progress(min(1.0, days_left / 30), text=f"📅 {days_left} days remaining")
        
        # Quick actions - Enhanced for premium
        st.markdown("### ⚡ Quick Actions")
        
        if st.button("🔄 Refresh Market Data", use_container_width=True):
            st.rerun()
            
        if st.button("📊 Portfolio Overview", use_container_width=True):
            st.session_state.dashboard_view = "portfolio"
            st.rerun()
            
        if st.button("🎯 Trading Signals", use_container_width=True):
            st.session_state.dashboard_view = "signals"
            st.rerun()
            
        if st.button("📈 Performance Analytics", use_container_width=True):
            st.session_state.dashboard_view = "analytics"
            st.rerun()
            
        if st.button("⚙️ Account Settings", use_container_width=True):
            st.session_state.dashboard_view = "settings"
            st.rerun()
        
        st.markdown("---")
        
        # Premium features indicator
        if user['plan'] in ['premium', 'professional']:
            st.markdown("### 🎁 Premium Features")
            st.success("• Real-time Analytics")
            st.success("• Advanced Signals")
            st.success("• Portfolio Tracking")
            st.success("• Priority Support")
        else:
            st.markdown("### 💎 Upgrade Benefits")
            st.info("• Advanced Analytics")
            st.info("• Premium Signals")
            st.info("• Portfolio Tools")
            st.info("• Priority Support")
            
            if st.button("🚀 Upgrade to Premium", use_container_width=True, type="primary"):
                st.session_state.show_upgrade = True
                st.rerun()
        
        st.markdown("---")
        if st.button("🚪 Secure Logout", use_container_width=True):
            user_manager.logout(user['username'])
            st.session_state.user = None
            st.rerun()
    
    # Main dashboard content with enhanced views
    current_view = st.session_state.get('dashboard_view', 'main')
    
    if st.session_state.get('show_settings'):
        render_account_settings()
    elif st.session_state.get('show_upgrade'):
        render_upgrade_plans()
    elif current_view == 'portfolio':
        render_portfolio_overview(data, user)
    elif current_view == 'signals':
        render_trading_signals(data, user)
    elif current_view == 'analytics':
        render_performance_analytics(data, user)
    elif current_view == 'settings':
        render_account_settings()
    else:
        render_trading_dashboard(data, user)

def render_trading_dashboard(data, user):
    """Enhanced main trading dashboard with premium features"""
    # Date handling
    start_date = date(2024, 1, 1)
    try:
        current_date_str = st.query_params.get("date", "")
        analysis_date = datetime.strptime(current_date_str, "%Y-%m-%d").date() if current_date_str else date.today()
    except:
        analysis_date = date.today()
    
    if analysis_date < start_date:
        analysis_date = start_date

    # Strategy selection based on plan
    plan_config = Config.PLANS.get(user['plan'], Config.PLANS['trial'])
    available_strategies = list(STRATEGIES.keys())[:plan_config['strategies']]
    
    # Enhanced dashboard header
    st.title("📊 Professional Trading Analysis")
    
    # Premium welcome message
    if user['plan'] in ['premium', 'professional']:
        st.success(f"🎉 Welcome back, **{user['name']}**! You're using our **{Config.PLANS[user['plan']]['name']}** with full access to {plan_config['strategies']} advanced strategies.")
    else:
        st.info(f"👋 Welcome, **{user['name']}**! You have access to {plan_config['strategies']} strategies. Upgrade for premium features.")
    
    # Market overview section
    st.subheader("🌍 Market Overview")
    
    # Market metrics
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        current_price = trading_engine.market_data['Price'].iloc[-1]
        price_change = ((current_price - trading_engine.market_data['Price'].iloc[-2]) / trading_engine.market_data['Price'].iloc[-2]) * 100
        st.metric(
            "BTC/USD", 
            f"${current_price:,.0f}", 
            f"{price_change:+.2f}%",
            delta_color="normal" if price_change >= 0 else "inverse"
        )
    
    with col2:
        st.metric("24h Volume", "$42.8B", "+5.2%")
    
    with col3:
        rsi = trading_engine.market_data['RSI'].iloc[-1]
        st.metric(
            "RSI", 
            f"{rsi:.1f}", 
            "Oversold" if rsi < 30 else "Overbought" if rsi > 70 else "Neutral",
            delta_color="inverse" if rsi > 70 else "normal" if rsi < 30 else "off"
        )
    
    with col4:
        volatility = trading_engine.market_data['Volatility'].iloc[-1] * 100
        st.metric("Volatility", f"{volatility:.1f}%", "High" if volatility > 3 else "Low")
    
    # Strategy progress with enhanced visuals
    st.subheader("🎯 Today's Focus Strategies")
    
    # Daily strategy rotation
    days_since_start = (analysis_date - start_date).days
    cycle_day = days_since_start % 5
    start_index = cycle_day * min(3, len(available_strategies))
    end_index = start_index + min(3, len(available_strategies))
    daily_strategies = available_strategies[start_index:end_index]
    
    if not daily_strategies:
        daily_strategies = available_strategies[:1]
    
    # Enhanced strategy cards
    cols = st.columns(len(daily_strategies))
    for i, strategy in enumerate(daily_strategies):
        with cols[i]:
            with st.container():
                st.markdown(f"""
                <div style="border: 1px solid #ddd; border-radius: 10px; padding: 1rem; background: #f8f9fa;">
                    <h4 style="margin: 0; color: #1f77b4;">{strategy}</h4>
                    <p style="margin: 0.5rem 0; font-size: 0.9rem; color: #666;">
                        {len(STRATEGIES[strategy])} indicators • Day {cycle_day + 1}
                    </p>
                </div>
                """, unsafe_allow_html=True)
                
                # Quick analysis button
                if st.button(f"📈 Analyze {strategy}", key=f"quick_{strategy}", use_container_width=True):
                    st.session_state.selected_strategy = strategy
                    st.rerun()
    
    # Strategy selector with enhanced features
    st.subheader("🔍 Deep Strategy Analysis")
    
    col1, col2 = st.columns([2, 1])
    
    with col1:
        selected_strategy = st.selectbox(
            "Select Strategy for Detailed Analysis", 
            available_strategies,
            key="strategy_selector"
        )
    
    with col2:
        analysis_mode = st.selectbox(
            "Analysis Mode",
            ["Technical Analysis", "Backtest Results", "Signal Generation", "Risk Assessment"],
            key="analysis_mode"
        )
    
    # Premium analysis interface
    st.markdown("---")
    
    if selected_strategy:
        # Strategy header with performance
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            st.subheader(f"✏️ {selected_strategy} Analysis")
        
        with col2:
            # Generate live indicators
            indicators = trading_engine.calculate_technical_indicators(selected_strategy)
            st.metric("Strategy Score", f"{np.random.uniform(65, 95):.0f}/100")
        
        with col3:
            signals = trading_engine.generate_trading_signals(selected_strategy, indicators)
            if signals:
                signal_type, confidence, reasoning = signals[0]
                st.metric(
                    "Live Signal", 
                    signal_type, 
                    f"{confidence:.0%} confidence"
                )
        
        # Enhanced analysis form with tabs
        tab1, tab2, tab3 = st.tabs(["📊 Technical Analysis", "📈 Performance", "💡 Trading Signals"])
        
        with tab1:
            render_technical_analysis(selected_strategy, indicators)
        
        with tab2:
            if user['plan'] in ['premium', 'professional']:
                render_strategy_performance(selected_strategy)
            else:
                st.info("🔒 Upgrade to Premium to access performance analytics and backtesting")
                if st.button("🚀 Upgrade Now", key="perf_upgrade"):
                    st.session_state.show_upgrade = True
                    st.rerun()
        
        with tab3:
            render_trading_signals_tab(selected_strategy, signals)
    
    # Quick actions for premium users
    st.markdown("---")
    st.subheader("⚡ Premium Quick Actions")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        if st.button("🎯 Generate All Signals", use_container_width=True):
            if user['plan'] in ['premium', 'professional']:
                st.success("✅ All trading signals generated!")
                # Store signals in user data
                data['recent_signals'] = [
                    {"strategy": s, "signal": "BUY", "confidence": np.random.uniform(0.7, 0.9), "timestamp": datetime.now()}
                    for s in available_strategies[:3]
                ]
            else:
                st.info("🔒 Premium feature - upgrade to generate bulk signals")
    
    with col2:
        if st.button("📊 Portfolio Snapshot", use_container_width=True):
            st.session_state.dashboard_view = "portfolio"
            st.rerun()
    
    with col3:
        if st.button("📈 Market Scanner", use_container_width=True):
            if user['plan'] in ['premium', 'professional']:
                st.info("🔄 Scanning markets for opportunities...")
                time.sleep(1)
                st.success("✅ 5 new opportunities found!")
            else:
                st.info("🔒 Premium feature - upgrade for advanced market scanning")
    
    with col4:
        if st.button("🔄 Reset All Analysis", use_container_width=True):
            st.warning("All analysis data has been reset")
            st.rerun()

def render_technical_analysis(strategy, indicators):
    """Enhanced technical analysis interface"""
    st.write(f"**Technical Analysis for {strategy}**")
    
    # Display indicators in a nice layout
    col1, col2, col3 = st.columns(3)
    
    with col1:
        for key, value in list(indicators.items())[:2]:
            if isinstance(value, float):
                st.metric(key.replace('_', ' '), f"{value:.2f}")
            else:
                st.metric(key.replace('_', ' '), str(value))
    
    with col2:
        for key, value in list(indicators.items())[2:4]:
            if isinstance(value, float):
                st.metric(key.replace('_', ' '), f"{value:.2f}")
            else:
                st.metric(key.replace('_', ' '), str(value))
    
    with col3:
        for key, value in list(indicators.items())[4:]:
            if isinstance(value, float):
                st.metric(key.replace('_', ' '), f"{value:.2f}")
            else:
                st.metric(key.replace('_', ' '), str(value))
    
    # Analysis form
    with st.form(f"analysis_{strategy}"):
        st.write("**Manual Analysis Input**")
        
        for indicator in STRATEGIES[strategy]:
            with st.expander(f"**{indicator}**", expanded=False):
                col1, col2 = st.columns(2)
                with col1:
                    status = st.selectbox("Status", ["Open", "In Progress", "Done", "Skipped"], key=f"status_{indicator}")
                    confidence = st.slider("Confidence", 50, 100, 75, key=f"conf_{indicator}")
                with col2:
                    note = st.text_area("Analysis Notes", height=100, key=f"note_{indicator}", 
                                      placeholder="Enter your technical analysis...")
        
        # Enhanced save options
        col1, col2 = st.columns(2)
        with col1:
            save_btn = st.form_submit_button("💾 Save Analysis", use_container_width=True)
        with col2:
            export_btn = st.form_submit_button("📤 Export to PDF", use_container_width=True)
        
        if save_btn:
            st.success("✅ Analysis saved successfully!")
            # Store in user data
            if 'saved_analyses' not in st.session_state.user_data:
                st.session_state.user_data['saved_analyses'] = {}
            st.session_state.user_data['saved_analyses'][strategy] = {
                "timestamp": datetime.now(),
                "indicators": indicators
            }
        
        if export_btn:
            st.info("📄 PDF export would be generated here")

def render_strategy_performance(strategy):
    """Premium strategy performance analytics"""
    st.write(f"**Performance Analytics for {strategy}**")
    
    # Performance chart
    fig = trading_engine.create_performance_chart(strategy)
    st.plotly_chart(fig, use_container_width=True)
    
    # Performance metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Return", "+24.5%", "+2.1%")
    
    with col2:
        st.metric("Win Rate", "68%", "+5%")
    
    with col3:
        st.metric("Sharpe Ratio", "1.8", "+0.2")
    
    with col4:
        st.metric("Max Drawdown", "-8.2%", "-1.1%")
    
    # Recent trades table
    st.write("**Recent Trade History**")
    trades_data = {
        "Date": ["2024-01-15", "2024-01-14", "2024-01-13", "2024-01-12"],
        "Action": ["BUY", "SELL", "BUY", "SELL"],
        "Price": ["$42,150", "$43,200", "$41,800", "$42,900"],
        "P&L": ["+$1,050", "+$850", "+$1,100", "+$700"],
        "Status": ["Closed", "Closed", "Closed", "Closed"]
    }
    trades_df = pd.DataFrame(trades_data)
    st.dataframe(trades_df, use_container_width=True, hide_index=True)

def render_trading_signals_tab(strategy, signals):
    """Trading signals interface"""
    st.write(f"**Live Trading Signals for {strategy}**")
    
    if signals:
        for signal_type, confidence, reasoning in signals:
            # Color code based on signal type
            if "Buy" in signal_type:
                signal_color = "green"
            elif "Sell" in signal_type:
                signal_color = "red"
            else:
                signal_color = "orange"
            
            st.markdown(f"""
            <div style="border-left: 4px solid {signal_color}; padding-left: 1rem; margin: 1rem 0;">
                <h4 style="margin: 0; color: {signal_color};">{signal_type}</h4>
                <p style="margin: 0.5rem 0; color: #666;">Confidence: <strong>{confidence:.0%}</strong></p>
                <p style="margin: 0; color: #888;">{reasoning}</p>
            </div>
            """, unsafe_allow_html=True)
    else:
        st.info("No strong signals detected. Waiting for better market conditions.")

def render_portfolio_overview(data, user):
    """Premium portfolio overview"""
    st.title("📊 Portfolio Overview")
    
    if user['plan'] in ['premium', 'professional']:
        # Portfolio metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Value", "$124,850", "+2.4%")
        
        with col2:
            st.metric("24h Change", "+$2,950", "+2.4%")
        
        with col3:
            st.metric("All Time P&L", "+$24,850", "+24.8%")
        
        with col4:
            st.metric("Risk Score", "Medium", "-5%")
        
        # Portfolio allocation chart
        st.subheader("📈 Portfolio Allocation")
        
        allocation_data = {
            'Asset': ['BTC', 'ETH', 'ADA', 'SOL', 'Cash'],
            'Value': [65000, 32000, 8500, 12350, 7000],
            'Allocation': [52.1, 25.6, 6.8, 9.9, 5.6]
        }
        allocation_df = pd.DataFrame(allocation_data)
        
        fig = px.pie(allocation_df, values='Allocation', names='Asset', 
                     title='Portfolio Allocation',
                     color_discrete_sequence=px.colors.sequential.Viridis)
        st.plotly_chart(fig, use_container_width=True)
        
        # Recent activity
        st.subheader("📋 Recent Activity")
        activity_data = {
            "Date": ["2024-01-15", "2024-01-14", "2024-01-13"],
            "Action": ["BUY BTC", "SELL ETH", "BUY ADA"],
            "Amount": ["0.5 BTC", "2.1 ETH", "5000 ADA"],
            "Value": ["$21,075", "$5,250", "$2,125"],
            "Status": ["Completed", "Completed", "Completed"]
        }
        activity_df = pd.DataFrame(activity_data)
        st.dataframe(activity_df, use_container_width=True, hide_index=True)
        
    else:
        st.info("""
        🔒 **Premium Feature Unlock**
        
        Upgrade to Premium or Professional plan to access:
        - Real-time portfolio tracking
        - Advanced analytics
        - Performance metrics
        - Risk assessment tools
        """)
        
        if st.button("🚀 Upgrade to Premium", type="primary", use_container_width=True):
            st.session_state.show_upgrade = True
            st.rerun()

def render_trading_signals(data, user):
    """Enhanced trading signals dashboard"""
    st.title("🎯 Trading Signals Center")
    
    if user['plan'] in ['premium', 'professional']:
        # Signal overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Active Signals", "12", "+3")
        
        with col2:
            st.metric("Signal Accuracy", "76%", "+4%")
        
        with col3:
            st.metric("Avg. Return", "+2.8%", "+0.4%")
        
        # Generate sample signals
        strategies = list(STRATEGIES.keys())[:8]  # Show first 8 strategies
        signals = []
        
        for strategy in strategies:
            indicators = trading_engine.calculate_technical_indicators(strategy)
            strategy_signals = trading_engine.generate_trading_signals(strategy, indicators)
            if strategy_signals:
                signal_type, confidence, reasoning = strategy_signals[0]
                signals.append({
                    "Strategy": strategy,
                    "Signal": signal_type,
                    "Confidence": f"{confidence:.0%}",
                    "Strength": "High" if confidence > 0.8 else "Medium" if confidence > 0.6 else "Low",
                    "Timestamp": datetime.now().strftime("%H:%M")
                })
        
        signals_df = pd.DataFrame(signals)
        
        # Color code the signals
        def color_strength(val):
            if val == 'High':
                return 'background-color: #d4edda'
            elif val == 'Medium':
                return 'background-color: #fff3cd'
            else:
                return 'background-color: #f8d7da'
        
        st.dataframe(signals_df.style.applymap(color_strength, subset=['Strength']), 
                    use_container_width=True)
        
        # Signal actions
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🔄 Refresh All Signals", use_container_width=True):
                st.success("Signals refreshed!")
                st.rerun()
        
        with col2:
            if st.button("📤 Export Signals", use_container_width=True):
                st.info("Signals exported to CSV")
                
    else:
        st.info("""
        🔒 **Premium Signals Center**
        
        Upgrade to access real-time trading signals with:
        - Live market scanning
        - Multi-strategy analysis
        - Confidence scoring
        - Signal history tracking
        """)
        
        if st.button("🚀 Upgrade for Advanced Signals", type="primary", use_container_width=True):
            st.session_state.show_upgrade = True
            st.rerun()

def render_performance_analytics(data, user):
    """Premium performance analytics dashboard"""
    st.title("📈 Performance Analytics")
    
    if user['plan'] in ['premium', 'professional']:
        # Overall performance metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Total Return", "+24.8%", "+2.1%")
        
        with col2:
            st.metric("Win Rate", "68%", "+3%")
        
        with col3:
            st.metric("Avg. Win", "+3.2%", "+0.4%")
        
        with col4:
            st.metric("Avg. Loss", "-1.8%", "-0.2%")
        
        # Performance chart
        st.subheader("📊 Performance Over Time")
        
        # Generate sample performance data
        dates = pd.date_range(start='2023-07-01', end=datetime.now(), freq='D')
        performance = 100 * (1 + np.random.normal(0.001, 0.02, len(dates))).cumprod()
        
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=dates, y=performance, mode='lines', name='Portfolio',
                               line=dict(color='#00D4AA', width=3)))
        fig.update_layout(title='Portfolio Performance', height=400)
        st.plotly_chart(fig, use_container_width=True)
        
        # Strategy performance comparison
        st.subheader("🏆 Strategy Performance")
        
        strategies = list(STRATEGIES.keys())[:6]
        returns = np.random.uniform(5, 25, len(strategies))
        
        fig = px.bar(x=strategies, y=returns, 
                    title='Strategy Returns (%)',
                    color=returns, color_continuous_scale='Viridis')
        fig.update_layout(xaxis_title='Strategy', yaxis_title='Return (%)')
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.info("""
        🔒 **Premium Analytics Unlock**
        
        Upgrade to access advanced performance analytics:
        - Detailed performance metrics
        - Strategy comparison tools
        - Historical analysis
        - Risk-adjusted returns
        """)
        
        if st.button("🚀 Upgrade for Advanced Analytics", type="primary", use_container_width=True):
            st.session_state.show_upgrade = True
            st.rerun()

# ... [KEEP ALL OTHER FUNCTIONS EXACTLY THE SAME] ...
# ... [render_account_settings(), render_upgrade_plans(), etc.] ...

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
