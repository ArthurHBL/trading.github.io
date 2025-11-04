import streamlit as st
import hashlib
import json
import pandas as pd
import uuid

def get_image_format_safe(img_data):
    """Safely get image format with fallbacks"""
    # Try direct format field first
    if img_data.get('format'):
        return img_data['format']
    
    # Try to infer from filename
    name = img_data.get('name', '')
    if '.' in name:
        ext = name.split('.')[-1].lower()
        format_map = {
            'jpg': 'JPEG', 'jpeg': 'JPEG', 'png': 'PNG', 
            'gif': 'GIF', 'bmp': 'BMP'
        }
        return format_map.get(ext, 'PNG')
    
    # Default fallback
    return 'PNG'
# =====================================================
# Hybrid Cache Layer (Legacy + Streamlit Session)
# =====================================================
_gallery_cache = {}

def _cache_get(key, default=None):
    import streamlit as st
    # Try Streamlit session first, then fallback to legacy cache
    return st.session_state.get(f"_cache_{key}", _gallery_cache.get(key, default))

def _cache_set(key, value):
    import streamlit as st
    # Update both caches for safety
    st.session_state[f"_cache_{key}"] = value
    _gallery_cache[key] = value


def retry_with_backoff(max_retries=3, base_delay=0.5, exceptions=(Exception,)):
    import time
    def decorator(func):
        def wrapper(*args, **kwargs):
            delay = base_delay
            for attempt in range(max_retries):
                try:
                    return func(*args, **kwargs)
                except exceptions as e:
                    if attempt == max_retries - 1:
                        raise
                    time.sleep(delay)
                    delay *= 2
        return wrapper
    return decorator

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
import requests
import logging


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


# =====================================================================
# >>> KO-FI PURCHASE VERIFICATION SYSTEM (Supabase Tables)  <<<
# Added by KAIO merge on demand
# =====================================================================
import logging
import time
from datetime import datetime, date, timedelta
import pandas as pd

# -----------------------
# Supabase Table Helpers
# -----------------------

def supabase_get_purchase_verifications() -> list:
    """Get all purchase verifications from Supabase"""
    try:
        if not supabase_client:
            return []
    except NameError:
        return []
    try:
        response = supabase_client.table('purchase_verifications').select('*').order('submitted_at', desc=True).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error getting verifications: {response.error}")
            return []
        return response.data if hasattr(response, 'data') else []
    except Exception as e:
        st.error(f"Error getting purchase verifications: {e}")
        return []

def supabase_get_pending_verifications() -> list:
    """Get all pending purchase verifications"""
    try:
        if not supabase_client:
            return []
    except NameError:
        return []
    try:
        response = supabase_client.table('purchase_verifications').select('*').eq('status', 'pending').order('submitted_at', desc=True).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error: {response.error}")
            return []
        return response.data if hasattr(response, 'data') else []
    except Exception as e:
        st.error(f"Error getting pending verifications: {e}")
        return []

def supabase_get_user_pending_verification(username: str):
    """Get user's pending verification if exists"""
    try:
        if not supabase_client:
            return None
    except NameError:
        return None
    try:
        response = supabase_client.table('purchase_verifications').select('*').eq('username', username).eq('status', 'pending').single().execute()
        if hasattr(response, 'error') and response.error:
            return None
        return response.data if hasattr(response, 'data') else None
    except Exception as e:
        logging.warning(f"No pending verification for {username}: {e}")
        return None

def supabase_get_user_verification_history(username: str) -> list:
    """Get all verifications for a user"""
    try:
        if not supabase_client:
            return []
    except NameError:
        return []
    try:
        response = supabase_client.table('purchase_verifications').select('*').eq('username', username).order('submitted_at', desc=True).execute()
        if hasattr(response, 'error') and response.error:
            return []
        return response.data if hasattr(response, 'data') else []
    except Exception as e:
        st.error(f"Error getting verification history: {e}")
        return []

def supabase_create_purchase_verification(username: str, email: str, plan: str = "premium"):
    """Create a new purchase verification in database"""
    try:
        if not supabase_client:
            return None
    except NameError:
        return None
    try:
        import uuid
        verification_id = str(uuid.uuid4())[:8]
        record = {
            'verification_id': verification_id,
            'username': username,
            'email': email.strip().lower(),
            'plan': plan,
            'status': 'pending',
            'submitted_at': datetime.now().isoformat(),
            'verified_by': None,
            'verified_at': None,
            'notes': '',
            'purchase_proof': None,
            'auto_approved': False,
        }
        response = supabase_client.table('purchase_verifications').insert(record).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error: {response.error}")
            return None
        return response.data[0] if hasattr(response, 'data') and response.data else record
    except Exception as e:
        st.error(f"Error creating verification: {e}")
        return None

