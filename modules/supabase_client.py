# Create a clean, complete supabase_client.py file
cat > /mount/src/trading.github.io/modules/supabase_client.py << 'EOF'
# modules/supabase_client.py - COMPLETE FILE
import base64
import logging
import uuid
from datetime import datetime
from supabase import create_client, Client
import streamlit as st

# ---------------------------------------------------------
#  Supabase Client Initialization
# ---------------------------------------------------------
try:
    SUPABASE_URL = st.secrets["supabase"]["SUPABASE_URL"]
    SUPABASE_KEY = st.secrets["supabase"]["SUPABASE_KEY"]
    supabase_client = create_client(SUPABASE_URL, SUPABASE_KEY)
    logging.info("✅ Supabase client initialized successfully")
except Exception as e:
    logging.error(f"❌ Error initializing Supabase client: {e}")
    supabase_client = None

# ---------------------------------------------------------
#  Users table functions
# ---------------------------------------------------------
def supabase_get_users():
    """Get all users from Supabase"""
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
    """Save users to Supabase"""
    if not supabase_client:
        return False
    try:
        users_list = []
        for username, user_data in users.items():
            user_data['username'] = username
            users_list.append(user_data)

        response = supabase_client.table('users').upsert(users_list).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error saving users: {response.error}")
            return False
        return True
    except Exception as e:
        st.error(f"Error saving users: {e}")
        return False

def supabase_delete_user(username):
    """Delete user from Supabase"""
    if not supabase_client:
        return False
    try:
        response = supabase_client.table('users').delete().eq('username', username).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error deleting user: {response.error}")
            return False
        return True
    except Exception as e:
        st.error(f"Error deleting user: {e}")
        return False

# ---------------------------------------------------------
#  Analytics table functions
# ---------------------------------------------------------
def supabase_get_analytics():
    """Get analytics data from Supabase"""
    if not supabase_client:
        return {}
    try:
        response = supabase_client.table('analytics').select('*').execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error getting analytics: {response.error}")
            return {}
        if response.data:
            return response.data[0]
        return {}
    except Exception as e:
        st.error(f"Error getting analytics: {e}")
        return {}

def supabase_save_analytics(analytics):
    """Save analytics to Supabase"""
    if not supabase_client:
        return False
    try:
        analytics['id'] = 1
        response = supabase_client.table('analytics').upsert(analytics).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error saving analytics: {response.error}")
            return False
        return True
    except Exception as e:
        st.error(f"Error saving analytics: {e}")
        return False

# ---------------------------------------------------------
#  Helper functions for other modules
# ---------------------------------------------------------
def load_data():
    """Load strategy analyses from Supabase"""
    return supabase_get_strategy_analyses()

def load_gallery_images():
    """Load gallery images from Supabase"""
    return supabase_get_gallery_images()

def load_strategy_indicator_images():
    """Load strategy indicator images from Supabase"""
    return supabase_get_strategy_indicator_images()

def load_signals_data():
    """Load trading signals from Supabase"""
    return supabase_get_trading_signals()

def load_app_settings():
    """Load app settings from Supabase"""
    return supabase_get_app_settings()

def save_app_settings(settings):
    """Save app settings to Supabase"""
    return supabase_save_app_settings(settings)

# ---------------------------------------------------------
#  Constants
# ---------------------------------------------------------
DEEPSEEK_API_KEY = st.secrets.get("deepseek", {}).get("API_KEY", "")
EOF
