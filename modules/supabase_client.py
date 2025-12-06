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

# SIMPLE DATABASE FUNCTIONS
def supabase_get_signals_access_tracking():
    """Simple: Get who accessed signals room"""
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
    """Simple: Save access tracking"""
    if not supabase_client:
        return False
    try:
        # Clear and replace (simple approach)
        delete_response = supabase_client.table('signals_access_tracking').delete().neq('id', 0).execute()
        
        if tracking_data:
            response = supabase_client.table('signals_access_tracking').insert(tracking_data).execute()
        return True
    except Exception:
        return False

def load_signals_access_tracking():
    """Load access tracking from Supabase - FIXED VERSION"""
    try:
        if not supabase_client:
            logging.warning("⚠️ Supabase client not available")
            return []
        
        response = supabase_client.table('signals_access_tracking').select('*').execute()
        
        if hasattr(response, 'error') and response.error:
            logging.warning(f"⚠️ Database load error (may be normal): {response.error}")
            return []
        
        data = response.data if hasattr(response, 'data') else []
        logging.info(f"✅ Loaded {len(data)} access tracking records")
        return data or []
        
    except Exception as e:
        logging.warning(f"⚠️ Error loading access tracking (may be normal): {e}")
        return []
        
def save_signals_access_tracking(tracking_data):
    """Save access tracking to Supabase - FIXED VERSION"""
    try:
        if not supabase_client:
            logging.warning("⚠️ Supabase client not available")
            return False
        
        # Clear existing tracking data first
        try:
            delete_response = supabase_client.table('signals_access_tracking').delete().neq('id', 0).execute()
            if hasattr(delete_response, 'error') and delete_response.error:
                logging.warning(f"⚠️ Could not clear existing tracking (may be normal): {delete_response.error}")
        except Exception as delete_error:
            logging.warning(f"⚠️ Clear operation failed (may be normal): {delete_error}")
        
        # If we have tracking data to save
        if tracking_data:
            # Ensure each record has required fields
            cleaned_data = []
            for track in tracking_data:
                cleaned_track = {
                    'username': track.get('username', 'unknown'),
                    'first_access': track.get('first_access', datetime.now().isoformat()),
                    'last_access': track.get('last_access', datetime.now().isoformat()),
                    'access_count': track.get('access_count', 1)
                }
                cleaned_data.append(cleaned_track)
            
            # Insert the cleaned data
            insert_response = supabase_client.table('signals_access_tracking').insert(cleaned_data).execute()
            
            if hasattr(insert_response, 'error') and insert_response.error:
                logging.error(f"❌ Database insert error: {insert_response.error}")
                return False
            
            logging.info(f"✅ Saved {len(cleaned_data)} access tracking records")
            return True
        else:
            # No data to save is still successful
            logging.info("✅ Cleared all access tracking (no data to save)")
            return True
        
    except Exception as e:
        logging.error(f"❌ Error saving access tracking: {e}")
        return False
        
def track_signals_access(username):
    """Track signals access - FIXED VERSION"""
    try:
        # Initialize if needed
        if 'signals_access_tracking' not in st.session_state:
            st.session_state.signals_access_tracking = load_signals_access_tracking()
        
        tracking = st.session_state.signals_access_tracking
        current_time = datetime.now().isoformat()
        
        # Find or create user entry
        user_entry = None
        for entry in tracking:
            if entry.get('username') == username:
                user_entry = entry
                break
        
        if user_entry:
            # Update existing
            user_entry['last_access'] = current_time
            user_entry['access_count'] = user_entry.get('access_count', 1) + 1
        else:
            # Create new
            tracking.append({
                'username': username,
                'first_access': current_time,
                'last_access': current_time,
                'access_count': 1
            })
        
        # Always update session state
        st.session_state.signals_access_tracking = tracking
        
        # Try to save to DB (don't block if fails)
        try:
            if supabase_client:
                # Clear old data first
                supabase_client.table('signals_access_tracking').delete().neq('id', 0).execute()
                # Insert new data
                if tracking:
                    supabase_client.table('signals_access_tracking').insert(tracking).execute()
        except Exception as db_error:
            logging.warning(f"⚠️ DB save failed but continuing: {db_error}")
        
        logging.info(f"✅ Tracked access for: {username}")
        
    except Exception as e:
        logging.error(f"❌ Track access failed: {e}")
        
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