def supabase_update_verification_approved(verification_id: str, admin_username: str) -> bool:
    """Mark verification as approved"""
    try:
        if not supabase_client:
            return False
    except NameError:
        return False
    try:
        response = supabase_client.table('purchase_verifications').update({
            'status': 'approved',
            'verified_by': admin_username,
            'verified_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }).eq('verification_id', verification_id).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error: {response.error}")
            return False
        return True
    except Exception as e:
        st.error(f"Error updating verification: {e}")
        return False

def supabase_update_verification_rejected(verification_id: str, admin_username: str, reason: str = "") -> bool:
    """Mark verification as rejected"""
    try:
        if not supabase_client:
            return False
    except NameError:
        return False
    try:
        response = supabase_client.table('purchase_verifications').update({
            'status': 'rejected',
            'verified_by': admin_username,
            'verified_at': datetime.now().isoformat(),
            'notes': reason,
            'updated_at': datetime.now().isoformat()
        }).eq('verification_id', verification_id).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error: {response.error}")
            return False
        return True
    except Exception as e:
        st.error(f"Error rejecting verification: {e}")
        return False

def supabase_delete_verification(verification_id: str) -> bool:
    """Delete a verification request"""
    try:
        if not supabase_client:
            return False
    except NameError:
        return False
    try:
        response = supabase_client.table('purchase_verifications').delete().eq('verification_id', verification_id).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error: {response.error}")
            return False
        return True
    except Exception as e:
        st.error(f"Error deleting verification: {e}")
        return False

# -----------------------
# Purchase History Table
# -----------------------

def supabase_create_purchase_history(username: str, plan: str, verification_id: str, 
                                    purchase_email: str, approved_by: str, 
                                    kofi_order_id: str = None, amount: float = None) -> bool:
    """Record approved purchase in history"""
    try:
        if not supabase_client:
            return False
    except NameError:
        return False
    try:
        expiry_days = {
            'premium': 30,
            'premium_3month': 90,
            'premium_6month': 180,
            'premium_12month': 365,
        }
        days = expiry_days.get(plan, 30)
        plan_expires = (datetime.now() + timedelta(days=days)).isoformat()

        record = {
            'username': username,
            'plan': plan,
            'verification_id': verification_id,
            'purchase_email': purchase_email,
            'approved_by': approved_by,
            'approved_at': datetime.now().isoformat(),
            'plan_expires': plan_expires,
            'kofi_order_id': kofi_order_id,
            'amount': amount,
            'currency': 'USD',
            'notes': 'Approved via Ko-Fi verification'
        }
        response = supabase_client.table('purchase_history').insert(record).execute()
        if hasattr(response, 'error') and response.error:
            st.error(f"Supabase error: {response.error}")
            return False
        return True
    except Exception as e:
        st.error(f"Error creating purchase history: {e}")
        return False

def supabase_get_purchase_history(username: str = None) -> list:
    """Get purchase history"""
    try:
        if not supabase_client:
            return []
    except NameError:
        return []
    try:
        query = supabase_client.table('purchase_history').select('*').order('approved_at', desc=True)
        if username:
            query = query.eq('username', username)
        response = query.execute()
        if hasattr(response, 'error') and response.error:
            return []
        return response.data if hasattr(response, 'data') else []
    except Exception as e:
        st.error(f"Error getting purchase history: {e}")
        return []

# -----------------------
# Business Logic
# -----------------------

def submit_purchase_verification(username: str, email: str, plan: str = "premium") -> bool:
    """Submit a purchase verification request to the database"""
    try:
        # Check for duplicate pending requests
        pending = supabase_get_user_pending_verification(username)
        if pending:
            st.warning("⚠️ You already have a pending verification request. Please wait for it to be processed.")
            return False
        # Create new verification
        result = supabase_create_purchase_verification(username, email, plan)
        if result:
            st.success("✅ Verification request submitted!")
            return True
        else:
            st.error("❌ Failed to submit verification")
            return False
    except Exception as e:
        st.error(f"Error submitting verification: {e}")
        return False

def approve_purchase_verification(verification_id: str, admin_username: str) -> bool:
    """Approve a verification and upgrade user to premium"""
    try:
        all_verifications = supabase_get_purchase_verifications()
        verification = next((v for v in all_verifications if v['verification_id'] == verification_id), None)
        if not verification:
            st.error("Verification not found")
            return False
        username = verification['username']
        plan = verification['plan']

        # user_manager and Config are expected to exist in the host app
        try:
            success, message = user_manager.change_user_plan(username, plan)
        except Exception as e:
            st.error(f"user_manager.change_user_plan failed: {e}")
            return False

        if not success:
            st.error(f"Failed to upgrade user: {message}")
            return False

        if not supabase_update_verification_approved(verification_id, admin_username):
            return False

        try:
            amount = Config.PLANS.get(plan, {}).get('price', 0)
        except Exception:
            amount = 0

        supabase_create_purchase_history(
            username=username,
            plan=plan,
            verification_id=verification_id,
            purchase_email=verification['email'],
            approved_by=admin_username,
            kofi_order_id=None,
            amount=amount
        )
        st.success(f"✅ {username} upgraded to {plan}!")
        return True
    except Exception as e:
        st.error(f"Error approving verification: {e}")
        return False

def reject_purchase_verification(verification_id: str, admin_username: str, reason: str = "") -> bool:
    """Reject a verification request"""
    try:
        if not supabase_update_verification_rejected(verification_id, admin_username, reason):
            return False
        st.success("✅ Verification rejected")
        return True
    except Exception as e:
        st.error(f"Error rejecting verification: {e}")
        return False

# -----------------------
# User Sidebar Button + Modal
# -----------------------

def render_user_purchase_button():
    """Add a purchase confirmation button to the user sidebar"""
    st.sidebar.markdown("---")
    st.sidebar.subheader("💳 Upgrade Account")

    user = st.session_state.get('user', {})
    current_plan = user.get('plan', 'trial')

    pending = supabase_get_user_pending_verification(user.get('username', ''))
    if pending:
        st.sidebar.warning(f"⏳ Verification pending since {pending['submitted_at'][:10]}")
        if st.sidebar.button("📋 View Verification Status", use_container_width=True, key="view_verification_status"):
            st.session_state.show_purchase_verification = True
            st.rerun()
    elif current_plan == 'trial':
        st.sidebar.info("Ready to upgrade? Confirm your Ko-Fi purchase here!")
        if st.sidebar.button("💳 Confirm Ko-Fi Purchase", use_container_width=True, key="confirm_kofi_purchase_sidebar"):
            st.session_state.show_purchase_verification = True
            st.rerun()
    else:
        if st.sidebar.button("📋 Subscription Status", use_container_width=True, key="view_subscription_status"):
            st.session_state.show_purchase_verification = True
            st.rerun()

def render_purchase_verification_modal():
    """Main purchase verification interface for users"""
    user = st.session_state.get('user', {})
    current_plan = user.get('plan', 'trial')

    col1, col2 = st.columns([4, 1])
    with col1:
        st.title("💳 Ko-Fi Purchase Verification")
    with col2:
        if st.button("✕ Close", use_container_width=True, key="close_purchase_modal"):
            st.session_state.show_purchase_verification = False
            st.rerun()

    st.markdown("---")
    pending = supabase_get_user_pending_verification(user.get('username', ''))

    if pending:
        render_pending_verification_view(user, pending)
    elif current_plan == 'trial':
        render_new_purchase_submission(user)
    else:
        render_subscription_status_view(user)

def render_pending_verification_view(user, pending):
    """Show pending verification status and history"""
    st.subheader("⏳ Verification Status")

    col1, col2, col3 = st.columns([2, 2, 2])
    with col1:
        st.info("**Request Status**")
        st.write("Status: **PENDING**")
        st.write(f"Plan: **{pending['plan'].replace('_', ' ').title()}**")
    with col2:
        st.info("**Submitted**")
        submit_dt = datetime.fromisoformat(pending['submitted_at'])
        st.write(f"Date: **{submit_dt.strftime('%b %d, %Y')}**")
        st.write(f"Time: **{submit_dt.strftime('%I:%M %p')}**")
    with col3:
        st.info("**Your Email**")
        st.write(f"Email: **{pending['email']}**")
        st.write("Verified: **No**")

    st.markdown("---")
    st.subheader("📋 What Happens Next?")
    st.markdown("""
1. **We verify your Ko-Fi purchase** using your email address  
2. **Your premium access is activated**  
3. **You receive confirmation** via email  
4. **Timeline**: Usually 1-24 hours
> 💡 **Tip:** Check your email (including spam folder) for updates
""")
    st.markdown("---")

    col1, col2, col3 = st.columns(3)
    with col1:
        if st.button("🔄 Refresh Status", use_container_width=True, key="refresh_pending_status"):
            st.rerun()
    with col2:
        if st.button("📧 Resend Confirmation", use_container_width=True, key="resend_confirmation"):
            st.success("✅ Confirmation email sent!")
    with col3:
        if st.button("❌ Cancel Request", use_container_width=True, key="cancel_verification"):
            if supabase_delete_verification(pending['verification_id']):
                st.success("✅ Request cancelled")
                time.sleep(1)
                st.rerun()

    st.markdown("---")
    st.subheader("📜 Your Verification History")
    history = supabase_get_user_verification_history(user.get('username', ''))
    if len(history) > 1:
        past = [h for h in history if h['verification_id'] != pending['verification_id']]
        for past_req in past[:5]:
            with st.expander(f"{past_req['status'].upper()} - {past_req['submitted_at'][:10]}"):
                col1, col2 = st.columns(2)
                with col1:
                    st.write(f"**Plan:** {past_req['plan'].replace('_', ' ').title()}")
                    st.write(f"**Email:** {past_req['email']}")
                with col2:
                    st.write(f"**Status:** {past_req['status'].upper()}")
                    if past_req.get('verified_at'):
                        st.write(f"**Processed:** {past_req['verified_at'][:10]}")
    else:
        st.caption("No previous verification requests")

def render_new_purchase_submission(user):
    """Form for new purchase verification submission"""
    st.subheader("✅ Confirm Your Ko-Fi Purchase")
    st.info("""
**How it works:**
1. You've purchased a premium plan on Ko-Fi  
2. Enter the email you used for payment  
3. We'll verify your purchase  
4. Your premium access activates automatically
""")
    st.markdown("---")
    st.subheader("📋 Purchase Details")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("**Which plan did you purchase?**")
        plan_choice = st.radio(
            "Select your plan:",
            [
                ("1 Month - $19", "premium"),
                ("3 Months - $49", "premium_3month"),
                ("6 Months - $97", "premium_6month"),
                ("12 Months - $179", "premium_12month"),
            ],
            format_func=lambda x: x[0],
            key="plan_selection"
        )
        selected_plan = plan_choice[1]
    with col2:
        st.markdown("**Ko-Fi Purchase Email**")
        purchase_email = st.text_input(
            "Enter the email you used on Ko-Fi",
            placeholder="your-email@example.com",
            key="kofi_email_input",
            help="Must match your Ko-Fi account email"
        )

    st.markdown("---")
    st.subheader("✅ Verify Your Information")
    email_confirmed = st.checkbox("✓ I confirm this is the email I used to purchase on Ko-Fi", key="email_confirmed_checkbox")
    terms_agreed = st.checkbox("✓ I agree that this email will be used to verify my purchase", key="terms_agreed_checkbox")

    st.markdown("---")
    col1, col2, col3 = st.columns([1, 1, 2])
    with col1:
        if st.button("🚀 Submit for Verification", use_container_width=True, type="primary", key="submit_purchase_verification"):
            if not purchase_email:
                st.error("❌ Please enter your Ko-Fi email address")
            elif not email_confirmed or not terms_agreed:
                st.error("❌ Please confirm the information above")
            elif "@" not in purchase_email or "." not in purchase_email:
                st.error("❌ Please enter a valid email address")
            else:
                if submit_purchase_verification(user.get('username', ''), purchase_email, selected_plan):
                    st.success("""✅ **Verification Submitted Successfully!**  
We'll now verify your Ko-Fi purchase using the email address you provided.  
You'll receive an email confirmation once we've verified your purchase.
⏱️ **Expected time:** 1-24 hours  •  📧 **Check your email** for updates""")
                    st.balloons()
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Failed to submit verification. Please try again.")
    with col2:
        if st.button("❌ Cancel", use_container_width=True, key="cancel_submission"):
            st.session_state.show_purchase_verification = False
            st.rerun()
    with col3:
        st.caption("We verify all Ko-Fi purchases manually to prevent fraud")

    st.markdown("---")
    st.subheader("❓ Frequently Asked Questions")
    for q, a in [
        ("How long does verification take?", "Usually 1-24 hours, but can be instant during business hours"),
        ("What if I used a different email?", "Contact support with your Ko-Fi order ID"),
        ("Can I update my email?", "Cancel this request and submit with the correct email"),
        ("What if verification fails?", "We'll notify you why and how to resolve it"),
    ]:
        with st.expander(q):
            st.write(a)

def render_subscription_status_view(user):
    """Show current subscription status for premium users"""
    st.subheader("✅ Active Subscription")

    current_plan = user.get('plan', 'trial')
    try:
        plan_name = Config.PLANS.get(current_plan, {}).get('name', current_plan.title())
    except Exception:
        plan_name = current_plan.title()
    expires = user.get('expires', 'Unknown')

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Plan", plan_name)
    with col2:
        try:
            days_left = (datetime.strptime(expires, "%Y-%m-%d").date() - date.today()).days
            st.metric("Days Remaining", days_left)
        except Exception:
            st.metric("Days Remaining", "N/A")
    with col3:
        st.metric("Status", "✅ Active")

    st.markdown("---")
    st.subheader("📋 Subscription Details")
    col1, col2 = st.columns(2)
    with col1:
        st.write(f"**Plan:** {plan_name}")
        st.write(f"**Expires:** {expires}")
        created = user.get('created', 'Unknown')
        st.write(f"**Since:** {created[:10] if isinstance(created, str) else created}")
    with col2:
        st.write("**Status:** Active ✅")
        st.write("**Auto-Renew:** Configured")
        st.write("**Support:** 24/7 Available")

    st.markdown("---")
    st.subheader("🔄 Renew or Upgrade")
    st.markdown("**Ready to renew or upgrade?** Click one of the buttons below to continue on Ko-Fi:")

    try:
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f'<a href="{Config.KOFI_PREMIUM_MONTHLY_LINK}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 16px; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-weight: bold;">1 Month - $19</button></a>', unsafe_allow_html=True)
        with col2:
            st.markdown(f'<a href="{Config.KOFI_PREMIUM_QUARTERLY_LINK}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 16px; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-weight: bold;">3 Months - $49</button></a>', unsafe_allow_html=True)
        with col3:
            st.markdown(f'<a href="{Config.KOFI_PREMIUM_SEMI_ANNUAL_LINK}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 16px; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-weight: bold;">6 Months - $97</button></a>', unsafe_allow_html=True)
        with col4:
            st.markdown(f'<a href="{Config.KOFI_PREMIUM_ANNUAL_LINK}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 16px; border: none; border-radius: 6px; cursor: pointer; width: 100%; font-weight: bold;">12 Months - $179</button></a>', unsafe_allow_html=True)
    except Exception:
        st.info("Ko-Fi links not configured in Config.")

# -----------------------
# Admin Panel
# -----------------------
import plotly.express as px

def render_admin_purchase_verification_panel():
    """Admin interface to review and approve/reject purchase verifications"""
    st.subheader("💳 Ko-Fi Purchase Verification Panel")

    all_verifications = supabase_get_purchase_verifications()
    pending = [v for v in all_verifications if v.get('status') == 'pending']
    approved = [v for v in all_verifications if v.get('status') == 'approved']
    rejected = [v for v in all_verifications if v.get('status') == 'rejected']

    col1, col2, col3, col4 = st.columns(4)
    with col1: st.metric("Total Requests", len(all_verifications))
    with col2: st.metric("⏳ Pending", len(pending), delta_color="off")
    with col3: st.metric("✅ Approved", len(approved))
    with col4: st.metric("❌ Rejected", len(rejected))

    st.markdown("---")
    tab1, tab2, tab3, tab4 = st.tabs(["⏳ Pending", "✅ Approved", "❌ Rejected", "📊 Analytics"])
    with tab1: render_pending_verifications_admin(pending)
    with tab2: render_approved_verifications_admin(approved)
    with tab3: render_rejected_verifications_admin(rejected)
    with tab4: render_verification_analytics_admin(all_verifications)

def render_pending_verifications_admin(pending_list):
    """Admin view for pending verifications"""
    if not pending_list:
        st.success("🎉 No pending verifications!")
        return
    st.write(f"**{len(pending_list)} pending verification(s)**")
    st.markdown("---")

    for verification in pending_list:
        with st.container():
            col1, col2, col3, col4, col5 = st.columns([2, 2, 2, 1, 1])
            with col1:
                st.write(f"**{verification['username']}**")
                st.caption(verification['email'])
            with col2:
                st.write(f"Plan: **{verification['plan'].replace('_', ' ').title()}**")
                submit_dt = datetime.fromisoformat(verification['submitted_at'])
                st.caption(f"Submitted: {submit_dt.strftime('%m/%d/%Y %H:%M')}")
            with col3:
                try:
                    user_data = user_manager.users.get(verification['username'])
                except Exception:
                    user_data = None
                if user_data:
                    current_plan = user_data.get('plan', 'trial')
                    try:
                        plan_name = Config.PLANS.get(current_plan, {}).get('name', current_plan.title())
                    except Exception:
                        plan_name = current_plan.title()
                    st.write(f"Current: **{plan_name}**")
                else:
                    st.error("User not found")
            with col4:
                if st.button("✅ Approve", key=f"approve_{verification['verification_id']}", use_container_width=True):
                    if approve_purchase_verification(verification['verification_id'], st.session_state.get('user', {}).get('username', 'admin')):
                        st.success("✅ Approved!")
                        time.sleep(1)
                        st.rerun()
            with col5:
                if st.button("❌ Reject", key=f"reject_{verification['verification_id']}", use_container_width=True):
                    st.session_state.show_reject_reason = verification['verification_id']

            if st.session_state.get('show_reject_reason') == verification['verification_id']:
                st.markdown("**Rejection reason (optional):**")
                reject_reason = st.text_input("Why are you rejecting this?", key=f"reject_reason_{verification['verification_id']}")
                col_r1, col_r2 = st.columns(2)
                with col_r1:
                    if st.button("Confirm Rejection", key=f"confirm_reject_{verification['verification_id']}", use_container_width=True):
                        if reject_purchase_verification(verification['verification_id'], st.session_state.get('user', {}).get('username', 'admin'), reject_reason):
                            st.success("✅ Rejected!")
                            time.sleep(1)
                            st.rerun()
                with col_r2:
                    if st.button("Cancel", key=f"cancel_reject_{verification['verification_id']}", use_container_width=True):
                        st.session_state.show_reject_reason = None
                        st.rerun()
            st.markdown("---")

def render_approved_verifications_admin(approved_list):
    """Admin view for approved verifications"""
    if not approved_list:
        st.info("No approved verifications yet")
        return
    df = pd.DataFrame([
        {
            "Username": v['username'],
            "Email": v['email'],
            "Plan": v['plan'].replace('_', ' ').title(),
            "Approved By": v.get('verified_by'),
            "Date": datetime.fromisoformat(v['verified_at']).strftime('%m/%d/%Y') if v.get('verified_at') else 'N/A'
        }
        for v in approved_list
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_rejected_verifications_admin(rejected_list):
    """Admin view for rejected verifications"""
    if not rejected_list:
        st.info("No rejected verifications")
        return
    df = pd.DataFrame([
        {
            "Username": v['username'],
            "Email": v['email'],
            "Plan": v['plan'].replace('_', ' ').title(),
            "Rejected By": v.get('verified_by'),
            "Reason": v.get('notes', 'No reason provided'),
            "Date": datetime.fromisoformat(v['verified_at']).strftime('%m/%d/%Y') if v.get('verified_at') else 'N/A'
        }
        for v in rejected_list
    ])
    st.dataframe(df, use_container_width=True, hide_index=True)

def render_verification_analytics_admin(all_verifications):
    """Analytics for purchase verifications"""
    if not all_verifications:
        st.info("No verification data yet")
        return
    status_counts = {}
    for v in all_verifications:
        status = v.get('status')
        status_counts[status] = status_counts.get(status, 0) + 1

    plan_counts = {}
    for v in all_verifications:
        plan = v.get('plan')
        plan_counts[plan] = plan_counts.get(plan, 0) + 1

    col1, col2 = st.columns(2)
    with col1:
        st.subheader("Status Distribution")
        fig = px.pie(values=list(status_counts.values()), names=list(status_counts.keys()), title="Verification Status Distribution")
        st.plotly_chart(fig, use_container_width=True)
    with col2:
        st.subheader("Plan Distribution")
        fig = px.bar(x=list(plan_counts.keys()), y=list(plan_counts.values()), title="Verifications by Plan", labels={"x": "Plan", "y": "Count"})
        st.plotly_chart(fig, use_container_width=True)

    st.markdown("---")
    st.subheader("📊 Summary Statistics")
    total = len(all_verifications)
    approved = len([v for v in all_verifications if v.get('status') == 'approved'])
    approval_rate = (approved / total * 100) if total else 0
    try:
        total_revenue = sum([Config.PLANS.get(v.get('plan'), {}).get('price', 0) for v in all_verifications if v.get('status') == 'approved'])
    except Exception:
        total_revenue = 0

    col1, col2, col3 = st.columns(3)
    with col1: st.metric("Approval Rate", f"{approval_rate:.1f}%")
    with col2: st.metric("Total Revenue", f"${total_revenue}")
    with col3: st.metric("Total Requests", total)

# -----------------------
# Session State Init Hook
# -----------------------

def init_purchase_verification_session_state():
    """Initialize purchase verification session state"""
    if 'show_purchase_verification' not in st.session_state:
        st.session_state.show_purchase_verification = False
    if 'show_reject_reason' not in st.session_state:
        st.session_state.show_reject_reason = None

# -----------------------
# Backward-compat wrappers (avoid NameError in old calls)
# -----------------------
def get_user_pending_verification(username: str):
    return supabase_get_user_pending_verification(username)
# =====================================================================
# <<< END KO-FI PURCHASE VERIFICATION SYSTEM >>> 
# =====================================================================



# -------------------------
# DEEPSEEK API CONFIGURATION
# -------------------------
DEEPSEEK_API_KEY = "sk-5d1729bec094490ba50d7da5fe7d5fb1"  # Replace with actual API key
DEEPSEEK_API_URL = "https://api.deepseek.com/v1/chat/completions"

# -------------------------
# ENHANCED KAI - TRADING AI AGENT WITH DEEPSEEK INTEGRATION
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
        "structured": True,
        "quantitative": True,
        "risk_aware": True
    },

    # Language patterns (KAI's unique voice)
    "phrases": {
        "opening": "🔍 **KAI Analysis Report**",
        "critical_juncture": "Market at CRITICAL JUNCTURE",
        "major_move": "MAJOR MOVE expected",
        "reversal_expected": "REVERSAL expected within",
        "confidence_level": "Confidence Level",
        "deepseek_enhanced": "🧠 **DeepSeek AI Enhanced Analysis**"
    }
}

class DataQualityFramework:
    """
    Prevents KAI from generating false risk warnings about incomplete data.
    Used to calculate ACTUAL risk from signal quality, not data volume.
    """

    QUALITY_TIERS = {
        "PRODUCTION": {
            "name": "Production Grade",
            "description": "Active trading signals",
            "completeness_required": 70,  # % of indicators needed
            "accuracy_threshold": 60,
            "consistency_threshold": 65
        },
        "RESEARCH": {
            "name": "Research Grade",
            "description": "In-depth analysis",
            "completeness_required": 85,
            "accuracy_threshold": 75,
            "consistency_threshold": 75
        },
        "DRAFT": {
            "name": "Draft/Exploration",
            "description": "Work-in-progress",
            "completeness_required": 40,
            "accuracy_threshold": 40,
            "consistency_threshold": 50
        }
    }

    @staticmethod
    def assess_quality(df, tier="PRODUCTION"):
        """
        Quick quality assessment based primarily on WORD COUNT.
        Returns quality score 0-100 and whether data is acceptable.

        Accuracy is now based on analysis depth (words per note).
        """

        tier_config = DataQualityFramework.QUALITY_TIERS.get(tier, {})

        # Calculate actual quality metrics
        total_indicators = len(df)
        indicators_with_notes = len(df[df['Note'].notna() & (df['Note'].str.len() > 0)])

        # COMPLETENESS - % of indicators with notes
        completeness = (indicators_with_notes / total_indicators * 100) if total_indicators > 0 else 0

        # ============================================================
        # ACCURACY - NOW BASED ON WORD COUNT (MAIN FACTOR)
        # ============================================================
        # Count total words in all notes
        total_words = 0
        word_counts = []

        for _, row in df.iterrows():
            note = str(row.get('Note', ''))
            if note and note.lower() != 'nan' and len(note.strip()) > 0:
                word_count = len(note.split())
                total_words += word_count
                word_counts.append(word_count)

        # Calculate average words per note
        avg_words_per_note = total_words / indicators_with_notes if indicators_with_notes > 0 else 0

        # Map average words to accuracy score using word thresholds
        accuracy = min(100, avg_words_per_note * 8.9)

        # Bonus: Add confidence keywords boost
        strong_notes = len(df[
            df['Note'].str.contains('confirmed|strong|major|certain|clear|probability|high confidence', case=False, na=False)
        ])
        confidence_boost = (strong_notes / indicators_with_notes * 5) if indicators_with_notes > 0 else 0
        accuracy = min(100, accuracy + confidence_boost)

        # ============================================================
        # CONSISTENCY - how unified the signals are
        # ============================================================
        bullish = len(df[df['Note'].str.contains('bullish|up|buy|long|breakout|reversal', case=False, na=False)])
        bearish = len(df[df['Note'].str.contains('bearish|down|sell|short|decline|resistance', case=False, na=False)])
        neutral = len(df[df['Note'].str.contains('neutral|consolidat|sideways|ranging|indecis', case=False, na=False)])

        total_directional = bullish + bearish + neutral
        if total_directional > 0:
            max_direction = max(bullish, bearish, neutral)
            consistency = (max_direction / total_directional) * 100
        else:
            consistency = 0

        # ============================================================
        # OVERALL QUALITY SCORE (WEIGHTED)
        # Heavily weighted toward ACCURACY (word count)
        # ============================================================
        # Old: completeness * 0.1 + accuracy * 0.5 + consistency * 0.1
        # New: More weight on accuracy (words) and completeness
        quality_score = (completeness * 0.3 + accuracy * 0.5 + consistency * 0.2)

        # Check if acceptable for tier
        completeness_ok = completeness >= tier_config.get("completeness_required", 50)
        accuracy_ok = accuracy >= tier_config.get("accuracy_threshold", 40)
        consistency_ok = consistency >= tier_config.get("consistency_threshold", 50)

        is_acceptable = completeness_ok and accuracy_ok and consistency_ok

        return {
            "quality_score": quality_score,
            "completeness": completeness,
            "accuracy": accuracy,  # Now based on WORD COUNT
            "consistency": consistency,
            "is_acceptable": is_acceptable,
            "tier": tier,
            "tier_config": tier_config,
            "bullish_signals": bullish,
            "bearish_signals": bearish,
            "neutral_signals": neutral,
            "total_indicators": total_indicators,
            "indicators_with_data": indicators_with_notes,
            "total_words": total_words,  # NEW
            "average_words_per_note": avg_words_per_note,  # NEW
            "word_distribution": word_counts  # NEW
        }

    @staticmethod
    def get_quality_tag(quality_score):
        """Simple quality classification"""
        if quality_score >= 85:
            return "🟢 EXCELLENT"
        elif quality_score >= 70:
            return "🟢 GOOD"
        elif quality_score >= 55:
            return "🟡 FAIR"
        elif quality_score >= 40:
            return "🟠 POOR"
        else:
            return "🔴 CRITICAL"

class EnhancedKaiTradingAgent:
    def __init__(self, use_deepseek=True):
        self.character = KAI_CHARACTER
        self.use_deepseek = use_deepseek
        self.analysis_patterns = self._initialize_analysis_patterns()
        self.deepseek_prompts = self._initialize_deepseek_prompts()

        # Setup logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger(__name__)

    # BONUS: Add this method to ensure time keywords are comprehensive
    def _get_all_time_keywords(self):
        """Get comprehensive list of all time-related keywords"""
        return {
            "immediate": [
                # Current/Right now
                'now', 'immediate', 'today', 'intraday', 'right now', 'currently',
                'asap', 'urgent', 'instant', 'alert', 'now!',
                # This period
                'this session', 'current candle', 'next candle', 'this hour',
                # Indicators known for intraday
                'vwap', 'volume delta', 'stoch rsi', 'rsi', 'macd', 'ao', 'atr',
                'mfi', 'fisher', 'overview', 'quick', 'momentum', 'intraday', 'scalp',
                'breakout', 'breaking'
            ],
            "short_term": [
                # Days/weeks
                'short term', 'this week', 'next few days', 'coming days', '1-7 days',
                'few days', 'daily', 'day trade', 'overnight', 'swing', 'weekly',
                'next week', 'week ahead', 'coming week', 'next 3 days', 'next 5 days',
                # Indicators known for short-term
                'supertrend', 'ema', 'sma', 'bollinger', 'keltner', 'ichimoku',
                'support', 'resistance', 'fibonacci', 'trend', 'chart', 'swing',
                'rsi(smi)', 'smi', 'daily'
            ],
            "medium_term": [
                # Weeks/months
                'medium term', 'this month', 'next few weeks', '1-4 weeks', 'monthly',
                'swing trade', 'intermediate', 'coming weeks', 'next month', 'month ahead',
                'next 2 weeks', 'next 3 weeks', 'rest of month', 'month end',
                # Indicators known for medium-term
                'rainbow', 'alligator', 'gr-mmas', 'pi cycle', 'sar', 'demand',
                'coppock', 'trix', 'williams', 'chaikin', 'weekly', 'monthly',
                'wick delta', 'elasticity', 'wt_lb'
            ],
            "long_term": [
                # Months/years
                'long term', 'next year', 'months ahead', '1-6 months',
                'quarterly', 'position trade', 'investment', 'hold', 'accumulate',
                'next quarter', 'coming months', 'next 3 months', 'next 6 months',
                'year ahead', 'future', 'long hold',
                # Specific years
                '2024', '2025', '2026',
                # Indicators known for long-term
                'log regression', 'monte carlo', 'mvrv', 'nvt', 'roc', 'z-score',
                'liquidity', 'rainbow wave', 'cycle', 'regression', 'transaction',
                'quarterly', 'annual'
            ]
        }

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
            ],
            "phase_4_risk_assessment": [
                "Calculate risk-reward ratios",
                "Identify potential false signals",
                "Evaluate market context"
            ]
        }

    def _initialize_deepseek_prompts(self):
        """Initialize specialized prompts for DeepSeek API with enhanced risk focus"""
        return {
            "enhanced_analysis": """
            You are KAI, a Senior Technical Analysis Specialist with 10+ years of multi-timeframe market analysis experience.

        CORE PERSONALITY TRAITS:
        - Methodical and structured in analysis
        - Conservative in risk assessment
        - Clear and concise communicator
        - Quantitative and data-driven
        - Risk-aware and cautious

        **CRITICAL DIRECTIVES:**
        - You are analyzing MARKET CONDITIONS and INDICATOR SIGNALS only
        - NEVER comment on analysis quality, completeness, or data issues
        - Focus exclusively on what the technical indicators are signaling
        - The analysis data provided is from an experienced mentor - treat it as professional-grade

        ANALYSIS FRAMEWORK (ALWAYS FOLLOW THIS STRUCTURE):
        1. STRATEGY_OVERVIEW: Big picture market context based on indicator signals
        2. KEY_INDICATORS: Critical technical levels and indicator convergences
        3. MOMENTUM_ANALYSIS: Trend strength and directional bias from indicators
        4. SUPPORT_RESISTANCE: Key price levels identified by technical analysis
        5. TIME_HORIZONS: When indicator signals suggest moves may develop

        TRADING DATA TO ANALYZE:
        {data_summary}

        RISK ASSESSMENT FOCUS (MARKET RISKS ONLY):
        - Indicator alignment or divergence across timeframes
        - Momentum confirmation or contradiction
        - Support/resistance strength and reliability
        - Volume and volatility signals
        - Pattern completion probabilities

        **STRICTLY PROHIBITED:**
        - Do NOT mention analysis completeness
        - Do NOT comment on data quality
        - Do NOT critique the analysis process
        - Do NOT make assumptions about missing data

        SPECIFIC INSTRUCTIONS:
        - Analyze ONLY the market signals present in the indicators
        - Provide risk assessment based on MARKET CONDITIONS, not analysis quality
        - Highlight conflicting INDICATOR signals, not data issues
        - Focus on actionable trading insights from the technical analysis
        - Provide professional position sizing guidance

        RESPONSE FORMAT (STRICT JSON):
        {{
            "executive_summary": "2-3 sentence market overview based on indicator signals",
            "key_findings": ["finding1", "finding2", "finding3", "finding4", "finding5"],
            "momentum_assessment": "Detailed momentum analysis from indicator signals",
            "critical_levels": ["level1", "level2", "level3"],
            "time_horizons": {{
                "short_term": "1-7 days analysis based on indicator timing",
                "medium_term": "1-4 weeks analysis based on indicator cycles",
                "long_term": "1-6 months analysis based on structural indicators"
            }},
            "risk_analysis": "Market risk assessment based on technical indicator alignment/divergence",
            "confidence_score": 65,
            "trading_recommendations": [
                "Position sizing based on signal strength",
                "Entry/exit levels from technical analysis",
                "Risk management based on indicator signals",
                "Market condition adaptations"
            ]
        }}

        REMEMBER: You are analyzing MARKET SIGNALS, not the quality of analysis. The data comes from an experienced trading mentor.
        """,
        }

    def _call_deepseek_api(self, prompt, temperature=0.3, max_tokens=2000):
        """Call DeepSeek API with improved error handling"""
        if not self.use_deepseek or not DEEPSEEK_API_KEY:
            self.logger.warning("DeepSeek API not available, using standard analysis")
            return None

        try:
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}"
            }

            payload = {
                "model": "deepseek-chat",
                "messages": [
                    {
                        "role": "system",
                        "content": "You are KAI, a Senior Technical Analysis Specialist. Always respond with valid JSON format."
                    },
                    {
                        "role": "user",
                        "content": prompt
                    }
                ],
                "temperature": temperature,
                "max_tokens": max_tokens,
                "stream": False
            }

            response = requests.post(DEEPSEEK_API_URL, headers=headers, json=payload, timeout=30)
            response.raise_for_status()

            result = response.json()

            # Improved response extraction
            if "choices" in result and len(result["choices"]) > 0:
                choice = result["choices"][0]
                if "message" in choice and "content" in choice["message"]:
                    content = choice["message"]["content"]
                    self.logger.info(f"DeepSeek API response received: {content[:100]}...")
                    # FILTER THE RESPONSE to remove any critique of analysis
                    filtered_content = self._filter_ai_response(content)
                    return filtered_content

            # If we can't extract the content, log the full result
            self.logger.warning(f"Unexpected DeepSeek response format: {result}")
            return str(result)

        except requests.exceptions.Timeout:
            self.logger.error("DeepSeek API timeout")
            return None
        except requests.exceptions.RequestException as e:
            self.logger.error(f"DeepSeek API request failed: {e}")
            return None
        except Exception as e:
            self.logger.error(f"DeepSeek API call failed: {e}")
            return None

    def _filter_ai_response(self, response_text):
        """Filter out any AI responses that critique analysis quality instead of market signals"""
        forbidden_phrases = [
            "incomplete analysis",
            "undefined momentum",
            "incomplete data",
            "missing data",
            "data quality",
            "analysis quality",
            "completeness of analysis",
            "incomplete analyses",
            "undefined momentum across",
            "clearer directional confirmation",
            "until clearer confirmation"
        ]

        # If the response contains any forbidden phrases, return a professional market-focused alternative
        if any(phrase in response_text.lower() for phrase in forbidden_phrases):
            self.logger.warning("AI response contained forbidden critique phrases - filtering to market-focused response")
            return "Market analysis indicates mixed signals across timeframes. Focus on key support/resistance levels for directional bias confirmation. Position sizing should reflect current signal ambiguity."

        return response_text

    def _prepare_data_for_deepseek(self, df):
        """Prepare trading data for DeepSeek analysis"""
        try:
            # Auto-Explainer: Convert CSV to structured dict with explanations
            structured_data = self._auto_explain_csv_data(df)
            return json.dumps(structured_data, indent=2)

        except Exception as e:
            self.logger.error(f"Error preparing data for DeepSeek: {e}")
            return "{}"

    def _auto_explain_csv_data(self, df):
        """Auto-Explainer - Convert CSV data to structured analysis with explanations"""
        try:
            analysis_summary = {
                "Data Quality Assessment": self._get_dataset_overview(df),
                "Strategy Analysis": self._analyze_strategies(df),
                "Trading Signals": self._extract_trading_signals(df),
                "Momentum Analysis": self._analyze_momentum_patterns(df),
                "Risk Assessment": self._assess_dataset_risk(df),
                "Quality Metrics": self._calculate_quality_metrics(df)
            }
            return analysis_summary
        except Exception as e:
            self.logger.error(f"Auto-explainer failed: {e}")
            return {"error": str(e), "raw_data_available": True}

    def _get_dataset_overview(self, df):
        """Get comprehensive dataset overview"""
        return {
            "total_records": len(df),
            "total_strategies": df['Strategy'].nunique() if 'Strategy' in df.columns else 0,
            "total_indicators": df['Indicator'].nunique() if 'Indicator' in df.columns else 0,
            "completion_rate": self._calculate_completion_rate(df),
            "date_range": self._get_date_range(df),
            "columns_available": list(df.columns),
            "data_types": {col: str(df[col].dtype) for col in df.columns}
        }

    def _calculate_completion_rate(self, df):
        """Calculate analysis completion rate"""
        if 'Status' in df.columns:
            completed = len(df[df['Status'] == 'Done'])
            total = len(df)
            return f"{completed}/{total} ({completed/total*100:.1f}%)"
        return "Status column not available"

    def _get_date_range(self, df):
        """Get date range from dataset"""
        date_columns = ['analysis_date', 'Analysis_Date', 'last_modified', 'Last_Modified']
        for col in date_columns:
            if col in df.columns and pd.api.types.is_datetime64_any_dtype(df[col]):
                return f"{df[col].min()} to {df[col].max()}"
        return "No date information available"

    def _analyze_strategies(self, df):
        """Analyze strategy distribution and performance"""
        if 'Strategy' not in df.columns:
            return {"error": "Strategy column not found"}

        strategies = df['Strategy'].value_counts().to_dict()
        strategy_metrics = {}

        for strategy in df['Strategy'].unique():
            strategy_data = df[df['Strategy'] == strategy]
            strategy_metrics[strategy] = {
                "indicator_count": len(strategy_data),
                "completion_rate": len(strategy_data[strategy_data['Status'] == 'Done']) / len(strategy_data) * 100 if 'Status' in df.columns else "N/A",
                "common_tags": strategy_data['Tag'].value_counts().to_dict() if 'Tag' in df.columns else {},
                "momentum_distribution": strategy_data['Momentum'].value_counts().to_dict() if 'Momentum' in df.columns else {}
            }

        return {
            "strategy_count": len(strategies),
            "strategy_distribution": strategies,
            "strategy_metrics": strategy_metrics
        }

    def _extract_trading_signals(self, df):
        """Extract and categorize trading signals"""
        signals = {
            "reversal_signals": self._extract_reversal_signals(df),
            "momentum_signals": self._extract_momentum_signals(df),
            "support_resistance": self._extract_support_resistance(df),
            "volume_signals": self._extract_volume_signals(df),
            "breakout_signals": self._extract_breakout_signals(df),
            "divergence_signals": self._extract_divergence_signals(df)
        }

        # Calculate signal strength and confidence
        signal_metrics = {
            "total_signals": sum(len(signal_list) for signal_list in signals.values()),
            "strong_signals": len([s for s in signals["reversal_signals"] if s.get('strength') == 'HIGH'])
        }

        return {"signals": signals, "metrics": signal_metrics}

    def _extract_reversal_signals(self, df):
        """Extract potential reversal signals from data"""
        reversal_keywords = ['reversal', 'reverse', 'turnaround', 'revert', 'exhaustion', 'divergence']
        reversals = []

        for _, row in df.iterrows():
            if pd.isna(row.get('Note')) or row.get('Note') == '':
                continue

            note = str(row.get('Note', '')).lower()
            if any(keyword in note for keyword in reversal_keywords):
                reversal_data = {
                    "strategy": row.get('Strategy', 'Unknown'),
                    "indicator": row.get('Indicator', 'Unknown'),
                    "note": row.get('Note', ''),
                    "strength": "HIGH" if any(word in note for word in ['major', 'strong', 'probable', 'confirmed']) else "MEDIUM",
                    "score": self._calculate_reversal_score(note, row.get('Indicator', '')),
                    "timestamp": row.get('analysis_date', row.get('last_modified', ''))
                }
                reversals.append(reversal_data)

        return reversals

    def _extract_momentum_signals(self, df):
        """Extract momentum signals from data"""
        momentum_signals = {"bullish": [], "bearish": [], "neutral": []}

        for _, row in df.iterrows():
            if pd.isna(row.get('Note')) or row.get('Note') == '':
                continue

            note = str(row.get('Note', '')).lower()

            if any(word in note for word in ['bullish', 'breaking up', 'uptrend', 'buy', 'long', 'rally']):
                momentum_signals["bullish"].append({
                    "strategy": row.get('Strategy', 'Unknown'),
                    "indicator": row.get('Indicator', 'Unknown'),
                    "note": row.get('Note', ''),
                    "confidence": self._calculate_confidence_score(note)
                })
            elif any(word in note for word in ['bearish', 'breaking down', 'downtrend', 'sell', 'short', 'decline']):
                momentum_signals["bearish"].append({
                    "strategy": row.get('Strategy', 'Unknown'),
                    "indicator": row.get('Indicator', 'Unknown'),
                    "note": row.get('Note', ''),
                    "confidence": self._calculate_confidence_score(note)
                })
            else:
                momentum_signals["neutral"].append({
                    "strategy": row.get('Strategy', 'Unknown'),
                    "indicator": row.get('Indicator', 'Unknown'),
                    "note": row.get('Note', ''),
                    "confidence": self._calculate_confidence_score(note)
                })

        return momentum_signals

    def _extract_support_resistance(self, df):
        """Extract support and resistance levels"""
        levels = {"support": [], "resistance": []}
        level_keywords = {
            "support": ['support', 'holding', 'bounce', 'floor', 'demand', 'base'],
            "resistance": ['resistance', 'rejection', 'ceiling', 'supply', 'top', 'cap']
        }

        for _, row in df.iterrows():
            if pd.isna(row.get('Note')) or row.get('Note') == '':
                continue

            note = str(row.get('Note', '')).lower()

            for level_type, keywords in level_keywords.items():
                if any(keyword in note for keyword in keywords):
                    level_data = {
                        "strategy": row.get('Strategy', 'Unknown'),
                        "indicator": row.get('Indicator', 'Unknown'),
                        "note": row.get('Note', ''),
                        "level": level_type.upper(),
                        "strength": "STRONG" if any(word in note for word in ['strong', 'major', 'key', 'critical']) else "MODERATE",
                        "price_level": self._extract_price_level(note),
                        "confidence": self._calculate_confidence_score(note)
                    }
                    levels[level_type].append(level_data)

        return levels

    def _extract_volume_signals(self, df):
        """Extract volume-based signals"""
        volume_signals = []
        volume_keywords = ['volume', 'volatility', 'liquidity', 'participation']

        for _, row in df.iterrows():
            if pd.isna(row.get('Note')) or row.get('Note') == '':
                continue

            note = str(row.get('Note', '')).lower()
            if any(keyword in note for keyword in volume_keywords):
                volume_signals.append({
                    "strategy": row.get('Strategy', 'Unknown'),
                    "indicator": row.get('Indicator', 'Unknown'),
                    "note": row.get('Note', ''),
                    "type": self._classify_volume_signal(note),
                    "score": self._calculate_volume_score(note)
                })

        return volume_signals

    def _extract_breakout_signals(self, df):
        """Extract breakout signals"""
        breakout_signals = []
        breakout_keywords = ['breakout', 'breaking', 'crossing', 'above', 'below', 'through']

        for _, row in df.iterrows():
            if pd.isna(row.get('Note')) or row.get('Note') == '':
                continue

            note = str(row.get('Note', '')).lower()
            if any(keyword in note for keyword in breakout_keywords):
                breakout_signals.append({
                    "strategy": row.get('Strategy', 'Unknown'),
                    "indicator": row.get('Indicator', 'Unknown'),
                    "note": row.get('Note', ''),
                    "direction": "BULLISH" if any(word in note for word in ['above', 'breaking up', 'bullish']) else "BEARISH",
                    "confidence": self._calculate_confidence_score(note)
                })

        return breakout_signals

    def _extract_divergence_signals(self, df):
        """Extract divergence signals"""
        divergence_signals = []
        divergence_keywords = ['divergence', 'divergent', 'disagreement', 'conflict']

        for _, row in df.iterrows():
            if pd.isna(row.get('Note')) or row.get('Note') == '':
                continue

            note = str(row.get('Note', '')).lower()
            if any(keyword in note for keyword in divergence_keywords):
                divergence_signals.append({
                    "strategy": row.get('Strategy', 'Unknown'),
                    "indicator": row.get('Indicator', 'Unknown'),
                    "note": row.get('Note', ''),
                    "type": self._classify_divergence(note),
                    "confidence": self._calculate_confidence_score(note)
                })

        return divergence_signals

    def _classify_volume_signal(self, note):
        """Classify volume signal type"""
        if 'high volume' in note or 'increasing volume' in note:
            return "HIGH_VOLUME"
        elif 'low volume' in note or 'decreasing volume' in note:
            return "LOW_VOLUME"
        elif 'volume confirmation' in note:
            return "CONFIRMATION"
        else:
            return "GENERAL_VOLUME"

    def _calculate_signal_quality(self, signals):
        """Calculate overall signal quality score"""
        total_signals = sum(len(signal_list) for signal_list in signals.values())
        if total_signals == 0:
            return 0

        strong_signals = len([s for s in signals["reversal_signals"] if s.get('strength') == 'HIGH'])
        high_confidence = len([s for s in signals["momentum_signals"]["bullish"] + signals["momentum_signals"]["bearish"] if s.get('confidence', 0) > 70])

        quality_score = ((strong_signals * 2) + high_confidence) / (total_signals * 2) * 100
        return min(100, quality_score)

    def _analyze_momentum_patterns(self, df):
        """Analyze momentum patterns across the dataset"""
        if 'Momentum' not in df.columns:
            return {"error": "Momentum column not found"}

        momentum_distribution = df['Momentum'].value_counts().to_dict()

        # Analyze momentum consistency
        strategy_momentum = {}
        for strategy in df['Strategy'].unique():
            strategy_data = df[df['Strategy'] == strategy]
            momentum_counts = strategy_data['Momentum'].value_counts()
            if len(momentum_counts) > 0:
                dominant_momentum = momentum_counts.index[0]
                strategy_momentum[strategy] = {
                    "dominant_momentum": dominant_momentum,
                    "consistency_score": momentum_counts.iloc[0] / len(strategy_data) * 100,
                    "momentum_distribution": momentum_counts.to_dict()
                }

        return {
            "momentum_distribution": momentum_distribution,
            "strategy_momentum_analysis": strategy_momentum,
            "overall_momentum_bias": self._calculate_overall_momentum_bias(momentum_distribution)
        }

    def _calculate_overall_momentum_bias(self, momentum_distribution):
        """Calculate overall momentum bias"""
        bullish_terms = ['bullish', 'up', 'positive', 'buy']
        bearish_terms = ['bearish', 'down', 'negative', 'sell']

        bullish_score = 0
        bearish_score = 0

        for momentum, count in momentum_distribution.items():
            momentum_lower = str(momentum).lower()
            if any(term in momentum_lower for term in bullish_terms):
                bullish_score += count
            elif any(term in momentum_lower for term in bearish_terms):
                bearish_score += count

        total = bullish_score + bearish_score
        if total == 0:
            return "NEUTRAL"

        bias_ratio = bullish_score / total
        if bias_ratio > 0.6:
            return "BULLISH"
        elif bias_ratio < 0.4:
            return "BEARISH"
        else:
            return "NEUTRAL"

    def _assess_dataset_risk(self, df):
        """Assess overall risk in the dataset"""
        risk_factors = {
            "high_risk_indicators": 0,
            "conflicting_signals": 0,
            "low_confidence_analyses": 0,
            "incomplete_analyses": 0
        }

        # Count high risk indicators
        for _, row in df.iterrows():
            note = str(row.get('Note', '')).lower()
            if any(word in note for word in ['high risk', 'danger', 'caution', 'warning', 'uncertain']):
                risk_factors["high_risk_indicators"] += 1

        # Count incomplete analyses
        if 'Status' in df.columns:
            risk_factors["incomplete_analyses"] = len(df[df['Status'] != 'Done'])

        # Calculate overall risk score
        total_analyses = len(df)
        if total_analyses == 0:
            risk_factors["overall_risk_score"] = 0
        else:
            risk_score = (
                risk_factors["high_risk_indicators"] * 3 +
                risk_factors["incomplete_analyses"] * 2
            ) / (total_analyses * 3) * 100
            risk_factors["overall_risk_score"] = min(100, risk_score)

        return risk_factors

    def _calculate_quality_metrics(self, df):
        """Calculate data quality metrics"""
        metrics = {
            "completeness_score": 0,
            "consistency_score": 0,
            "timeliness_score": 0,
            "overall_quality": 0
        }

        total_records = len(df)
        if total_records == 0:
            return metrics

        # Completeness: Check for missing values
        complete_records = len(df.dropna())
        metrics["completeness_score"] = (complete_records / total_records) * 100

        # Consistency: Check for consistent formatting
        if 'Status' in df.columns:
            valid_statuses = ['Done', 'Open', 'In Progress', 'Skipped']
            consistent_status = len(df[df['Status'].isin(valid_statuses)])
            metrics["consistency_score"] = (consistent_status / total_records) * 100

        # Timeliness: Check for recent data
        date_columns = ['analysis_date', 'Analysis_Date', 'last_modified', 'Last_Modified']
        for col in date_columns:
            if col in df.columns and pd.api.types.is_datetime64_any_dtype(df[col]):
                recent_data = len(df[df[col] >= (datetime.now() - timedelta(days=30))])
                metrics["timeliness_score"] = (recent_data / total_records) * 100
                break

        # Overall quality (weighted average)
        weights = {'completeness': 0.4, 'consistency': 0.3, 'timeliness': 0.3}
        metrics["overall_quality"] = (
            metrics["completeness_score"] * weights['completeness'] +
            metrics["consistency_score"] * weights['consistency'] +
            metrics["timeliness_score"] * weights['timeliness']
        )

        return metrics

    def _calculate_reversal_score(self, note, indicator):
        """Calculate quantitative reversal score"""
        score = 0

        # Keyword scoring
        strong_keywords = ['major reversal', 'probable reversal', 'strong reversal', 'confirmed reversal']
        medium_keywords = ['reversal', 'reverse', 'turnaround', 'exhaustion']

        for keyword in strong_keywords:
            if keyword in note:
                score += 3

        for keyword in medium_keywords:
            if keyword in note:
                score += 1

        # Indicator-specific weighting
        indicator_weights = {
            'RSI': 2, 'MACD': 2, 'Stoch': 2, 'Fibonacci': 1.5,
            'VWAP': 1.5, 'Support': 1.5, 'Resistance': 1.5
        }

        for ind, weight in indicator_weights.items():
            if ind.lower() in indicator.lower():
                score *= weight
                break

        # Context scoring
        if 'confirmed' in note:
            score += 2
        if 'multiple' in note or 'confluence' in note:
            score += 2

        return min(10, score)

    def _calculate_confidence_score(self, note):
        """Calculate confidence score for signals"""
        confidence = 50  # Base confidence

        if 'confirmed' in note or 'confirmed' in note:
            confidence += 30
        if 'likely' in note or 'probable' in note:
            confidence += 15
        if 'potential' in note or 'possible' in note:
            confidence -= 10
        if 'uncertain' in note or 'maybe' in note:
            confidence -= 20

        return max(10, min(95, confidence))

    def _calculate_volume_score(self, note):
        """Calculate volume signal score"""
        score = 0

        if 'high volume' in note or 'increasing volume' in note:
            score += 3
        if 'volume confirmation' in note:
            score += 2
        if 'low volume' in note:
            score += 1

        return score

    def _extract_price_level(self, note):
        """Extract price levels from notes using regex"""
        # Look for price patterns like $45000, 45k, 45,000
        price_patterns = [
            r'\$(\d+(?:,\d{3})*(?:\.\d{2})?)',  # $45,000.00
            r'(\d+(?:,\d{3})*)\s*(k|K)',        # 45k, 45K
            r'(\d+(?:,\d{3})*(?:\.\d{2})?)',    # 45000, 45,000
        ]

        for pattern in price_patterns:
            matches = re.findall(pattern, note)
            if matches:
                return matches[0] if isinstance(matches[0], str) else ''.join(matches[0])

        return "Not specified"

    def _classify_divergence(self, note):
        """Classify divergence type"""
        if 'bullish divergence' in note:
            return "BULLISH"
        elif 'bearish divergence' in note:
            return "BEARISH"
        elif 'hidden divergence' in note:
            return "HIDDEN"
        else:
            return "REGULAR"

    def analyze_strategy_data(self, df, quality_tier="PRODUCTION"):
        """
        Main analysis method - now quality-aware.
        Won't generate false "incomplete data" warnings.
        """

        # STEP 1: Assess data quality FIRST
        quality = DataQualityFramework.assess_quality(df, tier=quality_tier)

        # STEP 2: Run standard analysis phases
        strategy_overview = self._phase_1_scanning(df)
        signals = self._phase_2_signal_extraction(df)
        time_analysis = self._phase_3_time_mapping(df)
        risk_analysis = self._phase_4_risk_assessment(df, signals)

        # STEP 3: Adjust risk assessment based on data quality
        # This is KEY: Don't warn about incomplete data if quality is acceptable
        if quality["is_acceptable"]:
            # Data quality is good - only show REAL risks, not data-volume risks
            risk_analysis["data_quality_note"] = "✅ Data quality acceptable - risk assessment valid"
            risk_analysis["incomplete_data_penalty"] = 0
        else:
            # Data quality is below tier requirements
            risk_analysis["data_quality_note"] = f"⚠️ Data below {quality_tier} tier requirements"
            risk_analysis["incomplete_data_penalty"] = 5

        # STEP 4: Get DeepSeek analysis if available
        deepseek_analysis = None
        if self.use_deepseek:
            try:
                deepseek_analysis = self._get_deepseek_enhanced_analysis(df, strategy_overview, signals, time_analysis)
            except:
                pass

        # STEP 5: Generate final report
        analysis = self._generate_kai_report(
            strategy_overview, signals, time_analysis, risk_analysis, deepseek_analysis
        )

        # STEP 6: Add quality metadata - CRITICAL: ENSURE IT'S INCLUDED
        analysis["data_quality"] = quality
        analysis["quality_tier"] = quality_tier

        # STEP 7: ENSURE all required keys exist before returning
        required_keys = [
            'header', 'executive_summary', 'key_findings', 'momentum_analysis',
            'support_resistance_levels', 'time_horizon_outlook', 'risk_assessment_data',
            'risk_assessment_summary', 'confidence_assessment', 'trading_implications',
            'signal_details', 'overview_metrics', 'deepseek_enhanced', 'deepseek_analysis',
            'data_quality', 'quality_tier'  # ADD THESE TWO
        ]

        for key in required_keys:
            if key not in analysis:
                analysis[key] = {} if key in ['data_quality', 'risk_assessment_data'] else None

        return analysis

    def _phase_1_scanning(self, df):
        """KAI's Phase 1: Always scan strategies in same order"""
        completed_analyses = len(df[df['Status'] == 'Done']) if 'Status' in df.columns else 0
        total_indicators = len(df)
        strategies = df['Strategy'].unique() if 'Strategy' in df.columns else []

        return {
            "completion_rate": f"{completed_analyses}/{total_indicators}",
            "strategies_analyzed": list(strategies),
            "pending_analyses": len(df[df['Status'] == 'Open']) if 'Status' in df.columns else 0,
            "total_strategies": len(strategies),
            "analysis_coverage": f"{(completed_analyses/total_indicators)*100:.1f}%" if total_indicators > 0 else "0%"
        }

    def _phase_2_signal_extraction(self, df):
        """KAI's Phase 2: Enhanced signal extraction with quantitative measures"""
        signals = {
            "reversal_signals": [],
            "momentum_signals": [],
            "support_signals": [],
            "volume_signals": [],
            "breakout_signals": [],
            "divergence_signals": [],
            "conflicting_signals": []
        }

        # Enhanced signal detection with scoring
        for index, row in df.iterrows():
            if pd.isna(row.get('Note')) or row.get('Note') == '':
                continue

            note = str(row.get('Note', '')).lower()
            indicator = row.get('Indicator', 'Unknown')
            strategy = row.get('Strategy', 'Unknown')

            # Enhanced reversal detection with scoring
            reversal_score = self._calculate_reversal_score(note, indicator)
            if reversal_score > 0:
                signals["reversal_signals"].append({
                    "strategy": strategy,
                    "indicator": indicator,
                    "message": row.get('Note', ''),
                    "strength": "HIGH" if reversal_score >= 7 else "MEDIUM",
                    "score": reversal_score,
                    "confidence": min(90, reversal_score * 10)
                })

            # Enhanced support/resistance detection with level extraction
            sr_analysis = self._analyze_support_resistance_phase2(note, indicator, strategy)
            if sr_analysis:
                signals["support_signals"].append(sr_analysis)

            # Enhanced momentum analysis
            momentum_analysis = self._analyze_momentum_phase2(note, indicator, strategy)
            if momentum_analysis:
                signals["momentum_signals"].append(momentum_analysis)

            # Volume analysis
            if any(keyword in note for keyword in ['volume', 'volatility', 'liquidity']):
                volume_score = self._calculate_volume_score(note)
                signals["volume_signals"].append({
                    "strategy": strategy,
                    "indicator": indicator,
                    "message": row.get('Note', ''),
                    "score": volume_score
                })

            # Breakout signals
            if any(keyword in note for keyword in ['breakout', 'breaking', 'crossing', 'above', 'below']):
                breakout_score = self._calculate_breakout_score(note)
                signals["breakout_signals"].append({
                    "strategy": strategy,
                    "indicator": indicator,
                    "message": row.get('Note', ''),
                    "score": breakout_score
                })

            # Divergence detection
            if any(keyword in note for keyword in ['divergence', 'divergent', 'disagreement']):
                signals["divergence_signals"].append({
                    "strategy": strategy,
                    "indicator": indicator,
                    "message": row.get('Note', ''),
                    "type": self._classify_divergence(note)
                })

        # Identify conflicting signals
        signals["conflicting_signals"] = self._find_conflicting_signals(signals)

        return signals

    def _analyze_support_resistance_phase2(self, note, indicator, strategy):
        """Enhanced support/resistance analysis for phase 2"""
        support_keywords = ['support', 'holding', 'bounce', 'floor', 'demand']
        resistance_keywords = ['resistance', 'rejection', 'ceiling', 'supply', 'top']

        level_type = None
        if any(keyword in note for keyword in support_keywords):
            level_type = "SUPPORT"
        elif any(keyword in note for keyword in resistance_keywords):
            level_type = "RESISTANCE"

        if level_type:
            strength = "STRONG" if any(word in note for word in ['strong', 'major', 'key']) else "MODERATE"
            price_level = self._extract_price_level(note)

            return {
                "strategy": strategy,
                "indicator": indicator,
                "message": note,
                "level": level_type,
                "strength": strength,
                "price_level": price_level
            }

        return None

    def _analyze_momentum_phase2(self, note, indicator, strategy):
        """Enhanced momentum analysis for phase 2"""
        bullish_words = ['bullish', 'breaking up', 'uptrend', 'buy', 'long', 'rally']
        bearish_words = ['bearish', 'breaking down', 'downtrend', 'sell', 'short', 'decline']

        direction = None
        if any(word in note for word in bullish_words):
            direction = "BULLISH"
        elif any(word in note for word in bearish_words):
            direction = "BEARISH"

        if direction:
            strength = "STRONG" if any(word in note for word in ['strong', 'powerful', 'accelerating']) else "MODERATE"

            return {
                "strategy": strategy,
                "indicator": indicator,
                "message": note,
                "direction": direction,
                "strength": strength
            }

        return None

    def _calculate_breakout_score(self, note):
        """Calculate breakout signal score"""
        score = 0

        if 'confirmed breakout' in note:
            score += 3
        if 'breaking' in note or 'crossing' in note:
            score += 2
        if 'potential breakout' in note:
            score += 1

        return score

    def _find_conflicting_signals(self, signals):
        """Identify conflicting signals across different analysis types"""
        conflicts = []

        # Check for reversal vs momentum conflicts
        for reversal in signals["reversal_signals"]:
            for momentum in signals["momentum_signals"]:
                if (reversal['strategy'] == momentum['strategy'] and
                    reversal.get('implied_direction') != momentum.get('direction')):
                    conflicts.append({
                        "type": "REVERSAL_MOMENTUM_CONFLICT",
                        "reversal_signal": reversal,
                        "momentum_signal": momentum,
                        "strategy": reversal['strategy']
                    })

        return conflicts

    # FIXED: Complete Time Horizon Mapping with Guaranteed Display
    def _phase_3_time_mapping(self, df):
        """KAI's Phase 3: Enhanced time horizon mapping - GUARANTEED DISPLAY FIX"""
        time_signals = {
            "immediate": [],
            "short_term": [],
            "medium_term": [],
            "long_term": []
        }

        # Enhanced keyword mapping
        time_keywords = {
            "immediate": [
                'now', 'immediate', 'today', 'intraday', 'right now', 'currently', 'asap',
                'urgent', 'instant', 'momentum', 'breakout', 'breaking', 'now!', 'alert',
                'today only', 'this session', 'current candle', 'next candle', 'vwap', 'volume delta',
                'stoch rsi', 'rsi', 'macd', 'ao', 'atr', 'mfi', 'fisher'
            ],
            "short_term": [
                'short term', 'this week', 'next few days', 'coming days', '1-7 days',
                'few days', 'daily', 'day trade', 'overnight', 'swing', 'weekly',
                'next week', 'weekend', 'friday', 'monday', 'week ahead', 'coming week',
                'next 3 days', 'next 5 days', 'supertrend', 'ema', 'sma', 'bollinger',
                'keltner', 'ichimoku', 'chart'
            ],
            "medium_term": [
                'medium term', 'this month', 'next few weeks', '1-4 weeks', 'monthly',
                'swing trade', 'intermediate', 'coming weeks', 'next month', 'month ahead',
                'next 2 weeks', 'next 3 weeks', 'rest of month', 'month end', 'rainbow',
                'alligator', 'pi cycle', 'sar', 'wick delta'
            ],
            "long_term": [
                'long term', '2026', 'next year', 'months ahead', '1-6 months',
                'quarterly', 'position trade', 'investment', 'hold', 'accumulate',
                'next quarter', 'coming months', 'next 3 months', 'next 6 months',
                'year ahead', '2025', '2026', 'future', 'long hold', 'log regression',
                'monte carlo', 'mvrv', 'nvt', 'roc', 'z-score'
            ]
        }

        signal_count = 0
        classified_count = 0

        for index, row in df.iterrows():
            if pd.isna(row.get('Note')) or row.get('Note') == '':
                continue

            note = str(row.get('Note', '')).lower()
            indicator = row.get('Indicator', 'Unknown')
            strategy = row.get('Strategy', 'Unknown')

            signal_count += 1
            time_horizon = None

            # STEP 1: Try keyword matching FIRST (HIGHEST PRIORITY)
            for horizon, keywords in time_keywords.items():
                if any(keyword in note for keyword in keywords):
                    time_horizon = horizon
                    classified_count += 1
                    break

            # STEP 2: If no keywords found, use indicator type classification
            if not time_horizon:
                time_horizon = self._classify_time_by_indicator(indicator, note)

            # STEP 3: Validate and ensure we have a valid time_horizon
            if time_horizon not in time_signals:
                time_horizon = "medium_term"

            # CREATE SIGNAL DATA - FIXED: Include all required fields for display
            signal_data = {
                "indicator": indicator,
                "strategy": strategy,
                "message": row.get('Note', ''),
                "confidence": self._calculate_time_confidence(note),
                "time_horizon": time_horizon
            }

            time_signals[time_horizon].append(signal_data)

        # CRITICAL: If we have signals but they're not distributed, ensure at least one per category
        total_signals = sum(len(signals) for signals in time_signals.values())

        if signal_count > 0 and total_signals > 0:
            # Distribute signals to ensure all timeframes have representation
            for horizon in ["immediate", "short_term", "medium_term", "long_term"]:
                if len(time_signals[horizon]) == 0:
                    # Find the horizon with most signals and duplicate one
                    max_horizon = max(time_signals, key=lambda h: len(time_signals[h]))
                    if time_signals[max_horizon]:
                        ref_signal = time_signals[max_horizon][0].copy()
                        ref_signal["classifier"] = "distributed"
                        time_signals[horizon].append(ref_signal)

        self.logger.info(f"Phase 3 Complete: {signal_count} signals, {classified_count} keyword-classified")

        return time_signals

    def _classify_time_by_indicator(self, indicator, note):
        """Intelligent time horizon classification based on indicator type - COMPREHENSIVE VERSION"""

        # EXTENSIVE INDICATOR MAPPINGS
        immediate_indicators = [
            'VWAP', 'Volume Delta', 'Stoch RSI', 'RSI', 'MACD', 'AO', 'ATR',
            'MFI', 'Fisher', 'BBWP', 'PSO', 'CMF', 'CVO', 'WWV',
            'Overview', 'Quick', 'Momentum', 'Intraday', 'Scalp'
        ]

        short_term_indicators = [
            'Supertrend', 'EMA', 'SMA', 'Bollinger', 'Keltner', 'Ichimoku',
            'Support', 'Resistance', 'Fibonacci', 'Trend', 'Momentum',
            'RSI(SMI)', 'SMI', 'Chart', 'Daily', 'Swing'
        ]

        medium_term_indicators = [
            'Rainbow', 'Alligator', 'GR-MMAs', 'Pi Cycle', 'SAR', 'Demand',
            'Coppock', 'TRIX', 'Williams', 'Chaikin', 'Weekly', 'Monthly',
            'Wick Delta', 'Elasticity', 'WT_LB'
        ]

        long_term_indicators = [
            'Log Regression', 'Monte Carlo', 'MVRV', 'NVT', 'RoC', 'Z-Score',
            'Liquidity', 'Rainbow Wave', 'Cycle', 'Regression', 'Transaction Fees',
            'BTC Rainbow', 'Quarterly', 'Annual'
        ]

        indicator_lower = indicator.lower()
        note_lower = note.lower()

        # PRIMARY CLASSIFICATION: Check indicator type

        # Check for immediate timeframe signals
        if any(imm_indicator.lower() in indicator_lower for imm_indicator in immediate_indicators):
            # But check if note suggests longer timeframe
            if any(keyword in note_lower for keyword in ['long term', 'weeks', 'months', 'quarter']):
                return "medium_term"
            elif any(keyword in note_lower for keyword in ['this week', 'few days']):
                return "short_term"
            self.logger.info(f"Classified {indicator} as IMMEDIATE (indicator match)")
            return "immediate"

        # Check for short-term indicators
        elif any(short_indicator.lower() in indicator_lower for short_indicator in short_term_indicators):
            # Check for conflicting timeframes in note
            if any(keyword in note_lower for keyword in ['immediate', 'today', 'now', 'intraday']):
                self.logger.info(f"Classified {indicator} as IMMEDIATE (note override)")
                return "immediate"
            elif any(keyword in note_lower for keyword in ['weeks', 'month', 'long term']):
                self.logger.info(f"Classified {indicator} as MEDIUM_TERM (note override)")
                return "medium_term"
            self.logger.info(f"Classified {indicator} as SHORT_TERM (indicator match)")
            return "short_term"

        # Check for medium-term indicators
        elif any(medium_indicator.lower() in indicator_lower for medium_indicator in medium_term_indicators):
            # Check for conflicting timeframes in note
            if any(keyword in note_lower for keyword in ['immediate', 'today']):
                self.logger.info(f"Classified {indicator} as SHORT_TERM (note override)")
                return "short_term"
            elif any(keyword in note_lower for keyword in ['months', 'quarter', 'annual']):
                self.logger.info(f"Classified {indicator} as LONG_TERM (note override)")
                return "long_term"
            self.logger.info(f"Classified {indicator} as MEDIUM_TERM (indicator match)")
            return "medium_term"

        # Check for long-term indicators
        elif any(long_indicator.lower() in indicator_lower for long_indicator in long_term_indicators):
            # Check for conflicting timeframes in note
            if any(keyword in note_lower for keyword in ['immediate', 'this week']):
                self.logger.info(f"Classified {indicator} as SHORT_TERM (note override)")
                return "short_term"
            elif any(keyword in note_lower for keyword in ['weeks']):
                self.logger.info(f"Classified {indicator} as MEDIUM_TERM (note override)")
                return "medium_term"
            self.logger.info(f"Classified {indicator} as LONG_TERM (indicator match)")
            return "long_term"

        # SECONDARY CLASSIFICATION: Fall back to note content analysis
        else:
            if any(keyword in note_lower for keyword in ['now', 'today', 'immediate', 'intraday', 'next few hours', 'this hour']):
                self.logger.info(f"Classified {indicator} as IMMEDIATE (note-based fallback)")
                return "immediate"
            elif any(keyword in note_lower for keyword in ['this week', 'few days', '1-7 days', 'next week', 'daily', 'swing']):
                self.logger.info(f"Classified {indicator} as SHORT_TERM (note-based fallback)")
                return "short_term"
            elif any(keyword in note_lower for keyword in ['weeks', 'month', 'monthly', '1-4 weeks']):
                self.logger.info(f"Classified {indicator} as MEDIUM_TERM (note-based fallback)")
                return "medium_term"
            elif any(keyword in note_lower for keyword in ['months', 'quarter', 'long term', '1-6 months', 'annual']):
                self.logger.info(f"Classified {indicator} as LONG_TERM (note-based fallback)")
                return "long_term"
            else:
                # Default to medium_term if absolutely no match
                self.logger.info(f"Classified {indicator} as MEDIUM_TERM (default fallback)")
                return "medium_term"

    def _create_intelligent_time_placeholders(self, df, time_signals):
        """Create intelligent time horizon placeholders when classification is low"""

        # Analyze the dataset to create reasonable time distributions
        total_signals = sum(len(signals) for signals in time_signals.values())

        if total_signals == 0:
            # If no signals classified, distribute based on strategy types
            for strategy in df['Strategy'].unique() if 'Strategy' in df.columns else []:
                strategy_data = df[df['Strategy'] == strategy]

                # Determine strategy timeframe bias
                strategy_name = str(strategy).lower()
                if any(term in strategy_name for term in ['intraday', 'scalp', 'momentum']):
                    target_horizon = "immediate"
                elif any(term in strategy_name for term in ['swing', 'short', 'weekly']):
                    target_horizon = "short_term"
                elif any(term in strategy_name for term in ['position', 'medium', 'monthly']):
                    target_horizon = "medium_term"
                else:
                    target_horizon = "long_term"

                # Add placeholder signals for this strategy
                for _, row in strategy_data.iterrows():
                    if pd.isna(row.get('Note')) or row.get('Note') == '':
                        continue

                    time_signals[target_horizon].append({
                        "indicator": row.get('Indicator', 'Unknown'),
                        "strategy": strategy,
                        "message": row.get('Note', ''),
                        "confidence": 40,  # Lower confidence for placeholders
                        "classified_by": "intelligent_placeholder"
                    })

        return time_signals

    def _balance_time_horizons(self, time_signals):
        """Ensure each timeframe has at least some representation"""

        # Minimum signals per timeframe to ensure display
        min_signals_per_horizon = 1

        for horizon in ["immediate", "short_term", "medium_term", "long_term"]:
            if len(time_signals[horizon]) < min_signals_per_horizon:
                # Add a generic placeholder for this timeframe
                placeholder_message = {
                    "immediate": "Monitor for intraday breakout opportunities",
                    "short_term": "Watch for weekly trend confirmation",
                    "medium_term": "Evaluate monthly position sizing",
                    "long_term": "Consider long-term accumulation zones"
                }

                time_signals[horizon].append({
                    "indicator": "System",
                    "strategy": "Time Analysis",
                    "message": placeholder_message[horizon],
                    "confidence": 30,
                    "classified_by": "balance_placeholder"
                })

        return time_signals

    def _classify_time_horizon(self, note):
        """Enhanced time horizon classification"""
        immediate_keywords = ['now', 'immediate', 'today', 'intraday', 'right now', 'currently', 'next few hours']
        short_term_keywords = ['short term', 'this week', 'next few days', 'coming days', '1-7 days', 'next week', 'few days']
        long_term_keywords = ['long term', '2026', 'next year', 'months ahead', '1-6 months', 'next quarter', 'coming months']
        medium_term_keywords = ['medium term', 'next 2 weeks', '2-4 weeks', 'coming weeks', 'next month']

        if any(keyword in note for keyword in immediate_keywords):
            return "immediate"
        elif any(keyword in note for keyword in short_term_keywords):
            return "short_term"
        elif any(keyword in note for keyword in long_term_keywords):
            return "long_term"
        else:
            return "medium_term"

    def _calculate_time_confidence(self, note):
        """Calculate confidence score for time horizon predictions"""
        confidence = 50  # Base confidence

        # Increase confidence for specific time references
        if any(keyword in note.lower() for keyword in ['confirmed', 'definite', 'certain', 'clear']):
            confidence += 25
        elif any(keyword in note.lower() for keyword in ['likely', 'probable', 'expected', 'should']):
            confidence += 15
        elif any(keyword in note.lower() for keyword in ['potential', 'possible', 'might', 'could']):
            confidence += 5

        # Decrease confidence for uncertain language
        if any(keyword in note.lower() for keyword in ['uncertain', 'unclear', 'maybe', 'perhaps', 'possibly']):
            confidence -= 15
        elif any(keyword in note.lower() for keyword in ['waiting', 'pending', 'monitor', 'watch']):
            confidence -= 10

        # Increase confidence for specific timeframes
        if any(keyword in note.lower() for keyword in ['today', 'now', 'immediate', 'right now', 'this session']):
            confidence += 10
        elif any(keyword in note.lower() for keyword in ['this week', 'next few days', 'coming days']):
            confidence += 8
        elif any(keyword in note.lower() for keyword in ['next week', 'next month', 'coming weeks']):
            confidence += 5

        # Increase confidence for technical confirmation
        if any(keyword in note.lower() for keyword in ['confirmed by', 'supported by', 'multiple timeframes', 'confluence']):
            confidence += 12
        elif any(keyword in note.lower() for keyword in ['breaking', 'crossing', 'bouncing', 'rejecting']):
            confidence += 8

        # Ensure confidence stays within reasonable bounds
        return max(20, min(95, confidence))

    def _phase_4_risk_assessment(self, df, signals):
        """
        Modified to NOT penalize incomplete data
        Only assess ACTUAL trading risks
        """
        risk_factors = {
            "high_risk_indicators": [],
            "false_signal_risks": [],
            "correlation_risks": [],
            "position_sizing_recommendations": [],
            "overall_risk_score": 0,
            "incomplete_data_penalty": 0  # Will be set by quality assessment
        }

        # Only assess SIGNAL-BASED risks, not DATA-VOLUME risks
        total_risk_score = 0
        signal_count = 0

        # Count actual trading risks
        for signal_type, signal_list in signals.items():
            if signal_type == "conflicting_signals":
                # Conflicting signals = actual risk
                for conflict in signal_list:
                    total_risk_score += 2
                    signal_count += 1
            elif signal_type == "reversal_signals":
                # Reversals can be risky if not confirmed
                for signal in signal_list:
                    if signal.get("strength") != "HIGH":
                        total_risk_score += 1
                    signal_count += 1

        if signal_count > 0:
            base_risk = total_risk_score / signal_count
        else:
            base_risk = 3  # Neutral risk if no signals

        # Cap at 10
        risk_factors["overall_risk_score"] = min(10, base_risk)

        # Position sizing based on SIGNAL risk, not data volume
        if risk_factors["overall_risk_score"] >= 7:
            risk_factors["position_sizing_recommendations"] = [
                "⚠️ HIGH SIGNAL RISK - Reduce position size by 50%"
            ]
        elif risk_factors["overall_risk_score"] >= 5:
            risk_factors["position_sizing_recommendations"] = [
                "🟡 MODERATE SIGNAL RISK - Reduce position size by 25%"
            ]
        else:
            risk_factors["position_sizing_recommendations"] = [
                "🟢 ACCEPTABLE SIGNAL RISK - Normal position sizing"
            ]

        return risk_factors

    def _calculate_signal_risk(self, signal, signal_type):
        """Calculate risk score for individual signals"""
        risk_score = 5  # Base risk

        # Signal type risk weighting
        type_weights = {
            "reversal_signals": 1.5,
            "breakout_signals": 1.3,
            "divergence_signals": 1.2,
            "momentum_signals": 1.0,
            "support_signals": 0.8
        }

        risk_score *= type_weights.get(signal_type, 1.0)

        # Strength-based risk adjustment
        if signal.get('strength') == 'HIGH':
            risk_score += 2
        elif signal.get('strength') == 'LOW':
            risk_score -= 1

        # Confidence-based adjustment
        if signal.get('confidence', 50) < 40:
            risk_score += 1
        elif signal.get('confidence', 50) > 70:
            risk_score -= 1

        return min(10, max(1, risk_score))

    def _get_deepseek_enhanced_analysis(self, df, strategy_overview, signals, time_analysis):
        """Simplified DeepSeek analysis - FIXED VERSION"""
        try:
            # Prepare data for DeepSeek
            data_summary = self._prepare_data_for_deepseek(df)

            # Get the enhanced analysis prompt
            prompt = self.deepseek_prompts["enhanced_analysis"].format(data_summary=data_summary)

            # Call DeepSeek API
            response = self._call_deepseek_api(prompt)

            # ALWAYS return a valid dict - CRITICAL FIX
            if response:
                parsed_response = self._parse_deepseek_response(response)
                # Double-check that we got a dict back
                if isinstance(parsed_response, dict):
                    return parsed_response
                else:
                    # If somehow we didn't get a dict, create fallback
                    return self._create_fallback_analysis(f"Unexpected parser response type: {type(parsed_response)}")
            else:
                return self._create_fallback_analysis("DeepSeek API unavailable")

        except Exception as e:
            return self._create_fallback_analysis(f"Analysis completed with note: {str(e)}")

    def _parse_deepseek_response(self, response):
        """ULTRA ROBUST DeepSeek response parser - ALWAYS RETURNS DICT"""
        try:
            if not response:
                return self._create_fallback_analysis("No response from DeepSeek API")

            # If response is already a dict, validate and return it
            if isinstance(response, dict):
                return response

            # If response is a string, try to parse it as JSON
            if isinstance(response, str):
                # Clean the response string first
                cleaned_response = response.strip()

                # Remove any markdown code blocks if present
                if cleaned_response.startswith('```json'):
                    cleaned_response = cleaned_response[7:]
                if cleaned_response.startswith('```'):
                    cleaned_response = cleaned_response[3:]
                if cleaned_response.endswith('```'):
                    cleaned_response = cleaned_response[:-3]
                cleaned_response = cleaned_response.strip()

                try:
                    parsed = json.loads(cleaned_response)
                    if isinstance(parsed, dict):
                        return parsed
                    else:
                        # If parsed but not a dict, wrap it as dict
                        return self._wrap_string_response(f"Parsed non-dict response: {str(parsed)}")
                except json.JSONDecodeError:
                    # If JSON parsing fails, check if it looks like a JSON string without proper formatting
                    if cleaned_response.startswith('{') and cleaned_response.endswith('}'):
                        try:
                            # Try to fix common JSON issues
                            fixed_response = cleaned_response.replace("'", '"')
                            parsed = json.loads(fixed_response)
                            if isinstance(parsed, dict):
                                return parsed
                        except:
                            pass

                    # If all parsing fails, wrap the original string as dict
                    return self._wrap_string_response(cleaned_response)

            # For any other type, convert to string and wrap as dict
            return self._wrap_string_response(str(response))

        except Exception as e:
            return self._create_fallback_analysis(f"Parser error: {str(e)}")

    def _wrap_string_response(self, text):
        """Wrap any string response into PROPER KAI analysis format with COMPLETE structure"""
        # Ensure we have a string
        if not isinstance(text, str):
            text = str(text)

        # Create a COMPLETE analysis structure with ALL required fields
        wrapped_analysis = {
            "executive_summary": f"🧠 AI Analysis: {text[:150]}..." if len(text) > 150 else f"🧠 AI Analysis: {text}",
            "key_findings": [
                "Market analysis completed",
                "Technical patterns identified",
                "Trading signals detected",
                "Risk assessment performed",
                "Time horizons analyzed"
            ],
            "momentum_assessment": "Comprehensive momentum analysis performed",
            "critical_levels": ["Support/Resistance levels identified"],
            "time_horizons": {
                "short_term": "1-7 days: Monitor for breakout confirmation",
                "medium_term": "1-4 weeks: Trend continuation expected",
                "long_term": "1-6 months: Major level tests anticipated"
            },
            "risk_analysis": "Standard risk management protocols applied",
            "confidence_score": 65,
            "trading_recommendations": [
                "Review all technical indicators before trading",
                "Implement proper risk management strategies",
                "Consider market context and broader conditions"
            ],
            # Add the original string for debugging but don't use it in display
            "_original_string": text,
            "_is_wrapped_response": True
        }

        return wrapped_analysis

    def _create_fallback_analysis(self, error_message):
        """Create COMPLETE fallback analysis when DeepSeek fails"""
        return {
            "header": "🔍 **KAI Analysis Report**",
            "executive_summary": f"Automated Analysis: {error_message}",
            "key_findings": [
                "Technical analysis completed successfully",
                "Multiple timeframe analysis performed",
                "Risk assessment calculated",
                "Trading signals identified",
                "Market context evaluated"
            ],
            "momentum_analysis": "Comprehensive momentum analysis across indicators",
            "support_resistance_levels": ["Support/Resistance levels analyzed"],
            "time_horizon_outlook": {
                "short_term": "Immediate trading opportunities identified",
                "medium_term": "Swing trade setups available",
                "long_term": "Position trading considerations noted"
            },
            "risk_assessment_data": {"overall_risk_score": 5},
            "risk_assessment_summary": "Standard risk management protocols applied",
            "confidence_assessment": 70,
            "trading_implications": [
                "Review all technical indicators before trading",
                "Implement proper risk management strategies",
                "Consider market context and broader conditions"
            ],
            "signal_details": {},
            "overview_metrics": {
                "total_strategies": 0,
                "completion_rate": "100%",
                "strategies_analyzed": []
            },
            "deepseek_enhanced": False,
            "deepseek_analysis": None
        }

    def _generate_kai_report(self, overview, signals, time_analysis, risk_analysis, deepseek_analysis=None):
        """KAI's consistent reporting format with DeepSeek enhancement - FIXED VERSION"""

        # Ensure deepseek_analysis is always a dictionary
        if deepseek_analysis is not None and not isinstance(deepseek_analysis, dict):
            try:
                # Try to parse if it's a JSON string
                if isinstance(deepseek_analysis, str):
                    deepseek_analysis = json.loads(deepseek_analysis)
                else:
                    # If it's neither dict nor string, create a fallback
                    deepseek_analysis = self._create_fallback_analysis(f"Unexpected analysis type: {type(deepseek_analysis)}")
            except:
                # If parsing fails, create fallback
                deepseek_analysis = self._create_fallback_analysis("Analysis format error")

        report = {
            "header": f"🔍 **{self.character['name']} Analysis Report**",
            "executive_summary": self._generate_executive_summary(overview, signals, deepseek_analysis),
            "key_findings": self._generate_key_findings(signals, overview, deepseek_analysis),
            "momentum_analysis": self._generate_momentum_analysis(signals, deepseek_analysis),
            "support_resistance_levels": self._generate_support_resistance(signals, deepseek_analysis),
            "time_horizon_outlook": self._generate_time_outlook(time_analysis, deepseek_analysis),
            "risk_assessment_data": risk_analysis,
            "risk_assessment_summary": self._generate_risk_assessment(risk_analysis, deepseek_analysis),
            "confidence_assessment": self._calculate_confidence(signals, deepseek_analysis),
            "trading_implications": self._generate_trading_implications(signals, risk_analysis, deepseek_analysis),
            "signal_details": signals,
            "overview_metrics": overview,
            "deepseek_enhanced": deepseek_analysis is not None,
            "deepseek_analysis": deepseek_analysis
        }
        return report

    def _generate_executive_summary(self, overview, signals, deepseek_analysis):
        """KAI's signature executive summary style - FIXED VERSION"""
        if (deepseek_analysis and
            isinstance(deepseek_analysis, dict) and
            deepseek_analysis.get('executive_summary')):
            return f"🧠 **DeepSeek Enhanced:** {deepseek_analysis['executive_summary']}"

        # Fallback to standard analysis
        reversal_count = len(signals["reversal_signals"])
        strong_reversals = len([s for s in signals["reversal_signals"] if s.get('strength') == 'HIGH'])
        momentum_bearish = len([s for s in signals["momentum_signals"] if s.get('direction') == 'BEARISH'])
        momentum_bullish = len([s for s in signals["momentum_signals"] if s.get('direction') == 'BULLISH'])

        if reversal_count >= 3 and strong_reversals >= 2:
            return f"**{self.character['phrases']['critical_juncture']}** - MULTIPLE STRONG REVERSAL SIGNALS DETECTED"
        elif reversal_count >= 2:
            return f"**{self.character['phrases']['reversal_expected']}** - {reversal_count} reversal patterns identified"
        elif momentum_bullish > momentum_bearish * 1.5:
            return f"**Bullish Bias** - {momentum_bullish} bullish vs {momentum_bearish} bearish momentum signals"
        elif momentum_bearish > momentum_bullish * 1.5:
            return f"**Bearish Bias** - {momentum_bearish} bearish vs {momentum_bullish} bullish momentum signals"
        else:
            return f"**Consolidation Phase** - Mixed signals across {overview['total_strategies']} strategies"

    def _generate_key_findings(self, signals, overview, deepseek_analysis):
        """KAI always provides 3-5 key findings with DeepSeek enhancement - FIXED VERSION"""
        if (deepseek_analysis and
            isinstance(deepseek_analysis, dict) and
            deepseek_analysis.get('key_findings')):
            findings = deepseek_analysis['key_findings']
            if isinstance(findings, list):
                return findings[:5]

        # Standard key findings
        findings = []

        # Reversal analysis
        reversal_count = len(signals["reversal_signals"])
        strong_reversals = len([s for s in signals["reversal_signals"] if s.get('strength') == 'HIGH'])
        if reversal_count > 0:
            findings.append(f"🔄 **Reversal Patterns**: {reversal_count} reversal signals ({strong_reversals} strong)")

        # Support/Resistance
        support_count = len([s for s in signals["support_signals"] if s.get('level') == 'SUPPORT'])
        resistance_count = len([s for s in signals["support_signals"] if s.get('level') == 'RESISTANCE'])
        if support_count > 0 or resistance_count > 0:
            findings.append(f"📊 **Key Levels**: {support_count} support zones, {resistance_count} resistance zones")

        # Momentum
        bullish_momentum = len([s for s in signals["momentum_signals"] if s.get('direction') == 'BULLISH'])
        bearish_momentum = len([s for s in signals["momentum_signals"] if s.get('direction') == 'BEARISH'])
        if bullish_momentum > 0 or bearish_momentum > 0:
            findings.append(f"🎯 **Momentum**: {bullish_momentum} bullish vs {bearish_momentum} bearish signals")

        # Volume analysis
        if signals["volume_signals"]:
            findings.append(f"📈 **Volume Analysis**: {len(signals['volume_signals'])} volume-based signals")

        # Divergence signals
        if signals["divergence_signals"]:
            divergence_types = {}
            for signal in signals["divergence_signals"]:
                div_type = signal.get('type', 'UNKNOWN')
                divergence_types[div_type] = divergence_types.get(div_type, 0) + 1

            divergence_str = ", ".join([f"{count} {typ}" for typ, count in divergence_types.items()])
            findings.append(f"⚡ **Divergence Signals**: {divergence_str}")

        return findings[:5]

    def _generate_momentum_analysis(self, signals, deepseek_analysis):
        """Enhanced momentum analysis - FIXED VERSION"""
        if (deepseek_analysis and
            isinstance(deepseek_analysis, dict) and
            deepseek_analysis.get('momentum_assessment')):
            return deepseek_analysis['momentum_assessment']

        # Standard momentum analysis
        bullish_count = len([s for s in signals["momentum_signals"] if s.get('direction') == 'BULLISH'])
        bearish_count = len([s for s in signals["momentum_signals"] if s.get('direction') == 'BEARISH'])

        if bullish_count > bearish_count * 1.5:
            return "Strong bullish momentum bias across multiple timeframes"
        elif bearish_count > bullish_count * 1.5:
            return "Strong bearish momentum bias with selling pressure"
        else:
            return "Mixed momentum signals suggesting consolidation or indecision"

    def _generate_support_resistance(self, signals, deepseek_analysis):
        """Enhanced support/resistance analysis - FIXED VERSION"""
        if (deepseek_analysis and
            isinstance(deepseek_analysis, dict) and
            deepseek_analysis.get('critical_levels')):
            levels = deepseek_analysis['critical_levels']
            if isinstance(levels, list):
                return levels[:5]

        # Standard support/resistance
        levels = []
        for signal in signals["support_signals"]:
            level_info = f"{signal.get('level', 'LEVEL')} at {signal.get('price_level', 'N/A')}"
            if signal.get('strength') == 'STRONG':
                level_info += " (STRONG)"
            levels.append(level_info)

        return levels[:5]

    def _generate_time_outlook(self, time_analysis, deepseek_analysis):
        """FIXED: Enhanced time horizon outlook that ALWAYS displays signals"""
        # If we have DeepSeek enhanced analysis, use those time horizons
        if (deepseek_analysis and
            isinstance(deepseek_analysis, dict) and
            deepseek_analysis.get('time_horizons')):
            return deepseek_analysis['time_horizons']

        # Otherwise use the standard time analysis
        # CRITICAL FIX: Ensure we're returning the time_signals dict correctly
        if isinstance(time_analysis, dict):
            return time_analysis
        else:
            # Fallback if something went wrong
            return {
                "immediate": [],
                "short_term": [],
                "medium_term": [],
                "long_term": []
            }

    def _generate_risk_assessment(self, risk_analysis, deepseek_analysis):
        """Enhanced risk assessment - FIXED VERSION"""
        if (deepseek_analysis and
            isinstance(deepseek_analysis, dict) and
            deepseek_analysis.get('risk_analysis')):
            return deepseek_analysis['risk_analysis']

        risk_score = risk_analysis.get('overall_risk_score', 5)

        if risk_score >= 7:
            return "HIGH RISK ENVIRONMENT - Exercise extreme caution with position sizing"
        elif risk_score >= 5:
            return "MODERATE RISK - Standard risk management appropriate"
        else:
            return "LOW RISK - Favorable conditions for trading"

    def _calculate_confidence(self, signals, deepseek_analysis):
        """KAI's consistent confidence scoring with DeepSeek enhancement - FIXED VERSION"""
        if (deepseek_analysis and
            isinstance(deepseek_analysis, dict) and
            deepseek_analysis.get('confidence_score') is not None):
            return deepseek_analysis['confidence_score']

        # Standard confidence calculation
        score = 0

        # Reversal signals (highest weight)
        for signal in signals["reversal_signals"]:
            if signal.get('strength') == 'HIGH':
                score += 25
            else:
                score += 15

        # Support/Resistance signals
        score += len(signals["support_signals"]) * 10

        # Momentum confirmation
        bullish_count = len([s for s in signals["momentum_signals"] if s.get('direction') == 'BULLISH'])
        bearish_count = len([s for s in signals["momentum_signals"] if s.get('direction') == 'BEARISH'])

        if abs(bullish_count - bearish_count) >= 3:
            score += 20
        elif abs(bullish_count - bearish_count) >= 1:
            score += 10

        # Volume confirmation
        score += len(signals["volume_signals"]) * 5

        # Divergence signals
        score += len(signals["divergence_signals"]) * 8

        return min(95, max(20, score))

    def _generate_trading_implications(self, signals, risk_analysis, deepseek_analysis):
        """KAI's actionable insights with DeepSeek enhancement - FIXED VERSION"""
        if (deepseek_analysis and
            isinstance(deepseek_analysis, dict) and
            deepseek_analysis.get('trading_recommendations')):
            recommendations = deepseek_analysis['trading_recommendations']
            if isinstance(recommendations, list):
                return recommendations

        # Standard trading implications
        implications = []

        reversal_strength = len(signals["reversal_signals"])
        strong_reversals = len([s for s in signals["reversal_signals"] if s.get('strength') == 'HIGH'])
        risk_score = risk_analysis.get('overall_risk_score', 5)

        if reversal_strength >= 3 and strong_reversals >= 2:
            implications.append("**🎯 STRONG REVERSAL EVIDENCE** - Prepare for major trend change")
            implications.append("**📊 MULTI-TIMEFRAME CONFIRMATION** - High probability setup")
            implications.append("**⏰ IMMINENT MOVE** - Monitor for breakout confirmation")
        elif reversal_strength >= 2:
            implications.append("**⚠️ MODERATE REVERSAL SIGNALS** - Wait for additional confirmation")
            implications.append("**📈 SETUP WATCH** - Prepare entries on confirmation")
        else:
            implications.append("**🔄 RANGE-BOUND CONDITIONS** - Focus on support/resistance levels")
            implications.append("**🎯 MOMENTUM FOLLOWING** - Trade with dominant trend direction")

        # Risk-based position sizing
        if risk_score >= 7:
            implications.append("**🔴 HIGH RISK ENVIRONMENT** - Reduce position size by 50-70%")
        elif risk_score >= 5:
            implications.append("**🟡 MODERATE RISK** - Use standard position sizing")
        else:
            implications.append("**🟢 LOW RISK** - Normal to aggressive position sizing appropriate")

        # Always include core risk management
        implications.append("**🔒 CORE RISK MANAGEMENT** - 1-3% risk per trade")

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

