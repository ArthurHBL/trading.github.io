
 WITH STRATEGY INDICATOR IMAGES - FIXED VERSION
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


 WITH STRATEGY INDICATOR IMAGES - FIXED VERSION
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

    # ADD THIS: Check if purchase verification modal should be shown
    if st.session_state.get('show_purchase_verification'):
        render_purchase_verification_modal()
        return  # Return early to prevent showing other content when modal is open

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


 WITH DUAL MODE - FIXED VERSION
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
            if st.button("💳 Ko-Fi", use_container_width=True, key="sidebar_kofi_verification_btn"):
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

