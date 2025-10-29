# ================================
# Phish or Safe — Cyber Galaxy 🌌
# Streamlit + Supabase + (Optional) OpenAI
# ================================

import os, json, random, base64
from datetime import datetime
import streamlit as st
from supabase import create_client, Client

# -----------------------------
# Page config + Galaxy theme
# -----------------------------
st.set_page_config(page_title="Phish or Safe: The Cyber Challenge", page_icon="🛡️", layout="wide")
# Background gradient + subtle card glow
st.markdown("""
<style>
/* page background */
.stApp {
  background: radial-gradient(1200px 600px at 10% 10%, #1c1f38 0%, #0f1224 40%, #090b18 100%) !important;
}
/* headers glow */
h1, h2, h3 { text-shadow: 0 0 10px rgba(120,100,255,.25); }
/* cards */
.block-container { padding-top: 2rem; }
.stExpander, .stButton>button, .stRadio, .stSelectbox, .stTextInput, .stTabs [data-baseweb="tab"] {
  border-radius: 12px !important;
}
/* buttons */
.stButton>button {
  background: linear-gradient(90deg,#6a5cff,#9a5fff);
  border: 0; color: white; font-weight: 600;
  box-shadow: 0 8px 20px rgba(120,100,255,.25);
}
.stButton>button:hover { filter: brightness(1.07); }
/* metrics stars line */
.starline { font-size:1.4rem; letter-spacing:1px }
.badge {
  display:inline-block; padding:.35rem .7rem; border-radius:999px; font-weight:700;
  background: #1e223f; color: #e6e6ff; border: 1px solid rgba(150,130,255,.35);
}
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Defensive secrets loader
# -----------------------------
SUPABASE_URL = st.secrets.get("supabase", {}).get("url") or st.secrets.get("SUPABASE_URL")
SUPABASE_KEY = st.secrets.get("supabase", {}).get("key") or st.secrets.get("SUPABASE_KEY")
OPENAI_KEY   = st.secrets.get("openai", {}).get("api_key") or st.secrets.get("OPENAI_API_KEY")

if not SUPABASE_URL or not SUPABASE_KEY:
    st.error("🚨 Missing Supabase credentials in Secrets. Add them in Streamlit → Settings → Secrets.")
    st.stop()

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# Tiny celebration sound (base64)
# -----------------------------
# a short 'ping' tone (22050Hz mono wav) base64-encoded
PING_WAV = (
    "UklGRrQAAABXQVZFZm10IBAAAAABAAEAESsAACJWAAACABAAZGF0YQwAAAABAQEBAgICAwMDAwQE"
    "BAUFBQYGBgcHBwgICAkJCgoKCwsMDQ0ODw8QEBA="
)
def play_chime():
    try:
        audio_bytes = base64.b64decode(PING_WAV)
        st.audio(audio_bytes, format="audio/wav", start_time=0)
    except Exception:
        pass

# -----------------------------
# Helpers
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

def load_json(path, default=None):
    default = default or []
    try:
        with open(os.path.join(BASE_DIR, path), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"⚠️ Missing or unreadable file: {path} — {e}")
        return default

def save_result(email, score, total, level, mode):
    try:
        supabase.table("simulation_results").insert({
            "email": email or "guest@demo",
            "score": score, "total": total,
            "level": level, "mode": mode,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        st.warning(f"Could not save results (RLS/policy?): {e}")

def ai_summary(text: str) -> str:
    # Try new SDK
    try:
        from openai import OpenAI
        client = OpenAI(api_key=OPENAI_KEY)
        r = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system","content":"You are a friendly cybersecurity coach. Be concise and practical."},
                {"role":"user","content": text}
            ],
            max_tokens=220, temperature=0.7
        )
        return r.choices[0].message.content.strip()
    except Exception:
        pass
    # Try legacy SDK
    try:
        import openai
        openai.api_key = OPENAI_KEY
        r = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role":"system","content":"You are a friendly cybersecurity coach. Be concise and practical."},
                {"role":"user","content": text}
            ],
            max_tokens=220, temperature=0.7
        )
        return r["choices"][0]["message"]["content"].strip()
    except Exception:
        # Offline fallback
        tips = [
            "Great work! 👏 Watch for urgency, odd sender domains, and unexpected attachments.",
            "Tip: Hover links to preview URLs. Real services don’t ask for passwords or codes by email.",
            "Enable MFA and use a password manager. When in doubt, verify via the official app/site."
        ]
        return random.choice(tips)

def badge_for(score, total):
    pct = (score/total*100) if total else 0
    if pct >= 80:  return "🥇 Gold Defender"
    if pct >= 50:  return "🥈 Silver Scout"
    return "🥉 Bronze Trainee"

def star_bar(n):  # visual cap at 10
    n = max(0, min(10, n))
    return "⭐"*n + "☆"*(10-n)

# -----------------------------
# Session State
# -----------------------------
if "user_email" not in st.session_state: st.session_state.user_email = None
if "level" not in st.session_state:      st.session_state.level = "Basic"  # Basic | Advanced
if "learn_done" not in st.session_state: st.session_state.learn_done = {"Basic": False, "Advanced": False}
if "game" not in st.session_state:
    st.session_state.game = {"bank": [], "index": 0, "score": 0, "stars": 0, "finished": False}

# -----------------------------
# Auth (simple)
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
        except Exception as e:
            st.error(f"Login failed: {e}")

def signup_ui():
    st.subheader("✨ Create account")
    email = st.text_input("New email", key="signup_email")
    pwd   = st.text_input("Create password", type="password", key="signup_pwd")
    if st.button("Sign Up", use_container_width=True):
        try:
            supabase.auth.sign_up({"email": email, "password": pwd})
            st.success("Account created! Verify your email before logging in.")
        except Exception as e:
            st.error(f"Sign-up failed: {e}")

# -----------------------------
# Content builders (aligned)
# -----------------------------
def load_lessons(level):
    if level == "Basic":
        return load_json("content/cards_basic.json", default=[
            {"title":"Suspicious Email Traits","content":"Urgency, threats, poor grammar, unknown sender, mismatched display name vs address."},
            {"title":"Links & Domains","content":"Hover to preview URLs. Lookalikes like paypa1.com are malicious."},
            {"title":"Attachments","content":"Unexpected ZIP/EXE/HTML attachments are dangerous."},
            {"title":"Personal Info","content":"Legit orgs won’t ask for passwords/2FA codes by email."}
        ])
    else:
        return load_json("content/cards_advanced.json", default=[
            {"title":"Spear Phishing","content":"Personalized scams using job roles/projects/social info."},
            {"title":"Business Email Compromise","content":"Exec/vendor impersonation requesting urgent payment."},
            {"title":"Credential Harvesting","content":"Fake login portals; always open official site instead."},
            {"title":"Malicious Attachments","content":"Office macros, HTML attachments, or links to drive-by malware."}
        ])

def build_bank_for_level(level):
    bank = []
    # Email simulations (preferred) with level flag
    emails = load_json("content/simulation.json")
    if not emails:
        emails = load_json("content/sim_templates.json")
    for i, em in enumerate(emails):
        # If your JSON contains "level": "basic"/"advanced", we’ll filter; else split by index
        em_level = (em.get("level") or "basic").lower()
        want_lvl = level.lower()
        # heuristic: if file has no explicit levels, split first half basic, rest advanced
        if "level" not in em and want_lvl == "basic" and i >= len(emails)//2: 
            continue
        if "level" not in em and want_lvl == "advanced" and i < len(emails)//2:
            continue
        if "level" in em and em_level != want_lvl: 
            continue
        subj = em.get("subject", f"Email {i+1}")
        body = em.get("body", "No content")
        is_phish = bool(em.get("is_phishing") or (em.get("label") == "Phishing"))
        bank.append({"type":"email","subject":subj,"body":body,"answer":"Phishing" if is_phish else "Safe"})

    # MCQ quiz (optionally with level in JSON; else same heuristic)
    quiz = load_json("quizzes/main.json")
    for j, q in enumerate(quiz):
        q_level = (q.get("level") or "basic").lower()
        if "level" in q and q_level != level.lower(): 
            continue
        if "level" not in q:
            # split by index if not provided
            half = len(quiz)//2
            if level == "Basic" and j >= half: 
                continue
            if level == "Advanced" and j < half: 
                continue
        bank.append({
            "type":"quiz",
            "question": q.get("question", "Untitled"),
            "options": q.get("options", []),
            "answer": q.get("answer")
        })

    random.shuffle(bank)
    return bank

def reset_game(level):
    st.session_state.game = {"bank": build_bank_for_level(level), "index": 0, "score": 0, "stars": 0, "finished": False}

# -----------------------------
# Pages
# -----------------------------
def page_home():
    st.title("🛡️ Phish or Safe: The Cyber Challenge")
    st.caption("Learn → Play → Earn badges. Train your eye to spot phishing like a pro.")
    st.write("Use the sidebar to choose **level**, start with **Learn**, then play the **Game**, and view your **Results**.")
    if st.session_state.user_email:
        st.success(f"Signed in as {st.session_state.user_email}")
    else:
        st.info("You’re playing as guest. Results save under guest@demo.")

def page_learn(level):
    st.header(f"📚 Learn — {level}")
    lessons = load_lessons(level)
    for c in lessons:
        with st.expander(c.get("title","Untitled")):
            st.write(c.get("content","No details."))
    st.markdown("<span class='badge'>Complete this section to unlock the game</span>", unsafe_allow_html=True)
    if st.button("✅ Mark Learn as Complete", use_container_width=True):
        st.session_state.learn_done[level] = True
        st.balloons()
        play_chime()
        st.success(f"{level} learning completed. You can proceed to the game!")

def page_game(level):
    st.header(f"🎮 Phish or Safe — {level}")
    if not st.session_state.learn_done[level]:
        st.warning("Complete the Learn section first to unlock the game.")
        return

    if not st.session_state.game["bank"]:
        reset_game(level)

    bank = st.session_state.game["bank"]
    idx  = st.session_state.game["index"]

    if idx >= len(bank):
        st.session_state.game["finished"] = True

    if st.session_state.game["finished"]:
        total = len(bank)
        score = st.session_state.game["score"]
        stars = min(score, 10)
        st.subheader("🏁 Section Complete!")
        st.write(f"**Score:** {score} / {total}")
        st.markdown(f"<div class='starline'>{star_bar(stars)}</div>", unsafe_allow_html=True)
        final_badge = badge_for(score, total)
        st.markdown(f"<span class='badge'>{final_badge}</span>", unsafe_allow_html=True)
        st.balloons(); play_chime()

        # AI summary tailored to performance
        summary_prompt = (
            f"User finished a phishing training ({level}) with score {score}/{total}. "
            "Give 3 short, encouraging improvement tips aligned with common phishing red flags "
            "(sender address, link hovering, attachments, urgency)."
        )
        st.info(ai_summary(summary_prompt))
        save_result(st.session_state.user_email, score, total, level, mode="game")

        col1, col2 = st.columns(2)
        if col1.button("🔁 Play Again", use_container_width=True):
            reset_game(level); st.experimental_rerun()
        if col2.button("➡️ Next Section", use_container_width=True):
            # handy hint: after Basic, suggest Advanced; after Advanced, suggest Results
            if level == "Basic":
                st.session_state.level = "Advanced"
                # clear learn gate for advanced so they go learn first
                st.experimental_rerun()
            else:
                st.experimental_rerun()
        return

    # HUD
    st.write(f"**Question {idx+1} of {len(bank)}**")
    st.markdown(f"<div class='starline'>{star_bar(min(st.session_state.game['stars'],10))}</div>", unsafe_allow_html=True)

    item = bank[idx]

    if item["type"] == "email":
        st.subheader(f"📧 Subject: {item['subject']}")
        st.write(item["body"])
        try:
            picked = st.radio("Your choice:", ["Phishing", "Safe"], index=None, key=f"pick_{idx}")
        except TypeError:
            # older Streamlit fallback (preselect nothing not supported): default to first
            picked = st.radio("Your choice:", ["Phishing", "Safe"], key=f"pick_{idx}")
        col1, col2 = st.columns(2)
        if col1.button("✅ Submit", use_container_width=True):
            correct = item["answer"]
            if picked == correct:
                st.success(f"Correct! ⭐ That was **{correct}**.")
                st.session_state.game["score"] += 1
                st.session_state.game["stars"] += 1
            else:
                st.error(f"Not quite. It was **{correct}**.")
            st.session_state.game["index"] += 1
            st.experimental_rerun()
        if col2.button("⏭️ Skip", use_container_width=True):
            st.session_state.game["index"] += 1; st.experimental_rerun()

    elif item["type"] == "quiz":
        st.subheader(f"🧠 {item['question']}")
        opts = item.get("options", [])
        ans  = item.get("answer")
        if not opts or not ans:
            st.warning("This quiz item is incomplete; skipping.")
            st.session_state.game["index"] += 1; st.experimental_rerun(); return
        try:
            choice = st.radio("Select one:", opts, index=None, key=f"quiz_{idx}")
        except TypeError:
            choice = st.radio("Select one:", opts, key=f"quiz_{idx}")
        col1, col2 = st.columns(2)
        if col1.button("✅ Submit", use_container_width=True):
            if choice == ans:
                st.success("Correct! ⭐")
                st.session_state.game["score"] += 1
                st.session_state.game["stars"] += 1
            else:
                st.error(f"Oops! Correct answer: **{ans}**")
            st.session_state.game["index"] += 1; st.experimental_rerun()
        if col2.button("⏭️ Skip", use_container_width=True):
            st.session_state.game["index"] += 1; st.experimental_rerun()

def page_results():
    st.header("📈 Your Results")
    who = st.session_state.user_email or "guest@demo"
    try:
        q = supabase.table("simulation_results").select("*").eq("email", who).order("created_at", desc=True).execute()
        rows = q.data or []
        if not rows:
            st.info("No results yet. Complete Learn + Game to see your progress here.")
            return
        for r in rows[:12]:
            when = r.get("created_at","—")
            st.write(f"• **{when}** — {r.get('level','?')} — Score: **{r.get('score','?')}/{r.get('total','?')}**  ({r.get('mode','game')})")
    except Exception as e:
        st.error(f"Could not load results: {e}")

def page_ai():
    st.header("🤖 Cybersecurity AI Assistant")
    q = st.text_area("Ask about phishing, suspicious links, or best practices:")
    if st.button("Ask AI", use_container_width=True):
        if not q.strip():
            st.warning("Type a question first.")
        else:
            with st.spinner("Thinking..."):
                st.write(ai_summary("User question: " + q.strip()))

def page_account():
    st.header("👤 Account")
    if st.session_state.user_email:
        st.success(f"Logged in as **{st.session_state.user_email}**")
        if st.button("Log out"):
            try: supabase.auth.sign_out()
            except Exception: pass
            st.session_state.user_email = None; st.experimental_rerun()
    else:
        t1, t2 = st.tabs(["Login","Sign Up"])
        with t1: login_ui()
        with t2: signup_ui()

# -----------------------------
# Sidebar
# -----------------------------
st.sidebar.title("🌐 Navigation")
st.sidebar.selectbox("Difficulty level", ["Basic","Advanced"], key="level")
if st.session_state.user_email:
    st.sidebar.caption(f"Signed in: {st.session_state.user_email}")
else:
    st.sidebar.caption("Signed in: guest (results saved as guest@demo)")

page = st.sidebar.radio("Go to:", ["Home","Learn","Phish or Safe (Game)","Results","AI Assistant","Account"])
st.sidebar.divider()
if st.sidebar.button("🔁 Reset Current Game"):
    reset_game(st.session_state.level); st.experimental_rerun()

# -----------------------------
# Router
# -----------------------------
if page == "Home": page_home()
elif page == "Learn": page_learn(st.session_state.level)
elif page == "Phish or Safe (Game)": page_game(st.session_state.level)
elif page == "Results": page_results()
elif page == "AI Assistant": page_ai()
elif page == "Account": page_account()
