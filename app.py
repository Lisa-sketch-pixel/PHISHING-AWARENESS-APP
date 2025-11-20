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
        # In production you might want to log this instead of warning
        st.warning(f"⚠️ Missing or unreadable file: {path} — {e}")
        return default

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
    pct = (score / total * 100) if total else 0
    if pct >= 80:
        return "🥇 Gold Defender"
    if pct >= 50:
        return "🥈 Silver Scout"
    return "🥉 Bronze Trainee"

def star_bar(n):  # visual cap at 10
    n = max(0, min(10, n))
    return "⭐" * n + "☆" * (10 - n)

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
            {
                "title": "What is Phishing?",
                "content": "Phishing is a social engineering attack where an attacker sends a fake email, SMS, "
                           "or message pretending to be a trusted organisation. The goal is to steal passwords, "
                           "bank details, or personal information, or to trick the victim into installing malware."
            },
            {
                "title": "Common Phishing Clues",
                "content": "Phishing messages often use urgent or threatening language, unexpected attachments, "
                           "poor spelling, strange grammar, or sender addresses that do not match the real company."
            },
            {
                "title": "Links & Fake Websites",
                "content": "Attackers hide fake websites behind links. Hover over links to see the real URL before "
                           "clicking, and watch out for look-alike domains like paypa1.com instead of paypal.com."
            },
            {
                "title": "Attachments & Information Requests",
                "content": "Unexpected attachments or messages asking for passwords, OTPs, PINs, or bank details "
                           "are strong signs of phishing. Legitimate organisations do not request this by email."
            }
        ])
    elif level == "Intermediate":
        return load_json("content/cards_intermediate.json", default=[
            {
                "title": "Look-Alike Domains & Spoofed Senders",
                "content": "Attackers often register domains that look almost correct, such as paypa1.com instead "
                           "of paypal.com. They may also fake the display name, like 'IT Support', while the real "
                           "email address is from a random domain. Always check the part after the @ symbol."
            },
            {
                "title": "Fake HR & Payroll Messages",
                "content": "Phishing emails often pretend to be from HR or Payroll and use salary, contracts, or "
                           "benefits to get attention. They might ask you to 'confirm bank details' or 'avoid salary "
                           "delays'. Real HR systems usually use official portals and already have your data."
            },
            {
                "title": "Malicious Attachments in Realistic Emails",
                "content": "Intermediate phishing attacks can look professional but hide dangerous attachments like "
                           ".zip, .html, or .exe files. These can install malware or remote access tools. Verify "
                           "unexpected files using another channel before opening them."
            },
            {
                "title": "Multi-Step & Multi-Channel Phishing",
                "content": "Attackers may combine email, SMS, and phone calls to make the story feel real. For "
                           "example, an email warns about a login issue, an SMS sends a code, and a phone call asks "
                           "you to share the code. Legitimate services never ask you to read out OTPs."
            },
            {
                "title": "Security Hygiene: Verify Before You Act",
                "content": "A strong defence is to pause and verify. Instead of clicking links in messages, open the "
                           "official app or type the official website address yourself. Use approved helpdesk or HR "
                           "channels to confirm unusual requests."
            }
        ])
    else:  # Advanced
        return load_json("content/cards_advanced.json", default=[
            {
                "title": "Spear Phishing",
                "content": "Spear phishing is highly targeted phishing aimed at specific people or roles. Attackers "
                           "use information from LinkedIn, data breaches, or social media to craft personalised, "
                           "believable messages."
            },
            {
                "title": "Business Email Compromise (BEC)",
                "content": "In BEC attacks, criminals impersonate executives, suppliers, or finance contacts to push "
                           "urgent payments or changes to bank details. These messages often avoid links and focus "
                           "on social pressure and urgency."
            },
            {
                "title": "Credential Harvesting & Fake Portals",
                "content": "Credential harvesting uses fake login pages to steal usernames and passwords. The page "
                           "may look identical to the real site. Always open important sites by typing the URL "
                           "yourself or using bookmarks, not email links."
            },
            {
                "title": "Detection & Reporting",
                "content": "At an advanced level, defence includes quickly reporting suspicious messages using 'Report "
                           "phishing' features in email clients and following internal incident response procedures. "
                           "Early reporting helps protect the whole organisation."
            }
        ])

def build_bank_for_level(level):
    # Map UI level to JSON level tags
    level_map = {
        "Beginner": "beginner",
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
            # Support tags like "beginner", "basic", "intermediate", "advanced"
            if want_lvl not in em_level_raw:
                # compatibility: treat "basic" as beginner if used
                if not (want_lvl == "beginner" and "basic" in em_level_raw):
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
            # Support "beginner"/"basic"/"intermediate"/"advanced"
            if want_lvl not in q_level_raw:
                if not (want_lvl == "beginner" and "basic" in q_level_raw):
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
    if not bank:
        st.info("No scenarios or quiz items available for this level.")
        return

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
    "🔍 Phishy or Safe?",
    ["Home", "Learn", "Phishy or Safe?", "Results", "AI Assistant", "Account"]
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
elif page == "Phishy or Safe?":
    page_game(st.session_state.level)
elif page == "Results":
    page_results()
elif page == "AI Assistant":
    page_ai()
elif page == "Account":
    page_account()
