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
import plotly.express as px

# -------------------------
# SUPABASE SETUP - FIXED VERSION
# -------------------------
try:
    from supabase import create_client, Client
    import supabase
except ImportError:
    st.error("Required packages not installed. Please install: pip install supabase python-dotenv")
    st.stop()

# Initialize Supabase client
@st.cache_resource
def init_supabase():
    """Initialize Supabase client - FIXED VERSION"""
    try:
        # You'll need to set these in your Streamlit Cloud secrets
        SUPABASE_URL = "https://mowuitmupjyhczczzslw.supabase.co"
        SUPABASE_KEY = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJzdXBhYmFzZSIsInJlZiI6Im1vd3VpdG11cGp5aGN6Y3p6c2x3Iiwicm9sZSI6InNlcnZpY2Vfcm9sZSIsImlhdCI6MTc2MDkyNDE4NSwiZXhwIjoyMDc2NTAwMTg1fQ._iSHD2E5dyAzcUjWRuKIqP7e1OYd7R3y7wJawPlVqTY"
        
        if not SUPABASE_URL or not SUPABASE_KEY:
            st.error("Supabase credentials not found. Please set SUPABASE_URL and SUPABASE_KEY in Streamlit secrets.")
            return None
            
        return create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        st.error(f"Error initializing Supabase: {e}")
        return None

supabase_client = init_supabase()

# -------------------------
# KAI - TRADING AI AGENT CHARACTER
# -------------------------

KAI_CHARACTER = {
    "name": "KAI",
    "title": "Senior Technical Analysis Specialist", 
    "experience": "10+ years multi-timeframe market analysis",
    "specialty": "Pattern recognition & reversal signal detection",
    
    # Consistent analytical framework
    "analysis_hierarchy": [
        "STRATEGY_OVERVIEW",
        "KEY_INDICATORS", 
        "MOMENTUM_ANALYSIS",
        "SUPPORT_RESISTANCE",
        "TIME_HORIZONS"
    ],
    
    # Personality traits
    "traits": {
        "methodical": True,
        "conservative": True, 
        "clear_communicator": True,
        "structured": True
    },
    
    # Language patterns (KAI's unique voice)
    "phrases": {
        "opening": "🔍 **KAI Analysis Report**",
        "critical_juncture": "Market at CRITICAL JUNCTURE",
        "major_move": "MAJOR MOVE expected",
        "reversal_expected": "REVERSAL expected within",
        "confidence_level": "Confidence Level"
    }
}

class KaiTradingAgent:
    def __init__(self):
        self.character = KAI_CHARACTER
        self.analysis_patterns = self._initialize_analysis_patterns()
    
    def _initialize_analysis_patterns(self):
        """KAI's consistent analysis methodology"""
        return {
            "phase_1_scanning": [
                "Identify completed vs pending analyses",
                "Flag indicators with actual notes", 
                "Look for confluence across indicators"
            ],
            "phase_2_signal_extraction": [
                "Detect reversal patterns (highest priority)",
                "Confirm momentum signals",
                "Validate support/resistance levels"
            ],
            "phase_3_time_mapping": [
                "Map signals to time horizons",
                "Resolve conflicting timeframes",
                "Generate confidence scores"
            ]
        }
    
    def analyze_strategy_data(self, df):
        """KAI's main analysis method - ALWAYS follows same structure"""
        # PHASE 1: Strategy Scanning (KAI always starts here)
        strategy_overview = self._phase_1_scanning(df)
        
        # PHASE 2: Signal Extraction  
        signals = self._phase_2_signal_extraction(df)
        
        # PHASE 3: Time Horizon Mapping
        time_analysis = self._phase_3_time_mapping(df)
        
        # Compile KAI's final report
        analysis = self._generate_kai_report(strategy_overview, signals, time_analysis)
        return analysis
    
    def _phase_1_scanning(self, df):
        """KAI's Phase 1: Always scan strategies in same order"""
        completed_analyses = len(df[df['Status'] == 'Done'])
        total_indicators = len(df)
        strategies = df['Strategy'].unique()
        
        return {
            "completion_rate": f"{completed_analyses}/{total_indicators}",
            "strategies_analyzed": list(strategies),
            "pending_analyses": len(df[df['Status'] == 'Open']),
            "total_strategies": len(strategies)
        }
    
    def _phase_2_signal_extraction(self, df):
        """KAI's Phase 2: Always look for these signal patterns"""
        signals = {
            "reversal_signals": [],
            "momentum_signals": [],
            "support_signals": [],
            "volume_signals": [],
            "breakout_signals": [],
            "conflicting_signals": []
        }
        
        # KAI always prioritizes reversal patterns first
        for index, row in df.iterrows():
            if pd.isna(row['Note']) or row['Note'] == '':
                continue
                
            note = str(row['Note']).lower()
            indicator = row['Indicator']
            strategy = row['Strategy']
            
            # Reversal detection (KAI's specialty)
            if any(keyword in note for keyword in ['reversal', 'reverse', 'turnaround', 'revert']):
                signals["reversal_signals"].append({
                    "strategy": strategy,
                    "indicator": indicator,
                    "message": row['Note'],
                    "strength": "HIGH" if 'major' in note or 'probable' in note else "MEDIUM"
                })
            
            # Support/Resistance detection  
            if any(keyword in note for keyword in ['support', 'resistance', 'holding', 'bounce']):
                signals["support_signals"].append({
                    "strategy": strategy,
                    "indicator": indicator,
                    "message": row['Note'], 
                    "level": "SUPPORT" if 'support' in note else "RESISTANCE"
                })
            
            # Momentum signals
            if any(keyword in note for keyword in ['momentum', 'trend', 'going down', 'bullish', 'bearish']):
                signals["momentum_signals"].append({
                    "strategy": strategy,
                    "indicator": indicator,
                    "message": row['Note'],
                    "direction": "BEARISH" if 'bearish' in note or 'going down' in note else "BULLISH"
                })
            
            # Volume signals
            if any(keyword in note for keyword in ['volume', 'volatility']):
                signals["volume_signals"].append({
                    "strategy": strategy,
                    "indicator": indicator,
                    "message": row['Note']
                })
            
            # Breakout signals
            if any(keyword in note for keyword in ['breakout', 'breaking', 'crossing']):
                signals["breakout_signals"].append({
                    "strategy": strategy,
                    "indicator": indicator,
                    "message": row['Note']
                })
        
        return signals
    
    def _phase_3_time_mapping(self, df):
        """KAI's Phase 3: Always map to time horizons"""
        time_signals = {
            "short_term": [],
            "medium_term": [], 
            "long_term": []
        }
        
        for index, row in df.iterrows():
            if pd.isna(row['Note']) or row['Note'] == '':
                continue
                
            note = str(row['Note']).lower()
            
            # KAI's time classification logic
            if any(word in note for word in ['next week', 'imminent', 'currently', 'short term']):
                time_signals["short_term"].append({
                    "indicator": row['Indicator'],
                    "strategy": row['Strategy'],
                    "message": row['Note']
                })
            elif any(word in note for word in ['2026', 'long-term', 'major move', 'next year']):
                time_signals["long_term"].append({
                    "indicator": row['Indicator'],
                    "strategy": row['Strategy'],
                    "message": row['Note']
                })
            else:
                time_signals["medium_term"].append({
                    "indicator": row['Indicator'],
                    "strategy": row['Strategy'],
                    "message": row['Note']
                })
                
        return time_signals
    
    def _generate_kai_report(self, overview, signals, time_analysis):
        """KAI's consistent reporting format"""
        report = {
            "header": f"🔍 **{self.character['name']} Analysis Report**",
            "executive_summary": self._generate_executive_summary(overview, signals),
            "key_findings": self._generate_key_findings(signals, overview),
            "confidence_assessment": self._calculate_confidence(signals),
            "time_horizon_outlook": time_analysis,
            "trading_implications": self._generate_trading_implications(signals),
            "signal_details": signals,
            "overview_metrics": overview
        }
        return report
    
    def _generate_executive_summary(self, overview, signals):
        """KAI's signature executive summary style"""
        reversal_count = len(signals["reversal_signals"])
        momentum_bearish = len([s for s in signals["momentum_signals"] if s.get('direction') == 'BEARISH'])
        momentum_bullish = len([s for s in signals["momentum_signals"] if s.get('direction') == 'BULLISH'])
        
        if reversal_count >= 2:
            return f"**{self.character['phrases']['critical_juncture']}** - STRONG REVERSAL EVIDENCE DETECTED across {reversal_count} indicators"
        elif reversal_count == 1:
            return f"**Potential Trend Change** - MODERATE REVERSAL SIGNALS with {momentum_bullish} bullish vs {momentum_bearish} bearish momentum"
        else:
            return f"**Consolidation Phase** - Analyzing {overview['total_strategies']} strategies with {overview['completion_rate']} completion rate"
    
    def _generate_key_findings(self, signals, overview):
        """KAI always provides 3-5 key findings"""
        findings = []
        
        # KAI always starts with reversal signals
        reversal_count = len(signals["reversal_signals"])
        if reversal_count > 0:
            strong_reversals = len([s for s in signals["reversal_signals"] if s['strength'] == 'HIGH'])
            findings.append(f"🔄 **Reversal Patterns**: {reversal_count} reversal signals ({strong_reversals} strong)")
        
        # Support/Resistance levels
        support_count = len([s for s in signals["support_signals"] if s['level'] == 'SUPPORT'])
        resistance_count = len([s for s in signals["support_signals"] if s['level'] == 'RESISTANCE'])
        if support_count > 0 or resistance_count > 0:
            findings.append(f"📊 **Key Levels**: {support_count} support zones, {resistance_count} resistance zones")
        
        # Momentum analysis
        bullish_momentum = len([s for s in signals["momentum_signals"] if s.get('direction') == 'BULLISH'])
        bearish_momentum = len([s for s in signals["momentum_signals"] if s.get('direction') == 'BEARISH'])
        if bullish_momentum > 0 or bearish_momentum > 0:
            findings.append(f"🎯 **Momentum**: {bullish_momentum} bullish vs {bearish_momentum} bearish signals")
        
        # Volume analysis
        if signals["volume_signals"]:
            findings.append(f"📈 **Volume Analysis**: {len(signals['volume_signals'])} volume-based signals")
        
        # Always include completion status
        findings.append(f"📋 **Analysis Coverage**: {overview['completion_rate']} indicators completed across {overview['total_strategies']} strategies")
        
        return findings[:5]  # KAI always provides max 5 key findings
    
    def _calculate_confidence(self, signals):
        """KAI's consistent confidence scoring"""
        score = 0
        
        # Reversal signals (highest weight)
        for signal in signals["reversal_signals"]:
            if signal['strength'] == 'HIGH':
                score += 25
            else:
                score += 15
        
        # Support/Resistance signals
        score += len(signals["support_signals"]) * 10
        
        # Momentum confirmation
        bullish_count = len([s for s in signals["momentum_signals"] if s.get('direction') == 'BULLISH'])
        bearish_count = len([s for s in signals["momentum_signals"] if s.get('direction') == 'BEARISH'])
        
        if bullish_count > bearish_count:
            score += 20
        elif bearish_count > bullish_count:
            score += 10
        
        # Volume confirmation
        score += len(signals["volume_signals"]) * 5
            
        return min(95, score)  # KAI is conservative, never gives 100%
    
    def _generate_trading_implications(self, signals):
        """KAI's actionable insights"""
        implications = []
        
        reversal_strength = len(signals["reversal_signals"])
        strong_reversals = len([s for s in signals["reversal_signals"] if s['strength'] == 'HIGH'])
        
        if reversal_strength >= 2 and strong_reversals >= 1:
            implications.append("**🎯 STRONG REVERSAL SIGNAL** - Position for major trend change")
            implications.append("**📊 CONFIRMATION** - Multiple indicators suggesting same direction")
            implications.append("**⏰ TIMING** - Monitor for breakout confirmation")
        elif reversal_strength >= 1:
            implications.append("**⚠️ CAUTIOUS POSITIONING** - Monitor for additional confirmation")
            implications.append("**📈 SETUP WATCH** - Prepare for potential reversal entries")
        else:
            implications.append("**🔄 RANGE TRADING** - Focus on support/resistance levels")
            implications.append("**🎯 MOMENTUM FOLLOW** - Trade with current trend direction")
            
        # Always include risk management
        implications.append("**🔒 RISK MANAGEMENT** - Always use stop losses, position size appropriately")
        
        return implications

