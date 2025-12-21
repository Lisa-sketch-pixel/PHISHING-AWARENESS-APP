# ================================
# THAT'S PHISHY 🎣 — Complete app.py (ready to drop in)
# Streamlit + Supabase + (Optional) OpenAI
# ================================

import os
import json
import random
from datetime import datetime
import streamlit as st
from supabase import create_client, Client

# -----------------------------
# Page config + Theme
# -----------------------------
st.set_page_config(
    page_title="THAT'S PHISHY 🎣",
    page_icon="🎣",
    layout="wide"
)

st.markdown("""
<style>
.stApp {
  background: radial-gradient(1200px 600px at 10% 10%, #1c1f38 0%, #0f1224 40%, #090b18 100%) !important;
}
h1, h2, h3 { text-shadow: 0 0 10px rgba(120,100,255,.25); }
.block-container { padding-top: 2rem; }
.stExpander, .stButton>button, .stRadio, .stSelectbox, .stTextInput, .stTabs [data-baseweb="tab"] {
  border-radius: 12px !important;
}
.stButton>button {
  background: linear-gradient(90deg,#6a5cff,#9a5fff);
  border: 0;
  color: white;
  font-weight: 600;
  box-shadow: 0 8px 20px rgba(120,100,255,.25);
}
.stButton>button:hover { filter: brightness(1.07); }
.starline { font-size:1.4rem; letter-spacing:1px }
.badge {
  display:inline-block;
  padding:.35rem .7rem;
  border-radius:999px;
  font-weight:700;
  background:#1e223f;
  color:#e6e6ff;
  border:1px solid rgba(150,130,255,.35);
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Secrets / Supabase
# -----------------------------
SUPABASE_URL = st.secrets.get("supabase", {}).get("url") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("supabase", {}).get("key") or st.secrets.get("SUPABASE_KEY")
OPENAI_KEY = st.secrets.get("openai", {}).get("api_key") or st.secrets.get("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.warning(
        "Supabase credentials not found in Secrets. "
        "Results will not be saved remotely in this session."
    )
    supabase = None
else:
    try:
        supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception:
        supabase = None

# -----------------------------
# Helpers & default content
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

def load_json(path, default=None):
    default = default or []
    try:
        full = os.path.join(BASE_DIR, path)
        with open(full, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

# -----------------------------
# Default simulations
# -----------------------------
DEFAULT_SIMULATIONS = [
    {
        "channel": "email",
        "subject": "Your account has been locked — verify now",
        "sender": "support@secure-bank.com",
        "message": (
            "Dear user,\n\n"
            "We noticed suspicious activity on your account. "
            "Please verify your details immediately at "
            "https://secure-bank-verify.example.com "
            "to avoid suspension.\n\nSecurity Team"
        ),
        "is_phishing": True,
        "level": "beginner"
    },
    {
        "channel": "email",
        "subject": "Password change confirmation",
        "sender": "no-reply@yourbank.com",
        "message": (
            "Hello,\n\n"
            "This is to confirm your password was changed. "
            "If this was not you, login to the official site "
            "and reset your password.\n\nBank Team"
        ),
        "is_phishing": False,
        "level": "beginner"
    },
    {
        "channel": "sms",
        "sender": "YourBank",
        "message": "Your OTP is 123456. Do not share this with anyone.",
        "is_phishing": False,
        "level": "beginner"
    },
    {
        "channel": "email",
        "subject": "Action required: Update payroll details",
        "sender": "payroll@company-pay.com",
        "message": (
            "Hi,\n\n"
            "Please confirm your bank details by replying "
            "with account number and branch code "
            "to avoid payment delays.\n\nPayroll"
        ),
        "is_phishing": True,
        "level": "intermediate"
    },
    {
        "channel": "whatsapp",
        "sender": "+447700900123",
        "message": (
            "Hey, this is HR, please click this link "
            "to confirm your details: "
            "http://hr-confirm.example.com"
        ),
        "is_phishing": True,
        "level": "intermediate"
    },
    {
        "channel": "popup",
        "subject": "WARNING: Your device is infected",
        "sender": "System Alert",
        "message": (
            "Your device shows critical infections. "
            "Call +1-800-FAKEHELP or install our cleanup tool now."
        ),
        "is_phishing": True,
        "level": "advanced"
    }
]

# -----------------------------
# Default quizzes
# -----------------------------
DEFAULT_QUIZZES = [
    {
        "question": "What is the main purpose of a phishing attack?",
        "options": [
            "To steal information or trick the victim",
            "To fix device problems",
            "To update software",
            "To test internet connection"
        ],
        "answer": "To steal information or trick the victim",
        "level": "beginner"
    },
    {
        "question": "What should you do with an unexpected attachment?",
        "options": [
            "Open it immediately",
            "Forward it",
            "Verify or delete it",
            "Ignore antivirus warnings"
        ],
        "answer": "Verify or delete it",
        "level": "beginner"
    }
]

# -----------------------------
# AI helper
# -----------------------------
def ai_summary(text: str) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_KEY)
        r = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly cybersecurity coach."},
                {"role": "user", "content": text}
            ],
            max_tokens=220,
            temperature=0.7
        )
        return r.choices[0].message.content.strip()
    except Exception:
        return random.choice([
            "Watch for urgency and strange sender domains.",
            "Never share passwords or OTPs.",
            "Verify using official websites or apps."
        ])

# -----------------------------
# Session state
# -----------------------------
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "level" not in st.session_state:
    st.session_state.level = "Beginner"

# -----------------------------
# Pages
# -----------------------------
def page_home():
    st.title("🎣 THAT'S PHISHY")
    st.caption(
        "Interactive, gamified phishing awareness across email, "
        "SMS, WhatsApp, and fake virus popups."
    )

def page_learn(level):
    st.header(f"📚 Learn — {level}")
    st.write("Learning content goes here.")

def page_game(level):
    st.header(f"🎮 THAT'S PHISHY — {level}")
    st.write("Game logic runs here.")

def page_results():
    st.header("📈 Results")
    st.write("Results history.")

def page_account():
    st.header("👤 Account")
    st.write("Login / signup.")

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("🌐 Navigation")
page = st.sidebar.radio(
    "Go to:",
    ["Home", "Learn", "Phishy oor safe?", "Results", "Account"]
)

# -----------------------------
# Router
# -----------------------------
if page == "Home":
    page_home()
elif page == "Learn":
    page_learn(st.session_state.level)
elif page == "Phishy or safe?":
    page_game(st.session_state.level)
elif page == "Results":
    page_results()
elif page == "Account":
    page_account()
