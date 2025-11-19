# ================================
# THAT'S PHISHY 🎣 — Cyber Galaxy
# Streamlit + Supabase + (Optional) OpenAI
# ================================

import os, json, random, base64, time
from datetime import datetime
import streamlit as st
from supabase import create_client, Client

# -----------------------------
# Page config + Galaxy theme
# -----------------------------
st.set_page_config(page_title="THAT'S PHISHY 🎣", page_icon="🎣", layout="wide")

# Background gradient + subtle card glow
st.markdown("""
<style>
/* page background */
.stApp {
  background: radial-gradient(1200px 600px at 10% 10%, #1c1f38 0%, #0f1224 40%, #090b18 100%) !important;
}
/* headers glow */
h1, h2, h3 { text-shadow: 0 0 10px rgba(120,100,255,.25); }
/* cards and inputs */
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

def explain_email_scenario(item, picked):
    """
    Build a short, scenario-style explanation for an email.
    Uses ai_summary() so it stays in simple English.
    """
    correct_label = item["answer"]  # "Phishing" or "Safe"
    verdict_text = "phishing" if correct_label == "Phishing" else "safe"
    user_choice_text = "phishing" if picked == "Phishing" else "safe"

    prompt = f"""
You are a friendly cybersecurity coach. The learner just classified an email as {user_choice_text},
but the correct classification is {verdict_text}.

Explain this situation as a short training scenario.

Email subject: {item.get('subject','(no subject)')}
Email body: {item.get('body','(no body)')}

In 3 short bullet points, explain in very simple English:
- Why this email is actually {verdict_text}
- What clues they should have noticed
- What the user should do in this situation (for example: ignore, report, verify via official app/site)

Avoid technical jargon. Write for complete beginners.
"""
    return ai_summary(prompt)

# -----------------------------
# Session State
# -----------------------------
if "user_email" not in st.session_state:
    st.session_state.user_email = None

# Three difficulty levels
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
# Content builders
# -----------------------------
def load_lessons(level):
    """
    Beginner  -> very simple, intro concepts
    Intermediate -> some experience
    Advanced  -> deeper / targeted attacks
    """
    if level == "Beginner":
        return load_json("content/cards_beginner.json", default=[
            {"title": "What is Phishing?", "content": "Phishing is a fake message that tries to trick you into giving away information, money, or access."},
            {"title": "Common Phishing Clues", "content": "Urgent tone, threats, unknown sender, bad spelling, or offers that seem too good to be true."},
            {"title": "Links & Buttons", "content": "Always hover over links to see where they really go before clicking."},
            {"title": "Never Share Codes", "content": "Legit companies don’t ask for passwords, OTPs, or PINs in messages or emails."}
        ])
    elif level == "Intermediate":
        return load_json("content/cards_intermediate.json", default=[
            {"title": "More Sneaky Tricks", "content": "Attackers may copy real logos, names, and signatures to look legit."},
            {"title": "Domain Look-Alikes", "content": "Watch out for slight changes like amaz0n.com or support-paypal.com instead of the real site."},
            {"title": "Attachments", "content": "Unexpected ZIP, EXE, or HTML attachments can install malware or steal your data."},
            {"title": "Multi-Channel Phishing", "content": "Scams can come via SMS, WhatsApp, social media DMs, or fake support calls."}
        ])
    else:  # Advanced
        return load_json("content/cards_advanced.json", default=[
            {"title": "Spear Phishing", "content": "Highly targeted messages built using info from LinkedIn, email leaks, or social media."},
            {"title": "Business Email Compromise", "content": "Attackers impersonate a boss, supplier, or finance to push urgent payments."},
            {"title": "Credential Harvesting", "content": "Fake login pages steal usernames and passwords. Always type the official URL yourself."},
            {"title": "Reporting & Response", "content": "Use 'Report phishing' in mail clients and notify IT/security when you spot something suspicious."}
        ])

def build_bank_for_level(level):
    # Map UI level to internal label for old JSON that uses "basic"/"advanced"
    level_map = {
        "Beginner": "basic",
        "Intermediate": "intermediate",
        "Advanced": "advanced"
    }
    want_lvl = level_map.get(level, level).lower()

    bank = []

    # ----- EMAIL SCENARIOS -----
    emails = load_json("content/simulation.json")
    if not emails:
        emails = load_json("content/sim_templates.json")

    n_e = len(emails)
    if n_e:
        third_e = max(1, n_e // 3)

    for i, em in enumerate(emails):
        em_level_raw = (em.get("level") or "").lower()

        if em_level_raw:
            # If level is specified in JSON, support both new and old tags
            # e.g. "basic", "beginner", "intermediate", "advanced"
            if want_lvl not in em_level_raw:
                continue
        else:
            # No explicit level: split by index into 3 bands
            if n_e >= 3:
                if level == "Beginner" and i >= third_e:
                    continue
                elif level == "Intermediate" and not (third_e <= i < 2 * third_e):
                    continue
                elif level == "Advanced" and i < 2 * third_e:
                    continue
            else:
                # If very few items, just include all
                pass

        subj = em.get("subject", f"Email {i+1}")
        body = em.get("body", "No content")
        is_phish = bool(em.get("is_phishing") or (em.get("label") == "Phishing"))
        bank.append({
            "type": "email",
            "subject": subj,
            "body": body,
            "answer": "Phishing" if is_phish else "Safe"
        })

    # ----- QUIZ QUESTIONS -----
    quiz = load_json("quizzes/main.json")
    n_q = len(quiz)
    if n_q:
        third_q = max(1, n_q // 3)

    for j, q in enumerate(quiz):
        q_level_raw = (q.get("level") or "").lower()

        if q_level_raw:
            # Support "basic"/"beginner"/"intermediate"/"advanced"
            if want_lvl not in q_level_raw:
                continue
        else:
            # No explicit level: split quiz by index into 3 bands
            if n_q >= 3:
                if level == "Beginner" and j >= third_q:
                    continue
                elif level == "Intermediate" and not (third_q <= j < 2 * third_q):
                    continue
                elif level == "Advanced" and j < 2 * third_q:
                    continue
            else:
                pass

        bank.append({
            "type": "quiz",
            "question": q.get("question", "Untitled"),
            "options": q.get("options", []),
            "answer": q.get("answer")
        })

    random.shuffle(bank)
    return bank

def reset_game(level):
    st.session_state.game = {
        "bank": build_bank_for_level(level),
        "index": 0,
        "score": 0,
        "stars": 0,
        "finished": False,
        "feedback": None
    }

# -----------------------------
# PAGES
# -----------------------------
def page_home():
    st.title("🎣 THAT'S PHISHY")
    st.caption("Interactive, gamified phishing awareness. Spot the bait before you get hooked.")
    if st.session_state.user_email:
        st.success(f"Signed in as {st.session_state.user_email}")
    else:
        st.info("You’re playing as guest. Results save under guest@demo.")

def page_learn(level):
    st.header(f"📚 Learn — {level}")
    lessons = load_lessons(level)
    for c in lessons:
        with st.expander(c.get("title", "Untitled")):
            st.write(c.get("content", "No details."))
    st.markdown("<span class='badge'>Complete this section to unlock the game</span>", unsafe_allow_html=True)
    if st.button("✅ Mark Learn as Complete", use_container_width=True):
        st.session_state.learn_done[level] = True
        st.balloons()
        play_chime()
        st.success(f"{level} learning completed. You can proceed to the game!")

# -----------------------------
# 🎮 GAME SECTION — Scenario-based
# -----------------------------
def page_game(level):
    st.header(f"🎮 THAT'S PHISHY — {level}")

    # Gate: must complete Learn first
    if not st.session_state.learn_done[level]:
        st.warning("Complete the Learn section first to unlock the game.")
        return

    # Ensure bank is built
    if not st.session_state.game["bank"]:
        reset_game(level)

    game = st.session_state.game
    bank = game["bank"]
    idx = game["index"]

    # If we've gone past the last item, mark finished
    if idx >= len(bank):
        game["finished"] = True
        st.session_state.game = game

    # If game finished: show summary + tips
    if game["finished"]:
        total = len(bank)
        score = game["score"]
        stars = min(score, 10)

        st.subheader("🏁 Training Section Complete!")
        st.write(f"**Score:** {score} / {total}")
        st.markdown(f"<div class='starline'>{star_bar(stars)}</div>", unsafe_allow_html=True)
        final_badge = badge_for(score, total)
        st.markdown(f"<span class='badge'>{final_badge}</span>", unsafe_allow_html=True)
        st.balloons()
        play_chime()

        summary_prompt = (
            f"User finished a phishing training ({level}) with score {score}/{total}. "
            "Give 3 short, encouraging improvement tips aligned with common phishing red flags "
            "(sender address, link hovering, attachments, urgency). Keep it very simple."
        )
        st.info(ai_summary(summary_prompt))
        save_result(st.session_state.user_email, score, total, level, mode="game")

        col1, col2 = st.columns(2)
        if col1.button("🔁 Play Again", use_container_width=True):
            reset_game(level)
            st.rerun()
        if col2.button("➡️ Next Section", use_container_width=True):
            if level == "Beginner":
                st.session_state.level = "Intermediate"
            elif level == "Intermediate":
                st.session_state.level = "Advanced"
            st.rerun()
        return

    # Progress / stars
    st.write(f"**Scenario {idx+1} of {len(bank)}**")
    st.progress((idx + 1) / len(bank))
    st.markdown(
        f"<div class='starline'>{star_bar(min(game['stars'], 10))}</div>",
        unsafe_allow_html=True
    )

    # If we already have feedback for this scenario, show it and a "Next" button
    if game["feedback"] is not None:
        fb = game["feedback"]
        # verdict message
        if fb.get("correct"):
            st.success(fb.get("message", "Correct! ⭐"))
        else:
            st.error(fb.get("message", "Not quite."))

        # scenario explanation if present
        explanation = fb.get("explanation")
        if explanation:
            st.markdown("### 🧠 Scenario Breakdown")
            st.write(explanation)

        if st.button("➡️ Next Scenario", use_container_width=True):
            game["index"] += 1
            game["feedback"] = None
            st.session_state.game = game
            st.rerun()
        return

    # No feedback yet → show the current item
    item = bank[idx]

    # ----- EMAIL SCENARIO MODE -----
    if item["type"] == "email":
        st.markdown("### 📘 Scenario")
        st.write(
            "Imagine you are checking your inbox and you receive the following email. "
            "Look at the sender, the wording, and any links carefully."
        )

        st.subheader(f"📧 Subject: {item['subject']}")
        st.write(item["body"])

        try:
            picked = st.radio(
                "How would you classify this email?",
                ["Phishing", "Safe"],
                index=None,
                key=f"pick_{idx}"
            )
        except TypeError:
            picked = st.radio(
                "How would you classify this email?",
                ["Phishing", "Safe"],
                key=f"pick_{idx}"
            )

        col1, col2 = st.columns(2)
        if col1.button("✅ Submit", use_container_width=True):
            if picked is None:
                st.warning("Please choose **Phishing** or **Safe** before submitting.")
            else:
                correct = item["answer"]
                is_correct = (picked == correct)

                if is_correct:
                    msg = f"Correct! ⭐ This email is **{correct}**."
                    game["score"] += 1
                    game["stars"] += 1
                else:
                    msg = f"Not quite. This email is actually **{correct}**."

                # Build a scenario explanation (AI or fallback)
                explanation = explain_email_scenario(item, picked)

                game["feedback"] = {
                    "correct": is_correct,
                    "message": msg,
                    "explanation": explanation
                }
                st.session_state.game = game
                st.rerun()

        if col2.button("⏭️ Skip Scenario", use_container_width=True):
            game["index"] += 1
            st.session_state.game = game
            st.rerun()

    # ----- QUIZ MODE (knowledge check) -----
    elif item["type"] == "quiz":
        st.subheader("🧠 Knowledge Check")
        st.write(item["question"])
        opts = item.get("options", [])
        ans = item.get("answer")

        if not opts or not ans:
            st.warning("This quiz item is incomplete; skipping.")
            game["index"] += 1
            st.session_state.game = game
            st.rerun()
            return

        try:
            choice = st.radio(
                "Select the best answer:",
                opts,
                index=None,
                key=f"quiz_{idx}"
            )
        except TypeError:
            choice = st.radio(
                "Select the best answer:",
                opts,
                key=f"quiz_{idx}"
            )

        col1, col2 = st.columns(2)
        if col1.button("✅ Submit Answer", use_container_width=True):
            if choice is None:
                st.warning("Please select an answer first.")
            else:
                is_correct = (choice == ans)
                if is_correct:
                    msg = "Correct! ⭐"
                    game["score"] += 1
                    game["stars"] += 1
                else:
                    msg = f"Oops! The correct answer is: **{ans}**."

                game["feedback"] = {
                    "correct": is_correct,
                    "message": msg,
                    "explanation": None  # we keep quiz feedback short
                }
                st.session_state.game = game
                st.rerun()

        if col2.button("⏭️ Skip Question", use_container_width=True):
            game["index"] += 1
            st.session_state.game = game
            st.rerun()

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
            when = r.get("created_at", "—")
            st.write(
                f"• **{when}** — {r.get('level','?')} — "
                f"Score: **{r.get('score','?')}/{r.get('total','?')}** "
                f"({r.get('mode','game')})"
            )
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
            try:
                supabase.auth.sign_out()
            except Exception:
                pass
            st.session_state.user_email = None
            st.rerun()
    else:
        t1, t2 = st.tabs(["Login", "Sign Up"])
        with t1:
            login_ui()
        with t2:
            signup_ui()

# -----------------------------
# Sidebar Navigation
# -----------------------------
st.sidebar.title("🌐 Navigation")
st.sidebar.selectbox(
    "Difficulty level",
    ["Beginner", "Intermediate", "Advanced"],
    key="level"
)

if st.session_state.user_email:
    st.sidebar.caption(f"Signed in: {st.session_state.user_email}")
else:
    st.sidebar.caption("Signed in: guest (results saved as guest@demo)")

page = st.sidebar.radio(
    "Go to:",
    ["Home", "Learn", "THAT'S PHISHY (Game)", "Results", "AI Assistant", "Account"]
)

st.sidebar.divider()
if st.sidebar.button("🔁 Reset Current Game"):
    reset_game(st.session_state.level)
    st.rerun()

# -----------------------------
# Router
# -----------------------------
if page == "Home":
    page_home()
elif page == "Learn":
    page_learn(st.session_state.level)
elif page == "THAT'S PHISHY (Game)":
    page_game(st.session_state.level)
elif page == "Results":
    page_results()
elif page == "AI Assistant":
    page_ai()
elif page == "Account":
    page_account()