# -------------------------
# SUPABASE DATABASE FUNCTIONS - FIXED WITH PROPER ERROR HANDLING
# -------------------------

# Users table functions - FIXED DELETION FUNCTIONS
def supabase_get_users():
    """Get all users from Supabase - FIXED VERSION"""
    if not supabase_client:
        return {}
    try:
        response = supabase_client.table('users').select('*').execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error getting users: {response.error}")
            return {}
        users = {}
        for user in response.data:
            users[user['username']] = user
        return users
    except Exception as e:
        st.error(f"Error getting users: {e}")
        return {}

def supabase_save_users(users):
    """Save users to Supabase - FIXED VERSION"""
    if not supabase_client:
        return False
    try:
        # Convert users dict to list
        users_list = []
        for username, user_data in users.items():
            user_data['username'] = username
            users_list.append(user_data)
        
        # Upsert all users
        response = supabase_client.table('users').upsert(users_list).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error saving users: {response.error}")
            return False
        return True
    except Exception as e:
        st.error(f"Error saving users: {e}")
        return False

def supabase_delete_user(username):
    """Delete user from Supabase - FIXED VERSION"""
    if not supabase_client:
        return False
    try:
        response = supabase_client.table('users').delete().eq('username', username).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error deleting user: {response.error}")
            return False
        st.success(f"✅ User '{username}' deleted from Supabase")
        return True
    except Exception as e:
        st.error(f"Error deleting user: {e}")
        return False

# Analytics table functions
def supabase_get_analytics():
    """Get analytics data from Supabase - FIXED VERSION"""
    if not supabase_client:
        return {}
    try:
        response = supabase_client.table('analytics').select('*').execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error getting analytics: {response.error}")
            return {}
        if response.data:
            return response.data[0]  # Assuming single analytics record
        return {}
    except Exception as e:
        st.error(f"Error getting analytics: {e}")
        return {}

def supabase_save_analytics(analytics):
    """Save analytics to Supabase - FIXED VERSION"""
    if not supabase_client:
        return False
    try:
        analytics['id'] = 1  # Single analytics record
        response = supabase_client.table('analytics').upsert(analytics).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error saving analytics: {response.error}")
            return False
        return True
    except Exception as e:
        st.error(f"Error saving analytics: {e}")
        return False

# Strategy analyses table functions - FIXED VERSION
def supabase_get_strategy_analyses():
    """Get strategy analyses from Supabase - FIXED"""
    if not supabase_client:
        return {}
    try:
        response = supabase_client.table('strategy_analyses').select('*').execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error getting strategy analyses: {response.error}")
            return {}
        strategies = {}
        for item in response.data:
            strategy_name = item['strategy_name']
            indicator_name = item['indicator_name']
            if strategy_name not in strategies:
                strategies[strategy_name] = {}
            strategies[strategy_name][indicator_name] = {
                "note": item.get('note', ''),
                "status": item.get('status', 'Open'),
                "momentum": item.get('momentum', 'Not Defined'),
                "strategy_tag": item.get('strategy_tag', 'Neutral'),
                "analysis_date": item.get('analysis_date', ''),
                "last_modified": item.get('last_modified', ''),
                "modified_by": item.get('modified_by', 'system')
            }
        return strategies
    except Exception as e:
        st.error(f"❌ Error getting strategy analyses: {e}")
        return {}

def supabase_save_strategy_analyses(strategy_data):
    """Save strategy analyses to Supabase - FIXED VERSION"""
    if not supabase_client:
        return False
    try:
        records = []
        for strategy_name, indicators in strategy_data.items():
            for indicator_name, meta in indicators.items():
                records.append({
                    'strategy_name': strategy_name,
                    'indicator_name': indicator_name,
                    'note': meta.get('note', ''),
                    'status': meta.get('status', 'Open'),
                    'momentum': meta.get('momentum', 'Not Defined'),
                    'strategy_tag': meta.get('strategy_tag', 'Neutral'),
                    'analysis_date': meta.get('analysis_date', ''),
                    'last_modified': meta.get('last_modified', ''),
                    'modified_by': meta.get('modified_by', 'system')
                })

        if records:
            # Use upsert with on_conflict to handle unique constraint
            response = supabase_client.table('strategy_analyses').upsert(
                records, 
                on_conflict='strategy_name,indicator_name'
            ).execute()
            if hasattr(response, 'error') and response.error:
                st.error(f"Supabase error saving strategy analyses: {response.error}")
                return False
        return True
    except Exception as e:
        st.error(f"❌ Error saving strategy analyses: {e}")
        return False

# Gallery images table functions
def supabase_get_gallery_images():
    """Get gallery images from Supabase - FIXED VERSION"""
    if not supabase_client:
        return []
    try:
        response = supabase_client.table('gallery_images').select('*').execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error getting gallery images: {response.error}")
            return []
        images = []
        for img in response.data:
            # Convert base64 back to bytes
            if 'bytes_b64' in img:
                img['bytes'] = base64.b64decode(img['bytes_b64'])
            images.append(img)
        return images
    except Exception as e:
        st.error(f"Error getting gallery images: {e}")
        return []

def supabase_save_gallery_images(images):
    """Save gallery images to Supabase - FIXED VERSION"""
    if not supabase_client:
        return False
    try:
        # First, clear all existing images (or we could update selectively)
        delete_response = supabase_client.table('gallery_images').delete().neq('id', 0).execute()
        if hasattr(delete_response, 'error') and delete_response.error:
            st.error(f"Supabase error clearing gallery images: {delete_response.error}")
            return False
        
        records = []
        for img in images:
            record = img.copy()
            # Convert bytes to base64 for storage
            if 'bytes' in record:
                record['bytes_b64'] = base64.b64encode(record['bytes']).decode('utf-8')
                del record['bytes']
            # Remove PIL Image objects
            if 'image' in record:
                del record['image']
            records.append(record)
        
        if records:
            response = supabase_client.table('gallery_images').insert(records).execute()
            if hasattr(response, 'error') and response.error:
                st.error(f"Supabase error saving gallery images: {response.error}")
                return False
        return True
    except Exception as e:
        st.error(f"Error saving gallery images: {e}")
        return False

def supabase_clear_gallery_images():
    """Clear all gallery images from Supabase - FIXED VERSION"""
    if not supabase_client:
        return False
    try:
        response = supabase_client.table('gallery_images').delete().neq('id', 0).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error clearing gallery images: {response.error}")
            return False
        return True
    except Exception as e:
        st.error(f"Error clearing gallery images: {e}")
        return False

# Trading signals table functions
def supabase_get_trading_signals():
    """Get trading signals from Supabase - FIXED VERSION"""
    if not supabase_client:
        return []
    try:
        response = supabase_client.table('trading_signals').select('*').execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error getting trading signals: {response.error}")
            return []
        return response.data
    except Exception as e:
        st.error(f"Error getting trading signals: {e}")
        return []

def supabase_save_trading_signals(signals):
    """Save trading signals to Supabase - FIXED VERSION"""
    if not supabase_client:
        return False
    try:
        # Clear and replace all signals
        delete_response = supabase_client.table('trading_signals').delete().neq('id', 0).execute()
        if hasattr(delete_response, 'error') and delete_response.error:
            st.error(f"Supabase error clearing trading signals: {delete_response.error}")
            return False
        
        if signals:
            response = supabase_client.table('trading_signals').insert(signals).execute()
            if hasattr(response, 'error') and response.error:
                st.error(f"Supabase error saving trading signals: {response.error}")
                return False
        return True
    except Exception as e:
        st.error(f"Error saving trading signals: {e}")
        return False

# NEW: App settings table functions for Signals Room Password
def supabase_get_app_settings():
    """Get app settings from Supabase - FIXED VERSION"""
    if not supabase_client:
        return {}
    try:
        response = supabase_client.table('app_settings').select('*').execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error getting app settings: {response.error}")
            return {}
        settings = {}
        for item in response.data:
            settings[item['setting_name']] = item['setting_value']
        return settings
    except Exception as e:
        st.error(f"Error getting app settings: {e}")
        return {}

def supabase_save_app_settings(settings):
    """Save app settings to Supabase - FIXED VERSION"""
    if not supabase_client:
        return False
    try:
        records = []
        for setting_name, setting_value in settings.items():
            records.append({
                'setting_name': setting_name,
                'setting_value': setting_value
            })
        
        if records:
            response = supabase_client.table('app_settings').upsert(records).execute()
            if hasattr(response, 'error') and response.error:
                st.error(f"Supabase error saving app settings: {response.error}")
                return False
        return True
    except Exception as e:
        st.error(f"Error saving app settings: {e}")
        return False

# Strategy indicator images table functions - FIXED VERSION
def supabase_get_strategy_indicator_images():
    """Get strategy indicator images from Supabase - FIXED"""
    if not supabase_client:
        return {}
    try:
        response = supabase_client.table('strategy_indicator_images').select('*').execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error getting strategy indicator images: {response.error}")
            return {}
        images_data = {}
        for item in response.data:
            strategy_name = item['strategy_name']
            indicator_name = item['indicator_name']
            if strategy_name not in images_data:
                images_data[strategy_name] = {}
            # Convert base64 back to bytes
            if 'bytes_b64' in item:
                try:
                    item['bytes'] = base64.b64decode(item['bytes_b64'])
                    images_data[strategy_name][indicator_name] = item
                except Exception as e:
                    st.error(f"Error decoding image for {strategy_name}/{indicator_name}: {e}")
                    continue
        return images_data
    except Exception as e:
        st.error(f"Error getting strategy indicator images: {e}")
        return {}

def supabase_save_strategy_indicator_images(images_data):
    """Save strategy indicator images to Supabase - FIXED"""
    if not supabase_client:
        return False
    try:
        # Get all existing records to delete only what we're replacing
        existing_response = supabase_client.table('strategy_indicator_images').select('*').execute()
        if hasattr(existing_response, 'error') and existing_response.error:
            st.error(f"Supabase error getting existing strategy indicator images: {existing_response.error}")
            return False
        existing_records = existing_response.data if existing_response.data else []
        
        records = []
        for strategy_name, indicators in images_data.items():
            for indicator_name, img_data in indicators.items():
                # Create a clean record
                record = {
                    'strategy_name': strategy_name,
                    'indicator_name': indicator_name,
                    'name': img_data.get('name', f"{strategy_name}_{indicator_name}"),
                    'format': img_data.get('format', 'PNG'),
                    'uploaded_by': img_data.get('uploaded_by', 'unknown'),
                    'timestamp': img_data.get('timestamp', datetime.now().isoformat())
                }
                
                # Convert bytes to base64
                if 'bytes' in img_data:
                    try:
                        record['bytes_b64'] = base64.b64encode(img_data['bytes']).decode('utf-8')
                    except Exception as e:
                        st.error(f"Error encoding image for {strategy_name}/{indicator_name}: {e}")
                        continue
                
                records.append(record)
        
        # Delete existing records for the strategies we're updating
        if records:
            strategies_to_update = list(set([r['strategy_name'] for r in records]))
            for strategy in strategies_to_update:
                delete_response = supabase_client.table('strategy_indicator_images').delete().eq('strategy_name', strategy).execute()
                if hasattr(delete_response, 'error') and delete_response.error:
                    st.error(f"Supabase error deleting strategy indicator images for {strategy}: {delete_response.error}")
                    return False
        
        # Insert new records
        if records:
            response = supabase_client.table('strategy_indicator_images').insert(records).execute()
            if hasattr(response, 'error') and response.error:
                st.error(f"Supabase error saving strategy indicator images: {response.error}")
                return False
        
        return True
    except Exception as e:
        st.error(f"❌ Error saving strategy indicator images: {e}")
        return False

