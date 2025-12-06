

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