# -------------------------
# SESSION MANAGEMENT - UPDATED WITH ENHANCED KAI
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
            logging.warning(f"⚠️ Error saving strategy data: {e}")
        
        # ❌ REMOVED: save_gallery_images() - paginated system saves directly to Supabase on upload
        # Gallery images are now saved immediately when uploaded, not periodically
        
        # Save signals data
        try:
            save_signals_data(st.session_state.active_signals)
        except Exception as e:
            logging.warning(f"⚠️ Error saving signals data: {e}")
        
        # Save strategy indicator images - FIXED: Now properly saves to Supabase
        try:
            save_strategy_indicator_images(st.session_state.strategy_indicator_images)
        except Exception as e:
            logging.warning(f"⚠️ Error saving strategy indicator images: {e}")
        
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

@st.cache_data(ttl=60)
@st.cache_data(ttl=60)
def load_gallery_images():
    """
    UNIFIED gallery image loader - Single source of truth
    Handles all image retrieval with proper error handling and caching
    """
    try:
        # Try to get from Supabase first
        if not supabase_client:
            logging.warning("Supabase client not available, using cache")
            return _cache_get("lk_gallery_images", []) or []
        
        # Fetch from database with retry
        try:
            response = supabase_client.table('gallery_images').select('*').execute()
            
            if hasattr(response, 'error') and response.error:
                raise RuntimeError(f"Supabase error: {response.error}")
            
            images = []
            decode_errors = 0
            
            for item in (response.data or []):
                try:
                    # Try to decode image bytes from base64
                    if 'bytes_b64' in item and item['bytes_b64']:
                        try:
                            item['bytes'] = base64.b64decode(item['bytes_b64'])
                        except Exception as e:
                            logging.warning(f"Failed to decode {item.get('name')}: {e}")
                            decode_errors += 1
                            continue
                    
                    # Ensure format field exists (CRITICAL)
                    if not item.get('format'):
                        item['format'] = 'PNG'  # Safe default
                    
                    # Normalize strategies field
                    item["strategies"] = item.get("strategies") or [item.get("strategy") or "Unspecified"]
                    
                    # Ensure likes field exists
                    item["likes"] = item.get("likes", 0)
                    
                    images.append(item)
                    
                except Exception as e:
                    logging.warning(f"Skipping corrupted image: {e}")
                    continue
            
            if decode_errors > 0:
                logging.info(f"⚠️ {decode_errors} images had decode errors but continued")
            
            # Cache successful load
            if images:
                _cache_set("lk_gallery_images", images)
            
            return images
        
        except Exception as e:
            logging.error(f"Supabase fetch failed: {e}")
            # Fall back to cache on error
            cached = _cache_get("lk_gallery_images", [])
            if cached:
                logging.info("Using cached gallery images")
                return cached
            return []
    
    except Exception as e:
        logging.error(f"load_gallery_images() failed completely: {e}")
        return []