def supabase_delete_strategy_indicator_image(strategy_name, indicator_name):
    """Delete specific strategy indicator image from Supabase - FIXED VERSION"""
    if not supabase_client:
        return False
    try:
        response = supabase_client.table('strategy_indicator_images').delete().eq('strategy_name', strategy_name).eq('indicator_name', indicator_name).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error deleting strategy indicator image: {response.error}")
            return False
        return True
    except Exception as e:
        st.error(f"Error deleting strategy indicator image: {e}")
        return False

# NEW: KAI Analyses table functions
def supabase_get_kai_analyses():
    """Get KAI analyses from Supabase - FIXED VERSION"""
    if not supabase_client:
        return []
    try:
        response = supabase_client.table('kai_analyses').select('*').order('created_at', desc=True).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error getting KAI analyses: {response.error}")
            return []
        return response.data
    except Exception as e:
        st.error(f"Error getting KAI analyses: {e}")
        return []

def supabase_save_kai_analysis(analysis_data):
    """Save KAI analysis to Supabase - FIXED VERSION"""
    if not supabase_client:
        return False
    try:
        # Prepare the record
        record = {
            'analysis_data': analysis_data,
            'uploaded_by': st.session_state.user['username'],
            'created_at': datetime.now().isoformat()
        }
        
        response = supabase_client.table('kai_analyses').insert(record).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error saving KAI analysis: {response.error}")
            return False
        return True
    except Exception as e:
        st.error(f"Error saving KAI analysis: {e}")
        return False

def supabase_get_latest_kai_analysis():
    """Get the latest KAI analysis from Supabase"""
    if not supabase_client:
        return None
    try:
        response = supabase_client.table('kai_analyses').select('*').order('created_at', desc=True).limit(1).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error getting latest KAI analysis: {response.error}")
            return None
        if response.data and len(response.data) > 0:
            return response.data[0]
        return None
    except Exception as e:
        st.error(f"Error getting latest KAI analysis: {e}")
        return None

# -------------------------
# SESSION MANAGEMENT - UPDATED WITH KAI
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
    # ENHANCED: Image gallery session state
    if 'uploaded_images' not in st.session_state:
        # Load images from Supabase on session init
        st.session_state.uploaded_images = load_gallery_images()
    if 'current_gallery_view' not in st.session_state:
        st.session_state.current_gallery_view = 'gallery'
    if 'selected_image' not in st.session_state:
        st.session_state.selected_image = None
    # NEW: Gallery clearance confirmation
    if 'show_clear_gallery_confirmation' not in st.session_state:
        st.session_state.show_clear_gallery_confirmation = False
    if 'clear_gallery_password' not in st.session_state:
        st.session_state.clear_gallery_password = ""
    if 'clear_gallery_error' not in st.session_state:
        st.session_state.clear_gallery_error = ""
    # NEW: Image viewer state
    if 'current_image_index' not in st.session_state:
        st.session_state.current_image_index = 0
    if 'image_viewer_mode' not in st.session_state:
        st.session_state.image_viewer_mode = False
    # NEW: Gallery filter and sort state
    if 'gallery_filter_author' not in st.session_state:
        st.session_state.gallery_filter_author = "All Authors"
    if 'gallery_filter_strategy' not in st.session_state:
        st.session_state.gallery_filter_strategy = "All Strategies"
    if 'gallery_sort_by' not in st.session_state:
        st.session_state.gallery_sort_by = "Newest First"
    # NEW: User navigation mode
    if 'user_navigation_mode' not in st.session_state:
        st.session_state.user_navigation_mode = "📊 Trading Dashboard"
    # NEW: Trading Signals Room state - SIMPLIFIED
    if 'signals_room_view' not in st.session_state:
        st.session_state.signals_room_view = 'active_signals'
    if 'active_signals' not in st.session_state:
        st.session_state.active_signals = load_signals_data()
    if 'signal_creation_mode' not in st.session_state:
        st.session_state.signal_creation_mode = 'quick'
    if 'signal_to_confirm' not in st.session_state:
        st.session_state.signal_to_confirm = None
    if 'signal_confirmation_step' not in st.session_state:
        st.session_state.signal_confirmation_step = 1
    # NEW: Strategy indicator images state - UPDATED LOADING
    if 'strategy_indicator_images' not in st.session_state:
        st.session_state.strategy_indicator_images = load_strategy_indicator_images()
    # NEW: Strategy indicator viewer state
    if 'strategy_indicator_viewer_mode' not in st.session_state:
        st.session_state.strategy_indicator_viewer_mode = False
    if 'current_strategy_indicator_image' not in st.session_state:
        st.session_state.current_strategy_indicator_image = None
    if 'current_strategy_indicator' not in st.session_state:
        st.session_state.current_strategy_indicator = None
    # NEW: Strategy analyses data state - CRITICAL FIX
    if 'strategy_analyses_data' not in st.session_state:
        st.session_state.strategy_analyses_data = load_data()
    # NEW: Signals Room Password Protection - LOAD FROM SUPABASE
    if 'signals_room_password' not in st.session_state:
        app_settings = load_app_settings()
        st.session_state.signals_room_password = app_settings.get('signals_room_password', 'trading123')
    if 'signals_room_access_granted' not in st.session_state:
        st.session_state.signals_room_access_granted = False
    if 'signals_password_input' not in st.session_state:
        st.session_state.signals_password_input = ""
    if 'signals_password_error' not in st.session_state:
        st.session_state.signals_password_error = ""
    # NEW: Signals Room Password Change
    if 'show_signals_password_change' not in st.session_state:
        st.session_state.show_signals_password_change = False
    # NEW: Manage User Plan Modal
    if 'show_manage_user_plan' not in st.session_state:
        st.session_state.show_manage_user_plan = False
    # NEW: User password change state
    if 'show_user_password_change' not in st.session_state:
        st.session_state.show_user_password_change = False
    # NEW: KAI AI Agent state
    if 'kai_analyses' not in st.session_state:
        st.session_state.kai_analyses = load_kai_analyses()
    if 'current_kai_analysis' not in st.session_state:
        st.session_state.current_kai_analysis = None

# -------------------------
# APP SETTINGS PERSISTENCE (FOR SIGNALS ROOM PASSWORD)
# -------------------------
def load_app_settings():
    """Load app settings from Supabase"""
    return supabase_get_app_settings()

def save_app_settings(settings):
    """Save app settings to Supabase"""
    return supabase_save_app_settings(settings)

# -------------------------
# KAI ANALYSES PERSISTENCE
# -------------------------
def load_kai_analyses():
    """Load KAI analyses from Supabase"""
    return supabase_get_kai_analyses()

def save_kai_analysis(analysis_data):
    """Save KAI analysis to Supabase"""
    return supabase_save_kai_analysis(analysis_data)

def get_latest_kai_analysis():
    """Get the latest KAI analysis from Supabase"""
    return supabase_get_latest_kai_analysis()

# -------------------------
# DATA PERSISTENCE SETUP
# -------------------------
def setup_data_persistence():
    """Set up periodic data saving to prevent data loss"""
    current_time = time.time()
    if current_time - st.session_state.last_save_time > 300:  # 5 minutes
        user_manager.save_users()
        user_manager.save_analytics()
        
        # Save strategy analyses data - FIXED: Save from session state
        try:
            if hasattr(st.session_state, 'strategy_analyses_data'):
                save_data(st.session_state.strategy_analyses_data)
        except Exception as e:
            st.error(f"⚠️ Error saving strategy data: {e}")
        
        # Save gallery images
        try:
            save_gallery_images(st.session_state.uploaded_images)
        except Exception as e:
            st.error(f"⚠️ Error saving gallery images: {e}")
        
        # Save signals data
        try:
            save_signals_data(st.session_state.active_signals)
        except Exception as e:
            st.error(f"⚠️ Error saving signals data: {e}")
            
        # Save strategy indicator images - FIXED: Now properly saves to Supabase
        try:
            save_strategy_indicator_images(st.session_state.strategy_indicator_images)
        except Exception as e:
            st.error(f"⚠️ Error saving strategy indicator images: {e}")
            
        st.session_state.last_save_time = current_time

# -------------------------
# STRATEGY ANALYSES DATA PERSISTENCE - FIXED VERSION
# -------------------------
def load_data():
    """Load strategy analyses data from Supabase - FIXED"""
    data = supabase_get_strategy_analyses()
    return data

def save_data(data):
    """Save strategy analyses data to Supabase - FIXED"""
    success = supabase_save_strategy_analyses(data)
    return success

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
# STRATEGY INDICATOR IMAGES PERSISTENCE - FIXED VERSION
# -------------------------
def load_strategy_indicator_images():
    """Load strategy indicator images from Supabase - FIXED"""
    images_data = supabase_get_strategy_indicator_images()
    return images_data

def save_strategy_indicator_images(images_data):
    """Save strategy indicator images to Supabase - FIXED"""
    success = supabase_save_strategy_indicator_images(images_data)
    return success

def get_strategy_indicator_image(strategy_name, indicator_name):
    """Get image for a specific strategy indicator - FIXED"""
    if strategy_name in st.session_state.strategy_indicator_images:
        if indicator_name in st.session_state.strategy_indicator_images[strategy_name]:
            return st.session_state.strategy_indicator_images[strategy_name][indicator_name]
    return None

def save_strategy_indicator_image(strategy_name, indicator_name, image_data):
    """Save image for a specific strategy indicator - FIXED"""
    if strategy_name not in st.session_state.strategy_indicator_images:
        st.session_state.strategy_indicator_images[strategy_name] = {}
    
    # Ensure we have the required fields
    if 'name' not in image_data:
        image_data['name'] = f"{strategy_name}_{indicator_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    if 'uploaded_by' not in image_data:
        image_data['uploaded_by'] = st.session_state.user['username']
    if 'timestamp' not in image_data:
        image_data['timestamp'] = datetime.now().isoformat()
    
    st.session_state.strategy_indicator_images[strategy_name][indicator_name] = image_data
    
    # Save to Supabase immediately
    success = save_strategy_indicator_images(st.session_state.strategy_indicator_images)
    
    return success

def delete_strategy_indicator_image(strategy_name, indicator_name):
    """Delete image for a specific strategy indicator"""
    if strategy_name in st.session_state.strategy_indicator_images:
        if indicator_name in st.session_state.strategy_indicator_images[strategy_name]:
            del st.session_state.strategy_indicator_images[strategy_name][indicator_name]
            
            # If no more images for this strategy, remove the strategy entry
            if not st.session_state.strategy_indicator_images[strategy_name]:
                del st.session_state.strategy_indicator_images[strategy_name]
            
            # Save to Supabase immediately
            success = save_strategy_indicator_images(st.session_state.strategy_indicator_images)
            
            # Also delete from Supabase directly
            supabase_delete_strategy_indicator_image(strategy_name, indicator_name)
            
            return success
    
    return False

# -------------------------
# TRADING SIGNALS DATA PERSISTENCE
# -------------------------
def load_signals_data():
    """Load trading signals from Supabase"""
    return supabase_get_trading_signals()

def save_signals_data(signals):
    """Save trading signals to Supabase"""
    return supabase_save_trading_signals(signals)

# -------------------------
# GALLERY IMAGE PERSISTENCE
# -------------------------
def load_gallery_images():
    """Load gallery images from Supabase"""
    return supabase_get_gallery_images()

def save_gallery_images(images):
    """Save gallery images to Supabase"""
    return supabase_save_gallery_images(images)

