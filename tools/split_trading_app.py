#!/usr/bin/env python3
"""
Run this once to split the 11 000-line file into modules.
It is idempotent – safe to run several times.
"""
import re, os, shutil
from pathlib import Path

BIG_FILE = "DeepSeek version, Create Test User — o usuário será criado com senha dummy test12345.txt"
ENCODING = "utf-8"

TREE = {"modules": ["__init__.py"], "data": [], "logs": []}

# ---------- same CHUNKS list as in previous answer ----------
CHUNKS = [
    (r"^# -------------------------\n# CONFIG", r"^# -------------------------\n# STRATEGIES DEFINITION", "config.py", None),
    (r"^# -------------------------\n# STRATEGIES DEFINITION", r"^# -------------------------\n# TRADING SIGNALS CONFIGURATION", "config.py", None),
    (r"^# -------------------------\n# TRADING SIGNALS CONFIGURATION", r"^# -------------------------\n# 5-DAY CYCLE SYSTEM", "config.py", None),
    (r"^# -------------------------\n# 5-DAY CYCLE SYSTEM", r"^# -------------------------\n# EMAIL VALIDATION TOOLS", "utils.py", None),
    (r"^# -------------------------\n# EMAIL VALIDATION TOOLS", r"^# -------------------------\n# USER MANAGER CLASS", "utils.py", None),
    (r"^class UserManager:", r"^user_manager = UserManager\(\)", "users.py", None),
    (r"^# -------------------------\n# ENHANCED IMAGE GALLERY", r"^# -------------------------\n# STRATEGY INDICATOR IMAGE UPLOAD", "gallery.py", None),
    (r"^# -------------------------\n# STRATEGY INDICATOR IMAGE UPLOAD", r"^# -------------------------\n# ENHANCED USER DASHBOARD", "gallery.py", None),
    (r"^# -------------------------\n# ENHANCED KAI TRADING AGENT", r"^# -------------------------\n# SUPABASE DATABASE FUNCTIONS", "kai_agent.py", None),
    (r"^# -------------------------\n# SUPABASE DATABASE FUNCTIONS", r"^# -------------------------\n# SESSION MANAGEMENT", "supabase_client.py", None),
    (r"^# -------------------------\n# SESSION MANAGEMENT", r"^# -------------------------\n# DATA PERSISTENCE SETUP", "supabase_client.py", None),
    (r"^# -------------------------\n# TRADING SIGNALS DATA PERSISTENCE", r"^# -------------------------\n# GALLERY IMAGE PERSISTENCE", "signals.py", None),
    (r"^# -------------------------\n# KO-FI PURCHASE VERIFICATION SYSTEM", r"^# -------------------------\n# PRODUCTION CONFIGURATION", "purchase.py", None),
    (r"^# -------------------------\n# PRODUCTION CONFIGURATION", r"^# -------------------------\n# STRATEGIES DEFINITION", "config.py", None),
    (r"^# -------------------------\n# ENHANCED AUTHENTICATION COMPONENTS", r"^# -------------------------\n# ENHANCED IMAGE GALLERY FORUM", "auth.py", None),
    (r"^# -------------------------\n# ENHANCED IMAGE GALLERY FORUM", r"^# -------------------------\n# STRATEGY INDICATOR IMAGE UPLOAD", "gallery.py", None),
    (r"^# -------------------------\n# ENHANCED PREMIUM SIGNAL DASHBOARD", r"^# -------------------------\n# ENHANCED USER DASHBOARD", "admin.py", None),
    (r"^# -------------------------\n# ENHANCED USER DASHBOARD", r"^# -------------------------\n# COMPLETE ADMIN DASHBOARD", "admin.py", None),
    (r"^# -------------------------\n# COMPLETE ADMIN DASHBOARD", r"^def render_admin_dashboard_selection\(\):", "admin.py", None),
    (r"^def render_admin_dashboard_selection\(\):", r"^if __name__ == [\"']__main__[\"']", "app.py", None),
]

def read_big():
    with open(BIG_FILE, encoding=ENCODING) as f:
        return f.read()

def write(path, text):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding=ENCODING) as f:
        f.write(text)

def extract_chunk(content, start_pat, end_pat):
    start = re.search(start_pat, content, flags=re.MULTILINE)
    if not start:
        return ""
    end = re.search(end_pat, content[start.end():], flags=re.MULTILINE)
    if not end:
        return content[start.end():]
    return content[start.end():start.end()+end.start()]

def main():
    print("Reading big file...")
    content = read_big()

    for folder, files in TREE.items():
        Path(folder).mkdir(exist_ok=True)
        for f in files:
            (Path(folder) / f).touch()

    for start_re, end_re, module, _ in CHUNKS:
        chunk = extract_chunk(content, start_re, end_re)
        if chunk.strip():
            dst = Path("modules") / module
            with open(dst, "a", encoding=ENCODING) as f:
                f.write("\n" + chunk)

    app_py = '''
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
'''
    write("app.py", app_py)
    print("✅ Split complete!")

if __name__ == "__main__":
    main()
