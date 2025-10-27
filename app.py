# =========================================================
# CYBERSECURITY AWARENESS SYSTEM & THREAT SIMULATOR (Layla)
# Final integrated version — Streamlit + Supabase + OpenAI
# =========================================================

import streamlit as st
from supabase import create_client
from openai import OpenAI
import json
from datetime import datetime

# ===============================
# ✅ Load Secrets from Streamlit
# ===============================
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    OPENAI_API_KEY = st.secrets["openai"]["api_key"]
except KeyError as e:
    st.error(f"Missing key in secrets.toml: {e}")
    st.stop()

# ===============================
# ✅ Initialize Connections
# ===============================
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    client = OpenAI(api_key=OPENAI_API_KEY)
except Exception as e:
    st.error(f"⚠️ Connection setup failed: {e}")
    st.stop()

# ===============================
# ✅ Optional — Test the Connections
# ===============================
try:
    # Simple ping to Supabase (table list)
    tables = supabase.table("profiles").select("*").limit(1).execute()
    st.sidebar.success("✅ Connected to Supabase successfully")
except Exception:
    st.sidebar.warning("⚠️ Supabase connection active but table may be empty")

try:
    # Simple OpenAI ping
    client.models.list()
    st.sidebar.success("✅ OpenAI API active")
except Exception:
    st.sidebar.warning("⚠️ OpenAI API not responding or rate limited")

# ===============================
# ✅ App Header UI
# ===============================
st.set_page_config(page_title="Cybersecurity Awareness System & Threat Simulator",
                   page_icon="🛡️", layout="wide")

st.title("🛡️ Cybersecurity Awareness System & Threat Simulator")
st.caption("Learn. Test. Simulate. Protect yourself from phishing and social engineering threats.")
st.divider()


# ==========================
# Sidebar & Navigation
# ==========================
pages = {
    "Home": home_section,
    "Learn": learn_section,
    "Simulate": simulate_section,
    "Quiz": quiz_section,
    "Results": results_section,
}

if "page" not in st.session_state:
    st.session_state["page"] = "Home"

st.sidebar.title("🌐 Go to")
page = st.sidebar.radio("", list(pages.keys()), index=list(pages.keys()).index(st.session_state["page"]))
st.session_state["page"] = page

# --- User Info & Logout ---
if "user" in st.session_state and st.session_state["user"]:
    user_email = st.session_state["user"].email
    st.sidebar.caption(f"👤 Logged in as: {user_email}")
    if st.sidebar.button("🚪 Log Out"):
        supabase.auth.sign_out()
        st.session_state["user"] = None
        st.success("You’ve been logged out.")
        st.rerun()
else:
    st.sidebar.caption("Not signed in")

# --- Render Selected Page ---
pages[page]()