# -------------------------
# KAI AI AGENT INTERFACE
# -------------------------
def render_kai_agent():
    """KAI AI Agent interface - Admin can upload CSV, Users can view only"""
    
    # Check if user is admin or regular user
    is_admin = st.session_state.user['plan'] == 'admin'
    
    st.title("🧠 KAI AI Agent - Technical Analysis")
    
    # KAI Introduction
    col1, col2 = st.columns([3, 1])
    with col1:
        st.markdown(f"""
        **Meet {KAI_CHARACTER['name']}** - {KAI_CHARACTER['title']}
        
        *{KAI_CHARACTER['experience']}. Specializes in {KAI_CHARACTER['specialty']}.*
        
        KAI provides consistent, structured analysis of trading strategies using a methodical 3-phase approach.
        """)
    
    with col2:
        st.info("""
        **KAI's Framework:**
        - Phase 1: Strategy Scanning
        - Phase 2: Signal Extraction  
        - Phase 3: Time Mapping
        """)
    
    # Load latest KAI analysis for display
    latest_analysis = get_latest_kai_analysis()
    
    # Admin Section - CSV Upload and Analysis
    if is_admin:
        st.markdown("### 📊 Upload Strategy CSV for Analysis")
        
        uploaded_file = st.file_uploader(
            "Upload your strategy analysis CSV", 
            type=['csv'],
            key="kai_csv_uploader",
            help="Upload the CSV export from your trading dashboard for KAI analysis"
        )
        
        if uploaded_file is not None:
            try:
                # Initialize KAI
                kai_agent = KaiTradingAgent()
                
                # Read and analyze data
                df = pd.read_csv(uploaded_file)
                
                # Display basic file info
                st.success(f"✅ CSV loaded successfully: {len(df)} rows, {len(df['Strategy'].unique())} strategies")
                
                # KAI analyzes the data
                with st.spinner("🧠 KAI is analyzing the trading data..."):
                    time.sleep(2)  # Simulate analysis time
                    analysis = kai_agent.analyze_strategy_data(df)
                
                # Display KAI's report
                display_kai_analysis_report(analysis)
                
                # Save analysis to Supabase
                if st.button("💾 Save Analysis to Database", use_container_width=True):
                    if save_kai_analysis(analysis):
                        st.success("✅ KAI analysis saved to database!")
                        # Refresh the analyses list
                        st.session_state.kai_analyses = load_kai_analyses()
                    else:
                        st.error("❌ Failed to save analysis to database")
                
            except Exception as e:
                st.error(f"❌ Error analyzing CSV: {str(e)}")
                st.info("Please ensure you're uploading a valid strategy analysis CSV export from the dashboard.")
    
    # Display latest analysis for all users (admin and regular users)
    if latest_analysis:
        st.markdown("---")
        st.subheader("📋 Latest KAI Analysis")
        st.info(f"**Generated by:** {latest_analysis['uploaded_by']} | **Date:** {latest_analysis['created_at'][:16]}")
        
        # Display the analysis
        display_kai_analysis_report(latest_analysis['analysis_data'])
    
    # Show analysis history for admin
    if is_admin and st.session_state.kai_analyses:
        st.markdown("---")
        st.subheader("📜 Analysis History")
        
        for analysis in st.session_state.kai_analyses[:5]:  # Show last 5 analyses
            with st.expander(f"Analysis by {analysis['uploaded_by']} - {analysis['created_at'][:16]}"):
                display_kai_analysis_summary(analysis['analysis_data'])
    
    # Show help information when no analysis available
    if not latest_analysis:
        st.markdown("---")
        st.info("""
        **📋 Expected CSV Format:**
        Your CSV should contain the following columns:
        - `Strategy` (Strategy name)
        - `Indicator` (Indicator name) 
        - `Note` (Analysis notes)
        - `Status` (Done/Open)
        - `Momentum` (Momentum type)
        - `Tag` (Buy/Sell/Neutral)
        - `Analysis_Date` (Date of analysis)
        - `Last_Modified` (Timestamp)
        
        **🎯 KAI's Analysis Focus:**
        - Reversal pattern detection
        - Support/resistance level identification  
        - Momentum confirmation
        - Time horizon mapping
        - Confidence scoring
        """)

def display_kai_analysis_report(analysis):
    """Display KAI's analysis report in a consistent format"""
    # Header
    st.markdown(f"### {analysis['header']}")
    
    # Executive Summary (KAI always starts with this)
    st.info(analysis["executive_summary"])
    
    # Confidence Score & Key Metrics
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric(
            f"🧠 {KAI_CHARACTER['phrases']['confidence_level']}", 
            f"{analysis['confidence_assessment']}%"
        )
    with col2:
        st.metric(
            "Strategies Analyzed", 
            f"{analysis['overview_metrics']['total_strategies']}"
        )
    with col3:
        st.metric(
            "Analysis Completion", 
            analysis['overview_metrics']['completion_rate']
        )
    
    # Key Findings (KAI always uses bullet points)
    st.markdown("### 🔑 Key Findings")
    for finding in analysis["key_findings"]:
        st.write(f"• {finding}")
    
    # Detailed Signal Breakdown
    st.markdown("### 📈 Signal Breakdown")
    
    signals = analysis['signal_details']
    
    # Reversal Signals (KAI's priority)
    if signals["reversal_signals"]:
        with st.expander(f"🔄 Reversal Signals ({len(signals['reversal_signals'])})", expanded=True):
            for signal in signals["reversal_signals"]:
                strength_icon = "🔥" if signal['strength'] == 'HIGH' else "⚠️"
                st.write(f"{strength_icon} **{signal['strategy']} - {signal['indicator']}**: {signal['message']}")
    
    # Support/Resistance Levels
    if signals["support_signals"]:
        with st.expander(f"📊 Support/Resistance Levels ({len(signals['support_signals'])})"):
            for signal in signals["support_signals"]:
                level_icon = "🟢" if signal['level'] == 'SUPPORT' else "🔴"
                st.write(f"{level_icon} **{signal['strategy']} - {signal['indicator']}**: {signal['message']}")
    
    # Momentum Analysis
    if signals["momentum_signals"]:
        with st.expander(f"🎯 Momentum Signals ({len(signals['momentum_signals'])})"):
            for signal in signals["momentum_signals"]:
                direction_icon = "📈" if signal.get('direction') == 'BULLISH' else "📉"
                st.write(f"{direction_icon} **{signal['strategy']} - {signal['indicator']}**: {signal['message']}")
    
    # Time Horizon Analysis
    st.markdown("### ⏰ Time Horizon Outlook")
    time_analysis = analysis['time_horizon_outlook']
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Short-Term", len(time_analysis['short_term']))
        if time_analysis['short_term']:
            with st.expander("View Short-Term Signals"):
                for signal in time_analysis['short_term'][:3]:  # Show first 3
                    st.write(f"• {signal['strategy']} - {signal['indicator']}")
    
    with col2:
        st.metric("Medium-Term", len(time_analysis['medium_term']))
        if time_analysis['medium_term']:
            with st.expander("View Medium-Term Signals"):
                for signal in time_analysis['medium_term'][:3]:
                    st.write(f"• {signal['strategy']} - {signal['indicator']}")
    
    with col3:
        st.metric("Long-Term", len(time_analysis['long_term']))
        if time_analysis['long_term']:
            with st.expander("View Long-Term Signals"):
                for signal in time_analysis['long_term'][:3]:
                    st.write(f"• {signal['strategy']} - {signal['indicator']}")
    
    # Trading Implications (KAI always ends with actionable insights)
    st.markdown("### 💡 Trading Implications & Recommendations")
    for implication in analysis["trading_implications"]:
        st.write(implication)