# NEW: KAI Analyses table functions - ENHANCED WITH COMPREHENSIVE ARCHIVE
def supabase_get_kai_analyses():
    """Get ALL KAI analyses from Supabase - FIXED VERSION"""
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
        # Generate a unique ID for this analysis
        analysis_id = str(uuid.uuid4())

        # Prepare the record with enhanced metadata
        record = {
            'id': analysis_id,
            'analysis_data': analysis_data,
            'uploaded_by': st.session_state.user['username'],
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


 - UPDATED WITH ENHANCED KAI
# -------------------------
# =====================================================================
# COMPLETE: init_session() - Copy and Replace the Entire Function
# =====================================================================

def init_session():
    """Initialize all session state variables - COMPLETE VERSION WITH TRACKING FIX"""
    try:
        init_purchase_verification_session_state()
    except Exception:
        pass
    
    # --- Gallery pagination state ---
    if 'gallery_page' not in st.session_state:
        st.session_state.gallery_page = 0
    if 'gallery_per_page' not in st.session_state:
        st.session_state.gallery_per_page = 15
    if 'gallery_total_count' not in st.session_state:
        st.session_state.gallery_total_count = 0
    if 'gallery_filter_active' not in st.session_state:
        st.session_state.gallery_filter_active = False
    if 'gallery_filter_author' not in st.session_state:
        st.session_state.gallery_filter_author = "All Authors"
    if 'gallery_filter_strategy' not in st.session_state:
        st.session_state.gallery_filter_strategy = "All Strategies"
    if 'gallery_sort_by' not in st.session_state:
        st.session_state.gallery_sort_by = "Newest First"
    if 'current_image_index' not in st.session_state:
        st.session_state.current_image_index = 0
    if 'image_viewer_mode' not in st.session_state:
        st.session_state.image_viewer_mode = False
    if 'current_page_images' not in st.session_state:
        st.session_state.current_page_images = []

    # --- Core authentication state ---
    if 'user' not in st.session_state:
        st.session_state.user = None
    if 'user_data' not in st.session_state:
        st.session_state.user_data = {}
    if 'app_started' not in st.session_state:
        st.session_state.app_started = True

    # --- User deletion/management modals ---
    if 'show_delete_confirmation' not in st.session_state:
        st.session_state.show_delete_confirmation = False
    if 'user_to_delete' not in st.session_state:
        st.session_state.user_to_delete = None
    if 'show_bulk_delete' not in st.session_state:
        st.session_state.show_bulk_delete = False

    # --- Admin dashboard navigation ---
    if 'admin_view' not in st.session_state:
        st.session_state.admin_view = 'overview'
    if 'manage_user_plan' not in st.session_state:
        st.session_state.manage_user_plan = None
    if 'show_password_change' not in st.session_state:
        st.session_state.show_password_change = False

    # --- User dashboard navigation ---
    if 'dashboard_view' not in st.session_state:
        st.session_state.dashboard_view = 'main'
    if 'show_settings' not in st.session_state:
        st.session_state.show_settings = False
    if 'show_upgrade' not in st.session_state:
        st.session_state.show_upgrade = False

    # --- Strategy selection state ---
    if 'selected_strategy' not in st.session_state:
        st.session_state.selected_strategy = None
    if 'analysis_date' not in st.session_state:
        st.session_state.analysis_date = date.today()
    if 'last_analysis_date' not in st.session_state:
        st.session_state.last_analysis_date = None

    # --- Data persistence tracking ---
    if 'last_save_time' not in st.session_state:
        st.session_state.last_save_time = time.time()

    # --- User credential display ---
    if 'show_user_credentials' not in st.session_state:
        st.session_state.show_user_credentials = False
    if 'user_to_manage' not in st.session_state:
        st.session_state.user_to_manage = None

    # --- Email verification state ---
    if 'admin_email_verification_view' not in st.session_state:
        st.session_state.admin_email_verification_view = 'pending'

    # --- Admin dashboard mode selection ---
    if 'admin_dashboard_mode' not in st.session_state:
        st.session_state.admin_dashboard_mode = None

    # --- Image gallery state ---
    if 'uploaded_images' not in st.session_state:
        st.session_state.uploaded_images = load_gallery_images()
    if 'current_gallery_view' not in st.session_state:
        st.session_state.current_gallery_view = 'gallery'
    if 'selected_image' not in st.session_state:
        st.session_state.selected_image = None

    # --- Gallery clearance confirmation ---
    if 'show_clear_gallery_confirmation' not in st.session_state:
        st.session_state.show_clear_gallery_confirmation = False
    if 'clear_gallery_password' not in st.session_state:
        st.session_state.clear_gallery_password = ""
    if 'clear_gallery_error' not in st.session_state:
        st.session_state.clear_gallery_error = ""

    # --- Image viewer state ---
    if 'current_image_index' not in st.session_state:
        st.session_state.current_image_index = 0
    if 'image_viewer_mode' not in st.session_state:
        st.session_state.image_viewer_mode = False

    # --- Gallery filter and sort state ---
    if 'gallery_filter_author' not in st.session_state:
        st.session_state.gallery_filter_author = "All Authors"
    if 'gallery_filter_strategy' not in st.session_state:
        st.session_state.gallery_filter_strategy = "All Strategies"
    if 'gallery_sort_by' not in st.session_state:
        st.session_state.gallery_sort_by = "Newest First"

    # --- User navigation mode ---
    if 'user_navigation_mode' not in st.session_state:
        st.session_state.user_navigation_mode = "📊 Trading Dashboard"

    # --- Trading Signals Room state ---
    if 'signals_room_view' not in st.session_state:
        st.session_state.signals_room_view = 'active_signals'
    if 'active_signals' not in st.session_state:
        st.session_state.active_signals = load_signals_data()
    
    # 🔧 FIX: Initialize signals_access_tracking PROPERLY
    if 'signals_access_tracking' not in st.session_state:
        st.session_state.signals_access_tracking = []
    # Then load from database
    try:
        st.session_state.signals_access_tracking = load_signals_access_tracking()
    except Exception as e:
        logging.warning(f"Could not load access tracking: {e}")
        st.session_state.signals_access_tracking = []
    
    if 'signal_creation_mode' not in st.session_state:
        st.session_state.signal_creation_mode = 'quick'
    if 'signal_to_confirm' not in st.session_state:
        st.session_state.signal_to_confirm = None
    if 'signal_confirmation_step' not in st.session_state:
        st.session_state.signal_confirmation_step = 1

    # --- Strategy indicator images state ---
    if 'strategy_indicator_images' not in st.session_state:
        st.session_state.strategy_indicator_images = load_strategy_indicator_images()

    # --- Strategy indicator viewer state ---
    if 'strategy_indicator_viewer_mode' not in st.session_state:
        st.session_state.strategy_indicator_viewer_mode = False
    if 'current_strategy_indicator_image' not in st.session_state:
        st.session_state.current_strategy_indicator_image = None
    if 'current_strategy_indicator' not in st.session_state:
        st.session_state.current_strategy_indicator = None

    # --- Strategy list ---
    if "STRATEGIES" not in st.session_state:
        st.session_state.STRATEGIES = {
            "Premium Stoch": "",
            "LS Copy": "",
            "PositionFlow": "",
            "RenkoVol": "",
            "10h WWV": "",
            "Premium Osc Volatility": "",
            "RSI": "",
            "WeisWaveVol": "",
            "PremiumACC": "",
            "VolPress": "",
            "Volatility": "",
            "ACC/DIST": "",
            "Lux Algo": "",
            "Point and Figure": "",
            "Rational Strategy LT": ""
        }

    # --- Strategy analyses data state ---
    if 'strategy_analyses_data' not in st.session_state:
        st.session_state.strategy_analyses_data = load_data()

    # --- Signals Room Password Protection ---
    if 'signals_room_password' not in st.session_state:
        app_settings = load_app_settings()
        st.session_state.signals_room_password = app_settings.get('signals_room_password', 'trading123')
    if 'signals_room_access_granted' not in st.session_state:
        st.session_state.signals_room_access_granted = False
    if 'signals_password_input' not in st.session_state:
        st.session_state.signals_password_input = ""
    if 'signals_password_error' not in st.session_state:
        st.session_state.signals_password_error = ""

    # --- Signals Room Password Change ---
    if 'show_signals_password_change' not in st.session_state:
        st.session_state.show_signals_password_change = False

    # --- Manage User Plan Modal ---
    if 'show_manage_user_plan' not in st.session_state:
        st.session_state.show_manage_user_plan = False

    # --- User password change state ---
    if 'show_user_password_change' not in st.session_state:
        st.session_state.show_user_password_change = False

    # --- Enhanced KAI AI Agent state ---
    if 'kai_analyses' not in st.session_state:
        st.session_state.kai_analyses = load_kai_analyses()
    if 'current_kai_analysis' not in st.session_state:
        st.session_state.current_kai_analysis = None
    if 'kai_analysis_view' not in st.session_state:
        st.session_state.kai_analysis_view = 'latest'
    if 'selected_kai_analysis_id' not in st.session_state:
        st.session_state.selected_kai_analysis_id = None
    if 'kai_analysis_filter' not in st.session_state:
        st.session_state.kai_analysis_filter = 'all'
    if 'kai_analysis_sort' not in st.session_state:
        st.session_state.kai_analysis_sort = 'newest'

    # --- DeepSeek API configuration ---
    if 'use_deepseek' not in st.session_state:
        st.session_state.use_deepseek = True
    if 'deepseek_api_key' not in st.session_state:
        st.session_state.deepseek_api_key = DEEPSEEK_API_KEY

    # --- Additional gallery states ---
    if '_last_user_author_choice' not in st.session_state:
        st.session_state._last_user_author_choice = "All Authors"
    if '_last_user_strategy_choice' not in st.session_state:
        st.session_state._last_user_strategy_choice = "All Strategies"
    if 'show_gallery_stats' not in st.session_state:
        st.session_state.show_gallery_stats = False
    if 'confirm_clear_tracking' not in st.session_state:
        st.session_state.confirm_clear_tracking = False

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
# KAI ANALYSES PERSISTENCE - ENHANCED WITH COMPREHENSIVE ARCHIVE
# -------------------------
def load_kai_analyses():
    """Load ALL KAI analyses from Supabase"""
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

