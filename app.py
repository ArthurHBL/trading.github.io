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

# [THE REST OF YOUR ORIGINAL CODE REMAINS EXACTLY THE SAME - ALL THE EXISTING FUNCTIONS, 
# INTERFACES, AND COMPONENTS ARE PRESERVED]

# ... [ALL YOUR EXISTING CODE FOR THE OTHER COMPONENTS] ...

# -------------------------
# MAIN APPLICATION - UPDATED WITH KAI INTEGRATION
# -------------------------
def main():
    init_session()
    
    # Setup data persistence
    setup_data_persistence()
    
    # Enhanced CSS for premium appearance including KAI styles
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
        background: linear-gradient(135deg, #f0e7ff 0%, #e2d5ff 100%);
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
    .kai-analysis {
        border: 2px solid #8B5CF6;
        border-radius: 10px;
        padding: 1.5rem;
        margin: 1rem 0;
        background: linear-gradient(135deg, #f8f7ff 0%, #ede9fe 100%);
    }
    .kai-confidence-high {
        color: #10B981;
        font-weight: bold;
    }
    .kai-confidence-medium {
        color: #F59E0B;
        font-weight: bold;
    }
    .kai-confidence-low {
        color: #EF4444;
        font-weight: bold;
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
            # FIXED: Users should have access to BOTH premium dashboard (view mode) AND image gallery AND signals room AND KAI
            # Add navigation for users to switch between dashboard and gallery
            
            # User navigation header
            st.sidebar.title("👤 User Navigation")
            
            # User mode selection - ADD KAI TO THIS LIST
            user_mode = st.sidebar.radio(
                "Select View:",
                ["📊 Trading Dashboard", "🖼️ Image Gallery", "⚡ Trading Signals", "🧠 KAI AI Agent"],
                key="user_navigation_mode"
            )
            
            # Display appropriate view based on user selection
            if user_mode == "🖼️ Image Gallery":
                render_user_image_gallery()
            elif user_mode == "⚡ Trading Signals":
                render_trading_signals_room()
            elif user_mode == "🧠 KAI AI Agent":
                render_kai_agent()  # NEW: KAI AI Agent interface (view only for users)
            else:
                render_user_dashboard()

# -------------------------
# UPDATED ADMIN DASHBOARD WITH KAI INTEGRATION
# -------------------------

def render_admin_dashboard():
    """Professional admin dashboard with KAI integration"""
    
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
        elif current_mode == "kai_agent":  # NEW: KAI mode
            st.success("🧠 KAI AI Agent Mode")
        else:
            st.success("🛠️ Admin Management Mode")
        
        # Dashboard mode switcher - ADD KAI OPTION
        st.markdown("---")
        st.subheader("Dashboard Mode")
        col1, col2, col3, col4, col5 = st.columns(5)  # Changed to 5 columns
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
        with col5:  # NEW: KAI button
            if st.button("🧠 KAI", use_container_width=True,
                        type="primary" if current_mode == "kai_agent" else "secondary",
                        key="sidebar_kai_btn"):
                st.session_state.admin_dashboard_mode = "kai_agent"
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
        elif current_mode == "kai_agent":  # NEW: KAI sidebar options
            st.subheader("KAI Analysis")
            st.info("Upload CSV exports for AI analysis")
            if st.button("📊 New Analysis", use_container_width=True, key="sidebar_kai_new"):
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
    
    # Main admin content based on selected mode - ADD KAI MODE
    if st.session_state.get('admin_dashboard_mode') == "admin":
        render_admin_management_dashboard()
    elif st.session_state.get('admin_dashboard_mode') == "premium":
        render_premium_signal_dashboard()
    elif st.session_state.get('admin_dashboard_mode') == "signals_room":
        render_trading_signals_room()
    elif st.session_state.get('admin_dashboard_mode') == "kai_agent":  # NEW: KAI mode
        render_kai_agent()  # Admin gets full KAI functionality with CSV upload
    else:
        render_image_gallery()

def render_admin_dashboard_selection():
    """Interface for admin to choose between admin dashboard and premium dashboard"""
    st.title("👑 Admin Portal - Choose Dashboard")
    st.markdown("---")
    
    col1, col2, col3, col4, col5 = st.columns(5)  # Changed to 5 columns
    
    with col1:
        st.subheader("🛠️ Admin Management")
        st.markdown("""
        **Full System Control:**
        - User management & analytics
        - Email verification
        - Plan management
        - Business metrics
        """)
        if st.button("🚀 Admin Dashboard", use_container_width=True, key="admin_dash_btn"):
            st.session_state.admin_dashboard_mode = "admin"
            st.rerun()
    
    with col2:
        st.subheader("📊 Premium Signals")
        st.markdown("""
        **Signal Management:**
        - Edit trading signals
        - Update market analysis  
        - Manage 5-day cycle
        - Advanced analytics
        """)
        if st.button("📈 Premium Dashboard", use_container_width=True, key="premium_dash_btn"):
            st.session_state.admin_dashboard_mode = "premium"
            st.rerun()
    
    with col3:
        st.subheader("🖼️ Image Gallery")
        st.markdown("""
        **Community Features:**
        - Upload trading charts
        - Share analysis images
        - Community discussions
        - Strategy visualization
        """)
        if st.button("🖼️ Image Gallery", use_container_width=True, key="gallery_dash_btn"):
            st.session_state.admin_dashboard_mode = "gallery"
            st.rerun()
    
    with col4:
        st.subheader("⚡ Trading Signals")
        st.markdown("""
        **Signal Workflow:**
        - Launch trading signals
        - Multi-confirmation system
        - Publish to all users
        - Track performance
        """)
        if st.button("⚡ Signals Room", use_container_width=True, key="signals_dash_btn"):
            st.session_state.admin_dashboard_mode = "signals_room"
            st.rerun()
    
    with col5:  # NEW: KAI column
        st.subheader("🧠 KAI AI Agent")
        st.markdown("""
        **AI Analysis:**
        - CSV strategy analysis
        - Pattern recognition
        - Confidence scoring
        - Time horizon mapping
        - Consistent reporting
        """)
        if st.button("🧠 KAI Agent", use_container_width=True, key="kai_dash_btn"):
            st.session_state.admin_dashboard_mode = "kai_agent"
            st.rerun()
    
    st.markdown("---")
    st.info("💡 **Tip:** Use different dashboards for different management tasks.")

# [ALL YOUR OTHER EXISTING FUNCTIONS REMAIN EXACTLY THE SAME]

if __name__ == "__main__":
    main()