def display_kai_analysis_summary(analysis):
    """Display a summary of KAI analysis for history view"""
    st.write(f"**{analysis['executive_summary']}**")
    st.write(f"**Confidence Level:** {analysis['confidence_assessment']}%")
    st.write(f"**Strategies Analyzed:** {analysis['overview_metrics']['total_strategies']}")
    
    # Show top 3 key findings
    st.write("**Key Findings:**")
    for finding in analysis["key_findings"][:3]:
        st.write(f"• {finding}")

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
# TRADING SIGNALS CONFIGURATION - SIMPLIFIED
# -------------------------
SIGNAL_CONFIG = {
    "timeframes": {
        "short": {"name": "Short Term", "duration": "1-7 days", "color": "#FF6B6B"},
        "medium": {"name": "Medium Term", "duration": "1-4 weeks", "color": "#4ECDC4"},
        "long": {"name": "Long Term", "duration": "1-6 months", "color": "#45B7D1"}
    },
    "assets": [
        "BTC/USD", "ETH/USD", "ADA/USD", "DOT/USD", "LINK/USD", 
        "LTC/USD", "BCH/USD", "XRP/USD", "XLM/USD", "EOS/USD",
        "BNB/USD", "SOL/USD", "MATIC/USD", "AVAX/USD", "ATOM/USD"
    ],
    "signal_types": ["BUY", "SELL", "HOLD", "STRONG_BUY", "STRONG_SELL"],
    "confidence_levels": ["Low", "Medium", "High", "Very High"]
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
# EMAIL VALIDATION TOOLS
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

# -------------------------
# SECURE USER MANAGEMENT WITH SUPABASE PERSISTENCE - FIXED VERSION
# -------------------------
class UserManager:
    def __init__(self):
        self.load_data()
    
    def load_data(self):
        """Load users and analytics data from Supabase - FIXED VERSION"""
        try:
            self.users = supabase_get_users()
            self.analytics = supabase_get_analytics()
            
            # Create default admin if it doesn't exist
            if "admin" not in self.users:
                self.create_default_admin()
                self.save_users()
            
            # Initialize analytics if empty
            if not self.analytics:
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
                
        except Exception as e:
            st.error(f"❌ Error loading data: {e}")
            # Initialize with default data
            self.users = {}
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
            self.create_default_admin()
            self.save_users()
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
            "email_verified": True,  # Admin email is always verified
            "verification_date": datetime.now().isoformat()
        }
    
    def hash_password(self, password):
        """Secure password hashing"""
        salt = "default-salt-change-in-production"
        return hashlib.sha256((password + salt).encode()).hexdigest()
    
    def save_users(self):
        """Save users to Supabase - FIXED VERSION"""
        return supabase_save_users(self.users)
    
    def save_analytics(self):
        """Save analytics data to Supabase - FIXED VERSION"""
        return supabase_save_analytics(self.analytics)
    
    def periodic_cleanup(self):
        """Periodic cleanup that doesn't delete user data"""
        # Only reset session counts, don't delete users
        session_reset_count = 0
        for username in self.users:
            if self.users[username].get('active_sessions', 0) > 0:
                self.users[username]['active_sessions'] = 0
                session_reset_count += 1
        
        if session_reset_count > 0:
            self.save_users()
    
    def register_user(self, username, password, name, email, plan="trial"):
        """Register new user with proper validation and persistence - FIXED VERSION"""
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
            "email_verified": False,  # NEW: Email verification status
            "verification_date": None,  # NEW: When email was verified
            "verification_notes": "",  # NEW: Admin notes for verification
            "verification_admin": None  # NEW: Which admin verified the email
        }
        
        # Update analytics
        if 'user_registrations' not in self.analytics:
            self.analytics['user_registrations'] = []
        
        self.analytics["user_registrations"].append({
            "username": username,
            "plan": plan,
            "timestamp": datetime.now().isoformat()
        })
        
        # Save both files
        users_saved = self.save_users()
        analytics_saved = self.save_analytics()
        
        if users_saved and analytics_saved:
            return True, f"Account created successfully! {plan_config['name']} activated."
        else:
            # Remove the user if save failed
            if username in self.users:
                del self.users[username]
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
            "payment_status": "active",
            "email_verified": False,  # Test users start unverified
            "verification_date": None,
            "verification_notes": "",
            "verification_admin": None
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
        """Delete a user account completely - FIXED VERSION"""
        if username not in self.users:
            return False, "User not found"
        
        if username == "admin":
            return False, "Cannot delete admin account"
        
        user_data = self.users[username]
        
        # Store user info for analytics before deletion
        user_plan = user_data.get('plan', 'unknown')
        user_created = user_data.get('created', 'unknown')
        
        # Delete the user
        del self.users[username]
        
        # Update analytics
        if 'deleted_users' not in self.analytics:
            self.analytics['deleted_users'] = []
        
        self.analytics['deleted_users'].append({
            "username": username,
            "plan": user_plan,
            "created": user_created,
            "deleted_at": datetime.now().isoformat()
        })
        
        # Delete from Supabase
        supabase_success = supabase_delete_user(username)
        
        # Save changes to local data
        users_saved = self.save_users()
        analytics_saved = self.save_analytics()
        
        if users_saved and analytics_saved and supabase_success:
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
        """Authenticate user WITHOUT email verification blocking - FIXED VERSION"""
        # Increment login attempts first
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
        
        # REMOVED: Email verification check - users can login immediately
        # Email verification status is only for admin monitoring
        
        if not self.verify_password(password, user["password_hash"]):
            # Save analytics for failed login
            self.save_analytics()
            return False, "Invalid username or password"
        
        expires = user.get("expires")
        if expires and datetime.strptime(expires, "%Y-%m-%d").date() < date.today():
            return False, "Subscription expired. Please renew your plan."
        
        user["last_login"] = datetime.now().isoformat()
        user["login_count"] = user.get("login_count", 0) + 1
        user["active_sessions"] += 1
        
        self.analytics["login_history"][-1]["success"] = True
        
        # Save both users and analytics - FIXED: Check both saves
        users_saved = self.save_users()
        analytics_saved = self.save_analytics()
        
        if users_saved and analytics_saved:
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
        for user in self.users.values():
            plan = user.get('plan', 'unknown')
            plan_counts[plan] = plan_counts.get(plan, 0) + 1
        
        # NEW: Email verification metrics
        verified_users = sum(1 for u in self.users.values() if u.get('email_verified', False))
        unverified_users = total_users - verified_users
        
        return {
            "total_users": total_users,
            "active_users": active_users,
            "online_users": online_users,
            "plan_distribution": plan_counts,
            "total_logins": self.analytics.get("total_logins", 0),
            "revenue_today": self.analytics.get("revenue_today", 0),
            "verified_users": verified_users,
            "unverified_users": unverified_users
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
                    "email_verified": user_data.get("email_verified", False),  # NEW
                    "verification_date": user_data.get("verification_date", ""),  # NEW
                    "verification_admin": user_data.get("verification_admin", "")  # NEW
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
                "email_verified": user_data.get("email_verified", False),  # NEW
                "verification_date": user_data.get("verification_date", ""),  # NEW
                "verification_admin": user_data.get("verification_admin", "")  # NEW
            })
        return users_list

    # NEW FUNCTION: Verify user email manually
    def verify_user_email(self, username, admin_username, notes=""):
        """Manually verify a user's email address (admin function)"""
        if username not in self.users:
            return False, "User not found"
        
        if username == "admin":
            return False, "Cannot modify admin account verification"
        
        user_data = self.users[username]
        
        if user_data.get("email_verified", False):
            return False, "Email is already verified"
        
        # Update verification status
        user_data["email_verified"] = True
        user_data["verification_date"] = datetime.now().isoformat()
        user_data["verification_admin"] = admin_username
        user_data["verification_notes"] = notes
        
        # Update analytics
        if 'email_verifications' not in self.analytics:
            self.analytics['email_verifications'] = []
        
        self.analytics['email_verifications'].append({
            "username": username,
            "email": user_data.get("email", ""),
            "verified_by": admin_username,
            "timestamp": datetime.now().isoformat(),
            "notes": notes
        })
        
        if self.save_users() and self.save_analytics():
            return True, f"Email for '{username}' has been verified successfully!"
        else:
            return False, "Error saving verification data"

    # NEW FUNCTION: Revoke email verification
    def revoke_email_verification(self, username, admin_username, reason=""):
        """Revoke email verification (admin function)"""
        if username not in self.users:
            return False, "User not found"
        
        if username == "admin":
            return False, "Cannot modify admin account verification"
        
        user_data = self.users[username]
        
        if not user_data.get("email_verified", False):
            return False, "Email is not verified"
        
        # Update verification status
        user_data["email_verified"] = False
        user_data["verification_date"] = None
        user_data["verification_admin"] = None
        user_data["verification_notes"] = reason
        
        # Update analytics
        if 'email_verifications' not in self.analytics:
            self.analytics['email_verifications'] = []
        
        self.analytics['email_verifications'].append({
            "username": username,
            "email": user_data.get("email", ""),
            "action": "revoked",
            "revoked_by": admin_username,
            "timestamp": datetime.now().isoformat(),
            "reason": reason
        })
        
        if self.save_users() and self.save_analytics():
            return True, f"Email verification for '{username}' has been revoked!"
        else:
            return False, "Error saving verification data"

    # NEW FUNCTION: Get email verification statistics
    def get_email_verification_stats(self):
        """Get statistics about email verification status"""
        total_users = len(self.users)
        verified_count = 0
        unverified_count = 0
        pending_verification = []
        recently_verified = []
        
        for username, user_data in self.users.items():
            if username == "admin":
                continue  # Skip admin
            
            if user_data.get("email_verified", False):
                verified_count += 1
                # Get recently verified (last 7 days)
                verification_date = user_data.get("verification_date")
                if verification_date:
                    try:
                        verify_dt = datetime.fromisoformat(verification_date)
                        if (datetime.now() - verify_dt).days <= 7:
                            recently_verified.append({
                                "username": username,
                                "email": user_data.get("email", ""),
                                "verified_date": verification_date,
                                "verified_by": user_data.get("verification_admin", "")
                            })
                    except:
                        pass
            else:
                unverified_count += 1
                pending_verification.append({
                    "username": username,
                    "email": user_data.get("email", ""),
                    "created": user_data.get("created", ""),
                    "plan": user_data.get("plan", "")
                })
        
        return {
            "total_users": total_users - 1,  # Exclude admin
            "verified_count": verified_count,
            "unverified_count": unverified_count,
            "verification_rate": (verified_count / (total_users - 1)) * 100 if total_users > 1 else 0,
            "pending_verification": pending_verification,
            "recently_verified": recently_verified
        }

    # NEW FUNCTION: Get inactive users for bulk deletion - FIXED COMPARISON ERROR
    def get_inactive_users(self, days_threshold=30):
        """Get users who haven't logged in for more than specified days - FIXED VERSION"""
        inactive_users = []
        cutoff_date = datetime.now() - timedelta(days=days_threshold)
        
        for username, user_data in self.users.items():
            if username == "admin":
                continue
                
            last_login = user_data.get('last_login')
            if not last_login:
                # If user never logged in, check creation date
                created_date = datetime.fromisoformat(user_data.get('created', datetime.now().isoformat()))
                if created_date.date() < cutoff_date.date():  # FIXED: Compare dates, not datetime with date
                    inactive_users.append(username)
            else:
                login_date = datetime.fromisoformat(last_login)
                if login_date.date() < cutoff_date.date():  # FIXED: Compare dates, not datetime with date
                    inactive_users.append(username)
        
        return inactive_users

    # NEW FUNCTION: Bulk delete inactive users - FIXED VERSION
    def bulk_delete_inactive_users(self, usernames):
        """Bulk delete specified users - FIXED VERSION"""
        success_count = 0
        error_count = 0
        errors = []
        
        for username in usernames:
            if username == "admin":
                errors.append(f"Cannot delete admin account: {username}")
                error_count += 1
                continue
                
            if username not in self.users:
                errors.append(f"User not found: {username}")
                error_count += 1
                continue
                
            # Store user info before deletion
            user_data = self.users[username]
            user_plan = user_data.get('plan', 'unknown')
            user_created = user_data.get('created', 'unknown')
            
            # Delete the user
            del self.users[username]
            
            # Update analytics
            if 'deleted_users' not in self.analytics:
                self.analytics['deleted_users'] = []
            
            self.analytics['deleted_users'].append({
                "username": username,
                "plan": user_plan,
                "created": user_created,
                "deleted_at": datetime.now().isoformat(),
                "reason": "bulk_delete_inactive"
            })
            
            # Delete from Supabase
            supabase_success = supabase_delete_user(username)
            if not supabase_success:
                errors.append(f"Failed to delete {username} from database")
                error_count += 1
                continue
            
            success_count += 1
        
        # Save changes
        if success_count > 0:
            self.save_users()
            self.save_analytics()
        
        return success_count, error_count, errors

    # NEW FUNCTION: User change their own password
    def change_own_password(self, username, current_password, new_password):
        """Allow user to change their own password"""
        if username not in self.users:
            return False, "User not found"
        
        user_data = self.users[username]
        
        # Verify current password
        if not self.verify_password(current_password, user_data["password_hash"]):
            return False, "Current password is incorrect"
        
        if len(new_password) < 8:
            return False, "New password must be at least 8 characters"
        
        # Check if new password is same as current
        if self.verify_password(new_password, user_data["password_hash"]):
            return False, "New password cannot be the same as current password"
        
        # Update password
        user_data["password_hash"] = self.hash_password(new_password)
        
        # Update analytics
        if 'password_changes' not in self.analytics:
            self.analytics['password_changes'] = []
        
        self.analytics['password_changes'].append({
            "username": username,
            "timestamp": datetime.now().isoformat(),
            "changed_by": username,
            "type": "user_self_change"
        })
        
        if self.save_users() and self.save_analytics():
            return True, "Password changed successfully!"
        else:
            return False, "Error saving password change"

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
    """Render the manage user plan interface - FIXED WORKING VERSION WITH BACK BUTTON"""
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
    
    # ADDED: Back button at the top
    if st.button("🔙 Back to User Management", key="manage_user_back_top"):
        st.session_state.manage_user_plan = None
        st.session_state.show_manage_user_plan = False
        st.rerun()
    
    st.subheader(f"⚙️ Manage User: {username}")
    
    # Main form for user details
    with st.form(f"manage_user_{username}"):
        col1, col2 = st.columns(2)
        
        with col1:
            # User information (read-only)
            st.write("**User Information:**")
            st.text_input("Name", value=user_data.get('name', ''), disabled=True, key=f"name_{username}")
            st.text_input("Email", value=user_data.get('email', ''), disabled=True, key=f"email_{username}")
            st.text_input("Created", value=user_data.get('created', '')[:10], disabled=True, key=f"created_{username}")
            
            # Email verification status
            email_verified = user_data.get('email_verified', False)
            verification_status = "✅ Verified" if email_verified else "❌ Unverified"
            st.text_input("Email Status", value=verification_status, disabled=True, key=f"email_status_{username}")
        
        with col2:
            # Plan management
            st.write("**Plan Management:**")
            current_plan = user_data.get('plan', 'trial')
            available_plans = list(Config.PLANS.keys()) + ['admin']
            index = available_plans.index(current_plan) if current_plan in available_plans else 0
            new_plan = st.selectbox(
                "Change Plan:",
                available_plans,
                index=index,
                key=f"plan_select_{username}"
            )
            
            # Expiry date
            current_expiry = user_data.get('expires', '')
            new_expiry = st.date_input(
                "Expiry Date:",
                value=datetime.strptime(current_expiry, "%Y-%m-%d").date() if current_expiry else datetime.now().date() + timedelta(days=30),
                key=f"expiry_{username}"
            )
            
            # Active status
            is_active = st.checkbox(
                "Account Active",
                value=user_data.get('is_active', True),
                key=f"active_{username}"
            )
            
            # Max sessions
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
            save_changes = st.form_submit_button("💾 Save Changes", use_container_width=True, type="primary")
        
        with col_b2:
            delete_user = st.form_submit_button("🗑️ Delete User", use_container_width=True, type="secondary")
        
        with col_b3:
            cancel = st.form_submit_button("🔙 Cancel", use_container_width=True)
        
        if save_changes:
            # Update user data
            user_data['plan'] = new_plan
            user_data['expires'] = new_expiry.strftime("%Y-%m-%d")
            user_data['is_active'] = is_active
            user_data['max_sessions'] = max_sessions
            
            # Save changes
            if user_manager.save_users():
                st.success("✅ User settings updated successfully!")
                time.sleep(2)
                st.session_state.manage_user_plan = None
                st.session_state.show_manage_user_plan = False
                st.rerun()
            else:
                st.error("❌ Error saving user settings")
        
        if delete_user:
            st.session_state.user_to_delete = username
            st.session_state.show_delete_confirmation = True
            st.rerun()
        
        if cancel:
            st.session_state.manage_user_plan = None
            st.session_state.show_manage_user_plan = False
            st.rerun()
    
    # Email verification and password reset outside the main form
    st.markdown("---")
    st.write("**Email Verification & Password Reset:**")
    col_v1, col_v2 = st.columns(2)
    
    with col_v1:
        # Email verification form
        with st.form(f"verify_email_{username}"):
            if not email_verified:
                if st.form_submit_button("✅ Verify Email", use_container_width=True, key=f"verify_email_btn_{username}"):
                    success, message = user_manager.verify_user_email(username, st.session_state.user['username'], "Manually verified by admin")
                    if success:
                        st.success(message)
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)
            else:
                if st.form_submit_button("❌ Revoke Verification", use_container_width=True, key=f"revoke_email_btn_{username}"):
                    success, message = user_manager.revoke_email_verification(username, st.session_state.user['username'], "Revoked by admin")
                    if success:
                        st.success(message)
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)
    
    with col_v2:
        # Password reset form
        with st.form(f"reset_password_{username}"):
            if st.form_submit_button("🔑 Reset Password", use_container_width=True, key=f"reset_password_btn_{username}"):
                new_password = f"TempPass{int(time.time()) % 10000}"
                success, message = user_manager.change_user_password(username, new_password, st.session_state.user['username'])
                if success:
                    st.success(f"✅ Password reset! New temporary password: {new_password}")
                    st.info("🔒 User should change this password immediately after login.")
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
    """Password gate for Trading Signals Room"""
    st.title("🔒 Trading Signals Room - Secure Access")
    st.markdown("---")
    
    st.warning("""
    ⚠️ **SECURE ACCESS REQUIRED**
    
    The Trading Signals Room contains sensitive trading information and strategies.
    Please enter the password to continue.
    """)
    
    with st.form("signals_room_password_form"):
        password_input = st.text_input(
            "🔑 Enter Signals Room Password:",
            type="password",
            placeholder="Enter password to access trading signals...",
            value=st.session_state.signals_password_input,
            key="signals_room_password_input"
        )
        
        submitted = st.form_submit_button("🚀 Access Trading Signals Room", use_container_width=True)
        
        if submitted:
            if not password_input:
                st.session_state.signals_password_error = "❌ Please enter the password"
                st.rerun()
            elif password_input == st.session_state.signals_room_password:
                st.session_state.signals_room_access_granted = True
                st.session_state.signals_password_error = ""
                st.success("✅ Access granted! Loading Trading Signals Room...")
                time.sleep(1)
                st.rerun()
            else:
                st.session_state.signals_password_error = "❌ Incorrect password. Please try again."
                st.rerun()
    
    # Display error message if any
    if st.session_state.signals_password_error:
        st.error(st.session_state.signals_password_error)
    
    # Admin hint
    if st.session_state.user['plan'] == 'admin':
        st.markdown("---")
        st.info("💡 **Admin Note:** You can change the Signals Room password in Admin Settings.")

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
                plan_choice = st.selectbox(
                    "Subscription Plan*", 
                    list(Config.PLANS.keys()),
                    format_func=lambda x: f"{Config.PLANS[x]['name']} - ${Config.PLANS[x]['price']}/month",
                    key="register_plan"
                )
            
            with col2:
                new_email = st.text_input("Email Address*", key="register_email")
                new_password = st.text_input("Create Password*", type="password", help="Minimum 8 characters", key="register_password")
                confirm_password = st.text_input("Confirm Password*", type="password", key="register_confirm_password")
            
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
    """Professional image gallery forum with enhanced navigation and persistence"""
    
    # If in image viewer mode, show the image viewer
    if st.session_state.image_viewer_mode:
        render_image_viewer()
        return
    
    # Gallery header
    st.title("🖼️ Trading Analysis Image Gallery")
    st.markdown("Share and discuss trading charts, analysis screenshots, and market insights with the community.")
    
    # Gallery navigation
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        gallery_view = st.radio(
            "Gallery View:",
            ["📸 Image Gallery", "⬆️ Upload Images"],
            horizontal=True,
            key="gallery_nav"
        )
    
    st.markdown("---")
    
    if gallery_view == "⬆️ Upload Images":
        render_image_uploader()
    else:
        render_gallery_display()