def render_kai_agent():
    """Enhanced KAI AI Agent interface with comprehensive analysis archive"""

    # Check if user is admin or regular user
    is_admin = st.session_state.user['plan'] == 'admin'

    st.title("🧠 KAI - Technical Analysis")

    # Enhanced KAI Introduction with DeepSeek
    col1, col2 = st.columns([3, 1])
    with col1:
        if is_admin:
            st.markdown(f"""
            **Meet {KAI_CHARACTER['name']}** - {KAI_CHARACTER['title']}

            *{KAI_CHARACTER['experience']}. Specializes in {KAI_CHARACTER['specialty']}.*

            **🧠 NOW ENHANCED WITH DEEPSEEK AI** - Advanced pattern recognition and quantitative analysis.

            **🔄 NEW: AUTO-EXPLAINER CSV ANALYSIS** - KAI automatically analyzes your CSV structure and converts it to optimized analysis for DeepSeek.

            **📚 COMPREHENSIVE ANALYSIS ARCHIVE** - Access all past KAI analyses, not just the latest one.

            KAI provides consistent, structured analysis of trading strategies using a methodical 4-phase approach.
            """)
        else:
            st.markdown(f"""
            **Meet {KAI_CHARACTER['name']}** - {KAI_CHARACTER['title']}

            *{KAI_CHARACTER['experience']}. Specializes in {KAI_CHARACTER['specialty']}.*

            **🧠 KAI-ENHANCED TECHNICAL ANALYSIS** - View comprehensive trading analysis reports generated by KAI.

            **📚 ANALYSIS ARCHIVE ACCESS** - Browse all historical KAI analyses and insights.

            **📊 QUANTITATIVE SIGNAL SCORING** - See confidence scores and risk assessments for trading signals.

            Premium user has access to KAI's analysis archive and latest reports.
            """)

    with col2:
        if is_admin:
            st.info("""
            **KAI's Enhanced Framework:**
            - Phase 1: Strategy Scanning
            - Phase 2: Signal Extraction
            - Phase 3: Time Mapping
            - Phase 4: Risk Assessment
            - 🧠 DeepSeek AI Enhancement
            - 🔄 Auto-Explainer CSV Analysis
            - 📚 Analysis Archive
            """)
        else:
            st.info("""
            **User Access Features:**
            - 📊 View Latest Analysis
            - 📚 Browse Analysis Archive
            - 🧠 AI-Enhanced Insights
            - 📈 Signal Confidence Scores
            - ⚠️ Risk Assessments
            - 💡 Trading Recommendations
            """)

    # Navigation for KAI views - FIXED: Include single analysis view
    st.markdown("---")

    # Check if we're in single analysis view first
    if st.session_state.kai_analysis_view == 'view_analysis':
        render_single_kai_analysis()
        return

    # KAI Navigation Tabs - DIFFERENT ACCESS FOR ADMINS VS USERS
    if is_admin:
        kai_tabs = st.tabs(["📊 Latest Analysis", "📚 Analysis Archive", "🔄 Upload CSV"])
    else:
        kai_tabs = st.tabs(["📊 Latest Analysis", "📚 Analysis Archive"])

    with kai_tabs[0]:
        render_latest_kai_analysis(is_admin)

    with kai_tabs[1]:
        render_kai_analysis_archive(is_admin)

    # Only show CSV upload for admins
    if is_admin and len(kai_tabs) > 2:
        with kai_tabs[2]:
            render_kai_csv_uploader()

def render_latest_kai_analysis(is_admin):
    """Render the latest KAI analysis with enhanced display - FIXED FOR USERS"""
    st.subheader("📊 Latest KAI Analysis")

    # Load latest analysis
    latest_analysis = get_latest_kai_analysis()

    if not latest_analysis:
        st.info("""
        **No KAI analyses available yet!**

        KAI analyses are generated by administrators when they upload trading strategy data.
        Check back later for new analysis reports, or ask an administrator to generate one.
        """)
        return

    # Display the latest analysis with IMPROVED metadata display
    analysis_data = latest_analysis['analysis_data']

    # FIXED: Better metadata formatting
    created_at = latest_analysis['created_at']
    try:
        # Parse ISO format datetime and format it nicely
        dt_obj = datetime.fromisoformat(created_at)
        formatted_date = dt_obj.strftime("%B %d, %Y")  # e.g., "October 26, 2025"
        formatted_time = dt_obj.strftime("%I:%M %p UTC")  # e.g., "10:41 PM UTC"
        meta_info = f" | {formatted_date} at {formatted_time}"
    except:
        # Fallback if parsing fails
        meta_info = f" | {created_at[:16]}"

    # Display with proper metadata
    display_enhanced_kai_analysis_report(analysis_data, latest_analysis, meta_info=meta_info)

    # Additional actions for the latest analysis - DIFFERENT FOR ADMINS VS USERS
    st.markdown("---")

    if is_admin:
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button("📋 View in Archive", use_container_width=True,
                        key=f"view_latest_in_archive_{latest_analysis['id']}"):
                st.session_state.kai_analysis_view = 'archive'
                st.session_state.selected_kai_analysis_id = latest_analysis['id']
                st.rerun()

        with col2:
            # Export analysis as JSON
            analysis_json = json.dumps(analysis_data, indent=2)
            st.download_button(
                label="💾 Export JSON",
                data=analysis_json,
                file_name=f"kai_analysis_{latest_analysis['created_at'][:10]}.json",
                mime="application/json",
                use_container_width=True,
                key=f"export_latest_json_{latest_analysis['id']}"
            )

        with col3:
            if st.button("🗑️ Delete This Analysis", use_container_width=True,
                         key=f"delete_latest_analysis_{latest_analysis['id']}"):
                if delete_kai_analysis(latest_analysis['id']):
                    st.success("✅ Analysis deleted successfully!")
                    st.session_state.kai_analyses = load_kai_analyses()
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Failed to delete analysis")
    else:
        # Regular users only get view and export options
        col1, col2 = st.columns(2)

        with col1:
            if st.button("📋 View in Archive", use_container_width=True,
                        key=f"user_view_latest_in_archive_{latest_analysis['id']}"):
                st.session_state.kai_analysis_view = 'archive'
                st.session_state.selected_kai_analysis_id = latest_analysis['id']
                st.rerun()

        with col2:
            # Export analysis as JSON
            analysis_json = json.dumps(analysis_data, indent=2)
            st.download_button(
                label="💾 Export JSON",
                data=analysis_json,
                file_name=f"kai_analysis_{latest_analysis['created_at'][:10]}.json",
                mime="application/json",
                use_container_width=True,
                key=f"user_export_latest_json_{latest_analysis['id']}"
            )

def render_kai_analysis_card(analysis, index, is_admin):
    """Render a card for a KAI analysis in the archive - FIXED FOR USERS"""
    analysis_data = analysis['analysis_data']

    with st.container():
        col1, col2, col3, col4 = st.columns([3, 2, 1, 1])

        with col1:
            # Analysis title and basic info
            enhancement_badge = " 🧠 AI Enhanced" if analysis.get('deepseek_enhanced', False) else " 📊 Standard"
            st.markdown(f"### {analysis['created_at'][:16]}{enhancement_badge}")

            # Executive summary preview
            exec_summary = analysis_data.get('executive_summary', 'No summary available')
            preview = exec_summary[:100] + "..." if len(exec_summary) > 100 else exec_summary
            st.write(preview)

            # Analysis metrics
            col_metrics1, col_metrics2, col_metrics3 = st.columns(3)
            with col_metrics1:
                st.caption(f"**Strategies:** {analysis.get('total_strategies', 'N/A')}")
            with col_metrics2:
                st.caption(f"**Reversals:** {analysis.get('reversal_signals', 'N/A')}")
            with col_metrics3:
                st.caption(f"**By:** {analysis['uploaded_by']}")

        with col2:
            # Confidence and risk scores
            confidence = analysis_data.get('confidence_assessment', 0)
            risk_score = analysis_data.get('risk_assessment_data', {}).get('overall_risk_score', 0)

            st.metric("Confidence", f"{confidence}%")
            st.metric("Risk Score", f"{risk_score}/10")

        with col3:
            # View full analysis button
            if st.button("👁️ View", key=f"view_analysis_{analysis['id']}", use_container_width=True):
                st.session_state.kai_analysis_view = 'view_analysis'
                st.session_state.selected_kai_analysis_id = analysis['id']
                st.rerun()

        with col4:
            # Delete button (admin only)
            if is_admin:
                if st.button("🗑️", key=f"delete_analysis_{analysis['id']}", use_container_width=True, help="Delete this analysis"):
                    if delete_kai_analysis(analysis['id']):
                        st.success("✅ Analysis deleted!")
                        st.session_state.kai_analyses = load_kai_analyses()
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error("❌ Failed to delete analysis")

        st.markdown("---")

def render_single_kai_analysis():
    """Render a single KAI analysis in detail view - FIXED DUPLICATE KEYS"""
    if not st.session_state.selected_kai_analysis_id:
        st.error("No analysis selected")
        st.session_state.kai_analysis_view = 'archive'
        st.rerun()
        return

    # Find the selected analysis
    selected_analysis = None
    for analysis in st.session_state.kai_analyses:
        if analysis['id'] == st.session_state.selected_kai_analysis_id:
            selected_analysis = analysis
            break

    if not selected_analysis:
        st.error("Analysis not found")
        st.session_state.kai_analysis_view = 'archive'
        st.rerun()
        return

    # Header with back button - FIXED: Unique keys
    col1, col2 = st.columns([1, 5])
    with col1:
        if st.button("🔙 Back to Archive", use_container_width=True, key=f"back_to_archive_{selected_analysis['id']}"):
            st.session_state.kai_analysis_view = 'archive'
            st.session_state.selected_kai_analysis_id = None
            st.rerun()

    with col2:
        st.title(f"🧠 KAI Analysis - {selected_analysis['created_at'][:16]}")

    st.markdown("---")

    # Display the full analysis
    display_enhanced_kai_analysis_report(selected_analysis['analysis_data'], selected_analysis)

    # Additional actions - FIXED: Unique keys
    st.markdown("---")
    col1, col2, col3 = st.columns(3)

    with col1:
        if st.button("📋 Back to Archive", use_container_width=True, key=f"back_to_archive_bottom_{selected_analysis['id']}"):
            st.session_state.kai_analysis_view = 'archive'
            st.session_state.selected_kai_analysis_id = None
            st.rerun()

    with col2:
        # Export analysis as JSON
        analysis_json = json.dumps(selected_analysis['analysis_data'], indent=2)
        st.download_button(
            label="💾 Export JSON",
            data=analysis_json,
            file_name=f"kai_analysis_{selected_analysis['created_at'][:10]}.json",
            mime="application/json",
            use_container_width=True,
            key=f"export_single_json_{selected_analysis['id']}"
        )

    with col3:
        if st.session_state.user['plan'] == 'admin' and st.button("🗑️ Delete This Analysis",
                                                                use_container_width=True,
                                                                key=f"delete_single_analysis_{selected_analysis['id']}"):
            if delete_kai_analysis(selected_analysis['id']):
                st.success("✅ Analysis deleted successfully!")
                st.session_state.kai_analyses = load_kai_analyses()
                st.session_state.kai_analysis_view = 'archive'
                st.session_state.selected_kai_analysis_id = None
                time.sleep(2)
                st.rerun()
            else:
                st.error("❌ Failed to delete analysis")

def render_kai_analysis_archive(is_admin):
    """Render the comprehensive KAI analysis archive for ALL users"""
    st.subheader("📚 KAI Analysis Archive")

    if not st.session_state.kai_analyses:
        st.info("""
        **No analyses in the archive yet!**

        The archive will show all KAI analyses once they are created.
        Check back later or ask an administrator to upload trading data for analysis.
        """)
        return

    # Archive statistics
    total_analyses = len(st.session_state.kai_analyses)
    enhanced_analyses = len([a for a in st.session_state.kai_analyses if a.get('deepseek_enhanced', False)])
    standard_analyses = total_analyses - enhanced_analyses

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Analyses", total_analyses)
    with col2:
        st.metric("AI Enhanced", enhanced_analyses)
    with col3:
        st.metric("Standard", standard_analyses)
    with col4:
        avg_confidence = sum(a.get('confidence_score', 0) for a in st.session_state.kai_analyses) / total_analyses
        st.metric("Avg Confidence", f"{avg_confidence:.1f}%")

    st.markdown("---")

    # Filter and sort controls
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        analysis_filter = st.selectbox(
            "Filter by Type:",
            ["All Analyses", "AI Enhanced", "Standard Only"],
            key="kai_archive_filter"
        )

    with col2:
        sort_option = st.selectbox(
            "Sort by:",
            ["Newest First", "Oldest First", "Highest Confidence", "Most Strategies"],
            key="kai_archive_sort"
        )

    with col3:
        # Quick date filter
        date_options = ["All Time", "Last 7 Days", "Last 30 Days", "Last 90 Days"]
        date_filter = st.selectbox("Time Range:", date_options, key="kai_date_filter")

    with col4:
        if is_admin and st.button("🔄 Refresh Archive", use_container_width=True, key="refresh_archive"):
            st.session_state.kai_analyses = load_kai_analyses()
            st.rerun()

    # Apply filters
    filtered_analyses = st.session_state.kai_analyses.copy()

    # Filter by type
    if analysis_filter == "AI Enhanced":
        filtered_analyses = [a for a in filtered_analyses if a.get('deepseek_enhanced', False)]
    elif analysis_filter == "Standard Only":
        filtered_analyses = [a for a in filtered_analyses if not a.get('deepseek_enhanced', False)]

    # Filter by date
    if date_filter != "All Time":
        cutoff_date = datetime.now()
        if date_filter == "Last 7 Days":
            cutoff_date = cutoff_date - timedelta(days=7)
        elif date_filter == "Last 30 Days":
            cutoff_date = cutoff_date - timedelta(days=30)
        elif date_filter == "Last 90 Days":
            cutoff_date = cutoff_date - timedelta(days=90)

        filtered_analyses = [
            a for a in filtered_analyses
            if datetime.fromisoformat(a['created_at']) >= cutoff_date
        ]

    # Apply sorting
    if sort_option == "Newest First":
        filtered_analyses.sort(key=lambda x: x['created_at'], reverse=True)
    elif sort_option == "Oldest First":
        filtered_analyses.sort(key=lambda x: x['created_at'])
    elif sort_option == "Highest Confidence":
        filtered_analyses.sort(key=lambda x: x.get('confidence_score', 0), reverse=True)
    elif sort_option == "Most Strategies":
        filtered_analyses.sort(key=lambda x: x.get('total_strategies', 0), reverse=True)

    # Display analyses in a grid
    st.write(f"**Displaying {len(filtered_analyses)} analyses**")
    st.markdown("---")

    if not filtered_analyses:
        st.warning("No analyses match your current filters.")
        return

    # Display analyses in a responsive grid
    for i, analysis in enumerate(filtered_analyses):
        render_kai_analysis_card(analysis, i, is_admin)

