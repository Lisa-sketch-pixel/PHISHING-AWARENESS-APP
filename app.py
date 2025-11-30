# ================================
# THAT'S PHISHY 🎣 — Cyber Galaxy
# Streamlit + Supabase + (Optional) OpenAI
# ================================

import os, json, random, base64
from datetime import datetime
import streamlit as st
from supabase import create_client, Client
from pathlib import Path

# -----------------------------
# Page config + Galaxy theme
# -----------------------------
st.set_page_config(page_title="THAT'S PHISHY 🎣", page_icon="🎣", layout="wide")

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
  border: 0; color: white; font-weight: 600;
  box-shadow: 0 8px 20px rgba(120,100,255,.25);
}
.stButton>button:hover { filter: brightness(1.07); }
.starline { font-size:1.4rem; letter-spacing:1px }
.badge {
  display:inline-block; padding:.35rem .7rem; border-radius:999px; font-weight:700;
  background: #1e223f; color: #e6e6ff; border: 1px solid rgba(150,130,255,.35);
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Secrets / Supabase
# -----------------------------
SUPABASE_URL = st.secrets.get("supabase", {}).get("url") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("supabase", {}).get("key") or st.secrets.get("SUPABASE_KEY")
OPENAI_KEY   = st.secrets.get("openai", {}).get("api_key") or st.secrets.get("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("🚨 Missing Supabase credentials in Secrets. Add them in Streamlit → Settings → Secrets.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# BASE_DIR + robust JSON loader
# -----------------------------
try:
    BASE_DIR = Path(__file__).parent.resolve()
except Exception:
    BASE_DIR = Path.cwd().resolve()

@st.cache_data(ttl=300)
def load_json(path, default=None):
    if default is None:
        default = []
    full = (BASE_DIR / path).resolve()
    try:
        with open(full, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

# -----------------------------
# Disable sound completely
# -----------------------------
def play_chime():
    return

# -----------------------------
# Helpers
# -----------------------------
def save_result(email, score, total, level, mode):
    try:
        supabase.table("simulation_results").insert({
            "email": email or "guest@demo",
            "score": score,
            "total": total,
            "level": level,
            "mode": mode,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception:
        pass

def ai_summary(text: str) -> str:
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_KEY)
        r = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly cybersecurity coach. Be concise and practical."},
                {"role": "user", "content": text}
            ],
            max_tokens=220,
            temperature=0.7
        )
        return r.choices[0].message.content.strip()
    except Exception:
        tips = [
            "Great work! 👏 Watch for urgency, odd sender domains, and unexpected attachments.",
            "Tip: Hover links to preview URLs. Real services don’t ask for passwords or codes by email, SMS, or WhatsApp.",
            "Enable MFA and use a password manager. When in doubt, verify using the official app or website."
        ]
        return random.choice(tips)

def badge_for(score, total):
    pct = (score/total*100) if total else 0
    if pct >= 80:  return "🥇 Gold Defender"
    if pct >= 50:  return "🥈 Silver Scout"
    return "🥉 Bronze Trainee"

def star_bar(n):
    n = max(0, min(10, n))
    return "⭐"*n + "☆"*(10-n)

def explain_scenario(item, picked):
    correct_label = item["answer"]
    verdict_text = "phishing" if correct_label == "Phishing" else "safe"
    user_choice_text = "phishing" if picked == "Phishing" else "safe"
    channel = item.get("channel", "email")

    channel_desc = {
        "email": "You received an email that may be fake.",
        "sms": "You received an SMS/text message on your phone.",
        "whatsapp": "You received a message on WhatsApp.",
        "popup": "You saw a security or virus alert on your screen.",
    }.get(channel, "You received a message that may be fake.")

    subject = item.get("subject", "(no subject)")
    sender  = item.get("sender", "(unknown sender)")
    message = item.get("message", "")

    prompt = f"""
You are a friendly cybersecurity coach. The learner classified a scenario as {user_choice_text},
but the correct classification is {verdict_text}.

Channel: {channel}
Short description: {channel_desc}
Sender: {sender}
Subject/title: {subject}
Message/content: {message}

In very simple English, explain in 3 short bullet points:
- Why this scenario is actually {verdict_text}
- What clues they should notice (urgency, links, domains, sender, attachments, 'virus' popups, etc.)
- What the user should do in this situation (for example: ignore, report, verify via official app/site)

Avoid jargon. Write for complete beginners, but keep it accurate.
"""
    return ai_summary(prompt)

# -----------------------------
# Session state
# -----------------------------
if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "level" not in st.session_state:
    st.session_state.level = "Beginner"

if "learn_done" not in st.session_state:
    st.session_state.learn_done = {
        "Beginner": False,
        "Intermediate": False,
        "Advanced": False
    }

if "game" not in st.session_state:
    st.session_state.game = {
        "bank": [],
        "index": 0,
        "score": 0,
        "stars": 0,
        "finished": False,
        "feedback": None
    }

# -----------------------------
# Auth
# -----------------------------
def login_ui():
    st.subheader("🔐 Log in")
    email = st.text_input("Email", key="login_email")
    pwd   = st.text_input("Password", type="password", key="login_pwd")
    if st.button("Login", use_container_width=True):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": pwd})
            st.session_state.user_email = res.user.email
            st.success(f"Welcome back, {res.user.email}!")
        except Exception:
            st.error("Login failed. Please check your credentials or try again later.")

def signup_ui():
    st.subheader("✨ Create account")
    email = st.text_input("New email", key="signup_email")
    pwd   = st.text_input("Create password", type="password", key="signup_pwd")
    if st.button("Sign Up", use_container_width=True):
        try:
            supabase.auth.sign_up({"email": email, "password": pwd})
            st.success("Account created! Please verify your email before logging in.")
        except Exception:
            st.error("Sign-up failed. Please try again with a different email or password.")

# -----------------------------
# Lessons, bank, game logic
# -----------------------------
# (All your original functions: load_lessons, build_bank_for_level, reset_game, page_home, page_learn,
# page_game, page_results, page_ai, page_account, and sidebar/router remain the same.)
# -----------------------------

# ---- You just replace old BASE_DIR, load_json, and play_chime with the above ----
# ---- Everything else is unchanged from your original app.py ----