def render_image_uploader():
    """Image upload interface with persistence"""
    st.subheader("📤 Upload New Images")
    
    with st.container():
        st.markdown("""
        <div style="
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 2rem;
            border-radius: 15px;
            margin-bottom: 2rem;
        ">
        <h3 style="color: white; margin-bottom: 1rem;">🎯 Upload Trading Analysis Images</h3>
        <p style="margin-bottom: 0;">Share your trading charts, technical analysis, market insights and strategy screenshots.</p>
        <p><strong>Supported formats:</strong> PNG, JPG, JPEG, GIF, BMP</p>
        </div>
        """, unsafe_allow_html=True)
    
    # Image upload section
    uploaded_files = st.file_uploader(
        "Choose trading analysis images to upload", 
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp'], 
        accept_multiple_files=True,
        help="Select one or more trading charts or analysis images",
        key="gallery_uploader"
    )
    
    # Image description
    image_description = st.text_area(
        "Image Description (Optional):",
        placeholder="Describe what this image shows - e.g., 'BTC/USD 4H chart with RSI divergence', 'ETH breakout analysis', etc.",
        height=100,
        key="gallery_description"
    )
    
    # Strategy tagging
    strategy_tags = st.multiselect(
        "Related Strategies (Optional):",
        list(STRATEGIES.keys()),
        help="Tag relevant trading strategies",
        key="gallery_strategy_tags"
    )
    
    # Upload button
    if st.button("🚀 Upload Images to Gallery", use_container_width=True, key="upload_images_btn"):
        if uploaded_files:
            for uploaded_file in uploaded_files:
                # Read image file
                image = Image.open(uploaded_file)
                
                # Convert to bytes for display - FIXED: Ensure proper format
                img_bytes = io.BytesIO()
                # Use the correct format for saving
                if image.format:
                    image.save(img_bytes, format=image.format)
                else:
                    image.save(img_bytes, format='PNG')  # Default to PNG if format not detected
                
                # Store in session state - FIXED: Ensure we're storing the bytes correctly
                image_data = {
                    'name': uploaded_file.name,
                    'bytes': img_bytes.getvalue(),
                    'format': image.format if image.format else 'PNG',
                    'description': image_description,
                    'strategies': strategy_tags,
                    'uploaded_by': st.session_state.user['username'],
                    'timestamp': datetime.now().isoformat(),
                    'likes': 0,
                    'comments': []
                }
                
                st.session_state.uploaded_images.append(image_data)
            
            # Save gallery images to Supabase
            save_gallery_images(st.session_state.uploaded_images)
            
            st.success(f"✅ Successfully uploaded {len(uploaded_files)} image(s) to the gallery!")
            st.balloons()
            time.sleep(1)
            st.rerun()  # Force refresh to show thumbnails immediately
        else:
            st.warning("⚠️ Please select at least one image to upload.")

