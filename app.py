# ============================================
# Cybersecurity Awareness — Phish or Safe Game
# Streamlit + Supabase + (Optional) OpenAI AI
# ============================================

import os, json, random
from datetime import datetime
import streamlit as st
from supabase import create_client, Client

# -----------------------------
# CONFIG & CLIENT INITIALIZATION
# -----------------------------
st.set_page_config(page_title="Phish or Safe: The Cyber Challenge", page_icon="🛡️", layout="wide")

# Secrets (must exist in Streamlit Cloud -> Settings -> Secrets)
# [supabase]
# url = "https://<your>.supabase.co"
# key = "<anon_key>"
# [openai]
# api_key = "sk-...."
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# -----------------------------
# AI (with graceful fallback)
# -----------------------------
def ai_summary_feedback(text: str) -> str:
    """
    Try OpenAI (either new SDK or legacy). If it fails (quota/SDK), fallback to offline tips.
    """
    # Try new SDK
    try:
        from openai import OpenAI
        client = OpenAI(api_key=st.secrets["openai"]["api_key"])
        r = client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly cybersecurity mentor. Keep responses short and practical."},
                {"role": "user", "content": text}
            ],
            max_tokens=220,
            temperature=0.7
        )
        return r.choices[0].message.content.strip()
    except Exception:
        pass

    # Try legacy SDK
    try:
        import openai
        openai.api_key = st.secrets["openai"]["api_key"]
        r = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=[
                {"role": "system", "content": "You are a friendly cybersecurity mentor. Keep responses short and practical."},
                {"role": "user", "content": text}
            ],
            max_tokens=220,
            temperature=0.7
        )
        return r["choices"][0]["message"]["content"].strip()
    except Exception:
        # Offline fallback
        fallback = [
            "Great effort! 🚀 Focus on checking sender addresses and hovering links before clicking.",
            "Nice work! ⭐ Watch for urgency, strange domains, and unexpected attachments.",
            "Keep it up! 🔐 Enable MFA, use strong passwords, and verify requests via official channels.",
            "Tip: Real services won’t ask for passwords or codes by email. When in doubt, don’t click.",
        ]
        return random.choice(fallback)

# -----------------------------
# HELPERS
# -----------------------------
BASE_DIR = os.path.dirname(__file__)