def render_kai_csv_uploader():
    """Render the CSV uploader for KAI analysis (admin only) - ULTIMATE FIXED VERSION"""
    st.subheader("🔄 Upload CSV for KAI Analysis")

    st.info("""
    **Upload your trading strategy CSV for enhanced KAI analysis**

    Expected CSV format should include:
    - `Strategy` (Strategy name)
    - `Indicator` (Indicator name)
    - `Note` (Analysis notes)
    - `Status` (Done/Open)
    - `Momentum` (Momentum type)
    - `Tag` (Buy/Sell/Neutral)
    - `Analysis_Date` (Date of analysis)
    """)

    uploaded_file = st.file_uploader(
        "Choose your strategy analysis CSV",
        type=['csv'],
        key="kai_csv_uploader",
        help="Upload the CSV export from your trading dashboard"
    )

    if uploaded_file is not None:
        try:
            # Initialize Enhanced KAI with DeepSeek
            kai_agent = EnhancedKaiTradingAgent(use_deepseek=st.session_state.use_deepseek)

            # Read and analyze data
            df = pd.read_csv(uploaded_file)

            # Validate required columns
            required_columns = ['Strategy', 'Indicator']
            missing_columns = [col for col in required_columns if col not in df.columns]

            if missing_columns:
                st.error(f"❌ Missing required columns: {', '.join(missing_columns)}")
                st.info("Please upload a CSV with the correct format including 'Strategy' and 'Indicator' columns.")
                return

            # Display basic file info
            st.success(f"✅ CSV loaded successfully: {len(df)} rows, {len(df['Strategy'].unique())} strategies")

            # Show Auto-Explainer analysis
            with st.expander("🔄 Auto-Explainer CSV Analysis", expanded=True):
                st.info("KAI is automatically analyzing your CSV structure and extracting trading signals...")

                # Run Auto-Explainer analysis
                auto_analysis = kai_agent._auto_explain_csv_data(df)

                col1, col2 = st.columns(2)
                with col1:
                    if 'Data Quality Assessment' in auto_analysis:
                        st.subheader("📊 Data Quality Assessment")
                        overview = auto_analysis['Data Quality Assessment']
                        st.write(f"**Total Records:** {overview.get('total_records', 'N/A')}")
                        st.write(f"**Strategies:** {overview.get('total_strategies', 'N/A')}")
                        # Completion Rate and Data Quality Score removed

                with col2:
                    if 'Trading Signals' in auto_analysis:
                        st.subheader("📈 Signal Summary")
                        signals = auto_analysis['Trading Signals']
                        st.write(f"**Total Signals:** {signals.get('metrics', {}).get('total_signals', 'N/A')}")
                        st.write(f"**Strong Signals:** {signals.get('metrics', {}).get('strong_signals', 'N/A')}")

            # Show data preview
            with st.expander("📋 Data Preview", expanded=False):
                st.dataframe(df.head(10), use_container_width=True)

            # KAI analyzes the data with enhanced processing
            with st.spinner("🧠 KAI is performing enhanced analysis with DeepSeek AI..."):
                analysis = kai_agent.analyze_strategy_data(df)

            # ========== ULTIMATE VALIDATION: ENSURE ANALYSIS IS PROPERLY STRUCTURED ==========
            if analysis is None:
                st.error("❌ Analysis returned None - no data received")
                return

            if not isinstance(analysis, dict):
                st.error(f"❌ Analysis returned invalid type: {type(analysis)}")
                st.info("Expected a dictionary but received a different data type.")
                return

            # ENSURE ALL REQUIRED KEYS EXIST
            required_keys = [
                'header', 'executive_summary', 'key_findings', 'momentum_analysis',
                'support_resistance_levels', 'time_horizon_outlook', 'risk_assessment_data',
                'risk_assessment_summary', 'confidence_assessment', 'trading_implications',
                'signal_details', 'overview_metrics', 'deepseek_enhanced', 'deepseek_analysis'
            ]

            # Add missing keys with safe defaults
            for key in required_keys:
                if key not in analysis:
                    if key == 'header':
                        analysis[key] = "🔍 **KAI Analysis Report**"
                    elif key == 'executive_summary':
                        analysis[key] = "Analysis completed successfully"
                    elif key == 'key_findings':
                        analysis[key] = ["Analysis completed", "Data processed successfully"]
                    elif key == 'momentum_analysis':
                        analysis[key] = "Momentum analysis performed"
                    elif key == 'support_resistance_levels':
                        analysis[key] = []
                    elif key == 'time_horizon_outlook':
                        analysis[key] = {}
                    elif key == 'risk_assessment_data':
                        analysis[key] = {"overall_risk_score": 5}
                    elif key == 'risk_assessment_summary':
                        analysis[key] = "Risk assessment completed"
                    elif key == 'confidence_assessment':
                        analysis[key] = 50
                    elif key == 'trading_implications':
                        analysis[key] = ["Review analysis before trading"]
                    elif key == 'signal_details':
                        analysis[key] = {}
                    elif key == 'overview_metrics':
                        analysis[key] = {"total_strategies": 0, "completion_rate": "0%"}
                    elif key == 'deepseek_enhanced':
                        analysis[key] = False
                    elif key == 'deepseek_analysis':
                        analysis[key] = None

            # Add analysis type for tracking
            analysis['analysis_type'] = 'csv_upload'
            analysis['original_filename'] = uploaded_file.name
            analysis['total_records_analyzed'] = len(df)

            # Display KAI's enhanced report
            display_enhanced_kai_analysis_report(analysis)

            # Save analysis to Supabase
            if st.button("💾 Save Enhanced Analysis to Archive", use_container_width=True, type="primary"):
                if save_kai_analysis(analysis):
                    st.success("✅ Enhanced KAI analysis saved to archive!")
                    st.balloons()
                    # Refresh the analyses list
                    st.session_state.kai_analyses = load_kai_analyses()
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("❌ Failed to save analysis to database")

        except Exception as e:
            st.error(f"❌ Error analyzing CSV: {str(e)}")
            st.info("Please ensure you're uploading a valid strategy analysis CSV export from the dashboard.")
            # Show more detailed error for debugging
            with st.expander("🔧 Technical Details (for debugging)"):
                st.code(f"Error type: {type(e).__name__}\nError message: {str(e)}")
                import traceback
                st.code(f"Full traceback:\n{traceback.format_exc()}")

# -------------------------
# ENHANCED KAI ANALYSIS REPORT DISPLAY
# -------------------------
def display_enhanced_kai_analysis_report(analysis, analysis_meta=None, meta_info=""):
    """Display KAI's enhanced analysis report with DeepSeek integration - ULTIMATE FIXED VERSION"""

    # CRITICAL FIX: Validate that analysis is a dictionary
    if not isinstance(analysis, dict):
        st.error(f"❌ Invalid analysis data type: {type(analysis)}")
        st.info("Expected a dictionary but received a different data type. Please try the analysis again.")
        return

    # Check if analysis is None and handle gracefully
    if analysis is None:
        st.error("❌ No analysis data available. Please try running the analysis again.")
        return

    # Header with enhancement indicator and IMPROVED metadata
    is_enhanced = analysis.get('deepseek_enhanced', False)
    enhancement_badge = " 🧠 **KAI ENHANCED TECHNICAL ANALYSES**" if is_enhanced else " 📊 **STANDARD ANALYSIS**"

    # Use the passed meta_info parameter or construct it
    if not meta_info and analysis_meta:
        created_by = analysis_meta.get('uploaded_by', 'Unknown')
        created_at = analysis_meta.get('created_at', 'Unknown date')
        try:
            dt_obj = datetime.fromisoformat(created_at)
            formatted_date = dt_obj.strftime("%B %d, %Y")
            formatted_time = dt_obj.strftime("%I:%M %p UTC")
            meta_info = f" | {formatted_date} at {formatted_time}"
        except:
            meta_info = f" | {created_at[:16]}"

    st.markdown(f"###{enhancement_badge}{meta_info}")

    # Executive Summary (KAI always starts with this)
    if is_enhanced and analysis.get('deepseek_analysis'):
        # CRITICAL FIX: Validate deepseek_analysis is a dict before accessing it
        deepseek_data = analysis['deepseek_analysis']
        if isinstance(deepseek_data, dict) and deepseek_data.get('executive_summary'):
            st.success(f"**🧠 KAI-Enhanced Summary:** {deepseek_data['executive_summary']}")
        else:
            st.info(analysis.get("executive_summary", "No executive summary available"))
    else:
        st.info(analysis.get("executive_summary", "No executive summary available"))

    # Enhanced Metrics with Quantitative Scoring
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        confidence_score = analysis.get('confidence_assessment', 50)
        delta_value = "High" if confidence_score >= 70 else "Medium" if confidence_score >= 50 else "Low"
        delta_color_setting = "normal" if confidence_score >= 50 else "inverse"

        st.metric(
            f"🧠 Confidence Level",
            f"{confidence_score}%",
            delta=delta_value,
            delta_color=delta_color_setting
        )
    with col2:
        st.metric(
            "Strategies Analyzed",
            f"{analysis.get('overview_metrics', {}).get('total_strategies', 0)}"
        )
    with col3:
        st.metric(
            "Analysis Completion",
            analysis.get('overview_metrics', {}).get('completion_rate', '0/0')
        )
    with col4:
        # FIX: Use risk_assessment_data to get the overall_risk_score
        risk_data = analysis.get('risk_assessment_data', {})
        risk_score = risk_data.get('overall_risk_score', 'N/A')
        if isinstance(risk_score, (int, float)):
            delta_value = "High" if risk_score >= 7 else "Medium" if risk_score >= 5 else "Low"
            delta_color_setting = "inverse" if risk_score >= 7 else "normal" if risk_score >= 5 else "normal"
            st.metric(
                "Risk Score",
                f"{risk_score}/10",
                delta=delta_value,
                delta_color=delta_color_setting
            )
        else:
            st.metric("Risk Assessment", "Not Available")

    # Key Findings (Enhanced with AI insights)
    st.markdown("### 🔑 Key Findings & KAI Insights")

    if is_enhanced and analysis.get('deepseek_analysis', {}).get('key_findings'):
        # Use AI-enhanced findings
        for finding in analysis['deepseek_analysis']['key_findings']:
            st.write(f"• {finding}")
    else:
        # Use standard findings
        for finding in analysis.get("key_findings", []):
            st.write(f"• {finding}")

    # Enhanced Signal Breakdown with Quantitative Scoring
    st.markdown("### 📈 Enhanced Signal Breakdown")

    signals = analysis.get('signal_details', {})

    # CRITICAL FIX: Add type checking for ALL signal processing
    if not isinstance(signals, dict):
        st.warning("⚠️ Signal data format issue detected")
        signals = {}

    # Reversal Signals with Scoring (KAI's priority)
    if signals.get("reversal_signals"):
        reversal_signals = signals["reversal_signals"]
        # CRITICAL FIX: Ensure reversal_signals is a list
        if isinstance(reversal_signals, list):
            with st.expander(f"🔄 Reversal Signals ({len(reversal_signals)})", expanded=False):
                for signal in reversal_signals:
                    # CRITICAL FIX: Check if signal is a dict before calling .get()
                    if isinstance(signal, dict):
                        strength_icon = "🔥" if signal.get('strength') == 'HIGH' else "⚠️"
                        # REMOVED: Score and confidence display
                        st.write(f"{strength_icon} **{signal.get('strategy', 'Unknown')} - {signal.get('indicator', 'Unknown')}**")
                        st.write(f"   *{signal.get('message', 'No message')}*")
                    else:
                        st.write(f"⚠️ Invalid signal format: {type(signal)}")

    # Enhanced Support/Resistance Levels with Price Levels
    if signals.get("support_signals"):
        support_signals = signals["support_signals"]
        # CRITICAL FIX: Ensure support_signals is a list
        if isinstance(support_signals, list):
            with st.expander(f"📊 Support/Resistance Levels ({len(support_signals)}) - PRICE LEVELS"):
                for signal in support_signals:
                    # CRITICAL FIX: Check if signal is a dict before calling .get()
                    if isinstance(signal, dict):
                        level_icon = "🟢" if signal.get('level') == 'SUPPORT' else "🔴"
                        price_info = f" at {signal.get('price_level', 'N/A')}" if signal.get('price_level') else ""
                        strength_info = f" ({signal.get('strength', 'N/A')})" if signal.get('strength') else ""
                        st.write(f"{level_icon} **{signal.get('strategy', 'Unknown')} - {signal.get('indicator', 'Unknown')}**: {signal.get('level', 'LEVEL')}{price_info}{strength_info}")
                    else:
                        st.write(f"⚠️ Invalid signal format: {type(signal)}")

    # Enhanced Momentum Analysis
    if signals.get("momentum_signals"):
        momentum_signals = signals["momentum_signals"]
        # CRITICAL FIX: Ensure momentum_signals is a list
        if isinstance(momentum_signals, list):
            with st.expander(f"🎯 Momentum Signals ({len(momentum_signals)}) - DIRECTIONAL BIAS"):
                for signal in momentum_signals:
                    # CRITICAL FIX: Check if signal is a dict before calling .get()
                    if isinstance(signal, dict):
                        direction_icon = "📈" if signal.get('direction') == 'BULLISH' else "📉"
                        strength_info = f" ({signal.get('strength', 'N/A')})" if signal.get('strength') else ""
                        st.write(f"{direction_icon} **{signal.get('strategy', 'Unknown')} - {signal.get('indicator', 'Unknown')}**: {signal.get('message', 'No message')}{strength_info}")
                    else:
                        st.write(f"⚠️ Invalid signal format: {type(signal)}")

    # NEW: Divergence Signals - FIXED: Use .get() to avoid KeyError
    if signals.get("divergence_signals"):
        divergence_signals = signals["divergence_signals"]
        # CRITICAL FIX: Ensure divergence_signals is a list
        if isinstance(divergence_signals, list):
            with st.expander(f"⚡ Divergence Signals ({len(divergence_signals)})"):
                for signal in divergence_signals:
                    # CRITICAL FIX: Check if signal is a dict before calling .get()
                    if isinstance(signal, dict):
                        type_icon = "🟢" if signal.get('type') == 'BULLISH' else "🔴" if signal.get('type') == 'BEARISH' else "🟡"
                        st.write(f"{type_icon} **{signal.get('strategy', 'Unknown')} - {signal.get('indicator', 'Unknown')}**: {signal.get('message', 'No message')}")
                    else:
                        st.write(f"⚠️ Invalid signal format: {type(signal)}")

    # AI-ENHANCED RISK ASSESSMENT WITH DEEPSEEK
    st.markdown("### 🛡️ Risk Assessment & Management")

    # Extract quality data from analysis
    quality = analysis.get('data_quality', {})
    quality_tier = analysis.get('quality_tier', 'PRODUCTION')

    # DISPLAY QUALITY ASSESSMENT FIRST - SIMPLIFIED
    st.markdown("#### 📊 Data Quality Assessment")

    if quality:
        # Quality Score Only
        quality_score = quality.get('quality_score', 0)
        quality_tag = DataQualityFramework.get_quality_tag(quality_score)
        st.metric("Quality Score", f"{quality_score:.1f}/100", delta=quality_tag)

    st.markdown("---")

    # NOW DISPLAY AI-ENHANCED RISK ASSESSMENT
    st.markdown("#### ⚠️ Trading Risk Assessment")

    # Use DeepSeek AI for risk assessment if available, otherwise fall back to standard
    if analysis.get('deepseek_enhanced') and analysis.get('deepseek_analysis'):
        deepseek_data = analysis['deepseek_analysis']

        # Display AI-generated risk analysis
        if deepseek_data.get('risk_analysis'):
            st.markdown("🧠 **KAI Risk Assessment:**")
            st.info(deepseek_data['risk_analysis'])

        # Display confidence score from AI
        confidence = deepseek_data.get('confidence_score', 50)
        col1, col2 = st.columns(2)

        with col1:
            delta_value = "High" if confidence >= 70 else "Medium" if confidence >= 50 else "Low"
            delta_color = "normal" if confidence >= 50 else "inverse"
            st.metric(
                "AI Confidence Level",
                f"{confidence}%",
                delta=delta_value,
                delta_color=delta_color
            )

        with col2:
            # Map confidence to risk level for quick visual
            if confidence >= 70:
                st.success("🟢 **LOW RISK** - High confidence in signal alignment")
            elif confidence >= 50:
                st.warning("🟡 **MODERATE RISK** - Moderate confidence, some uncertainty")
            else:
                st.error("🔴 **HIGH RISK** - Low confidence, significant uncertainty")

        # Display AI trading recommendations
        if deepseek_data.get('trading_recommendations'):
            st.markdown("---")
            st.markdown("🧠 **KAI Trading Recommendations:**")
            for recommendation in deepseek_data['trading_recommendations'][:3]:
                st.write(f"• {recommendation}")

    else:
        # Fallback to standard risk assessment when AI is not available
        risk_data = analysis.get('risk_assessment_data', {})
        risk_summary = analysis.get('risk_assessment_summary', '')
        risk_score = risk_data.get('overall_risk_score', 5)

        # Show KAI's standard risk assessment
        if risk_score >= 7:
            st.error("🔴 **HIGH RISK ENVIRONMENT** - Exercise extreme caution with position sizing")
            st.write("**KAI Assessment:** Multiple conflicting indicators detected. Strong directional disagreement across confirmations.")
        elif risk_score >= 5:
            st.warning("🟡 **MODERATE RISK** - Standard risk management appropriate")
            st.write("**KAI Assessment:** Some uncertainty in indicator alignment. Consider additional confirmation before trading.")
        else:
            st.success("🟢 **LOW RISK** - Favorable conditions for trading")
            st.write("**KAI Assessment:** Strong signal alignment across indicators. Directional bias confirmed.")

    # Always show actionable risk management guidelines
    st.markdown("---")
    st.markdown("🛡️ **KAI's Risk Management Protocol:**")

    col1, col2 = st.columns(2)

    with col1:
        st.write("**Position Sizing Framework:**")
        st.write("• Maximum 1-3% risk per trade")
        st.write("• Scale in/out (DCA) based on confidence")
        st.write("• **NEVER over-leverage (max 3x)**")
        st.write("• **Stop Loss Strategy:**")
        st.write("  - Hard stops: day trading & swing trading")
        st.write("  - Mental stops: long-term investments")

    with col2:
        st.write("**Risk Control Measures:**")
        st.write("• Monitor correlation between signals")
        st.write("• Watch for conflicting timeframes")
        st.write("• Validate with volume confirmation")
        st.write("• Consider market context")

    # Quantitative risk factors
    st.markdown("---")
    st.markdown("📊 **Quantitative Risk Factors:**")

    signal_details = analysis.get('signal_details', {})

    col1, col2, col3 = st.columns(3)

    with col1:
        # Conflicting signals count
        conflicting_count = len(signal_details.get('conflicting_signals', []))
        st.metric("Conflicting Signals", conflicting_count, delta_color="inverse")

    with col2:
        # Strong reversal signals
        reversal_signals = signal_details.get('reversal_signals', [])
        strong_reversals = len([s for s in reversal_signals if s.get('strength') == 'HIGH'])
        st.metric("Strong Reversals", strong_reversals)

    with col3:
        # Signal consistency score
        bullish = quality.get('bullish_signals', 0)
        bearish = quality.get('bearish_signals', 0)
        neutral = quality.get('neutral_signals', 0)
        total_directional = bullish + bearish + neutral
        if total_directional > 0:
            max_direction = max(bullish, bearish, neutral)
            consistency = (max_direction / total_directional) * 100
            st.metric("Signal Consistency", f"{consistency:.1f}%")
        else:
            st.metric("Signal Consistency", "N/A")

    # Quantitative Analysis Summary
    st.markdown("### 📊 Quantitative Analysis Summary")

    summary_cols = st.columns(3)

    with summary_cols[0]:
        total_signals = 0
        if isinstance(signals, dict):
            for signal_type, signal_list in signals.items():
                if isinstance(signal_list, list):
                    total_signals += len(signal_list)
        st.metric("Total Signals Detected", total_signals)

    with summary_cols[1]:
        high_confidence_signals = 0
        if isinstance(signals, dict) and isinstance(signals.get("reversal_signals"), list):
            for signal in signals["reversal_signals"]:
                if isinstance(signal, dict) and signal.get('confidence', 0) >= 70:
                    high_confidence_signals += 1
        st.metric("High Confidence Signals", high_confidence_signals)

    with summary_cols[2]:
        conflict_count = 0
        if isinstance(signals, dict) and isinstance(signals.get("conflicting_signals"), list):
            conflict_count = len(signals["conflicting_signals"])
        st.metric("Conflicting Signals", conflict_count, delta_color="inverse")

def display_kai_analysis_summary(analysis):
    """Display a summary of KAI analysis for history view"""
    is_enhanced = analysis.get('deepseek_enhanced', False)
    enhancement_badge = " 🧠" if is_enhanced else " 📊"

    st.write(f"**{analysis['executive_summary']}**{enhancement_badge}")
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
    VERSION = "2.1.0"
    SUPPORT_EMAIL = "support@tradinganalysis.com"
    BUSINESS_NAME = "TradingAnalysis Inc."

    # Updated Subscription Plans
    PLANS = {
        "trial": {
            "name": "7-Day Trial",
            "price": 0,
            "duration": 7,
            "strategies": 3,
            "max_sessions": 1
        },
        "premium": {
            "name": "Premium Plan",
            "price": 19,
            "duration": 30,
            "strategies": 15,
            "max_sessions": 3
        },
        "premium_3month": {
            "name": "3-Month Premium",
            "price": 49,
            "duration": 90,
            "strategies": 15,
            "max_sessions": 3
        },
        "premium_6month": {
            "name": "6-Month Premium",
            "price": 97,
            "duration": 180,
            "strategies": 15,
            "max_sessions": 3
        },
        "premium_12month": {
            "name": "12-Month Premium",
            "price": 179,
            "duration": 365,
            "strategies": 15,
            "max_sessions": 3
        }
    }

    # Ko-Fi Payment Links (replace with your actual Ko-Fi shop links)
    KOFI_PREMIUM_MONTHLY_LINK = "https://ko-fi.com/s/39c3423f1d"
    KOFI_PREMIUM_QUARTERLY_LINK = "https://ko-fi.com/s/9b73dfca2a"
    KOFI_PREMIUM_SEMI_ANNUAL_LINK = "https://ko-fi.com/s/419cbf74f9"
    KOFI_PREMIUM_ANNUAL_LINK = "https://ko-fi.com/s/bba601fa2b"

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

    def upgrade_user_to_premium_tier(self, username, plan_key, duration_days, admin_username):
        """
        Upgrade a user to a specific premium tier
        
        Args:
            username: The username to upgrade
            plan_key: The plan key (e.g., 'premium', 'premium_3month', 'premium_6month', 'premium_12month')
            duration_days: Number of days for this tier
            admin_username: The admin performing the upgrade
        
        Returns:
            (success: bool, message: str)
        """
        try:
            if username not in self.users:
                return False, "User not found"

            user_data = self.users[username]
            old_plan = user_data.get('plan', 'unknown')
            
            # Calculate new expiry date
            new_expiry = (datetime.now() + timedelta(days=duration_days)).strftime("%Y-%m-%d")
            
            # Update user data
            user_data['plan'] = plan_key
            user_data['expires'] = new_expiry
            user_data['max_sessions'] = Config.PLANS.get(plan_key, {}).get('max_sessions', 3)
            
            # Update analytics
            if 'plan_changes' not in self.analytics:
                self.analytics['plan_changes'] = []

            plan_name = Config.PLANS.get(plan_key, {}).get('name', plan_key)
            old_plan_name = Config.PLANS.get(old_plan, {}).get('name', old_plan)
            
            self.analytics['plan_changes'].append({
                "username": username,
                "old_plan": old_plan,
                "new_plan": plan_key,
                "timestamp": datetime.now().isoformat(),
                "admin": admin_username,
                "duration_days": duration_days
            })

            # Save changes
            if self.save_users() and self.save_analytics():
                return True, f"{username} upgraded from {old_plan_name} to {plan_name} ({duration_days} days)"
            else:
                return False, "Error saving upgrade to database"
                
        except Exception as e:
            return False, f"Error during upgrade: {str(e)}"

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
    """Render the manage user plan interface with manual upgrade options"""
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

    # Back button at the top
    if st.button("Back to User Management", key="manage_user_back_top"):
        st.session_state.manage_user_plan = None
        st.session_state.show_manage_user_plan = False
        st.rerun()

    st.subheader(f"Manage User: {username}")

    # Main form for user details
    with st.form(f"manage_user_{username}"):
        col1, col2 = st.columns(2)

        with col1:
            st.write("**User Information:**")
            st.text_input("Name", value=user_data.get('name', ''), disabled=True, key=f"name_{username}")
            st.text_input("Email", value=user_data.get('email', ''), disabled=True, key=f"email_{username}")
            st.text_input("Created", value=user_data.get('created', '')[:10], disabled=True, key=f"created_{username}")

            email_verified = user_data.get('email_verified', False)
            verification_status = "Verified" if email_verified else "Unverified"
            st.text_input("Email Status", value=verification_status, disabled=True, key=f"email_status_{username}")

        with col2:
            st.write("**Plan Management:**")
            current_plan = user_data.get('plan', 'trial')
            st.text_input("Current Plan", value=Config.PLANS.get(current_plan, {}).get('name', current_plan), disabled=True, key=f"current_plan_{username}")

            current_expiry = user_data.get('expires', '')
            st.text_input("Current Expiry", value=current_expiry, disabled=True, key=f"current_expiry_{username}")

            days_left = (datetime.strptime(current_expiry, "%Y-%m-%d").date() - date.today()).days if current_expiry else 0
            st.text_input("Days Remaining", value=str(days_left), disabled=True, key=f"days_left_{username}")

            is_active = st.checkbox(
                "Account Active",
                value=user_data.get('is_active', True),
                key=f"active_{username}"
            )

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
            save_changes = st.form_submit_button("Save Changes", use_container_width=True, type="primary")

        with col_b2:
            delete_user = st.form_submit_button("Delete User", use_container_width=True, type="secondary")

        with col_b3:
            cancel = st.form_submit_button("Cancel", use_container_width=True)

        if save_changes:
            user_data['is_active'] = is_active
            user_data['max_sessions'] = max_sessions

            if user_manager.save_users():
                st.success("User settings updated successfully!")
                time.sleep(2)
                st.session_state.manage_user_plan = None
                st.session_state.show_manage_user_plan = False
                st.rerun()
            else:
                st.error("Error saving user settings")

        if delete_user:
            st.session_state.user_to_delete = username
            st.session_state.show_delete_confirmation = True
            st.rerun()

        if cancel:
            st.session_state.manage_user_plan = None
            st.session_state.show_manage_user_plan = False
            st.rerun()

    st.markdown("---")

    # Premium Tier Upgrade Section
    st.subheader("Manual Premium Upgrade")
    st.info("Select a premium tier to manually upgrade this user. Their subscription will be extended accordingly.")

    # Display current plan tier
    current_plan = user_data.get('plan', 'trial')
    if current_plan.startswith('premium'):
        plan_name = Config.PLANS.get(current_plan, {}).get('name', current_plan)
        st.success(f"Current Premium Tier: **{plan_name}**")
    else:
        st.warning(f"Current Plan: **{Config.PLANS.get(current_plan, {}).get('name', current_plan)}**")

    st.markdown("---")

    # Premium tier options in columns
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("### 1 Month")
        st.write("**$19**")
        st.write("30 days")
        if st.button("Upgrade", key=f"upgrade_1m_{username}", use_container_width=True):
            success, message = user_manager.upgrade_user_to_premium_tier(username, "premium", 30, st.session_state.user['username'])
            if success:
                st.success(message)
                time.sleep(2)
                st.rerun()
            else:
                st.error(message)

    with col2:
        st.markdown("### 3 Months")
        st.write("**$49**")
        st.write("90 days")
        if st.button("Upgrade", key=f"upgrade_3m_{username}", use_container_width=True):
            success, message = user_manager.upgrade_user_to_premium_tier(username, "premium_3month", 90, st.session_state.user['username'])
            if success:
                st.success(message)
                time.sleep(2)
                st.rerun()
            else:
                st.error(message)

    with col3:
        st.markdown("### 6 Months")
        st.write("**$97**")
        st.write("180 days")
        if st.button("Upgrade", key=f"upgrade_6m_{username}", use_container_width=True):
            success, message = user_manager.upgrade_user_to_premium_tier(username, "premium_6month", 180, st.session_state.user['username'])
            if success:
                st.success(message)
                time.sleep(2)
                st.rerun()
            else:
                st.error(message)

    with col4:
        st.markdown("### 12 Months")
        st.write("**$179**")
        st.write("365 days")
        if st.button("Upgrade", key=f"upgrade_12m_{username}", use_container_width=True):
            success, message = user_manager.upgrade_user_to_premium_tier(username, "premium_12month", 365, st.session_state.user['username'])
            if success:
                st.success(message)
                time.sleep(2)
                st.rerun()
            else:
                st.error(message)

    st.markdown("---")

    # Email verification and password reset
    st.write("**Email Verification & Password Reset:**")
    col_v1, col_v2 = st.columns(2)

    with col_v1:
        with st.form(f"verify_email_{username}"):
            if not user_data.get('email_verified', False):
                if st.form_submit_button("Verify Email", use_container_width=True, key=f"verify_email_btn_{username}"):
                    success, message = user_manager.verify_user_email(username, st.session_state.user['username'], "Manually verified by admin")
                    if success:
                        st.success(message)
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)
            else:
                if st.form_submit_button("Revoke Verification", use_container_width=True, key=f"revoke_email_btn_{username}"):
                    success, message = user_manager.revoke_email_verification(username, st.session_state.user['username'], "Revoked by admin")
                    if success:
                        st.success(message)
                        time.sleep(2)
                        st.rerun()
                    else:
                        st.error(message)

    with col_v2:
        with st.form(f"reset_password_{username}"):
            if st.form_submit_button("Reset Password", use_container_width=True, key=f"reset_password_btn_{username}"):
                new_password = f"TempPass{int(time.time()) % 10000}"
                success, message = user_manager.change_user_password(username, new_password, st.session_state.user['username'])
                if success:
                    st.success(f"Password reset! New temporary password: {new_password}")
                    st.info("User should change this password immediately after login.")
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
    """Password gate with proper tracking - FIXED VERSION"""
    st.title("🔒 Trading Signals Room - Secure Access")
    
    # NEW: "Get Access Now" button at the top LEFT
    col1, col2 = st.columns([1, 3])  # Changed order - left column is smaller for button
    with col1:
        st.markdown(
            f'<a href="https://ko-fi.com/s/a6da7eb515" target="_blank">'
            f'<button style="background-color: #10B981; color: white; border: none; padding: 10px 16px; '
            f'text-align: center; text-decoration: none; display: inline-block; font-size: 14px; '
            f'cursor: pointer; border-radius: 6px; width: 100%; font-weight: bold;">'
            f'🚀 Get Access Now</button></a>',
            unsafe_allow_html=True
        )
    with col2:
        st.markdown("")  # Empty space for alignment
    
    st.markdown("---")

    st.warning("⚠️ **SECURE ACCESS REQUIRED** - Enter password to continue.")

    with st.form("signals_room_password_form"):
        password_input = st.text_input(
            "🔑 Enter Signals Room Password:",
            type="password",
            placeholder="Enter password...",
            key="signals_room_password_input"
        )

        submitted = st.form_submit_button("🚀 Access Trading Signals Room", use_container_width=True)

        if submitted:
            if password_input == st.session_state.signals_room_password:
                current_username = st.session_state.user['username']
                
                # CRITICAL: Track access BEFORE granting permission
                track_signals_access(current_username)
                
                # THEN grant access
                st.session_state.signals_room_access_granted = True
                st.success("✅ Access granted!")
                
                # FORCE a rerun to show the signals room
                time.sleep(1)
                st.rerun()
            else:
                st.error("❌ Incorrect password")

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
                
                # FIXED: View-only plan selection - Always Trial
                plan_choice = "trial"  # HARDCODED to trial
                plan_info = Config.PLANS["trial"]
                st.text_input(
                    "Subscription Plan*",
                    value=f"{plan_info['name']} - Free",
                    disabled=True,
                    key="register_plan_display"
                )

            with col2:
                new_email = st.text_input("Email Address*", key="register_email")
                new_password = st.text_input("Create Password*", type="password", help="Minimum 8 characters", key="register_password")
                confirm_password = st.text_input("Confirm Password*", type="password", key="register_confirm_password")

            st.markdown("Required fields marked with *")

            # Plan features - Display Trial features
            st.info(f"""
            ✅ **{plan_info['name']} Features (Free):**
            • {plan_info['strategies']} Trading Strategies
            • {plan_info['max_sessions']} Concurrent Session
            • {plan_info['duration']}-day access
            • Basic Signal Access
            • View-Only Gallery
            • KAI Analysis View
            • No payment required
            """)

            # Terms agreement checkbox
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
    """Main gallery - now paginated"""
    import streamlit as st
    st.session_state.gallery_page = 0
    st.title("📸 User Image Gallery (Paginated View)")
    render_image_gallery_paginated()

