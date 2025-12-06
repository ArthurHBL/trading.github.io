

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

