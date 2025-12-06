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
#  Strategy analyses table functions
# ---------------------------------------------------------
def supabase_get_strategy_analyses():
    """Get strategy analyses from Supabase"""
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
        st.error(f"Error getting strategy analyses: {e}")
        return {}

def supabase_save_strategy_analyses(strategy_data):
    """Save strategy analyses to Supabase"""
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
            response = supabase_client.table('strategy_analyses').upsert(
                records,
                on_conflict='strategy_name,indicator_name'
            ).execute()
            if hasattr(response, 'error') and response.error:
                st.error(f"Supabase error saving strategy analyses: {response.error}")
                return False
        return True
    except Exception as e:
        st.error(f"Error saving strategy analyses: {e}")
        return False

# ---------------------------------------------------------
#  Gallery images table functions
# ---------------------------------------------------------
def supabase_get_gallery_images():
    """Get gallery images from Supabase"""
    if not supabase_client:
        return []
    try:
        response = supabase_client.table('gallery_images').select('*').execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error getting gallery images: {response.error}")
            return []
        images = []
        for img in response.data:
            if 'bytes_b64' in img:
                img['bytes'] = base64.b64decode(img['bytes_b64'])
            images.append(img)
        return images
    except Exception as e:
        st.error(f"Error getting gallery images: {e}")
        return []

def supabase_save_gallery_images(images):
    """Save gallery images to Supabase"""
    if not supabase_client:
        return False
    try:
        delete_response = supabase_client.table('gallery_images').delete().neq('id', 0).execute()
        if hasattr(delete_response, 'error') and delete_response.error:
            st.error(f"Supabase error clearing gallery images: {delete_response.error}")
            return False

        records = []
        for img in images:
            record = img.copy()
            if 'bytes' in record:
                record['bytes_b64'] = base64.b64encode(record['bytes']).decode('utf-8')
                del record['bytes']
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
    """Clear all gallery images from Supabase"""
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

# ---------------------------------------------------------
#  Trading signals table functions
# ---------------------------------------------------------
def supabase_get_trading_signals():
    """Get trading signals from Supabase"""
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
    """Save trading signals to Supabase"""
    if not supabase_client:
        return False
    try:
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

# ---------------------------------------------------------
#  Signals access tracking functions
# ---------------------------------------------------------
def supabase_get_signals_access_tracking():
    """Get signals access tracking from Supabase"""
    if not supabase_client:
        return []
    try:
        response = supabase_client.table('signals_access_tracking').select('*').execute()
        if hasattr(response, 'error') and response.error:
            return []
        return response.data
    except Exception:
        return []

def supabase_save_signals_access_tracking(tracking_data):
    """Save signals access tracking to Supabase"""
    if not supabase_client:
        return False
    try:
        delete_response = supabase_client.table('signals_access_tracking').delete().neq('id', 0).execute()
        if tracking_data:
            response = supabase_client.table('signals_access_tracking').insert(tracking_data).execute()
        return True
    except Exception:
        return False

def load_signals_access_tracking():
    """Load access tracking from Supabase"""
    try:
        if not supabase_client:
            logging.warning("⚠️ Supabase client not available")
            return []
        
        response = supabase_client.table('signals_access_tracking').select('*').execute()
        
        if hasattr(response, 'error') and response.error:
            logging.warning(f"⚠️ Database load error: {response.error}")
            return []
        
        data = response.data if hasattr(response, 'data') else []
        return data or []
        
    except Exception as e:
        logging.warning(f"⚠️ Error loading access tracking: {e}")
        return []

def save_signals_access_tracking(tracking_data):
    """Save access tracking to Supabase"""
    try:
        if not supabase_client:
            logging.warning("⚠️ Supabase client not available")
            return False
        
        try:
            delete_response = supabase_client.table('signals_access_tracking').delete().neq('id', 0).execute()
        except Exception as delete_error:
            logging.warning(f"⚠️ Clear operation failed: {delete_error}")
        
        if tracking_data:
            cleaned_data = []
            for track in tracking_data:
                cleaned_track = {
                    'username': track.get('username', 'unknown'),
                    'first_access': track.get('first_access', datetime.now().isoformat()),
                    'last_access': track.get('last_access', datetime.now().isoformat()),
                    'access_count': track.get('access_count', 1)
                }
                cleaned_data.append(cleaned_track)
            
            insert_response = supabase_client.table('signals_access_tracking').insert(cleaned_data).execute()
            
            if hasattr(insert_response, 'error') and insert_response.error:
                logging.error(f"❌ Database insert error: {insert_response.error}")
                return False
            
            return True
        else:
            return True
        
    except Exception as e:
        logging.error(f"❌ Error saving access tracking: {e}")
        return False

def track_signals_access(username):
    """Track signals access"""
    try:
        if 'signals_access_tracking' not in st.session_state:
            st.session_state.signals_access_tracking = load_signals_access_tracking()
        
        tracking = st.session_state.signals_access_tracking
        current_time = datetime.now().isoformat()
        
        user_entry = None
        for entry in tracking:
            if entry.get('username') == username:
                user_entry = entry
                break
        
        if user_entry:
            user_entry['last_access'] = current_time
            user_entry['access_count'] = user_entry.get('access_count', 1) + 1
        else:
            tracking.append({
                'username': username,
                'first_access': current_time,
                'last_access': current_time,
                'access_count': 1
            })
        
        st.session_state.signals_access_tracking = tracking
        
        try:
            if supabase_client:
                supabase_client.table('signals_access_tracking').delete().neq('id', 0).execute()
                if tracking:
                    supabase_client.table('signals_access_tracking').insert(tracking).execute()
        except Exception as db_error:
            logging.warning(f"⚠️ DB save failed but continuing: {db_error}")
        
        logging.info(f"✅ Tracked access for: {username}")
        
    except Exception as e:
        logging.error(f"❌ Track access failed: {e}")