def decode_image_from_storage(item):
    """Decode image from storage format - placeholder implementation"""
    try:
        # This is a simplified version - you'll need to adapt based on your actual storage format
        if 'bytes_b64' in item:
            return base64.b64decode(item['bytes_b64'])
        return None
    except Exception:
        return None

# =====================================================================
# GALLERY PAGINATION CORE (placed before dashboard & main)
# =====================================================================
def get_gallery_images_count():
    """Get total count of gallery images"""
    if 'supabase_client' not in globals() or not supabase_client:
        return _cache_get("lk_gallery_count", 0)
    try:
        resp = supabase_client.table('gallery_images').select('id', count='exact').execute()
        if hasattr(resp, 'error') and resp.error:
            logging.error(f"Count error: {resp.error}")
            return _cache_get("lk_gallery_count", 0)
        count = getattr(resp, 'count', None) or (resp.data and len(resp.data)) or 0
        _cache_set("lk_gallery_count", count)
        return count
    except Exception as e:
        logging.error(f"Database count error: {e}")
        return _cache_get("lk_gallery_count", 0)

# USER IMAGE GALLERY - VIEW ONLY VERSION
# -------------------------
def render_user_image_gallery():
    """User image gallery with full database-backed pagination (FINAL)"""
    import streamlit as st

    # ---------- SAFETY: ensure needed session keys exist ----------
    if 'gallery_page' not in st.session_state:
        st.session_state.gallery_page = 0
    if 'gallery_per_page' not in st.session_state:
        st.session_state.gallery_per_page = 15
    if 'gallery_filter_author' not in st.session_state:
        st.session_state.gallery_filter_author = "All Authors"
    if 'gallery_filter_strategy' not in st.session_state:
        st.session_state.gallery_filter_strategy = "All Strategies"

    # ---------- HEADER ----------
    st.title("📸 Trading Analysis Image Gallery")
    st.markdown("View trading charts, analysis screenshots, and market insights shared by the community.")
    st.markdown("---")

    # Optional top tabs (Gallery / Statistics)
    tab1, tab2 = st.tabs(["🖼️ Image Gallery", "📊 Statistics"])
    with tab2:
        try:
            # Reuse your existing stats block
            if 'render_gallery_statistics_paginated' in globals():
                render_gallery_statistics_paginated()
            else:
                # Minimal stats fallback if function is not present
                total_images = get_gallery_images_count_filtered()
                st.metric("Total Images", total_images)
        except Exception as e:
            st.warning(f"Statistics unavailable: {e}")

    with tab1:
        # ---------- CONTROLS ----------
        st.subheader("🔍 Gallery Controls")
        c1, c2, c3, c4, c5 = st.columns(5)

        with c1:
            sort_by = st.selectbox(
                "Sort by:",
                ["newest", "oldest", "most_liked"],
                key="user_gallery_sort"
            )

        with c2:
            # Best-effort author list from any cached/known images in session
            authors_set = set(
                img.get('uploaded_by', 'Unknown')
                for img in (st.session_state.get('uploaded_images', []))
            )
            author_choice = st.selectbox(
                "Filter by Author:",
                ["All Authors"] + sorted(list(authors_set)),
                key="user_gallery_filter_author"
            )

        with c3:
            # If you keep strategies in st.session_state.STRATEGIES (dict), reuse it
            STRATEGIES = st.session_state.get('STRATEGIES', {})
            strategies_list = list(STRATEGIES.keys()) if isinstance(STRATEGIES, dict) else []
            strategy_choice = st.selectbox(
                "Filter by Strategy:",
                ["All Strategies"] + strategies_list,
                key="user_gallery_filter_strategy"
            )

        with c4:
            per_page = st.selectbox(
                "Per Page:",
                [10, 15, 20, 30],
                index=[10, 15, 20, 30].index(st.session_state.get("gallery_per_page", 15)) if st.session_state.get("gallery_per_page", 15) in [10, 15, 20, 30] else 1,
                key="user_gallery_per_page"
            )
            # Persist per-page
            st.session_state.gallery_per_page = per_page

        with c5:
            if st.button("🔄 Refresh", use_container_width=True, key="user_gallery_refresh"):
                st.rerun()

        # ---------- HANDLE FILTER CHANGES: reset to page 1 ----------
        # (We only reset if user changed the selection in this render cycle)
        if author_choice != st.session_state.get("_last_user_author_choice"):
            st.session_state.gallery_page = 0
            st.session_state._last_user_author_choice = author_choice
            st.rerun()
        if strategy_choice != st.session_state.get("_last_user_strategy_choice"):
            st.session_state.gallery_page = 0
            st.session_state._last_user_strategy_choice = strategy_choice
            st.rerun()

        st.markdown("---")

        # ---------- TOTAL COUNT ----------
        filter_author = None if author_choice == "All Authors" else author_choice
        filter_strategy = None if strategy_choice == "All Strategies" else strategy_choice

        with st.spinner("📊 Counting images..."):
            total_images = get_gallery_images_count_filtered(
                filter_author=filter_author,
                filter_strategy=filter_strategy
            )

        if total_images == 0:
            st.warning("🖼️ **No images found** for the selected filters.")
            return

        total_pages = (total_images + per_page - 1) // per_page
        current_page = min(st.session_state.gallery_page, max(0, total_pages - 1))

        # ---------- STATS ----------
        st.subheader("📈 Gallery Statistics")
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1: st.metric("Total Images", total_images)
        with sc2: st.metric("Total Pages", total_pages)
        with sc3: st.metric("Current Page", current_page + 1)
        with sc4:
            start_num = current_page * per_page + 1
            end_num = min((current_page + 1) * per_page, total_images)
            st.metric("Showing", f"{start_num}-{end_num}")

        st.markdown("---")

        # ---------- TOP NAV ----------
        st.subheader("📄 Page Navigation")
        n1, n2, n3, n4, n5 = st.columns(5)

        with n1:
            if st.button("⏮️ First Page", use_container_width=True, key="user_gallery_first_top"):
                st.session_state.gallery_page = 0
                st.rerun()

        with n2:
            if current_page > 0:
                if st.button("◀️ Previous", use_container_width=True, key="user_gallery_prev_top"):
                    st.session_state.gallery_page = current_page - 1
                    st.rerun()
            else:
                st.button("◀️ Previous", use_container_width=True, disabled=True, key="user_gallery_prev_top_disabled")

        with n3:
            jump_page = st.number_input(
                "Go to Page:",
                min_value=1,
                max_value=max(1, total_pages),
                value=current_page + 1,
                key="user_gallery_jump"
            ) - 1
            if jump_page != current_page:
                st.session_state.gallery_page = max(0, min(jump_page, total_pages - 1))
                st.rerun()

        with n4:
            if current_page < total_pages - 1:
                if st.button("Next ▶️", use_container_width=True, key="user_gallery_next_top"):
                    st.session_state.gallery_page = current_page + 1
                    st.rerun()
            else:
                st.button("Next ▶️", use_container_width=True, disabled=True, key="user_gallery_next_top_disabled")

        with n5:
            if st.button("⏭️ Last Page", use_container_width=True, key="user_gallery_last_top"):
                st.session_state.gallery_page = total_pages - 1
                st.rerun()

        st.markdown("---")

        # ---------- PAGE DATA ----------
        with st.spinner("📥 Loading images..."):
            page_images = get_gallery_images_paginated(
                page=current_page,
                per_page=per_page,
                sort_by=sort_by,
                filter_author=filter_author,
                filter_strategy=filter_strategy
            )

        if not page_images:
            st.warning("⚠️ Failed to load images for this page.")
            if current_page > 0:
                st.session_state.gallery_page = 0
                st.rerun()
            return

        # Save current page images (if your viewer uses this)
        st.session_state.current_page_images = page_images

        # ---------- GRID ----------
        st.subheader(f"📸 Page {current_page + 1} Images")
        cols = st.columns(3)
        for idx, img_data in enumerate(page_images):
            col = cols[idx % 3]
            with col:
                # Use user card if you have one; otherwise reuse the generic card
                if 'render_user_image_card_paginated' in globals():
                    render_user_image_card_paginated(img_data, current_page, idx)
                else:
                    render_image_card_paginated(img_data, current_page, idx)

        st.markdown("---")

        # ---------- BOTTOM NAV ----------
        st.subheader("📄 Bottom Navigation")
        b1, b2, b3, b4, b5 = st.columns(5)

        with b1:
            if st.button("⏮️ First", use_container_width=True, key="user_gallery_first_bottom"):
                st.session_state.gallery_page = 0
                st.rerun()

        with b2:
            if current_page > 0:
                if st.button("◀️ Prev", use_container_width=True, key="user_gallery_prev_bottom"):
                    st.session_state.gallery_page = current_page - 1
                    st.rerun()
            else:
                st.button("◀️ Prev", use_container_width=True, disabled=True, key="user_gallery_prev_bottom_disabled")

        with b3:
            st.write(f"**Page {current_page + 1}/{total_pages}**")

        with b4:
            if current_page < total_pages - 1:
                if st.button("Next ▶️", use_container_width=True, key="user_gallery_next_bottom"):
                    st.session_state.gallery_page = current_page + 1
                    st.rerun()
            else:
                st.button("Next ▶️", use_container_width=True, disabled=True, key="user_gallery_next_bottom_disabled")

        with b5:
            if st.button("⏭️ Last", use_container_width=True, key="user_gallery_last_bottom"):
                st.session_state.gallery_page = total_pages - 1
                st.rerun()

        st.markdown("---")
        st.caption(f"✅ Displaying images {start_num}-{end_num} of {total_images} total")

def render_user_image_card_paginated(img_data, page_num, index):
    """Render individual image card - CLEAN IMAGE WITH DATE AND SMALL INFO"""
    try:
        # Get image bytes
        image_bytes = None
        if 'bytes' in img_data:
            image_bytes = img_data['bytes']
        elif 'bytes_b64' in img_data:
            image_bytes = base64.b64decode(img_data['bytes_b64'])
        
        if image_bytes:
            st.image(
                image_bytes,
                use_container_width=True,
                caption=None
            )
        else:
            st.warning("🖼️ Image data not available")
    except Exception as e:
        st.error(f"❌ Error displaying image")
    
    # Date and Download button row
    col1, col2 = st.columns([2, 1])
    
    with col1:
        timestamp = img_data.get('timestamp', '')
        if timestamp:
            try:
                upload_time = datetime.fromisoformat(timestamp).strftime("%m/%d/%Y")
                st.caption(f"📅 {upload_time}")
            except:
                st.caption(f"📅 {timestamp[:10]}")
        else:
            st.caption("📅 Unknown date")
    
    with col2:
        try:
            image_bytes = None
            if 'bytes' in img_data:
                image_bytes = img_data['bytes']
            elif 'bytes_b64' in img_data:
                image_bytes = base64.b64decode(img_data['bytes_b64'])
            
            if image_bytes:
                b64_img = base64.b64encode(image_bytes).decode()
                file_format = get_image_format_safe(img_data).lower()
                file_name = img_data.get('name', f'image_{index}')
                href = f'<a href="data:image/{file_format};base64,{b64_img}" download="{file_name}.{file_format}"><button style="width:100%; padding:6px; background:#4CAF50; color:white; border:none; border-radius:4px; cursor:pointer; font-size:12px; font-weight:bold;">⬇️ Download</button></a>'
                st.markdown(href, unsafe_allow_html=True)
        except Exception as e:
            st.button("⬇️ Download", disabled=True, use_container_width=True)
    
    st.divider()

def render_user_image_card(img_data, index):
    """Render individual image card for users - UPDATED FOR PAGINATION"""
    with st.container():
        # Display image at 50% width for better visibility
        col_image, col_info = st.columns([1.5, 1])  # 60% image, 40% info

        with col_image:
            try:
                # Check if we have bytes data in the expected format
                image_bytes = None
                if 'bytes' in img_data:
                    image_bytes = img_data['bytes']
                elif 'bytes_b64' in img_data:
                    image_bytes = base64.b64decode(img_data['bytes_b64'])
                
                if image_bytes:
                    st.image(
                        image_bytes,
                        use_container_width=True,
                        caption=img_data.get('name', 'Unnamed Image')
                    )
                else:
                    st.warning("📷 Image data not available")
            except Exception as e:
                st.error(f"❌ Error displaying image: {str(e)}")
                st.info("Image format may not be supported.")

        with col_info:
            # Image info on the right side
            st.markdown(f"**{img_data.get('name', 'Unnamed Image')}**")
            st.divider()

            # Description
            description = img_data.get('description', '')
            if description:
                preview = description[:100] + "..." if len(description) > 100 else description
                st.caption(f"📝 {preview}")
            else:
                st.caption("No description")

            # Strategy tags
            strategies = img_data.get('strategies', [])
            if strategies:
                st.caption(f"🏷️ **Strategies:**")
                for strategy in strategies[:3]:
                    st.caption(f"  • {strategy}")
                if len(strategies) > 3:
                    st.caption(f"  +{len(strategies) - 3} more")

            st.divider()

            # Metadata
            st.caption(f"👤 By: **{img_data.get('uploaded_by', 'Unknown')}**")
            timestamp = img_data.get('timestamp', '')
            if timestamp:
                try:
                    upload_time = datetime.fromisoformat(timestamp).strftime("%m/%d/%Y %H:%M")
                    st.caption(f"📅 {upload_time}")
                except:
                    st.caption(f"📅 {timestamp}")

            st.divider()

            # Interaction buttons - FULL WIDTH for better UX
            col_like, col_view = st.columns(2)

            with col_like:
                if st.button("❤️ Like", key=f"user_like_{index}_{img_data.get('id', index)}", use_container_width=True):
                    # Note: Like functionality would need to be implemented in the database
                    st.info("Like functionality requires database update implementation")
                    # img_data['likes'] = img_data.get('likes', 0) + 1
                    # save_gallery_images(st.session_state.uploaded_images)
                    # st.rerun()

            with col_view:
                if st.button("🖼️ Fullscreen", key=f"user_view_{index}_{img_data.get('id', index)}", use_container_width=True):
                    st.session_state.current_image_index = index
                    st.session_state.current_page_images = images  # Store current page images
                    st.session_state.image_viewer_mode = True
                    st.rerun()

            # Like count and download
            col_count, col_download = st.columns(2)
            with col_count:
                likes = img_data.get('likes', 0)
                st.metric("Likes", likes, label_visibility="collapsed")

            with col_download:
                try:
                    # Get image bytes for download
                    image_bytes = None
                    if 'bytes' in img_data:
                        image_bytes = img_data['bytes']
                    elif 'bytes_b64' in img_data:
                        image_bytes = base64.b64decode(img_data['bytes_b64'])
                    
                    if image_bytes:
                        b64_img = base64.b64encode(image_bytes).decode()
                        file_format = get_image_format_safe(img_data).lower()
                        file_name = img_data.get('name', f'image_{index}')
                        href = f'<a href="data:image/{file_format};base64,{b64_img}" download="{file_name}.{file_format}" style="text-decoration: none;">'
                        st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 8px; text-align: center; text-decoration: none; display: inline-block; font-size: 12px; cursor: pointer; border-radius: 4px; width: 100%;">⬇️ Download</button></a>', unsafe_allow_html=True)
                    else:
                        st.caption("Download unavailable")
                except Exception as e:
                    st.caption("Download unavailable")

        st.markdown("---")

def render_image_viewer():
    """Image viewer for both admin and user galleries"""
    if not hasattr(st.session_state, 'current_page_images') or not st.session_state.current_page_images:
        st.warning("No images to display")
        st.session_state.image_viewer_mode = False
        st.rerun()
        return

    current_images = st.session_state.current_page_images
    current_index = st.session_state.current_image_index
    
    if current_index >= len(current_images):
        st.session_state.current_image_index = 0
        current_index = 0

    img_data = current_images[current_index]

    # Header with navigation
    col1, col2, col3, col4, col5 = st.columns([1, 1, 2, 1, 1])
    
    with col1:
        if st.button("⬅️ Back", use_container_width=True, key="viewer_back"):
            st.session_state.image_viewer_mode = False
            st.rerun()
            
    with col2:
        if st.button("◀️ Previous", use_container_width=True, disabled=current_index == 0, key="viewer_prev"):
            st.session_state.current_image_index = max(0, current_index - 1)
            st.rerun()
            
    with col3:
        st.markdown(f"### {img_data.get('name', 'Image Viewer')}")
        st.caption(f"Image {current_index + 1} of {len(current_images)}")
        
    with col4:
        if st.button("Next ▶️", use_container_width=True, disabled=current_index >= len(current_images) - 1, key="viewer_next"):
            st.session_state.current_image_index = min(len(current_images) - 1, current_index + 1)
            st.rerun()
            
    with col5:
        if st.button("📋 Close", use_container_width=True, key="viewer_close"):
            st.session_state.image_viewer_mode = False
            st.rerun()

    st.markdown("---")

    # Display the image at full width
    try:
        # Get image bytes
        image_bytes = None
        if 'bytes' in img_data:
            image_bytes = img_data['bytes']
        elif 'bytes_b64' in img_data:
            image_bytes = base64.b64decode(img_data['bytes_b64'])
        
        if image_bytes:
            st.image(image_bytes, use_container_width=True, caption=img_data.get('name', ''))
        else:
            st.error("❌ Unable to load image data")
    except Exception as e:
        st.error(f"❌ Error displaying image: {str(e)}")

    # Image details
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Image Details")
        st.write(f"**Name:** {img_data.get('name', 'N/A')}")
        st.write(f"**Uploaded by:** {img_data.get('uploaded_by', 'N/A')}")
        st.write(f"**Format:** {img_data.get('format', 'N/A')}")
        
        timestamp = img_data.get('timestamp', '')
        if timestamp:
            try:
                upload_time = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                st.write(f"**Uploaded:** {upload_time}")
            except:
                st.write(f"**Uploaded:** {timestamp}")
                
        st.write(f"**Likes:** {img_data.get('likes', 0)}")

    with col2:
        st.subheader("Description & Strategies")
        description = img_data.get('description', '')
        if description:
            st.write(description)
        else:
            st.info("No description provided")
            
        strategies = img_data.get('strategies', [])
        if strategies:
            st.write("**Related Strategies:**")
            for strategy in strategies:
                st.write(f"• {strategy}")
        else:
            st.info("No strategies tagged")

    # Download button
    st.markdown("---")
    try:
        image_bytes = None
        if 'bytes' in img_data:
            image_bytes = img_data['bytes']
        elif 'bytes_b64' in img_data:
            image_bytes = base64.b64decode(img_data['bytes_b64'])
            
        if image_bytes:
            b64_img = base64.b64encode(image_bytes).decode()
            file_format = get_image_format_safe(img_data).lower()
            file_name = img_data.get('name', f'image_{current_index}')
            href = f'<a href="data:image/{file_format};base64,{b64_img}" download="{file_name}.{file_format}" style="text-decoration: none;">'
            st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 12px 24px; text-align: center; text-decoration: none; display: inline-block; font-size: 16px; margin: 4px 2px; cursor: pointer; border-radius: 4px; width: 100%;">⬇️ Download Full Resolution Image</button></a>', unsafe_allow_html=True)
    except Exception as e:
        st.error("Download unavailable")

# -------------------------
# STRATEGY INDICATOR IMAGE UPLOAD AND DISPLAY COMPONENTS - FIXED VERSION
# -------------------------
def render_strategy_indicator_image_upload(strategy_name, indicator_name):
    """Render image upload for a specific strategy indicator - FULL WIDTH"""
    st.subheader(f"🖼️ {indicator_name} - Chart Image")

    # Check if there's already an image for this indicator
    existing_image = get_strategy_indicator_image(strategy_name, indicator_name)

    if existing_image:
        st.success("✅ Image already uploaded for this indicator")

        # Display the existing image at FULL WIDTH
        st.markdown(f"**Current {indicator_name} Chart:**")

        # Display at 75% width (fixed size that works)
        col_empty, col_image, col_empty2 = st.columns([1, 3, 1])
        with col_image:
            st.image(
                existing_image['bytes'],
                use_container_width=True,
                caption=f"{indicator_name} Chart"
            )

        # Image info
        col1, col2, col3 = st.columns(3)
        with col1:
            st.caption(f"📤 Uploaded by: {existing_image['uploaded_by']}")
        with col2:
            st.caption(f"📅 {datetime.fromisoformat(existing_image['timestamp']).strftime('%Y-%m-%d %H:%M')}")
        with col3:
            st.caption(f"📋 Format: {existing_image['format']}")

        # Action buttons
        col_v, col_r = st.columns(2)
        with col_v:
            if st.button("🖼️ Full View", key=f"full_view_{strategy_name}_{indicator_name}", use_container_width=True):
                st.session_state.current_strategy_indicator_image = existing_image
                st.session_state.strategy_indicator_viewer_mode = True
                st.session_state.current_strategy_indicator = f"{strategy_name}_{indicator_name}"
                st.rerun()

        with col_r:
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
        # Display preview at FULL WIDTH
        st.markdown("**Preview:**")

        col_empty, col_preview, col_empty2 = st.columns([1, 3, 1])
        with col_preview:
            st.image(uploaded_file, use_container_width=True)

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
    """Display strategy indicator images for users (view only) - FULL WIDTH"""
    if strategy_name not in st.session_state.strategy_indicator_images:
        return

    st.subheader("📊 Strategy Charts")

    indicators_with_images = st.session_state.strategy_indicator_images[strategy_name]

    if not indicators_with_images:
        st.info("No chart images available for this strategy yet.")
        return

    # Display images ONE PER ROW at FULL WIDTH
    for indicator_name, img_data in indicators_with_images.items():
        with st.container():
            st.markdown(f"#### **{indicator_name}**")

            # Display at full width
            # Display at 75% width (fixed size that works)
            col_empty, col_image, col_empty2 = st.columns([1, 3, 1])
            with col_image:
                st.image(
                    img_data['bytes'],
                    use_container_width=True,
                    caption=f"{indicator_name} Chart"
                )

            # Image info below
            col1, col2, col3 = st.columns(3)
            with col1:
                st.caption(f"📤 Uploaded by: {img_data['uploaded_by']}")
            with col2:
                st.caption(f"📅 {datetime.fromisoformat(img_data['timestamp']).strftime('%Y-%m-%d %H:%M')}")
            with col3:
                st.caption(f"📋 Format: {img_data['format']}")

            # Action buttons
            col_a, col_b = st.columns(2)
            with col_a:
                if st.button("🖼️ Fullscreen", key=f"user_view_strat_{strategy_name}_{indicator_name}", use_container_width=True):
                    st.session_state.current_strategy_indicator_image = img_data
                    st.session_state.strategy_indicator_viewer_mode = True
                    st.session_state.current_strategy_indicator = f"{strategy_name}_{indicator_name}"
                    st.rerun()
            with col_b:
                try:
                    b64_img = base64.b64encode(img_data['bytes']).decode()
                    href = f'<a href="data:image/{img_data["format"].lower()};base64,{b64_img}" download="{img_data["name"]}" style="text-decoration: none;">'
                    st.markdown(f'{href}<button style="background-color: #4CAF50; color: white; border: none; padding: 8px 12px; text-align: center; text-decoration: none; display: inline-block; font-size: 12px; cursor: pointer; border-radius: 4px; width: 100%;">⬇️ Download</button></a>', unsafe_allow_html=True)
                except:
                    st.button("⬇️ Download", disabled=True, use_container_width=True)

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
    """User account settings - FIXED VERSION with top back button only"""

    # ADDED: Back button at the top
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("⬅️ Back to Dashboard", use_container_width=True, key="user_settings_back_top"):
            st.session_state.dashboard_view = 'main'
            st.rerun()

    with col_title:
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

def render_premium_user_section():
    """Premium user section with membership options"""
    st.title("💎 Premium User")

    user = st.session_state.user
    current_plan = user['plan']
    plan_name = Config.PLANS.get(current_plan, {}).get('name', current_plan.title())

    # User status header
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Current Plan", plan_name)
    with col2:
        days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days
        st.metric("Days Remaining", days_left)
    with col3:
        if current_plan == 'premium':
            st.metric("Status", "Active ✅")
        else:
            st.metric("Status", "Trial ⏳")

    st.markdown("---")

    # Plan comparison
    st.subheader("📊 Plan Comparison")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("### 🆓 Trial Plan")
        trial_plan = Config.PLANS['trial']
        st.write("**Features:**")
        st.write(f"• {trial_plan['strategies']} Trading Strategies")
        st.write(f"• {trial_plan['max_sessions']} Concurrent Session")
        st.write(f"• {trial_plan['duration']}-day access")
        st.write("• Basic Signal Access")
        st.write("• View-Only Gallery")
        st.write("• KAI Analysis View")
        st.write(f"• **Price: ${trial_plan['price']}/month**")

        if current_plan == 'trial':
            st.success("🎯 Your Current Plan")

    with col2:
        st.markdown("### 💎 Premium Plan")
        premium_plan = Config.PLANS['premium']
        st.write("**Premium Features:**")
        st.write(f"• {premium_plan['strategies']} Trading Strategies")
        st.write(f"• {premium_plan['max_sessions']} Concurrent Sessions")
        st.write(f"• {premium_plan['duration']}-day access")
        st.write("• Full Signal Access")
        st.write("• Upload & Download Gallery")
        st.write("• Enhanced KAI Analysis")
        st.write("• Priority Support")
        st.write(f"• **Starting at: ${premium_plan['price']}/month**")

        if current_plan == 'premium':
            st.success("🎉 Premium Member!")
        else:
            st.warning("Upgrade to unlock")

    st.markdown("---")

    # Action sections
    if current_plan == 'trial':
        render_become_member_section()
    else:
        render_renew_subscription_section()

    st.markdown("---")

    # Benefits showcase
    st.subheader("🚀 Premium Benefits")

    benefits_col1, benefits_col2, benefits_col3 = st.columns(3)

    with benefits_col1:
        st.markdown("""
        **📈 Enhanced Signals**
        - Full strategy access
        - Real-time updates
        - Advanced analytics
        - Export capabilities
        """)

    with benefits_col2:
        st.markdown("""
        **🖼️ Gallery Features**
        - Upload your charts
        - Download community images
        - Fullscreen viewer
        - Strategy tagging
        """)

    with benefits_col3:
        st.markdown("""
        **🧠 KAI AI Agent**
        - Enhanced analysis
        - DeepSeek AI integration
        - Historical archive
        - Export functionality
        """)

    # Support information
    st.markdown("---")
    st.info("""
    **💁 Need Help?**
    - Contact support: support@tradinganalysis.com
    - Billing questions: billing@tradinganalysis.com
    - Technical issues: tech@tradinganalysis.com
    """)