def render_gallery_display():
    """Display the image gallery with ALWAYS VISIBLE thumbnails and persistence"""
    st.subheader("📸 Community Image Gallery")
    
    if not st.session_state.uploaded_images:
        st.info("""
        🖼️ **No images in the gallery yet!**
        
        Be the first to share your trading analysis! Upload charts, technical analysis screenshots, 
        or market insights to help the community learn and discuss trading strategies.
        """)
        return
    
    # Gallery stats
    total_images = len(st.session_state.uploaded_images)
    your_images = len([img for img in st.session_state.uploaded_images if img['uploaded_by'] == st.session_state.user['username']])
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Images", total_images)
    with col2:
        st.metric("Your Images", your_images)
    with col3:
        total_likes = sum(img['likes'] for img in st.session_state.uploaded_images)
        st.metric("Total Likes", total_likes)
    
    st.markdown("---")
    
    # Filter options - using session state to persist filter values
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_author = st.selectbox(
            "Filter by Author:",
            ["All Authors"] + list(set(img['uploaded_by'] for img in st.session_state.uploaded_images)),
            key="gallery_filter_author"
        )
    with col2:
        filter_strategy = st.selectbox(
            "Filter by Strategy:",
            ["All Strategies"] + list(STRATEGIES.keys()),
            key="gallery_filter_strategy"
        )
    with col3:
        sort_by = st.selectbox(
            "Sort by:",
            ["Newest First", "Oldest First", "Most Liked"],
            key="gallery_sort_by"
        )
    
    # Apply filters
    filtered_images = st.session_state.uploaded_images.copy()
    
    if filter_author != "All Authors":
        filtered_images = [img for img in filtered_images if img['uploaded_by'] == filter_author]
    
    if filter_strategy != "All Strategies":
        filtered_images = [img for img in filtered_images if filter_strategy in img.get('strategies', [])]
    
    # Apply sorting
    if sort_by == "Newest First":
        filtered_images.sort(key=lambda x: x['timestamp'], reverse=True)
    elif sort_by == "Oldest First":
        filtered_images.sort(key=lambda x: x['timestamp'])
    elif sort_by == "Most Liked":
        filtered_images.sort(key=lambda x: x['likes'], reverse=True)
    
    # Display gallery in a grid - ALWAYS SHOW THUMBNAILS WITHOUT EXPANDER
    if not filtered_images:
        st.warning("No images match your current filters.")
        return
    
    # Create responsive grid - ALWAYS SHOW THUMBNAILS WITHOUT EXPANDER
    st.markdown(f"**Displaying {len(filtered_images)} images**")
    st.markdown("---")
    
    # Use columns for grid layout - FIXED: Ensure proper image display
    cols_per_row = 3
    for i in range(0, len(filtered_images), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(filtered_images):
                img_data = filtered_images[i + j]
                with cols[j]:
                    render_image_card(img_data, i + j)
    
    # Clear gallery button (admin only)
    if st.session_state.user['plan'] == 'admin':
        st.markdown("---")
        
        if st.session_state.show_clear_gallery_confirmation:
            render_clear_gallery_confirmation()
        else:
            if st.button("🗑️ Clear Entire Gallery (Admin Only)", use_container_width=True, key="clear_gallery_btn"):
                st.session_state.show_clear_gallery_confirmation = True
                st.session_state.clear_gallery_password = ""
                st.session_state.clear_gallery_error = ""
                st.rerun()

def render_image_card(img_data, index):
    """Render individual image card with ALWAYS VISIBLE thumbnail - FIXED VERSION"""
    with st.container():
        # FIXED: Ensure the image bytes are properly displayed as thumbnail
        try:
            # Display thumbnail ALWAYS VISIBLE - FIXED: Use the bytes directly
            st.image(img_data['bytes'], use_container_width=True, caption=img_data['name'])
        except Exception as e:
            st.error(f"❌ Error displaying image: {str(e)}")
            st.info("Image format may not be supported. Try uploading as PNG or JPG.")
        
        # Image info - always visible
        st.markdown(f"**{img_data['name']}**")
        
        # Description preview
        if img_data.get('description'):
            # Show first 50 characters of description
            preview = img_data['description'][:50] + "..." if len(img_data['description']) > 50 else img_data['description']
            st.caption(preview)
        
        # Strategy tags preview
        if img_data.get('strategies'):
            tags_preview = ", ".join(img_data['strategies'][:2])  # Show first 2 strategies
            if len(img_data['strategies']) > 2:
                tags_preview += f" +{len(img_data['strategies']) - 2} more"
            st.caption(f"**Strategies:** {tags_preview}")
        
        # Author and date
        st.caption(f"By: **{img_data['uploaded_by']}**")
        upload_time = datetime.fromisoformat(img_data['timestamp']).strftime("%Y-%m-%d %H:%M")
        st.caption(f"Uploaded: {upload_time}")
        
        # Interaction buttons
        col_a, col_b, col_c, col_d = st.columns([1, 1, 2, 2])
        with col_a:
            if st.button("❤️", key=f"like_{index}_{img_data['name']}", help="Like this image"):
                img_data['likes'] += 1
                # Save gallery after like
                save_gallery_images(st.session_state.uploaded_images)
                st.rerun()
        with col_b:
            st.write(f" {img_data['likes']}")
        with col_c:
            # Full view button
            if st.button("🖼️ Full View", key=f"view_{index}_{img_data['name']}", help="View image in fullscreen mode"):
                # Find the index of this image in the original list
                original_index = st.session_state.uploaded_images.index(img_data)
                st.session_state.current_image_index = original_index
                st.session_state.image_viewer_mode = True
                st.rerun()
        with col_d:
            # Download button
            try:
                b64_img = base64.b64encode(img_data['bytes']).decode()
                href = f'<a href="data:image/{img_data["format"].lower()};base64,{b64_img}" download="{img_data["name"]}" style="text-decoration: none;">'
                st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 4px 8px; text-align: center; text-decoration: none; display: inline-block; font-size: 12px; cursor: pointer; border-radius: 4px; width: 100%;">Download</button></a>', unsafe_allow_html=True)
            except Exception as e:
                st.error("Download unavailable")

def render_image_viewer():
    """Enhanced image viewer with navigation controls and persistence - FIXED DUPLICATE KEY ISSUE"""
    if not st.session_state.uploaded_images:
        st.warning("No images in gallery")
        st.session_state.image_viewer_mode = False
        st.rerun()
        return
    
    current_index = st.session_state.current_image_index
    total_images = len(st.session_state.uploaded_images)
    img_data = st.session_state.uploaded_images[current_index]
    
    # Header with navigation - FIXED: Unique keys for all buttons
    col1, col2, col3, col4 = st.columns([1, 2, 2, 1])
    
    with col1:
        if st.button("⬅️ Back to Gallery", use_container_width=True, key="image_viewer_back_btn"):
            st.session_state.image_viewer_mode = False
            st.rerun()
    
    with col2:
        st.markdown(f"### Image {current_index + 1} of {total_images}")
    
    with col3:
        st.markdown(f"### {img_data['name']}")
    
    with col4:
        if st.button("📋 Gallery", use_container_width=True, key="image_viewer_gallery_btn"):
            st.session_state.image_viewer_mode = False
            st.rerun()
    
    st.markdown("---")
    
    # Main image display - FIXED: Unique keys for navigation buttons
    col1, col2, col3 = st.columns([1, 8, 1])
    
    with col1:
        if st.button("◀️ Previous", use_container_width=True, key="image_viewer_prev_btn"):
            st.session_state.current_image_index = (current_index - 1) % total_images
            st.rerun()
    
    with col2:
        # Display the main image - FIXED: Ensure proper display
        try:
            st.image(img_data['bytes'], use_container_width=True)
        except Exception as e:
            st.error(f"Error displaying image: {str(e)}")
    
    with col3:
        if st.button("Next ▶️", use_container_width=True, key="image_viewer_next_btn"):
            st.session_state.current_image_index = (current_index + 1) % total_images
            st.rerun()
    
    # Image information and controls below
    st.markdown("---")
    
    col1, col2 = st.columns([3, 1])
    
    with col1:
        # Image details
        st.subheader("Image Details")
        
        # Description
        if img_data.get('description'):
            st.write("**Description:**")
            st.info(img_data['description'])
        else:
            st.write("**Description:** No description provided")
        
        # Strategy tags
        if img_data.get('strategies'):
            st.write("**Related Strategies:**")
            tags = " ".join([f"`{tag}`" for tag in img_data['strategies']])
            st.markdown(tags)
        
        # Author and metadata
        st.write("**Upload Information:**")
        col_meta1, col_meta2 = st.columns(2)
        with col_meta1:
            st.write(f"**Author:** {img_data['uploaded_by']}")
            st.write(f"**Likes:** {img_data['likes']} ❤️")
        with col_meta2:
            upload_time = datetime.fromisoformat(img_data['timestamp']).strftime("%Y-%m-%d %H:%M")
            st.write(f"**Uploaded:** {upload_time}")
            st.write(f"**Format:** {img_data['format']}")
    
    with col2:
        # Quick navigation and actions - FIXED: Unique keys
        st.subheader("Quick Navigation")
        
        # Image selector
        selected_index = st.selectbox(
            "Jump to Image:",
            range(total_images),
            format_func=lambda i: f"Image {i+1}: {st.session_state.uploaded_images[i]['name'][:20]}...",
            index=current_index,
            key="image_viewer_selector"
        )
        
        if selected_index != current_index:
            st.session_state.current_image_index = selected_index
            st.rerun()
        
        st.markdown("---")
        
        # Action buttons - FIXED: Unique keys
        st.subheader("Actions")
        
        # Like button
        if st.button(f"❤️ Like ({img_data['likes']})", use_container_width=True, key="image_viewer_like_btn"):
            img_data['likes'] += 1
            # Save gallery after like
            save_gallery_images(st.session_state.uploaded_images)
            st.rerun()
        
        # Download button
        try:
            b64_img = base64.b64encode(img_data['bytes']).decode()
            href = f'<a href="data:image/{img_data["format"].lower()};base64,{b64_img}" download="{img_data["name"]}" style="text-decoration: none;">'
            st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 10px; text-align: center; text-decoration: none; display: inline-block; font-size: 14px; cursor: pointer; border-radius: 4px; width: 100%;">⬇️ Download Image</button></a>', unsafe_allow_html=True)
        except Exception as e:
            st.error("Download unavailable")
    
    # Navigation controls at bottom - FIXED: Unique keys for all bottom navigation buttons
    st.markdown("---")
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        if st.button("⏮️ First", use_container_width=True, key="image_viewer_first_btn"):
            st.session_state.current_image_index = 0
            st.rerun()
    
    with col2:
        if st.button("◀️ Previous", use_container_width=True, key="image_viewer_prev_bottom_btn"):
            st.session_state.current_image_index = (current_index - 1) % total_images
            st.rerun()
    
    with col3:
        if st.button("📋 Gallery", use_container_width=True, key="image_viewer_gallery_bottom_btn"):
            st.session_state.image_viewer_mode = False
            st.rerun()
    
    with col4:
        if st.button("Next ▶️", use_container_width=True, key="image_viewer_next_bottom_btn"):
            st.session_state.current_image_index = (current_index + 1) % total_images
            st.rerun()
    
    with col5:
        if st.button("Last ⏭️", use_container_width=True, key="image_viewer_last_btn"):
            st.session_state.current_image_index = total_images - 1
            st.rerun()

def render_clear_gallery_confirmation():
    """Security confirmation for clearing gallery - REQUIRES ADMIN PASSWORD"""
    st.warning("🚨 **SECURITY CONFIRMATION REQUIRED**")
    
    with st.container():
        st.error("""
        ⚠️ **DESTRUCTIVE ACTION - IRREVERSIBLE**
        
        You are about to permanently delete ALL images from the gallery.
        This action cannot be undone!
        
        **Total images to be deleted:** {} images
        """.format(len(st.session_state.uploaded_images)))
        
        admin_password = st.text_input(
            "🔒 Enter Admin Password to Confirm:",
            type="password",
            placeholder="Enter your admin password to proceed",
            help="This is a security measure to prevent accidental data loss",
            value=st.session_state.clear_gallery_password,
            key="admin_password_input_clear_gallery"
        )
        
        # Update session state with password input
        st.session_state.clear_gallery_password = admin_password
        
        col1, col2 = st.columns(2)
        with col1:
            if st.button("✅ CONFIRM DELETE ALL IMAGES", use_container_width=True, type="primary", key="confirm_clear_gallery"):
                if not admin_password:
                    st.session_state.clear_gallery_error = "❌ Please enter your admin password to confirm"
                    st.rerun()
                else:
                    # Verify admin password
                    success, message = user_manager.authenticate("admin", admin_password)
                    if success:
                        # Password verified - proceed with deletion
                        image_count = len(st.session_state.uploaded_images)
                        st.session_state.uploaded_images = []
                        st.session_state.show_clear_gallery_confirmation = False
                        st.session_state.clear_gallery_password = ""
                        st.session_state.clear_gallery_error = ""
                        st.session_state.image_viewer_mode = False  # Exit viewer if active
                        
                        # Save empty gallery to Supabase
                        supabase_clear_gallery_images()
                        
                        st.success(f"✅ Gallery cleared! {image_count} images have been permanently deleted.")
                        st.rerun()
                    else:
                        st.session_state.clear_gallery_error = "❌ Invalid admin password. Gallery clearance cancelled."
                        st.rerun()
        
        with col2:
            if st.button("❌ CANCEL", use_container_width=True, key="cancel_clear_gallery"):
                st.session_state.show_clear_gallery_confirmation = False
                st.session_state.clear_gallery_password = ""
                st.session_state.clear_gallery_error = ""
                st.rerun()
        
        # Display error message if any
        if st.session_state.clear_gallery_error:
            st.error(st.session_state.clear_gallery_error)

# -------------------------
# USER IMAGE GALLERY - VIEW ONLY VERSION
# -------------------------
def render_user_image_gallery():
    """Image gallery for regular users - VIEW ONLY (no upload)"""
    
    # If in image viewer mode, show the image viewer
    if st.session_state.image_viewer_mode:
        render_image_viewer()
        return
    
    # Gallery header - VIEW ONLY for users
    st.title("🖼️ Trading Analysis Image Gallery")
    st.markdown("View trading charts, analysis screenshots, and market insights shared by the community.")
    
    # User-specific info
    st.info(f"👤 **Viewing as:** {st.session_state.user['name']} | 📊 **Access:** View Only")
    
    if not st.session_state.uploaded_images:
        st.info("""
        🖼️ **No images in the gallery yet!**
        
        The gallery will show trading charts and analysis images once they are uploaded by administrators.
        """)
        return
    
    # Gallery stats for users
    total_images = len(st.session_state.uploaded_images)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Images", total_images)
    with col2:
        your_images = len([img for img in st.session_state.uploaded_images if img['uploaded_by'] == st.session_state.user['username']])
        st.metric("Your Images", your_images)
    with col3:
        total_likes = sum(img['likes'] for img in st.session_state.uploaded_images)
        st.metric("Total Likes", total_likes)
    
    st.markdown("---")
    
    # Filter options for users
    col1, col2, col3 = st.columns(3)
    with col1:
        filter_author = st.selectbox(
            "Filter by Author:",
            ["All Authors"] + list(set(img['uploaded_by'] for img in st.session_state.uploaded_images)),
            key="user_gallery_filter_author"
        )
    with col2:
        filter_strategy = st.selectbox(
            "Filter by Strategy:",
            ["All Strategies"] + list(STRATEGIES.keys()),
            key="user_gallery_filter_strategy"
        )
    with col3:
        sort_by = st.selectbox(
            "Sort by:",
            ["Newest First", "Oldest First", "Most Liked"],
            key="user_gallery_sort_by"
        )
    
    # Apply filters
    filtered_images = st.session_state.uploaded_images.copy()
    
    if filter_author != "All Authors":
        filtered_images = [img for img in filtered_images if img['uploaded_by'] == filter_author]
    
    if filter_strategy != "All Strategies":
        filtered_images = [img for img in filtered_images if filter_strategy in img.get('strategies', [])]
    
    # Apply sorting
    if sort_by == "Newest First":
        filtered_images.sort(key=lambda x: x['timestamp'], reverse=True)
    elif sort_by == "Oldest First":
        filtered_images.sort(key=lambda x: x['timestamp'])
    elif sort_by == "Most Liked":
        filtered_images.sort(key=lambda x: x['likes'], reverse=True)
    
    # Display gallery in a grid - VIEW ONLY
    if not filtered_images:
        st.warning("No images match your current filters.")
        return
    
    # Create responsive grid
    st.markdown(f"**Displaying {len(filtered_images)} images**")
    st.markdown("---")
    
    # Use columns for grid layout
    cols_per_row = 3
    for i in range(0, len(filtered_images), cols_per_row):
        cols = st.columns(cols_per_row)
        for j in range(cols_per_row):
            if i + j < len(filtered_images):
                img_data = filtered_images[i + j]
                with cols[j]:
                    render_user_image_card(img_data, i + j)

def render_user_image_card(img_data, index):
    """Render individual image card for users - VIEW ONLY"""
    with st.container():
        # Display thumbnail
        try:
            st.image(img_data['bytes'], use_container_width=True, caption=img_data['name'])
        except Exception as e:
            st.error(f"❌ Error displaying image: {str(e)}")
            st.info("Image format may not be supported.")
        
        # Image info
        st.markdown(f"**{img_data['name']}**")
        
        # Description preview
        if img_data.get('description'):
            preview = img_data['description'][:50] + "..." if len(img_data['description']) > 50 else img_data['description']
            st.caption(preview)
        
        # Strategy tags preview
        if img_data.get('strategies'):
            tags_preview = ", ".join(img_data['strategies'][:2])
            if len(img_data['strategies']) > 2:
                tags_preview += f" +{len(img_data['strategies']) - 2} more"
            st.caption(f"**Strategies:** {tags_preview}")
        
        # Author and date
        st.caption(f"By: **{img_data['uploaded_by']}**")
        upload_time = datetime.fromisoformat(img_data['timestamp']).strftime("%Y-%m-%d %H:%M")
        st.caption(f"Uploaded: {upload_time}")
        
        # Interaction buttons - VIEW ONLY (can like and view, but not upload)
        col_a, col_b, col_c, col_d = st.columns([1, 1, 2, 2])
        with col_a:
            if st.button("❤️", key=f"user_like_{index}_{img_data['name']}", help="Like this image"):
                img_data['likes'] += 1
                save_gallery_images(st.session_state.uploaded_images)
                st.rerun()
        with col_b:
            st.write(f" {img_data['likes']}")
        with col_c:
            # Full view button
            if st.button("🖼️ Full View", key=f"user_view_{index}_{img_data['name']}", help="View image in fullscreen mode"):
                original_index = st.session_state.uploaded_images.index(img_data)
                st.session_state.current_image_index = original_index
                st.session_state.image_viewer_mode = True
                st.rerun()
        with col_d:
            # Download button
            try:
                b64_img = base64.b64encode(img_data['bytes']).decode()
                href = f'<a href="data:image/{img_data["format"].lower()};base64,{b64_img}" download="{img_data["name"]}" style="text-decoration: none;">'
                st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 4px 8px; text-align: center; text-decoration: none; display: inline-block; font-size: 12px; cursor: pointer; border-radius: 4px; width: 100%;">Download</button></a>', unsafe_allow_html=True)
            except Exception as e:
                st.error("Download unavailable")

# -------------------------
# STRATEGY INDICATOR IMAGE UPLOAD AND DISPLAY COMPONENTS - FIXED VERSION
# -------------------------
def render_strategy_indicator_image_upload(strategy_name, indicator_name):
    """Render image upload for a specific strategy indicator - FIXED VERSION"""
    st.subheader(f"🖼️ {indicator_name} - Chart Image")
    
    # Check if there's already an image for this indicator
    existing_image = get_strategy_indicator_image(strategy_name, indicator_name)
    
    if existing_image:
        st.success("✅ Image already uploaded for this indicator")
        
        # Display the existing image as thumbnail
        col1, col2 = st.columns([2, 1])
        with col1:
            st.image(existing_image['bytes'], use_container_width=True, caption=f"Current {indicator_name} Chart")
        
        with col2:
            # Full view button
            if st.button("🖼️ Full View", key=f"full_view_{strategy_name}_{indicator_name}", use_container_width=True):
                # Set up the image viewer for strategy indicator images
                st.session_state.current_strategy_indicator_image = existing_image
                st.session_state.strategy_indicator_viewer_mode = True
                st.session_state.current_strategy_indicator = f"{strategy_name}_{indicator_name}"
                st.rerun()
            
            # Remove image button
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
        # Display preview
        st.image(uploaded_file, caption="Preview", use_container_width=True)
        
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
    """Display strategy indicator images for users (view only)"""
    if strategy_name not in st.session_state.strategy_indicator_images:
        return
    
    st.subheader("📊 Strategy Charts")
    
    indicators_with_images = st.session_state.strategy_indicator_images[strategy_name]
    
    if not indicators_with_images:
        st.info("No chart images available for this strategy yet.")
        return
    
    # Display images in a grid
    cols = st.columns(2)
    for i, (indicator_name, img_data) in enumerate(indicators_with_images.items()):
        col = cols[i % 2]
        
        with col:
            with st.container():
                st.markdown(f"**{indicator_name}**")
                
                # Display thumbnail
                st.image(img_data['bytes'], use_container_width=True, caption=f"{indicator_name} Chart")
                
                # Full view button
                if st.button("🖼️ Full View", key=f"user_view_{strategy_name}_{indicator_name}", use_container_width=True):
                    st.session_state.current_strategy_indicator_image = img_data
                    st.session_state.strategy_indicator_viewer_mode = True
                    st.session_state.current_strategy_indicator = f"{strategy_name}_{indicator_name}"
                    st.rerun()
                
                st.caption(f"Updated: {datetime.fromisoformat(img_data['timestamp']).strftime('%Y-%m-%d %H:%M')}")
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
    """User account settings - FIXED VERSION"""
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
    
    st.markdown("---")
    
    if st.button("⬅️ Back to Dashboard", use_container_width=True, key="user_back_to_dash_btn"):
        st.session_state.dashboard_view = 'main'
        st.rerun()

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
    """Detailed strategy notes interface with full admin editing - FIXED VERSION"""
    st.title("📝 Admin Signal Editor")
    
    # Header with cycle info - CHANGED: Removed " - ADMIN EDIT MODE" and added green BUY button
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
        current_strategy_type = next(iter(existing_data.values()), {}).get("momentum", "Not Defined")
        
        # Strategy-level settings
        col1, col2 = st.columns(2)
        with col1:
            strategy_tag = st.selectbox("Strategy Tag:", ["Neutral", "Buy", "Sell"], 
                                      index=["Neutral","Buy","Sell"].index(current_strategy_tag),
                                      key="admin_strategy_tag")
        with col2:
            strategy_type = st.selectbox("Strategy Type:", ["Momentum", "Extreme", "Not Defined"], 
                                       index=["Momentum","Extreme","Not Defined"].index(current_strategy_type),
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
        
        # Save button - FIXED: Now saves to session state and Supabase
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
                    "momentum": strategy_type,
                    "strategy_tag": strategy_tag,
                    "analysis_date": analysis_date.strftime("%Y-%m-%d"),
                    "last_modified": datetime.utcnow().isoformat() + "Z",
                    "modified_by": "admin"  # Mark as admin-edited
                }
            
            # Save to Supabase - FIXED: Now saves the entire session state data
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
                    momentum_type = meta.get("momentum", "Not Defined")
                    status_icon = "✅ Done" if meta.get("status", "Open") == "Done" else "🕓 Open"
                    modified_by = meta.get("modified_by", "system")
                    with st.expander(f"{ind_name} ({momentum_type}) — {status_icon} — Edited by: {modified_by}", expanded=False):
                        st.write(meta.get("note", "") or "_No notes yet_")
                        st.caption(f"Last updated: {meta.get('last_modified', 'N/A')}")
            st.markdown("---")

def render_admin_account_settings():
    """Admin account settings in premium mode"""
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
    
    with col3:
        if st.button("⬅️ Back to Signals", use_container_width=True, key="back_signals_admin_btn"):
            st.session_state.dashboard_view = 'main'
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
        
        # Export functionality - READ ONLY
        csv_bytes = generate_filtered_csv_bytes(strategy_data, analysis_date)
        st.subheader("📄 Export Data")
        st.download_button(
            label="⬇️ Download CSV",
            data=csv_bytes,
            file_name=f"strategy_analyses_{analysis_date.strftime('%Y%m%d')}.csv",
            mime="text/csv",
            use_container_width=True,
            key="user_export_btn"
        )
        
        st.markdown("---")
        if st.button("🚪 Logout", use_container_width=True, key="user_logout_btn"):
            user_manager.logout(user['username'])
            st.session_state.user = None
            st.rerun()
    
    # Main dashboard content - READ ONLY for users but same layout as admin
    current_view = st.session_state.get('dashboard_view', 'main')
    
    if current_view == 'settings':
        render_user_account_settings()
    else:
        render_user_trading_dashboard(data, user, daily_strategies, cycle_day, analysis_date, selected_strategy)

def render_user_trading_dashboard(data, user, daily_strategies, cycle_day, analysis_date, selected_strategy):
    """User trading dashboard - ENHANCED INTERACTIVE VERSION WITH EXPANDABLE BOXES"""
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
    
    # Selected strategy analysis - ENHANCED INTERACTIVE VERSION WITH EXPANDABLE BOXES
    col_header1, col_header2 = st.columns([3, 1])
    with col_header1:
        st.subheader(f"🔍 {selected_strategy} Analysis")
    with col_header2:
        st.button("🟢 BUY Strategy", 
                 use_container_width=True, 
                 key=f"user_buy_bundle_{selected_strategy}",
                 help="Purchase to use in TradingView")
    
    # Display existing analysis - ENHANCED WITH EXPANDABLE BOXES
    strategy_data = st.session_state.strategy_analyses_data
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
def render_admin_dashboard():
    """Professional admin dashboard with dual mode selection"""
    
    # If admin hasn't chosen a dashboard mode, show selection
    if st.session_state.get('admin_dashboard_mode') is None:
        render_admin_dashboard_selection()
        return
    
    # Check if we're in strategy indicator image viewer mode
    if hasattr(st.session_state, 'strategy_indicator_viewer_mode') and st.session_state.strategy_indicator_viewer_mode:
        render_strategy_indicator_image_viewer()
        return
    
    # Always render the sidebar first, regardless of current view
    with st.sidebar:
        st.title("👑 Admin Panel")
        st.markdown("---")
        st.write(f"Welcome, **{st.session_state.user['name']}**")
        
        # Show current mode
        current_mode = st.session_state.admin_dashboard_mode
        if current_mode == "admin":
            st.success("🛠️ Admin Management Mode")
        elif current_mode == "premium":
            st.success("📊 Premium Signal Mode")
        elif current_mode == "gallery":
            st.success("🖼️ Image Gallery Mode")
        elif current_mode == "signals_room":
            st.success("⚡ Trading Signals Room")
        else:
            st.success("🛠️ Admin Management Mode")
        
        # Dashboard mode switcher
        st.markdown("---")
        st.subheader("Dashboard Mode")
        col1, col2, col3, col4 = st.columns(4)
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
    else:
        render_image_gallery()

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
        """)
        if st.button("🧠 Go to KAI Agent", use_container_width=True, key="kai_dash_btn"):
            st.session_state.admin_dashboard_mode = "kai_agent"
            st.rerun()
    
    st.markdown("---")
    st.info("💡 **Tip:** Use different dashboards for different management tasks.")

def render_admin_management_dashboard():
    """Complete admin management dashboard with all rich features"""
    st.title("🛠️ Admin Management Dashboard")
    
    # Get business metrics
    metrics = user_manager.get_business_metrics()
    
    # Key metrics
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        st.metric("Total Users", metrics["total_users"])
    with col2:
        st.metric("Active Users", metrics["active_users"])
    with col3:
        st.metric("Online Now", metrics["online_users"])
    with col4:
        st.metric("Verified Users", metrics["verified_users"])
    with col5:
        st.metric("Unverified Users", metrics["unverified_users"])
    
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
    elif current_view == 'kai_agent':
        render_kai_agent()  # NEW: KAI AI Agent integration
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
        padding: 2px 8px !important;
        border-radius: 12px !important;
        font-weight: 600 !important;
        min-width: 60px !important;
        display: inline-block !important;
        text-align: center !important;
        border: 1px solid !important;
    }
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
                ["📊 Trading Dashboard", "🖼️ Image Gallery", "⚡ Trading Signals", "🧠 KAI AI Agent"],
                key="user_navigation_mode"
            )
            
            # Display appropriate view based on user selection
            if user_mode == "🖼️ Image Gallery":
                # For gallery, ensure user can only view (not upload)
                render_user_image_gallery()
            elif user_mode == "⚡ Trading Signals":
                # Show the trading signals room in VIEW MODE
                render_trading_signals_room()
            elif user_mode == "🧠 KAI AI Agent":
                # Show the KAI AI Agent in VIEW MODE (users can view but not upload)
                render_kai_agent()
            else:
                # Show the premium trading dashboard in VIEW MODE
                render_user_dashboard()

if __name__ == "__main__":
    main()