# ---------------------------------------------------------
#  App settings table functions
# ---------------------------------------------------------
def supabase_get_app_settings():
    """Get app settings from Supabase"""
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
    """Save app settings to Supabase"""
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

# ---------------------------------------------------------
#  Strategy indicator images table functions
# ---------------------------------------------------------
def supabase_get_strategy_indicator_images():
    """Get strategy indicator images from Supabase"""
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
    """Save strategy indicator images to Supabase"""
    if not supabase_client:
        return False
    try:
        existing_response = supabase_client.table('strategy_indicator_images').select('*').execute()
        if hasattr(existing_response, 'error') and existing_response.error:
            st.error(f"Supabase error getting existing strategy indicator images: {existing_response.error}")
            return False
        existing_records = existing_response.data if existing_response.data else []

        records = []
        for strategy_name, indicators in images_data.items():
            for indicator_name, img_data in indicators.items():
                record = {
                    'strategy_name': strategy_name,
                    'indicator_name': indicator_name,
                    'name': img_data.get('name', f"{strategy_name}_{indicator_name}"),
                    'format': img_data.get('format', 'PNG'),
                    'uploaded_by': img_data.get('uploaded_by', 'unknown'),
                    'timestamp': img_data.get('timestamp', datetime.now().isoformat())
                }

                if 'bytes' in img_data:
                    try:
                        record['bytes_b64'] = base64.b64encode(img_data['bytes']).decode('utf-8')
                    except Exception as e:
                        st.error(f"Error encoding image for {strategy_name}/{indicator_name}: {e}")
                        continue

                records.append(record)

        if records:
            strategies_to_update = list(set([r['strategy_name'] for r in records]))
            for strategy in strategies_to_update:
                delete_response = supabase_client.table('strategy_indicator_images').delete().eq('strategy_name', strategy).execute()
                if hasattr(delete_response, 'error') and delete_response.error:
                    st.error(f"Supabase error deleting strategy indicator images for {strategy}: {delete_response.error}")
                    return False

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
    """Delete specific strategy indicator image from Supabase"""
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

# ---------------------------------------------------------
#  KAI Analyses table functions
# ---------------------------------------------------------
def supabase_get_kai_analyses():
    """Get ALL KAI analyses from Supabase"""
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
    """Save KAI analysis to Supabase"""
    if not supabase_client:
        return False
    try:
        analysis_id = str(uuid.uuid4())

        record = {
            'id': analysis_id,
            'analysis_data': analysis_data,
            'uploaded_by': st.session_state.get('user', {}).get('username', 'anonymous'),
            'created_at': datetime.now().isoformat(),
            'analysis_type': analysis_data.get('analysis_type', 'standard'),
            'deepseek_enhanced': analysis_data.get('deepseek_enhanced', False),
            'confidence_score': analysis_data.get('confidence_assessment', 0),
            'total_strategies': analysis_data.get('overview_metrics', {}).get('total_strategies', 0),
            'reversal_signals': len(analysis_data.get('signal_details', {}).get('reversal_signals', [])),
            'risk_score': analysis_data.get('risk_assessment_data', {}).get('overall_risk_score', 0)
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

def supabase_delete_kai_analysis(analysis_id):
    """Delete a specific KAI analysis from Supabase"""
    if not supabase_client:
        return False
    try:
        response = supabase_client.table('kai_analyses').delete().eq('id', analysis_id).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error deleting KAI analysis: {response.error}")
            return False
        return True
    except Exception as e:
        st.error(f"Error deleting KAI analysis: {e}")
        return False

def supabase_clear_all_kai_analyses():
    """Clear ALL KAI analyses from Supabase (admin only)"""
    if not supabase_client:
        return False
    try:
        response = supabase_client.table('kai_analyses').delete().neq('id', 0).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error clearing KAI analyses: {response.error}")
            return False
        return True
    except Exception as e:
        st.error(f"Error clearing KAI analyses: {e}")
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

def load_kai_analyses():
    """Load KAI analyses from Supabase"""
    return supabase_get_kai_analyses()

def save_kai_analysis(analysis_data):
    """Save KAI analysis to Supabase"""
    return supabase_save_kai_analysis(analysis_data)

def get_latest_kai_analysis():
    """Get the latest KAI analysis from Supabase"""
    return supabase_get_latest_kai_analysis()

def delete_kai_analysis(analysis_id):
    """Delete a specific KAI analysis"""
    return supabase_delete_kai_analysis(analysis_id)

def clear_all_kai_analyses():
    """Clear ALL KAI analyses (admin only)"""
    return supabase_clear_all_kai_analyses()

# ---------------------------------------------------------
#  Constants for other modules
# ---------------------------------------------------------
DEEPSEEK_API_KEY = st.secrets.get("deepseek", {}).get("API_KEY", "")
EOF