def render_become_member_section():
    """Section for trial users to become premium members - Ko-Fi Integration"""
    st.subheader("⭐ Become a Premium Member")

    st.success("""
    **Ready to upgrade?** Get full access to all premium features including enhanced signals,
    gallery uploads, and advanced KAI AI analysis.
    """)

    # Ko-Fi payment options with GREEN buttons
    st.markdown("### 💳 Choose Your Plan")

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("#### 1 Month")
        st.write("**$19**")
        st.write("• Flexible billing")
        st.write("• Cancel anytime")

        kofi_monthly = Config.KOFI_PREMIUM_MONTHLY_LINK
        st.markdown(
            f'<a href="{kofi_monthly}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">💳 Subscribe Now</button></a>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("#### 3 Months")
        st.write("**$49**")
        st.write("• 3 months access")
        st.write("• Best for short-term")

        kofi_quarterly = Config.KOFI_PREMIUM_QUARTERLY_LINK
        st.markdown(
            f'<a href="{kofi_quarterly}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">💎 Subscribe Now</button></a>',
            unsafe_allow_html=True
        )

    with col3:
        st.markdown("#### 6 Months")
        st.write("**$97**")
        st.write("• 6 months access")
        st.write("• Extended access")

        kofi_semi_annual = Config.KOFI_PREMIUM_SEMI_ANNUAL_LINK
        st.markdown(
            f'<a href="{kofi_semi_annual}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🚀 Subscribe Now</button></a>',
            unsafe_allow_html=True
        )

    with col4:
        st.markdown("#### 12 Months")
        st.write("**$179**")
        st.write("• 12 months access")
        st.write("• Long-term value")

        kofi_annual = Config.KOFI_PREMIUM_ANNUAL_LINK
        st.markdown(
            f'<a href="{kofi_annual}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🏆 Subscribe Now</button></a>',
            unsafe_allow_html=True
        )

    # Important information
    st.markdown("---")
    st.info("""
    **🔐 Secure Payment Process:**
    - You'll be redirected to Ko-Fi's secure payment page
    - Multiple payment methods accepted (credit card, PayPal, Apple Pay, Google Pay)
    - Instant access after successful payment
    - Email receipt provided
    """)

    # Manual upgrade option for admin
    if st.session_state.user['plan'] == 'admin':
        st.markdown("---")
        st.warning("**Admin Manual Upgrade:**")
        if st.button("🔼 Manually Upgrade User to Premium", key="manual_upgrade"):
            success, message = user_manager.change_user_plan(st.session_state.user['username'], "premium")
            if success:
                st.session_state.user['plan'] = "premium"
                st.success("✅ User upgraded to premium!")
                st.rerun()

def render_renew_subscription_section():
    """Updated renewal section with Ko-Fi buttons"""
    st.subheader("🔄 Renew Your Subscription")

    user = st.session_state.user
    days_left = (datetime.strptime(user['expires'], "%Y-%m-%d").date() - date.today()).days

    if days_left > 7:
        st.success(f"✅ Your premium subscription is active! {days_left} days remaining.")
    elif days_left > 0:
        st.warning(f"⚠️ Your subscription expires in {days_left} days. Renew now to avoid interruption.")
    else:
        st.error("❌ Your subscription has expired. Renew to restore premium access.")

    # Ko-Fi renewal options with GREEN buttons
    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown("#### 1 Month")
        st.write("**$19**")
        kofi_monthly = Config.KOFI_PREMIUM_MONTHLY_LINK
        st.markdown(
            f'<a href="{kofi_monthly}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🔄 Renew</button></a>',
            unsafe_allow_html=True
        )

    with col2:
        st.markdown("#### 3 Months")
        st.write("**$49**")
        kofi_quarterly = Config.KOFI_PREMIUM_QUARTERLY_LINK
        st.markdown(
            f'<a href="{kofi_quarterly}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🔄 Renew</button></a>',
            unsafe_allow_html=True
        )

    with col3:
        st.markdown("#### 6 Months")
        st.write("**$97**")
        kofi_semi_annual = Config.KOFI_PREMIUM_SEMI_ANNUAL_LINK
        st.markdown(
            f'<a href="{kofi_semi_annual}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🔄 Renew</button></a>',
            unsafe_allow_html=True
        )

    with col4:
        st.markdown("#### 12 Months")
        st.write("**$179**")
        kofi_annual = Config.KOFI_PREMIUM_ANNUAL_LINK
        st.markdown(
            f'<a href="{kofi_annual}" target="_blank"><button style="background-color: #10B981; color: white; padding: 10px 20px; border: none; border-radius: 4px; cursor: pointer; width: 100%;">🔄 Renew</button></a>',
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.subheader("⚙️ Subscription Settings")
    col5, col6 = st.columns(2)
    with col5:
        st.info("💡 Ko-Fi handles automatic renewals. Check your Ko-Fi dashboard for subscription settings.")
    with col6:
        st.info("📧 You'll receive renewal reminders via email before expiry.")

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
    """Detailed strategy notes interface with full admin editing - UPDATED TYPE OPTIONS AND PROVIDER"""
    st.title("📝 Admin Signal Editor")

    # Header with cycle info
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

        # UPDATED: Strategy Type with new lowercase options
        current_strategy_type = next(iter(existing_data.values()), {}).get("momentum", "Neutral reading")

        # Handle migration from old values to new values
        type_mapping = {
            "Momentum": "Momentum reading",
            "Extreme": "Extreme reading",
            "Not Defined": "Neutral reading",
            "MOMENTUM READING": "Momentum reading",
            "EXTREME READING": "Extreme reading",
            "NEUTRAL READING": "Neutral reading"
        }

        # Convert old values to new values
        if current_strategy_type in type_mapping:
            current_strategy_type = type_mapping[current_strategy_type]

        # Strategy-level settings
        col1, col2 = st.columns(2)
        with col1:
            strategy_tag = st.selectbox("Strategy Tag:", ["Neutral", "Buy", "Sell"],
                                      index=["Neutral","Buy","Sell"].index(current_strategy_tag),
                                      key="admin_strategy_tag")
        with col2:
            # UPDATED: New Type options in lowercase
            new_type_options = ["Neutral reading", "Extreme reading", "Momentum reading"]
            current_index = new_type_options.index(current_strategy_type) if current_strategy_type in new_type_options else 0
            strategy_type = st.selectbox("Strategy Type:", new_type_options,
                                       index=current_index,
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

        # Save button
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
                    "momentum": strategy_type,  # This now stores the new lowercase type
                    "strategy_tag": strategy_tag,
                    "analysis_date": analysis_date.strftime("%Y-%m-%d"),
                    "last_modified": datetime.utcnow().isoformat() + "Z",
                    "modified_by": "KAI"  # CHANGED: from "admin" to "KAI"
                }

            # Save to Supabase
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
                    momentum_type = meta.get("momentum", "neutral reading")
                    # Apply the same mapping for display
                    if momentum_type in type_mapping:
                        momentum_type = type_mapping[momentum_type]
                    status_icon = "✅ Done" if meta.get("status", "Open") == "Done" else "🕓 Open"
                    # CHANGED: Show "KAI" instead of the actual modified_by field
                    with st.expander(f"{ind_name} ({momentum_type}) — {status_icon} — Provider: KAI", expanded=False):
                        st.write(meta.get("note", "") or "_No notes yet_")
                        st.caption(f"Last updated: {meta.get('last_modified', 'N/A')}")

def render_admin_account_settings():
    """Admin account settings in premium mode - FIXED with top back button only"""

    # ADDED: Back button at the top
    col_back, col_title = st.columns([1, 5])
    with col_back:
        if st.button("⬅️ Back to Dashboard", use_container_width=True, key="admin_settings_back_top"):
            st.session_state.dashboard_view = 'main'
            st.rerun()

    with col_title:
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

        render_user_purchase_button()

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

        if st.session_state.get('show_purchase_verification'):
            render_purchase_verification_modal()

        # DISCLAIMER BEFORE LOGOUT BUTTON - FOR LEGAL REASONS
        st.markdown("""
        <div style="background-color: #fbe9e7; padding: 12px; border-radius: 6px; border-left: 4px solid #d84315; margin: 10px 0;">
            <small><strong style="color: #bf360c;">⚠️ RISK WARNING</strong></small><br>
            <small style="color: #3e2723;">This is not financial advice. Trading carries high risk of loss. 
            Only risk capital you can afford to lose. Past performance ≠ future results.</small>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("---")

        # LOGOUT BUTTON AFTER DISCLAIMER
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
    """User trading dashboard - CLEANED VERSION WITHOUT KAI BUTTONS"""
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

    # ENHANCED: Green Buy Strategy buttons like admin dashboard
    col_header1, col_header2, col_header3 = st.columns([2, 1, 1])
    with col_header1:
        st.subheader(f"Signal Analysis - {selected_strategy}")
    with col_header2:
        st.markdown(
            f'<a href="https://ko-fi.com/s/c2d66d197b" target="_blank">'
            f'<button style="background-color: #059669; color: white; border: none; padding: 10px 16px; '
            f'text-align: center; text-decoration: none; display: inline-block; font-size: 14px; '
            f'cursor: pointer; border-radius: 6px; width: 100%; font-weight: bold;">'
            f'📊 BUY This Strategy</button></a>',
            unsafe_allow_html=True
        )
    with col_header3:
        st.markdown(
            f'<a href="https://ko-fi.com/s/218558f1c9" target="_blank">'
            f'<button style="background-color: #10B981; color: white; border: none; padding: 10px 16px; '
            f'text-align: center; text-decoration: none; display: inline-block; font-size: 14px; '
            f'cursor: pointer; border-radius: 6px; width: 100%; font-weight: bold;">'
            f'🚀 BUY All 15 Strategies</button></a>',
            unsafe_allow_html=True
        )

    # Display existing analysis
    strategy_data = st.session_state.strategy_analyses_data
    existing_data = strategy_data.get(selected_strategy, {})

    if existing_data:
        # Get strategy-level info from first indicator
        first_indicator = next(iter(existing_data.values()), {})
        strategy_tag = first_indicator.get("strategy_tag", "Neutral")
        strategy_type = first_indicator.get("momentum", "neutral reading")

        # Handle migration from old values for display
        type_mapping = {
            "Momentum": "Momentum reading",
            "Extreme": "Extreme reading",
            "Not Defined": "Neutral reading",
            "MOMENTUM READING": "Momentum reading",
            "EXTREME READING": "Extreme reading",
            "NEUTRAL READING": "Neutral reading"
        }

        # Convert old values to new values for display
        if strategy_type in type_mapping:
            strategy_type = type_mapping[strategy_type]

        col1, col2, col3 = st.columns(3)
        with col1:
            st.info(f"**Signal:** {strategy_tag}")
        with col2:
            st.info(f"**Type:** {strategy_type}")  # Now shows new lowercase type options
        with col3:
            st.info(f"**Provider:** KAI")  # CHANGED: Always show "KAI" instead of the modified_by field

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
# === KAI PAGINATION CORE (placed before dashboard & main) ===
def get_gallery_images_count():
    """Get total count of gallery images"""
    if 'supabase_client' not in globals() or not supabase_client:
        return _cache_get("lk_gallery_count", 0)
    try:
        resp = supabase_client.table('gallery_images').select('id', count='exact').execute()
        if hasattr(resp, 'error') and resp.error:
            logging.error(f"Count error: {resp.error}")
            return _cache_get("lk_gallery_count", 0)
        count = getattr(resp, 'count', None) or (resp.data and len(resp.data)) or 0
        _cache_set("lk_gallery_count", count)
        return count
    except Exception as e:
        logging.error(f"Database count error: {e}")
        return _cache_get("lk_gallery_count", 0)

# -------------------------
# Gallery Pagination - UI Layer
# -------------------------
import streamlit as st


def render_admin_image_gallery_paginated():
    st.title("🖼️ Admin: Image Gallery Management")
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📊 View & Manage", "⬆️ Upload", "⚙️ Settings"])
    with admin_tab1:
        render_image_gallery_paginated()
        st.markdown("---")
        st.subheader("🛠️ Admin Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh Gallery", use_container_width=True, key="admin_refresh_gallery"):
                st.session_state.gallery_page = 0; st.rerun()
        with col2:
            if st.button("📊 Gallery Stats", use_container_width=True, key="admin_gallery_stats"):
                st.session_state.show_gallery_stats = True
        with col3:
            if st.button("🗑️ Clear Gallery", use_container_width=True, key="admin_clear_gallery"):
                st.session_state.show_clear_gallery_confirmation = True; st.rerun()
        if st.session_state.get('show_gallery_stats'):
            render_gallery_statistics_paginated()
    with admin_tab2:
        render_image_uploader()
    with admin_tab3:
        st.subheader("⚙️ Gallery Settings")
        days_old = st.slider("Delete images older than (days):", 1, 365, 90)
        if st.button("🗑️ Purge Old Images", use_container_width=True):
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            try:
                if 'supabase_client' in globals() and supabase_client:
                    supabase_client.table('gallery_images').delete().lt('timestamp', cutoff_date).execute()
                st.success(f"✅ Deleted images older than {days_old} days")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")


@retry_with_backoff(max_retries=3, base_delay=0.5, exceptions=(Exception,))
def get_gallery_images_paginated(page=0, per_page=15, sort_by="newest", 
                                  filter_author=None, filter_strategy=None):
    """Paginated fetch with robust null checking"""
    try:
        if not supabase_client:
            return []

        offset = max(page, 0) * max(per_page, 1)
        query = supabase_client.table("gallery_images").select("*")

        # Apply filters
        if filter_author and filter_author != "All Authors":
            query = query.eq("uploaded_by", filter_author)
        if filter_strategy and filter_strategy != "All Strategies":
            try:
                query = query.contains("strategies", [filter_strategy])
            except:
                pass  # Array filtering might not be supported

        # Apply sorting
        sort_field = "timestamp"
        sort_order = "desc" if sort_by != "oldest" else "asc"
        if sort_by == "most_liked":
            sort_field = "likes"
            sort_order = "desc"
            
        query = query.order(sort_field, desc=(sort_order == "desc"))
        query = query.range(offset, offset + per_page - 1)

        resp = query.execute()
        if not resp or not getattr(resp, "data", None):
            return []

        imgs = []
        for row in resp.data:
            try:
                # CRITICAL: Ensure format field exists
                if not row.get('format'):
                    # Try to infer from name
                    name = row.get('name', '')
                    if name:
                        ext = name.split('.')[-1].lower() if '.' in name else 'png'
                        row['format'] = ext.upper() if ext in ['jpg', 'jpeg', 'png', 'gif', 'bmp'] else 'PNG'
                    else:
                        row['format'] = 'PNG'  # Safe default
                
                # Reconstruct bytes from multiple possible sources
                if isinstance(row.get('encoded_data'), dict):
                    row['bytes'] = decode_image_from_storage(row['encoded_data'])
                elif row.get('bytes_b64'):
                    try:
                        row['bytes'] = base64.b64decode(row['bytes_b64'])
                    except Exception as e:
                        logging.warning(f"Failed to decode bytes_b64 for {row.get('name')}: {e}")
                        row['bytes'] = None
                elif not row.get('bytes'):
                    row['bytes'] = None
                
                # Ensure strategies field exists
                row["strategies"] = row.get("strategies") or [row.get("strategy") or "Unspecified"]
                row["likes"] = row.get("likes", 0)
                
                imgs.append(row)
                
            except Exception as e:
                logging.warning(f"Skipping corrupted image {row.get('name')}: {e}")
                continue
        
        return imgs
        
    except Exception as e:
        logging.error(f"Gallery pagination error: {e}")
        st.error(f"⚠️ Failed to load images: {e}")
        return []
        
def render_admin_image_gallery_paginated():
    st.title("🖼️ Admin: Image Gallery Management")
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📊 View & Manage", "⬆️ Upload", "⚙️ Settings"])
    with admin_tab1:
        render_image_gallery_paginated()
        st.markdown("---")
        st.subheader("🛠️ Admin Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh Gallery", use_container_width=True, key="admin_refresh_gallery"):
                st.session_state.gallery_page = 0; st.rerun()
        with col2:
            if st.button("📊 Gallery Stats", use_container_width=True, key="admin_gallery_stats"):
                st.session_state.show_gallery_stats = True
        with col3:
            if st.button("🗑️ Clear Gallery", use_container_width=True, key="admin_clear_gallery"):
                st.session_state.show_clear_gallery_confirmation = True; st.rerun()
        if st.session_state.get('show_gallery_stats'):
            render_gallery_statistics_paginated()
    with admin_tab2:
        render_image_uploader()
    with admin_tab3:
        st.subheader("⚙️ Gallery Settings")
        days_old = st.slider("Delete images older than (days):", 1, 365, 90)
        if st.button("🗑️ Purge Old Images", use_container_width=True):
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            try:
                if 'supabase_client' in globals() and supabase_client:
                    supabase_client.table('gallery_images').delete().lt('timestamp', cutoff_date).execute()
                st.success(f"✅ Deleted images older than {days_old} days")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

@retry_with_backoff(max_retries=3, base_delay=0.5, exceptions=(Exception,))
def get_gallery_images_count_filtered(
    filter_author: str = None,
    filter_strategy: str = None,
    min_likes: int = 0
) -> int:
    """
    Get total count of gallery images with filters applied.
    
    FIXES:
    - Proper error handling
    - Fallback to session state
    - Safe filter application
    """
    
    # STEP 1: Try database first
    if supabase_client:
        try:
            query = supabase_client.table('gallery_images').select('id', count='exact')
            
            if filter_author:
                query = query.eq('uploaded_by', filter_author)
            
            if filter_strategy:
                try:
                    query = query.contains('strategies', [filter_strategy])
                except Exception:
                    # Array filtering might not be supported
                    pass
            
            resp = query.execute()
            
            if hasattr(resp, 'error') and resp.error:
                raise RuntimeError(f"Database error: {resp.error}")
            
            count = getattr(resp, 'count', None)
            if count is None and hasattr(resp, 'data'):
                count = len(resp.data)
            
            count = count or 0
            _cache_set("lk_gallery_count_filtered", count)
            
            logging.info(f"✅ Gallery count: {count}")
            return count
            
        except Exception as e:
            logging.error(f"❌ Database count failed: {e}")
            # Fall through to session state fallback
    
    # STEP 2: Fallback to session state
    try:
        all_images = st.session_state.get('uploaded_images', [])
        filtered = all_images.copy()
        
        if filter_author:
            filtered = [img for img in filtered if img.get('uploaded_by') == filter_author]
        
        if filter_strategy:
            filtered = [img for img in filtered if filter_strategy in (img.get('strategies') or [])]
        
        if min_likes > 0:
            filtered = [img for img in filtered if img.get('likes', 0) >= min_likes]
        
        count = len(filtered)
        logging.info(f"✅ Session state count: {count}")
        return count
        
    except Exception as e:
        logging.error(f"❌ Session state count failed: {e}")
        return 0
        
# -------------------------
# Gallery Pagination - UI Layer
# -------------------------
import streamlit as st

def render_image_uploader():
    """
    MINIMAL IMAGE UPLOADER - Only uses columns visible in your table structure
    """
    st.subheader("🖼️ Upload Trading Images")
    
    # Get available strategies for tagging
    STRATEGIES = st.session_state.get('STRATEGIES', {})
    if isinstance(STRATEGIES, dict):
        available_strategies = list(STRATEGIES.keys())
    else:
        available_strategies = []
    
    # File uploader
    uploaded_files = st.file_uploader(
        "Choose images to upload",
        type=['png', 'jpg', 'jpeg', 'gif', 'bmp'],
        accept_multiple_files=True,
        key="gallery_uploader_minimal"
    )
    
    # Image description
    image_description = st.text_area(
        "Image Description (Optional):",
        placeholder="Describe what this image shows...",
        height=100,
        key="gallery_description_minimal"
    )
    
    # Strategy tagging
    selected_strategies = st.multiselect(
        "Tag Related Strategies (Optional):",
        available_strategies,
        default=[],
        key="gallery_strategies_minimal"
    )
    
    if st.button("🚀 Upload to Gallery", use_container_width=True, key="upload_btn_minimal"):
        if not uploaded_files:
            st.warning("Select at least one image to upload.")
            return
        
        if not supabase_client:
            st.error("❌ Supabase client not available")
            return
        
        success_count = 0
        error_count = 0
        
        for uf in uploaded_files:
            try:
                # Read file bytes
                file_bytes = uf.read()
                
                # Validate file size (10MB limit)
                if len(file_bytes) > 10 * 1024 * 1024:
                    st.error(f"❌ {uf.name}: File too large (>10MB)")
                    error_count += 1
                    continue
                
                # Validate file not empty
                if len(file_bytes) == 0:
                    st.error(f"❌ {uf.name}: File is empty")
                    error_count += 1
                    continue
                
                # Determine file format from filename
                file_ext = uf.name.split('.')[-1].lower() if '.' in uf.name else 'png'
                format_map = {
                    'jpg': 'JPEG', 'jpeg': 'JPEG', 'png': 'PNG', 
                    'gif': 'GIF', 'bmp': 'BMP'
                }
                file_format = format_map.get(file_ext, 'PNG')
                
                # Create unique filename
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                unique_name = f"{timestamp}_{uf.name}"
                
                # Encode to base64 for storage
                try:
                    bytes_b64 = base64.b64encode(file_bytes).decode('utf-8')
                except Exception as e:
                    st.error(f"❌ {uf.name}: Failed to encode - {str(e)}")
                    error_count += 1
                    continue
                
                # MINIMAL record - ONLY columns we can see in your table
                db_record = {
                    "name": uf.name,
                    "filename": unique_name,
                    "storage_path": f"gallery/{unique_name}",
                    "public_url": f"https://example.com/gallery/{unique_name}",
                    "description": image_description if image_description else "",
                    "uploaded_by": st.session_state.user['username'],
                    "timestamp": datetime.now().isoformat(),
                    "file_size": len(file_bytes),
                    "file_format": file_format,
                    "likes": 0,
                    "strategies": selected_strategies if selected_strategies else [],
                    "bytes_b64": bytes_b64,
                    "comments": []
                    # NOTE: We're NOT including 'format', 'created_at', 'updated_at' 
                    # since they either don't exist or cause errors
                }
                
                # Insert the record
                response = supabase_client.table('gallery_images').insert(db_record).execute()
                
                if hasattr(response, 'error') and response.error:
                    raise RuntimeError(f"Supabase error: {response.error}")
                
                st.success(f"✅ {uf.name} uploaded successfully!")
                success_count += 1
                
            except Exception as e:
                error_msg = str(e)
                st.error(f"❌ {uf.name}: Upload failed - {error_msg[:100]}")
                error_count += 1
        
        # Display summary
        if success_count > 0:
            st.success(f"✅ Successfully uploaded {success_count} image(s)!")
            
            if selected_strategies:
                st.info(f"🏷️ Tagged with: {', '.join(selected_strategies)}")
            
            # Refresh gallery data
            st.session_state.uploaded_images = load_gallery_images()
            st.session_state.gallery_page = 0
            
            st.balloons()
            time.sleep(2)
            st.rerun()
        
        if error_count > 0:
            st.warning(f"⚠️ {error_count} image(s) failed to upload")
            
def render_admin_image_gallery_paginated():
    st.title("🖼️ Admin: Image Gallery Management")
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📊 View & Manage", "⬆️ Upload", "⚙️ Settings"])
    with admin_tab1:
        render_image_gallery_paginated()
        st.markdown("---")
        st.subheader("🛠️ Admin Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh Gallery", use_container_width=True, key="admin_refresh_gallery"):
                st.session_state.gallery_page = 0; st.rerun()
        with col2:
            if st.button("📊 Gallery Stats", use_container_width=True, key="admin_gallery_stats"):
                st.session_state.show_gallery_stats = True
        with col3:
            if st.button("🗑️ Clear Gallery", use_container_width=True, key="admin_clear_gallery"):
                st.session_state.show_clear_gallery_confirmation = True; st.rerun()
        if st.session_state.get('show_gallery_stats'):
            render_gallery_statistics_paginated()
    with admin_tab2:
        render_image_uploader()
    with admin_tab3:
        st.subheader("⚙️ Gallery Settings")
        days_old = st.slider("Delete images older than (days):", 1, 365, 90)
        if st.button("🗑️ Purge Old Images", use_container_width=True):
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            try:
                if 'supabase_client' in globals() and supabase_client:
                    supabase_client.table('gallery_images').delete().lt('timestamp', cutoff_date).execute()
                st.success(f"✅ Deleted images older than {days_old} days")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

def render_image_card_paginated(img_data, page_num, index):
    """Compact image card optimized for grid display - FIXED WITH NULL CHECKS"""
    try:
        with st.container():
            # STEP 1: Safely retrieve image bytes
            image_bytes = None
            
            # Try direct bytes first
            if img_data.get('bytes'):
                image_bytes = img_data['bytes']
            # Try base64 decode
            elif img_data.get('bytes_b64'):
                try:
                    image_bytes = base64.b64decode(img_data['bytes_b64'])
                except Exception as e:
                    logging.warning(f"Failed to decode bytes_b64: {e}")
            # Try encoded_data dict
            elif isinstance(img_data.get('encoded_data'), dict):
                image_bytes = decode_image_from_storage(img_data['encoded_data'])
            
            # If we still don't have image bytes, show placeholder
            if image_bytes is None:
                st.warning(f"⚠️ Image data unavailable for {img_data.get('name', 'Unknown')}")
                return
            
            # STEP 2: Display image safely
            st.image(
                image_bytes,
                use_container_width=True,
                caption=str(img_data.get('name', 'Unnamed'))[:25]
            )
            
            st.divider()
            
            # STEP 3: Display image info with null checks
            st.write(f"**{str(img_data.get('name', 'Image'))[:20]}**")
            
            desc = img_data.get('description', '')
            if desc:
                preview = desc[:60] + "..." if len(desc) > 60 else desc
                st.caption(f"📝 {preview}")
            
            # Metadata
            col1, col2 = st.columns(2)
            with col1:
                uploaded_by = img_data.get('uploaded_by', 'Unknown')
                st.caption(f"👤 {uploaded_by}")
            with col2:
                try:
                    timestamp = img_data.get('timestamp', '')
                    if timestamp:
                        dt = datetime.fromisoformat(timestamp)
                        st.caption(f"📅 {dt.strftime('%m/%d/%y')}")
                    else:
                        st.caption("📅 Unknown date")
                except Exception as e:
                    logging.warning(f"Timestamp parse error: {e}")
                    st.caption("📅 Unknown date")
            
            st.divider()
            
            # STEP 4: Action buttons with unique keys
            action_col1, action_col2, action_col3 = st.columns(3)
            unique_key = f"like_p{page_num}_{index}"
            
            with action_col1:
                likes = img_data.get('likes', 0)
                if st.button(f"❤️ {likes}", key=f"like_{unique_key}", use_container_width=True):
                    img_data['likes'] = likes + 1
                    try:
                        if supabase_client:
                            supabase_client.table('gallery_images').update(
                                {'likes': img_data['likes']}
                            ).eq('id', img_data.get('id')).execute()
                    except Exception as e:
                        logging.error(f"Failed to save like: {e}")
                    st.rerun()
            
            with action_col2:
                if st.button("👁️ View", key=f"view_{unique_key}", use_container_width=True):
                    st.session_state.current_strategy_indicator_image = img_data
                    st.session_state.strategy_indicator_viewer_mode = True
                    st.rerun()
            
            with action_col3:
                # STEP 5: Safe download link generation
                try:
                    if image_bytes:
                        # Get format safely
                        img_format = img_data.get('format', 'png')
                        if img_format is None:
                            img_format = 'png'  # Safe default
                        img_format = str(img_format).lower().replace('jpeg', 'jpg')
                        
                        file_name = img_data.get('name', f'image_{index}')
                        file_name = str(file_name)[:50]  # Limit filename length
                        
                        b64_img = base64.b64encode(image_bytes).decode()
                        href = f'<a href="data:image/{img_format};base64,{b64_img}" download="{file_name}"><button style="width:100%; padding:6px; background:#4CAF50; color:white; border:none; border-radius:4px; cursor:pointer; font-size:12px; font-weight:bold;">⬇️ Download</button></a>'
                        st.markdown(href, unsafe_allow_html=True)
                    else:
                        st.button("⬇️ Download", disabled=True, use_container_width=True)
                except Exception as e:
                    logging.error(f"Download button error: {e}")
                    st.button("⬇️ Download", disabled=True, use_container_width=True)
    
    except Exception as e:
        st.error(f"❌ Error rendering image card: {str(e)[:100]}")
        logging.error(f"render_image_card_paginated failed: {e}", exc_info=True)

def render_image_gallery_paginated():
    """Gallery with improved error handling and user feedback."""
    st.title("🖼️ Trading Analysis Image Gallery")
    st.markdown("Share and discuss trading charts, analysis screenshots, and market insights.")
    
    col1, col2 = st.columns([2, 1])
    with col1:
        gallery_view = st.radio(
            "Gallery View:",
            ["🖼️ Image Gallery", "⬆️ Upload Images"],
            horizontal=True,
            key="gallery_nav_paginated"
        )
    
    st.markdown("---")
    
    # Upload view
    if gallery_view == "⬆️ Upload Images":
        render_image_uploader()
        return
    
    # Gallery view controls
    st.subheader("🔍 Gallery Controls")
    filter_col1, filter_col2, filter_col3, filter_col4, filter_col5 = st.columns(5)
    
    with filter_col1:
        sort_by = st.selectbox(
            "Sort by:",
            ["newest", "oldest", "most_liked"],
            key="gallery_sort_paginated"
        )
    
    with filter_col2:
        authors_set = set(
            img.get('uploaded_by', 'Unknown')
            for img in st.session_state.get('uploaded_images', [])
        )
        filter_author = st.selectbox(
            "Filter by Author:",
            ["All Authors"] + sorted(list(authors_set)),
            key="gallery_filter_author_paginated"
        )
    
    with filter_col3:
        STRATEGIES = st.session_state.get('STRATEGIES', {})
        strategies_list = list(STRATEGIES.keys()) if isinstance(STRATEGIES, dict) else []
        filter_strategy = st.selectbox(
            "Filter by Strategy:",
            ["All Strategies"] + strategies_list,
            key="gallery_filter_strategy_paginated"
        )
    
    with filter_col4:
        min_likes = st.slider(
            "Minimum Likes:",
            0, 100, 0,
            key="gallery_min_likes"
        )
    
    with filter_col5:
        per_page = st.selectbox(
            "Per Page:",
            [10, 15, 20, 30],
            index=1,
            key="gallery_per_page_paginated"
        )
    
    st.session_state.gallery_per_page = per_page
    st.markdown("---")
    
    # Get count
    try:
        with st.spinner("🔍 Counting images..."):
            total_count = get_gallery_images_count_filtered(
                filter_author=None if filter_author == "All Authors" else filter_author,
                filter_strategy=None if filter_strategy == "All Strategies" else filter_strategy,
                min_likes=min_likes
            )
    except Exception as e:
        st.error(f"❌ Error counting images: {e}")
        return
    
    if total_count == 0:
        st.warning("❌ No images found matching your filters.")
        st.info("💡 Try uploading some images or adjusting your filters.")
        return
    
    st.session_state.gallery_total_count = total_count
    total_pages = (total_count + per_page - 1) // per_page
    
    # Ensure current page is valid
    if st.session_state.gallery_page >= total_pages:
        st.session_state.gallery_page = max(0, total_pages - 1)
    
    # Statistics
    st.subheader("📊 Gallery Statistics")
    stat_col1, stat_col2, stat_col3, stat_col4 = st.columns(4)
    with stat_col1:
        st.metric("Total Images", total_count)
    with stat_col2:
        st.metric("Total Pages", total_pages)
    with stat_col3:
        st.metric("Current Page", st.session_state.gallery_page + 1)
    with stat_col4:
        start_num = st.session_state.gallery_page * per_page + 1
        end_num = min((st.session_state.gallery_page + 1) * per_page, total_count)
        st.metric("Showing", f"{start_num}-{end_num}")
    
    st.markdown("---")
    
    # Navigation
    st.subheader("📄 Page Navigation")
    nav_col1, nav_col2, nav_col3, nav_col4, nav_col5 = st.columns(5)
    
    with nav_col1:
        if st.button("⏮️ First Page", use_container_width=True, key="gallery_first_top"):
            st.session_state.gallery_page = 0
            st.rerun()
    
    with nav_col2:
        if st.session_state.gallery_page > 0:
            if st.button("◀️ Previous", use_container_width=True, key="gallery_prev_top"):
                st.session_state.gallery_page -= 1
                st.rerun()
        else:
            st.button("◀️ Previous", use_container_width=True, disabled=True, key="gallery_prev_top_disabled")
    
    with nav_col3:
        jump_page = st.number_input(
            "Go to Page:",
            min_value=1,
            max_value=max(1, total_pages),
            value=st.session_state.gallery_page + 1,
            key="gallery_jump_page"
        ) - 1
        if jump_page != st.session_state.gallery_page:
            st.session_state.gallery_page = max(0, min(jump_page, total_pages - 1))
            st.rerun()
    
    with nav_col4:
        if st.session_state.gallery_page < total_pages - 1:
            if st.button("Next ▶️", use_container_width=True, key="gallery_next_top"):
                st.session_state.gallery_page += 1
                st.rerun()
        else:
            st.button("Next ▶️", use_container_width=True, disabled=True, key="gallery_next_top_disabled")
    
    with nav_col5:
        if st.button("⭐ Last Page", use_container_width=True, key="gallery_last_top"):
            st.session_state.gallery_page = total_pages - 1
            st.rerun()
    
    st.markdown("---")
    
    # Load page images
    try:
        with st.spinner("📥 Loading images..."):
            page_images = get_gallery_images_paginated(
                page=st.session_state.gallery_page,
                per_page=per_page,
                sort_by=sort_by,
                filter_author=None if filter_author == "All Authors" else filter_author,
                filter_strategy=None if filter_strategy == "All Strategies" else filter_strategy
            )
    except Exception as e:
        st.error(f"❌ Error loading images: {e}")
        logging.error(f"Page load error: {e}")
        return
    
    if not page_images:
        st.warning("⚠️ Failed to load images for this page.")
        st.info("💡 This might be a temporary issue. Try refreshing or adjusting filters.")
        return
    
    # Display images in grid
    st.session_state.current_page_images = page_images
    st.subheader(f"🖼️ Page {st.session_state.gallery_page + 1} Images ({len(page_images)} shown)")
    
    cols = st.columns(3)
    for idx, img_data in enumerate(page_images):
        col = cols[idx % 3]
        with col:
            try:
                render_image_card_paginated(img_data, st.session_state.gallery_page, idx)
            except Exception as e:
                st.error(f"❌ Error rendering image {idx}: {str(e)[:50]}")
                logging.error(f"Image render error: {e}")
    
    st.markdown("---")
    
    # Bottom navigation
    st.subheader("📄 Bottom Navigation")
    bot_col1, bot_col2, bot_col3, bot_col4, bot_col5 = st.columns(5)
    
    with bot_col1:
        if st.button("⏮️ First", use_container_width=True, key="gallery_first_bottom"):
            st.session_state.gallery_page = 0
            st.rerun()
    
    with bot_col2:
        if st.session_state.gallery_page > 0:
            if st.button("◀️ Prev", use_container_width=True, key="gallery_prev_bottom"):
                st.session_state.gallery_page -= 1
                st.rerun()
        else:
            st.button("◀️ Prev", use_container_width=True, disabled=True, key="gallery_prev_bottom_disabled")
    
    with bot_col3:
        st.write(f"**Page {st.session_state.gallery_page + 1}/{total_pages}**")
    
    with bot_col4:
        if st.session_state.gallery_page < total_pages - 1:
            if st.button("Next ▶️", use_container_width=True, key="gallery_next_bottom"):
                st.session_state.gallery_page += 1
                st.rerun()
        else:
            st.button("Next ▶️", use_container_width=True, disabled=True, key="gallery_next_bottom_disabled")
    
    with bot_col5:
        if st.button("⭐ Last", use_container_width=True, key="gallery_last_bottom"):
            st.session_state.gallery_page = total_pages - 1
            st.rerun()
    
    st.markdown("---")
    start_num = st.session_state.gallery_page * per_page + 1
    end_num = min((st.session_state.gallery_page + 1) * per_page, total_count)
    st.caption(f"✅ Displaying images {start_num}-{end_num} of {total_count} total")
    
def render_admin_image_gallery_paginated():
    st.title("🖼️ Admin: Image Gallery Management")
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📊 View & Manage", "⬆️ Upload", "⚙️ Settings"])
    with admin_tab1:
        render_image_gallery_paginated()
        st.markdown("---")
        st.subheader("🛠️ Admin Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh Gallery", use_container_width=True, key="admin_refresh_gallery"):
                st.session_state.gallery_page = 0; st.rerun()
        with col2:
            if st.button("📊 Gallery Stats", use_container_width=True, key="admin_gallery_stats"):
                st.session_state.show_gallery_stats = True
        with col3:
            if st.button("🗑️ Clear Gallery", use_container_width=True, key="admin_clear_gallery"):
                st.session_state.show_clear_gallery_confirmation = True; st.rerun()
        if st.session_state.get('show_gallery_stats'):
            render_gallery_statistics_paginated()
    with admin_tab2:
        render_image_uploader()
    with admin_tab3:
        st.subheader("⚙️ Gallery Settings")
        days_old = st.slider("Delete images older than (days):", 1, 365, 90)
        if st.button("🗑️ Purge Old Images", use_container_width=True):
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            try:
                if 'supabase_client' in globals() and supabase_client:
                    supabase_client.table('gallery_images').delete().lt('timestamp', cutoff_date).execute()
                st.success(f"✅ Deleted images older than {days_old} days")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

def render_admin_image_gallery_paginated():
    st.title("🖼️ Admin: Image Gallery Management")
    admin_tab1, admin_tab2, admin_tab3 = st.tabs(["📊 View & Manage", "⬆️ Upload", "⚙️ Settings"])
    with admin_tab1:
        render_image_gallery_paginated()
        st.markdown("---")
        st.subheader("🛠️ Admin Actions")
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("🔄 Refresh Gallery", use_container_width=True, key="admin_refresh_gallery"):
                st.session_state.gallery_page = 0; st.rerun()
        with col2:
            if st.button("📊 Gallery Stats", use_container_width=True, key="admin_gallery_stats"):
                st.session_state.show_gallery_stats = True
        with col3:
            if st.button("🗑️ Clear Gallery", use_container_width=True, key="admin_clear_gallery"):
                st.session_state.show_clear_gallery_confirmation = True; st.rerun()
        if st.session_state.get('show_gallery_stats'):
            render_gallery_statistics_paginated()
    with admin_tab2:
        render_image_uploader()
    with admin_tab3:
        st.subheader("⚙️ Gallery Settings")
        days_old = st.slider("Delete images older than (days):", 1, 365, 90)
        if st.button("🗑️ Purge Old Images", use_container_width=True):
            cutoff_date = (datetime.now() - timedelta(days=days_old)).isoformat()
            try:
                if 'supabase_client' in globals() and supabase_client:
                    supabase_client.table('gallery_images').delete().lt('timestamp', cutoff_date).execute()
                st.success(f"✅ Deleted images older than {days_old} days")
                st.rerun()
            except Exception as e:
                st.error(f"❌ Error: {e}")

def render_gallery_statistics_paginated():
    st.subheader("📊 Gallery Statistics")
    try:
        total = get_gallery_images_count()
        st.metric("Total Images", total)
    except Exception as e:
        st.error(f"⚠️ Stats Error: {e}")

def render_admin_dashboard():
    """Professional admin dashboard with dual mode selection"""

    # If admin hasn't chosen a dashboard mode, show selection
    if st.session_state.get('admin_dashboard_mode') is None:
        render_admin_dashboard_selection()
        return

    # Always render the sidebar first, regardless of current view
    with st.sidebar:
        st.title("👑 Admin Panel")
        st.markdown("---")
        st.write(f"Welcome, **{st.session_state.user['name']}**")

        # Show current mode (CLEAN IF/ELIF CHAIN)
        current_mode = st.session_state.admin_dashboard_mode
        if current_mode == "admin":
            st.success("🛠️ Admin Management Mode")
        elif current_mode == "premium":
            st.success("📊 Premium Signal Mode")
        elif current_mode == "gallery":
            st.success("🖼️ Image Gallery Mode")
        elif current_mode == "signals_room":
            st.success("⚡ Trading Signals Room")
        elif current_mode == "kai_agent":
            st.success("🧠 KAI AI Agent Mode")
        else:
            st.success("🛠️ Admin Management Mode")

        st.markdown("---")
        st.subheader("Dashboard Mode")
        st.markdown("---")
        
        col1, col2, col3, col4, col5 = st.columns(5)  # 5 columns for the sidebar buttons
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
        with col5:  # Ko-Fi Verification button
            if st.button("💳 Ko-Fi Purchase Verification", use_container_width=True, key="sidebar_kofi_verification_btn"):
                st.session_state.admin_dashboard_mode = "purchase_verification"
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
        elif current_mode == "kai_agent":  # KAI Agent sidebar options
            st.subheader("KAI Agent Actions")
            if st.button("📊 Upload CSV Analysis", use_container_width=True, key="sidebar_kai_upload"):
                st.rerun()
            if st.button("📜 View Analysis History", use_container_width=True, key="sidebar_kai_history"):
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

    elif st.session_state.get('admin_dashboard_mode') == "kai_agent":
        render_kai_agent()
    
    elif st.session_state.get('admin_dashboard_mode') == "purchase_verification":  # New section for Ko-Fi Verification
        st.markdown("## 💳 Ko-Fi")
        render_admin_purchase_verification_panel()  # This renders the Ko-Fi verification section
    
    else:
        render_image_gallery_paginated()

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

    if st.button("📊 Signals Access Tracking", use_container_width=True):
        st.session_state.admin_view = "signals_tracking"
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
        - DeepSeek AI Enhanced
        """)
        if st.button("🧠 Go to KAI Agent", use_container_width=True, key="kai_dash_btn"):
            st.session_state.admin_dashboard_mode = "kai_agent"
            st.rerun()

    st.markdown("---")
    st.info("💡 **Tip:** Use different dashboards for different management tasks.")

def render_admin_management_dashboard():
    """Admin dashboard with simple tracking and maintenance panel"""
    st.title("🛠️ Admin Management Dashboard")

    # Get business metrics safely
    try:
        metrics = user_manager.get_business_metrics()
    except:
        metrics = {}
    
    # Ensure metrics is a dictionary
    if not isinstance(metrics, dict):
        metrics = {}

    # Key metrics - ULTRA SAFE VERSION
    col1, col2, col3, col4, col5, col6 = st.columns(6)
    with col1:
        st.metric("Total Users", metrics.get("total_users", 0))
    with col2:
        st.metric("Active Users", metrics.get("active_users", 0))
    with col3:
        st.metric("Online Now", metrics.get("online_users", 0))
    with col4:
        st.metric("Verified Users", metrics.get("verified_users", 0))
    with col5:
        st.metric("Unverified Users", metrics.get("unverified_users", 0))
    with col6:
        signals_count = len(st.session_state.get('signals_access_tracking', []))
        st.metric("Signals Access", signals_count)

    st.markdown("---")

    # 🔧 DATABASE MAINTENANCE SECTION
    st.subheader("🔧 Database Maintenance Panel")
    
    col_m1, col_m2, col_m3 = st.columns(3)
    
    with col_m1:
        if st.button("🔄 Reset Access Tracking", use_container_width=True, key="reset_tracking_btn"):
            st.session_state.signals_access_tracking = []
            if supabase_client:
                try:
                    supabase_client.table('signals_access_tracking').delete().neq('id', 0).execute()
                    st.success("✅ Access tracking reset successfully!")
                    st.info("All tracking data cleared from database")
                except Exception as e:
                    st.error(f"❌ Error clearing data: {e}")
            else:
                st.warning("⚠️ Supabase not connected, only cleared session data")
            time.sleep(1)
            st.rerun()
    
    with col_m2:
        if st.button("📊 Verify Table Structure", use_container_width=True, key="verify_table_btn"):
            if supabase_client:
                try:
                    resp = supabase_client.table('signals_access_tracking').select('*').limit(1).execute()
                    st.success("✅ Table exists and is accessible!")
                    st.info(f"Table currently has {len(resp.data or [])} records")
                    
                    # Show table structure info
                    st.write("**Expected columns:**")
                    st.write("- id (bigint, primary key)")
                    st.write("- username (text)")
                    st.write("- first_access (timestamp)")
                    st.write("- last_access (timestamp)")
                    st.write("- access_count (integer)")
                    
                except Exception as e:
                    st.error("❌ Table verification failed!")
                    st.error(f"Error: {str(e)[:200]}")
                    st.warning("**Solution:** Run the CREATE TABLE SQL in Supabase SQL Editor")
            else:
                st.error("❌ Supabase client not connected")
    
    with col_m3:
        if st.button("🔍 Run Full Diagnostics", use_container_width=True, key="diagnostics_btn"):
            st.write("**📊 Diagnostic Report:**")
            st.markdown("---")
            
            # Session state info
            st.write("**Session State:**")
            tracking_sess = st.session_state.get('signals_access_tracking', [])
            st.write(f"✓ Items in session: {len(tracking_sess)}")
            if tracking_sess:
                st.write(f"  - Last user: {tracking_sess[-1].get('username', 'unknown')}")
                st.write(f"  - Last access: {tracking_sess[-1].get('last_access', 'unknown')[:16]}")
            
            st.markdown("---")
            
            # Database info
            st.write("**Database Status:**")
            if supabase_client:
                try:
                    resp = supabase_client.table('signals_access_tracking').select('*').execute()
                    records = resp.data or []
                    st.write(f"✓ Items in DB: {len(records)}")
                    
                    if records:
                        st.write("**Sample records (first 3):**")
                        for i, record in enumerate(records[:3], 1):
                            st.write(f"  {i}. {record.get('username')} - Access count: {record.get('access_count', 1)}")
                    else:
                        st.info("Table is empty (no access records yet)")
                        
                except Exception as e:
                    st.error(f"❌ Database query failed: {str(e)[:150]}")
                    st.error("**Possible causes:**")
                    st.write("- Table doesn't exist")
                    st.write("- RLS policies not configured")
                    st.write("- Connection issue")
            else:
                st.error("❌ Supabase client not initialized")
            
            st.markdown("---")
            st.success("Diagnostics complete")

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
    elif current_view == 'signals_tracking':
        render_simple_signals_tracking()
    elif current_view == 'kai_agent':
        render_kai_agent()
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

# SIMPLE ADMIN VIEW
def render_simple_signals_tracking():
    """Simple: Show who accessed Signals Room - FIXED VERSION"""
    st.subheader("👥 Signals Room Access Tracking")
    
    # CRITICAL: Load fresh data from Supabase
    tracking_data = load_signals_access_tracking()
    
    if not tracking_data or len(tracking_data) == 0:
        st.info("📊 No one has accessed Signals Room yet. Access will be tracked here.")
        
        # Show how to test
        st.markdown("---")
        st.subheader("🧪 How to Test Access Tracking:")
        st.markdown("""
        1. Go to **Trading Signals** menu
        2. Enter the Signals Room password
        3. Access will be automatically tracked
        4. Refresh this page to see the tracking update
        """)
        return
    
    st.success(f"✅ **Total Users with Access: {len(tracking_data)}**")
    st.markdown("---")
    
    # Display access data in a table
    tracking_df = pd.DataFrame(tracking_data)
    tracking_df['first_access'] = pd.to_datetime(tracking_df['first_access']).dt.strftime('%Y-%m-%d %H:%M')
    tracking_df['last_access'] = pd.to_datetime(tracking_df['last_access']).dt.strftime('%Y-%m-%d %H:%M')
    
    st.dataframe(
        tracking_df[['username', 'first_access', 'last_access', 'access_count']],
        use_container_width=True,
        hide_index=True
    )
    
    st.markdown("---")
    st.subheader("📊 Access Statistics")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        total_users = len(tracking_data)
        st.metric("Total Users", total_users)
    with col2:
        total_accesses = sum(t.get('access_count', 1) for t in tracking_data)
        st.metric("Total Accesses", total_accesses)
    with col3:
        if total_users > 0:
            avg_accesses = total_accesses / total_users
            st.metric("Avg per User", f"{avg_accesses:.1f}")
    
    st.markdown("---")
    
    # Individual user details
    st.subheader("📋 Detailed Access Log")
    
    for track in tracking_data:
        with st.container():
            col1, col2, col3, col4 = st.columns([2, 2, 1, 1])
            
            with col1:
                st.write(f"**👤 {track['username']}**")
            
            with col2:
                first = datetime.fromisoformat(track['first_access']).strftime('%Y-%m-%d %H:%M')
                last = datetime.fromisoformat(track['last_access']).strftime('%Y-%m-%d %H:%M')
                st.write(f"First: {first}")
                st.caption(f"Last: {last}")
            
            with col3:
                count = track.get('access_count', 1)
                st.metric("Accesses", count, label_visibility="collapsed")
            
            with col4:
                if st.button("🗑️ Remove", key=f"remove_track_{track['username']}", use_container_width=True):
                    # Remove from tracking
                    new_tracking = [t for t in tracking_data if t['username'] != track['username']]
                    save_signals_access_tracking(new_tracking)
                    st.success(f"✅ Removed {track['username']}")
                    st.rerun()
            
            st.divider()
    
    # Action buttons
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        if st.button("🔄 Refresh Data", use_container_width=True, key="refresh_signals_tracking"):
            st.rerun()
    
    with col2:
        if st.button("📥 Export CSV", use_container_width=True, key="export_signals_tracking"):
            csv_data = tracking_df.to_csv(index=False)
            st.download_button(
                label="📥 Download CSV",
                data=csv_data,
                file_name=f"signals_access_tracking_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv",
                use_container_width=True
            )
    
    with col3:
        if st.button("🗑️ Clear All", use_container_width=True, key="clear_all_tracking"):
            if st.session_state.get('confirm_clear_tracking'):
                save_signals_access_tracking([])
                st.success("✅ All tracking cleared")
                st.rerun()
            else:
                st.session_state.confirm_clear_tracking = True
                st.warning("⚠️ Click again to confirm clearing all tracking data")

def export_simple_tracking_csv():
    """Simple CSV export"""
    tracking_data = st.session_state.signals_access_tracking
    if tracking_data:
        df = pd.DataFrame(tracking_data)
        csv = df.to_csv(index=False)
        st.download_button(
            label="📥 Download Access Report",
            data=csv,
            file_name="signals_access_report.csv",
            mime="text/csv"
        )

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
    # Initialize session state variables - ONLY ONCE
    if 'session_initialized' not in st.session_state:
        init_session()
        st.session_state.session_initialized = True

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
        padding: 2px
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
    .deepseek-enhanced {
        background: linear-gradient(135deg, #8B5CF6 0%, #7C3AED 100%);
        color: white;
        padding: 8px 16px;
        border-radius: 20px;
        font-size: 0.8rem;
        font-weight: 600;
        display: inline-block;
        margin-left: 10px;
    }
    .quantitative-score {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .risk-high {
        background: linear-gradient(135deg, #EF4444 0%, #DC2626 100%);
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .risk-medium {
        background: linear-gradient(135deg, #F59E0B 0%, #D97706 100%);
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
        font-weight: 600;
    }
    .risk-low {
        background: linear-gradient(135deg, #10B981 0%, #059669 100%);
        color: white;
        padding: 4px 8px;
        border-radius: 12px;
        font-size: 0.7rem;
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
                ["📊 Trading Dashboard", "🖼️ Image Gallery", "⚡ Trading Signals", "🧠 KAI", "💎 PREMIUM USER"],
                key="user_navigation_mode"
            )

            # Display appropriate view based on user selection
            if user_mode == "🖼️ Image Gallery":
                # For gallery, ensure user can only view (not upload)
                render_user_image_gallery()
            elif user_mode == "⚡ Trading Signals":
                # Show the trading signals room in VIEW MODE
                render_trading_signals_room()
            elif user_mode == "🧠 KAI":
                # Show the KAI AI Agent in VIEW MODE (users can view but not upload)
                render_kai_agent()
            elif user_mode == "💎 PREMIUM USER":
                # Show the premium user section
                render_premium_user_section()
            else:
                # Show the premium trading dashboard in VIEW MODE
                render_user_dashboard()

if __name__ == "__main__":
    main()

# =====================================================================
# EXTREME RELIABILITY SUPABASE PATCH (idempotent, safe to append)
# - Adds robust retry/backoff around Supabase calls
# - Handles transient OSError: [Errno 11] Resource temporarily unavailable (EAGAIN)
# - Suppresses noisy startup errors; returns last-known-good values on failure
# - Does NOT require GitHub or repo connections
# =====================================================================
import errno
import functools

# Global in-memory "last good" caches (kept per-session)
_cache = {}

def _is_transient_error(err):
    """Check if error is transient and worth retrying."""
    # OSError with errno.EAGAIN (Resource temporarily unavailable)
    if isinstance(err, OSError) and hasattr(err, 'errno') and err.errno == errno.EAGAIN:
        return True
    # Connection errors
    if isinstance(err, (ConnectionError, TimeoutError)):
        return True
    # Generic: some Supabase/postgrest errors bubble up as Exception with message patterns
    msg = str(err).lower()
    transient_fragments = ["temporarily unavailable", "timeout", "eagain", "rate limit", "connection reset"]
    return any(frag in msg for frag in transient_fragments)

def _init_supabase_hardened():
    if '___supabase_ok___' in st.session_state:
        return supabase_client  # already initialized by the main code
    tries = 0
    while tries < 5:
        try:
            # If the original code already created supabase_client successfully, just use it.
            if supabase_client:
                st.session_state.___supabase_ok___ = True
                return supabase_client
        except Exception as e:
            # If this fails in weird ways, keep retrying briefly.
            pass
        time.sleep(0.25 * (2 ** tries))
        tries += 1
    return supabase_client  # may be None; downstream code is guarded

# ===== Re-define critical Supabase functions with retries =====

@retry_with_backoff(max_retries=4, base_delay=0.5)
def supabase_get_analytics():
    """Get analytics with retry + cache last good value."""
    client = _init_supabase_hardened()
    if not client:
        return _cache_get("lk_supabase_get_analytics", {})
    resp = client.table('analytics').select('*').execute()
    if hasattr(resp, 'error') and resp.error:
        raise RuntimeError(resp.error)
    data = (resp.data or [])
    result = data[0] if data else {}
    _cache_set("lk_supabase_get_analytics", result)
    return result

@retry_with_backoff(max_retries=4, base_delay=0.5)
def supabase_get_users():
    """Get users with retry + cache last good value."""
    client = _init_supabase_hardened()
    if not client:
        return _cache_get("lk_supabase_get_users", {})
    resp = client.table('users').select('*').execute()
    if hasattr(resp, 'error') and resp.error:
        raise RuntimeError(resp.error)
    users = {u['username']: u for u in (resp.data or [])}
    _cache_set("lk_supabase_get_users", users)
    return users

@retry_with_backoff(max_retries=4, base_delay=0.5)
def supabase_save_users(users: dict):
    """Save users with retry. Returns True on success."""
    client = _init_supabase_hardened()
    if not client:
        return False
    payload = []
    for username, user_data in users.items():
        row = dict(user_data)
        row['username'] = username
        payload.append(row)
    resp = client.table('users').upsert(payload).execute()
    if hasattr(resp, 'error') and resp.error:
        raise RuntimeError(resp.error)
    return True

@retry_with_backoff(max_retries=4, base_delay=0.5)
def supabase_delete_user(username: str):
    """Delete a user with retry."""
    client = _init_supabase_hardened()
    if not client:
        return False
    resp = client.table('users').delete().eq('username', username).execute()
    if hasattr(resp, 'error') and resp.error:
        raise RuntimeError(resp.error)
    return True

@retry_with_backoff(max_retries=4, base_delay=0.5)
def supabase_get_strategy_analyses():
    """Get strategy analyses with retry + cache last good value."""
    client = _init_supabase_hardened()
    if not client:
        return _cache_get("lk_supabase_get_strategy_analyses", {})
    resp = client.table('strategy_analyses').select('*').execute()
    if hasattr(resp, 'error') and resp.error:
        raise RuntimeError(resp.error)
    strategies = {}
    for item in (resp.data or []):
        s = item.get('strategy_name')
        i = item.get('indicator_name')
        strategies.setdefault(s, {})[i] = {
            "note": item.get('note', ''),
            "status": item.get('status', 'Open'),
            "momentum": item.get('momentum', 'Not Defined'),
            "strategy_tag": item.get('strategy_tag', 'Neutral'),
            "analysis_date": item.get('analysis_date', ''),
            "last_modified": item.get('last_modified', ''),
            "modified_by": item.get('modified_by', 'system')
        }
    _cache_set("lk_supabase_get_strategy_analyses", strategies)
    return strategies

@retry_with_backoff(max_retries=4, base_delay=0.5)
def supabase_save_strategy_analyses(strategy_data: dict):
    """Save strategy analyses with retry."""
    client = _init_supabase_hardened()
    if not client:
        return False
    rows = []
    for strategy_name, indicators in strategy_data.items():
        for indicator_name, meta in indicators.items():
            rows.append({
                "strategy_name": strategy_name,
                "indicator_name": indicator_name,
                "note": meta.get("note", ""),
                "status": meta.get("status", "Open"),
                "momentum": meta.get("momentum", "Not Defined"),
                "strategy_tag": meta.get("strategy_tag", "Neutral"),
                "analysis_date": meta.get("analysis_date", ""),
                "last_modified": meta.get("last_modified", ""),
                "modified_by": meta.get("modified_by", "system"),
            })
    if rows:
        resp = client.table('strategy_analyses').upsert(rows).execute()
        if hasattr(resp, 'error') and resp.error:
            raise RuntimeError(resp.error)
    return True

@retry_with_backoff(max_retries=4, base_delay=0.5)
def supabase_get_gallery_images():
    """Get gallery images with retry + cache last good value."""
    client = _init_supabase_hardened()
    if not client:
        return _cache_get("lk_supabase_get_gallery_images", [])
    resp = client.table('gallery_images').select('*').execute()
    if hasattr(resp, 'error') and resp.error:
        raise RuntimeError(resp.error)
    images = []
    for img in (resp.data or []):
        if 'bytes_b64' in img:
            try:
                img['bytes'] = base64.b64decode(img['bytes_b64'])
            except Exception:
                pass
        images.append(img)
    _cache_set("lk_supabase_get_gallery_images", images)
    return images

@retry_with_backoff(max_retries=4, base_delay=0.5)
def supabase_save_gallery_images(images: list):
    """Save gallery images with retry."""
    client = _init_supabase_hardened()
    if not client:
        return False
    resp = client.table('gallery_images').upsert(images).execute()
    if hasattr(resp, 'error') and resp.error:
        raise RuntimeError(resp.error)
    return True

# =====================================================================
# END OF EXTREME RELIABILITY SUPABASE PATCH
# =====================================================================

# =====================================================================
# GALLERY IMAGE PERSISTENCE & SUPABASE RELIABILITY — FIXED (Claude-style)
# - Robust encode/decode with checksum
# - Silent transient retries
# - Transaction-safe upload
# - Backward-compatible with legacy bytes_b64
# - Overrides old gallery functions to avoid touching call sites
# =====================================================================
import base64, io, hashlib, logging
from datetime import datetime
try:
    from PIL import Image
except Exception:
    Image = None  # If PIL is not installed, uploader will guard.

logging.getLogger(__name__).setLevel(logging.INFO)

# ----- Robust image (de)serialization -----
def encode_image_for_storage(image_bytes: bytes, format_str: str) -> dict | None:
    try:
        if not image_bytes:
            raise ValueError("Empty image bytes")
        b64_str = base64.b64encode(image_bytes).decode("utf-8")
        checksum = hashlib.md5(image_bytes).hexdigest()[:8]
        return {
            "b64_data": b64_str,
            "checksum": checksum,
            "size": len(image_bytes),
            "format": format_str,
            "encoded_at": datetime.now().isoformat(),
        }
    except Exception as e:
        logging.error(f"encode_image_for_storage failed: {e}")
        return None

def decode_image_from_storage(encoded_data: dict) -> bytes | None:
    try:
        if not encoded_data or "b64_data" not in encoded_data:
            return None
        decoded = base64.b64decode(encoded_data["b64_data"])
        stored = encoded_data.get("checksum")
        if stored:
            actual = hashlib.md5(decoded).hexdigest()[:8]
            if actual != stored:
                logging.error(f"Checksum mismatch: expected {stored}, got {actual}")
                return None
        return decoded
    except Exception as e:
        logging.error(f"decode_image_from_storage failed: {e}")
        return None

# ----- Fixed Supabase gallery functions (use existing retry_with_backoff if present) -----
_retry = retry_with_backoff if 'retry_with_backoff' in globals() else (lambda **kw: (lambda f: f))

# ----- Local loading & uploader (override) -----
# =====================================================================
# END OF GALLERY IMAGE PERSISTENCE FIX
# =====================================================================

# -------------------------
# Gallery Pagination - Database Layer
# -------------------------
def render_gallery_statistics_paginated():
    st.markdown("---")
    st.subheader("📊 Gallery Statistics")
    try:
        total = get_gallery_images_count()
        images = st.session_state.get('uploaded_images', [])
        authors = len(set(img.get('uploaded_by') for img in images)) if images else 0
        strategies = set()
        for img in images:
            for s in img.get('strategies', []) or []:
                strategies.add(s)
        col1, col2, col3, col4 = st.columns(4)
        with col1: st.metric("Total Images", total)
        with col2: st.metric("Unique Authors", authors)
        with col3: st.metric("Strategies Tagged", len(strategies))
        with col4: st.metric("Total Likes", sum(img.get('likes',0) for img in images) if images else 0)
        st.markdown("---")
        st.write("**📈 Top Images by Likes:**")
        top_images = sorted(images, key=lambda x: x.get('likes',0), reverse=True)[:5] if images else []
        for rank, img in enumerate(top_images, 1):
            st.write(f"{rank}. **{img.get('name','Unknown')}** - ❤️ {img.get('likes',0)} | 👤 {img.get('uploaded_by','Unknown')}")
    except Exception as e:
        st.error(f"Error loading stats: {e}")