def load_json(rel_path: str, default=None):
    """
    Robust loader: joins base dir + rel path, returns default on failure.
    """
    default = default or []
    try:
        with open(os.path.join(BASE_DIR, rel_path), "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"⚠️ Missing or unreadable file: {rel_path} — {e}")
        return default

def save_game_result(email: str, score: int, total: int, mode: str = "game"):
    """
    Saves result to 'simulation_results' (requires an 'email' column).
    For RLS: create an anon INSERT policy allowing true (demo) or bind to auth.uid().
    """
    try:
        supabase.table("simulation_results").insert({
            "email": email or "guest@demo",
            "score": score,
            "total": total,
            "mode": mode,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception as e:
        st.warning(f"Could not save results (RLS/policy?): {e}")

# -----------------------------
# SESSION STATE
# -----------------------------
if "user_email" not in st.session_state:
    st.session_state.user_email = None
if "page" not in st.session_state:
    st.session_state.page = "Home"
if "game" not in st.session_state:
    st.session_state.game = {
        "bank": [],
        "index": 0,
        "score": 0,
        "stars": 0,
        "finished": False
    }

# -----------------------------
# AUTH (SIMPLE)
# -----------------------------
def login_box():
    st.subheader("🔐 Log in")
    email = st.text_input("Email", key="login_email")
    pwd = st.text_input("Password", type="password", key="login_pwd")
    if st.button("Login", use_container_width=True):
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": pwd})
            st.session_state.user_email = res.user.email
            st.success(f"Welcome back, {res.user.email}!")
        except Exception as e:
            st.error(f"Login failed: {e}")

def signup_box():
    st.subheader("✨ Create account")
    email = st.text_input("New email", key="signup_email")
    pwd = st.text_input("Create password", type="password", key="signup_pwd")
    if st.button("Sign Up", use_container_width=True):
        try:
            supabase.auth.sign_up({"email": email, "password": pwd})
            st.success("Account created! Please verify your email before logging in.")
        except Exception as e:
            st.error(f"Sign-up failed: {e}")

# -----------------------------
# UI HELPERS (GAMIFICATION)
# -----------------------------
def badge_for_score(score: int, total: int):
    pct = (score / total) * 100 if total else 0
    if pct >= 80:
        return "🥇 **Gold Defender** — Incredible spotting skills!"
    elif pct >= 50:
        return "🥈 **Silver Scout** — Nice work! Keep sharpening your eye."
    else:
        return "🥉 **Bronze Trainee** — Good start, practice makes perfect!"

def star_bar(n: int):
    return "⭐" * n + "☆" * (10 - n if n <= 10 else 0)

# -----------------------------
# PAGES
# -----------------------------
def page_home():
    st.title("🛡️ Phish or Safe: The Cyber Challenge")
    st.write("Learn, play, and earn badges while training your phishing-spotting skills.")
    st.write("Use the sidebar to **Learn**, play the **Game**, view **Results**, or chat with the **AI Assistant**.")

def page_learn():
    st.header("📚 Learn — Basic & Advanced")
    tab1, tab2 = st.tabs(["🟢 Basic", "🔵 Advanced"])

    basic = load_json("content/cards_basic.json", default=[
        {"title": "What is Phishing?", "content": "Phishing is when attackers trick you into revealing data using fake messages."},
        {"title": "Urgency & Pressure", "content": "Warnings like 'account will be closed' try to make you rush."},
        {"title": "Attachments & Links", "content": "Unexpected attachments or odd links are a red flag."},
    ])
    adv = load_json("content/cards_advanced.json", default=[
        {"title": "Spear Phishing", "content": "Personalized attacks using info about you or your org."},
        {"title": "BEC", "content": "Impersonation of executives or vendors to request payments."},
        {"title": "Domain Spoofing", "content": "paypa1.com vs paypal.com — subtle domain tricks."},
    ])

    with tab1:
        for c in basic:
            with st.expander(c.get("title", "Untitled")):
                st.write(c.get("content", "No details."))

    with tab2:
        for c in adv:
            with st.expander(c.get("title", "Untitled")):
                st.write(c.get("content", "No details."))

    st.success("✅ Learning modules ready — jump into the game when you’re ready!")

def build_challenge_bank():
    """
    Build a combined challenge bank from:
      - content/simulation.json  (preferred)
      - OR content/sim_templates.json (fallback)
      - quizzes/main.json        (MCQ items)

    Email items -> binary 'Phish'/'Safe'.
    Quiz items  -> multiple-choice.
    """
    bank = []

    # 1) Email simulations (preferred filename)
    emails = load_json("content/simulation.json")
    if not emails:
        # fallback filename used earlier
        emails = load_json("content/sim_templates.json")

    for i, em in enumerate(emails):
        subj = em.get("subject") or em.get("Subject") or f"Email {i+1}"
        body = em.get("body") or em.get("text") or "No body text provided."
        is_phish = bool(em.get("is_phishing") or (em.get("label") == "Phishing"))
        bank.append({
            "type": "email",
            "subject": subj,
            "body": body,
            "answer": "Phishing" if is_phish else "Safe"
        })

    # 2) Quiz MCQs
    quiz = load_json("quizzes/main.json")
    for q in quiz:
        bank.append({
            "type": "quiz",
            "question": q.get("question", "Untitled question"),
            "options": q.get("options", []),
            "answer": q.get("answer", None)
        })

    # Shuffle for variety
    random.shuffle(bank)
    return bank

def reset_game():
    st.session_state.game = {
        "bank": build_challenge_bank(),
        "index": 0,
        "score": 0,
        "stars": 0,
        "finished": False
    }

def page_game():
    st.header("🎮 Phish or Safe: The Cyber Challenge")
    st.caption("Decide quickly and wisely. Earn ⭐ for correct answers and claim your badge at the end!")

    # Initialize bank on first visit
    if not st.session_state.game["bank"]:
        reset_game()

    bank = st.session_state.game["bank"]
    idx = st.session_state.game["index"]

    if st.session_state.game["finished"] or idx >= len(bank):
        total = len(bank)
        score = st.session_state.game["score"]
        stars = min(score, 10)  # cap visual stars at 10 for the meter
        st.subheader("🏁 Challenge Complete!")
        st.write(f"**Score:** {score} / {total}")
        st.write(f"**Stars:** {star_bar(stars)}")
        st.success(badge_for_score(score, total))

        # AI summary
        summary_prompt = (
            f"The learner completed a phishing awareness challenge with score {score}/{total}. "
            "Give 3 short, practical tips tailored to common mistakes people make with phishing. "
            "Keep it encouraging and easy to understand."
        )
        st.info(ai_summary_feedback(summary_prompt))

        # Save results
        save_game_result(st.session_state.user_email or "guest@demo", score, total, mode="game")

        if st.button("Play Again", use_container_width=True):
            reset_game()
            st.experimental_rerun()
        return

    # Progress header
    st.write(f"**Question {idx+1} of {len(bank)}**")
    item = bank[idx]

    if item["type"] == "email":
        st.subheader(f"📧 Subject: {item['subject']}")
        st.write(item["body"])

        col1, col2 = st.columns(2)
        picked = st.radio("Your choice:", ["Phishing", "Safe"], index=0, key=f"pick_{idx}")
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
            st.session_state.game["index"] += 1
            st.experimental_rerun()

    elif item["type"] == "quiz":
        st.subheader(f"🧠 {item['question']}")
        opts = item.get("options", [])
        ans = item.get("answer")
        if not opts or not ans:
            st.warning("This quiz item is incomplete.")
            st.session_state.game["index"] += 1
            st.experimental_rerun()
            return

        choice = st.radio("Select one:", opts, key=f"quiz_{idx}")
        col1, col2 = st.columns(2)
        if col1.button("✅ Submit", use_container_width=True):
            if choice == ans:
                st.success("Correct! ⭐")
                st.session_state.game["score"] += 1
                st.session_state.game["stars"] += 1
            else:
                st.error(f"Oops! Correct answer: **{ans}**")
            st.session_state.game["index"] += 1
            st.experimental_rerun()
        if col2.button("⏭️ Skip", use_container_width=True):
            st.session_state.game["index"] += 1
            st.experimental_rerun()

    # Live HUD
    st.write("---")
    st.metric("Score", st.session_state.game["score"])
    st.write("Stars:", star_bar(min(st.session_state.game["stars"], 10)))
    if st.session_state.user_email:
        st.caption(f"Results will be saved for: {st.session_state.user_email}")
    else:
        st.caption("Playing as guest (results saved with 'guest@demo').")

def page_results():
    st.header("📈 Your Results")
    who = st.session_state.user_email or "guest@demo"
    try:
        # If you prefer per-user: .eq("email", who)
        data = supabase.table("simulation_results").select("*").eq("email", who).order("created_at", desc=True).execute()
        rows = data.data or []
        if not rows:
            st.info("No results yet. Play the game first!")
            return
        for r in rows[:10]:
            when = r.get("created_at", "—")
            st.write(f"• **{when}** — Score: **{r.get('score', '?')} / {r.get('total', '?')}** — Mode: {r.get('mode', 'game')}")
    except Exception as e:
        st.error(f"Could not load results: {e}")

def page_ai():
    st.header("🤖 Cybersecurity AI Assistant")
    q = st.text_area("Ask about phishing, suspicious links, or staying safe online:")
    if st.button("Ask AI", use_container_width=True):
        if not q.strip():
            st.warning("Type a question first.")
        else:
            with st.spinner("Thinking..."):
                st.write(ai_summary_feedback("User question: " + q.strip()))

def page_account():
    st.header("👤 Account")
    if st.session_state.user_email:
        st.success(f"Logged in as **{st.session_state.user_email}**")
        if st.button("Log out"):
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            st.session_state.user_email = None
            st.experimental_rerun()
    else:
        tab1, tab2 = st.tabs(["Login", "Sign Up"])
        with tab1:
            login_box()
        with tab2:
            signup_box()

# -----------------------------
# SIDEBAR NAV
# -----------------------------
st.sidebar.title("🌐 Navigation")
if st.session_state.user_email:
    st.sidebar.caption(f"Signed in: {st.session_state.user_email}")
else:
    st.sidebar.caption("Signed in: guest (results saved as guest@demo)")

page = st.sidebar.radio(
    "Go to:",
    ["Home", "Learn", "Phish or Safe (Game)", "Results", "AI Assistant", "Account"],
    index=["Home", "Learn", "Phish or Safe (Game)", "Results", "AI Assistant", "Account"].index(st.session_state.page)
)
st.session_state.page = page

# -----------------------------
# RENDER
# -----------------------------
if page == "Home":
    page_home()
elif page == "Learn":
    page_learn()
elif page == "Phish or Safe (Game)":
    page_game()
elif page == "Results":
    page_results()
elif page == "AI Assistant":
    page_ai()
elif page == "Account":
    page_account()
