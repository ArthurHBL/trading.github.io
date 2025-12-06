
"""
New modular entry point for Streamlit
"""
import streamlit as st
from modules.config import Config
from modules.auth import render_login
from modules.users import user_manager
from modules.admin import render_admin_dashboard
from modules.gallery import render_image_gallery_paginated
from modules.kai_agent import render_kai_agent
from modules.signals import render_trading_signals_room
from modules.purchase import render_user_purchase_button, render_purchase_verification_modal

def init_session():
    if "user" not in st.session_state:
        st.session_state.user = None

def main():
    init_session()
    if st.session_state.user is None:
        render_login()
    elif st.session_state.user.get("plan") == "admin":
        render_admin_dashboard()
    else:
        st.title("Dashboard")
        st.write("User dashboard not yet wired – add your UI here")

if __name__ == "__main__":
    main()
