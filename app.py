# ================================
# THAT'S PHISHY 🎣 — Cyber Galaxy
# Streamlit + Supabase + (Optional) OpenAI
# ================================

import os, json, random, base64
from datetime import datetime
import streamlit as st
from supabase import create_client, Client

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
# Tiny celebration sound
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
    except Exception:
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
    except Exception:
        # Silent fail for users; can be logged separately if needed
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
    """
    Build a short, scenario-style explanation for any channel.
    """
    correct_label = item["answer"]  # "Phishing" or "Safe"
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
        except Exception as e:
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
# Content builders
# -----------------------------
def load_lessons(level):
    if level == "Beginner":
        return load_json("content/cards_beginner.json", default=[
            {
                "title": "What is Phishing?",
                "content": "Phishing is a social engineering attack where an attacker sends a fake email, SMS, or message pretending to be a trusted organisation. The goal is to steal passwords, banking details, or personal information, or to trick the victim into installing malware."
            },
            {
                "title": "Common Phishing Clues",
                "content": "Common signs include urgent or threatening language, poor spelling or strange grammar, unknown senders, unexpected attachments, and suspicious links that do not match the official website."
            },
            {
                "title": "Links & Fake Websites",
                "content": "Phishing often uses fake websites that look real. Always hover over links to see the real URL and be careful with look-alike domains like paypa1.com instead of paypal.com."
            },
            {
                "title": "Attachments & Information Requests",
                "content": "Unexpected attachments (ZIP, EXE, HTML) and messages asking for passwords, OTPs, or banking details are high-risk. Legitimate services do not ask for these through email, SMS, or WhatsApp."
            }
        ])
    elif level == "Intermediate":
        return load_json("content/cards_intermediate.json", default=[
            {
                "title": "Look-Alike Domains & Spoofed Senders",
                "content": "Attackers often register domains that look almost correct, such as paypa1.com instead of paypal.com, and fake display names like 'IT Support' or 'Your Bank'. Always check the real address after the @ symbol."
            },
            {
                "title": "Fake HR & Payroll Messages",
                "content": "Phishing emails often pretend to be from HR or Payroll and use salary, contracts, or benefits to grab attention. They may ask you to confirm bank details or fill in forms urgently. Real HR usually uses official portals."
            },
            {
                "title": "Malicious Attachments in Realistic Messages",
                "content": "Intermediate phishing messages can look professional but hide dangerous attachments like .zip, .html, or .exe files. These can install malware or remote access tools on your device."
            },
            {
                "title": "Multi-Channel Phishing",
                "content": "Attackers may combine email, SMS, WhatsApp, and phone calls in one campaign. For example, an email warns you, an SMS sends a code, and a call asks for that code. Legitimate services do not ask you to read out OTPs."
            },
            {
                "title": "Verify Before You Act",
                "content": "The best defence is to pause and verify. Do not click links or open attachments from unexpected messages. Instead, open the official app or type the official website yourself, or contact support via known channels."
            }
        ])
    else:
        return load_json("content/cards_advanced.json", default=[
            {
                "title": "Spear Phishing",
                "content": "Spear phishing is a highly targeted attack customised for a specific person or role, often using information from social media or breaches to make the message look legitimate."
            },
            {
                "title": "Business Email Compromise (BEC)",
                "content": "BEC attacks involve criminals taking over or spoofing a business email address to request urgent payments, change bank details, or approve fake invoices."
            },
            {
                "title": "Credential Harvesting & Fake Login Pages",
                "content": "Advanced phishing uses fake login pages that look identical to real ones. Victims are tricked into entering usernames, passwords, and sometimes MFA codes on the attacker’s site."
            },
            {
                "title": "“Your Device Has a Virus” Popups",
                "content": "Fake security popups claim your device is infected and push you to call a number or install 'cleaning' software. These are often scams used to gain remote access or make you pay for fake support."
            },
            {
                "title": "Report, Escalate, and Learn",
                "content": "For advanced users, it is important to report suspicious messages using official reporting tools, help improve filters, and share lessons with the rest of the team."
            }
        ])

def build_bank_for_level(level):
    level_map = {
        "Beginner": "beginner",
        "Intermediate": "intermediate",
        "Advanced": "advanced"
    }
    want_lvl = level_map.get(level, level).lower()

    bank = []

    # ----- Mixed-channel scenarios -----
    emails = load_json("content/simulation.json")
    if not emails:
        emails = []

    n_e = len(emails)
    if n_e:
        third_e = max(1, n_e // 3)

    for i, em in enumerate(emails):
        em_level_raw = (em.get("level") or "").lower()

        if em_level_raw:
            if want_lvl not in em_level_raw:
                continue
        else:
            if n_e >= 3:
                if level == "Beginner" and i >= third_e:
                    continue
                elif level == "Intermediate" and not (third_e <= i < 2 * third_e):
                    continue
                elif level == "Advanced" and i < 2 * third_e:
                    continue

        channel = em.get("channel", "email").lower()
        subj    = em.get("subject", "")
        sender  = em.get("from") or em.get("sender") or ""
        message = em.get("message") or em.get("body") or ""
        is_phish = bool(em.get("is_phishing") or (em.get("label") == "Phishing"))

        bank.append({
            "type": "scenario",
            "channel": channel,
            "subject": subj,
            "sender": sender,
            "message": message,
            "answer": "Phishing" if is_phish else "Safe"
        })

    # ----- Quiz questions -----
    quiz = load_json("quizzes/main.json")
    n_q = len(quiz)
    if n_q:
        third_q = max(1, n_q // 3)

    for j, q in enumerate(quiz):
        q_level_raw = (q.get("level") or "").lower()

        if q_level_raw:
            if want_lvl not in q_level_raw:
                continue
        else:
            if n_q >= 3:
                if level == "Beginner" and j >= third_q:
                    continue
                elif level == "Intermediate" and not (third_q <= j < 2 * third_q):
                    continue
                elif level == "Advanced" and j < 2 * third_q:
                    continue

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
# Pages
# -----------------------------
def page_home():
    st.title("🎣 THAT'S PHISHY")
    st.caption("Interactive, gamified phishing awareness across email, SMS, WhatsApp, and fake virus popups.")
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

def page_game(level):
    st.header(f"🎮 THAT'S PHISHY — {level}")

    if not st.session_state.learn_done[level]:
        st.warning("Complete the Learn section first to unlock the game.")
        return

    if not st.session_state.game["bank"]:
        reset_game(level)

    game = st.session_state.game
    bank = game["bank"]
    idx  = game["index"]

    if idx >= len(bank):
        game["finished"] = True
        st.session_state.game = game

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
            "(sender, links, domains, urgency, attachments, and 'virus' popups). Keep it very simple."
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

    st.write(f"**Scenario {idx+1} of {len(bank)}**")
    st.progress((idx + 1) / len(bank))
    st.markdown(
        f"<div class='starline'>{star_bar(min(game['stars'], 10))}</div>",
        unsafe_allow_html=True
    )

    if game["feedback"] is not None:
        fb = game["feedback"]
        if fb.get("correct"):
            st.success(fb.get("message", "Correct! ⭐"))
        else:
            st.error(fb.get("message", "Not quite."))

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

    item = bank[idx]

    # ---------- SCENARIO MODE ----------
    if item["type"] == "scenario":
        channel = item.get("channel", "email")

        if channel == "email":
            st.markdown("### 📘 Email Scenario")
            st.write(
                "Imagine you are checking your inbox and you receive the following email. "
                "Look carefully at the sender, wording, links, and any sense of urgency."
            )
            if item.get("sender"):
                st.write(f"**From:** {item['sender']}")
            if item.get("subject"):
                st.write(f"**Subject:** {item['subject']}")
            st.write(item.get("message", ""))

        elif channel == "sms":
            st.markdown("### 📱 SMS Scenario")
            st.write(
                "Imagine your phone buzzes with this SMS/text. "
                "Think about the sender, the link, and what it is asking you to do."
            )
            if item.get("sender"):
                st.write(f"**From:** {item['sender']}")
            st.write(item.get("message", ""))

        elif channel == "whatsapp":
            st.markdown("### 💬 WhatsApp Scenario")
            st.write(
                "Imagine this message appears in your WhatsApp chat. "
                "Consider whether you know the sender and if the request is reasonable."
            )
            if item.get("sender"):
                st.write(f"**From:** {item['sender']}")
            st.write(item.get("message", ""))

        elif channel == "popup":
            st.markdown("### 🖥️ Security / Virus Alert Scenario")
            st.write(
                "Imagine this security message suddenly appears on your screen while you are browsing. "
                "Is it a real alert or part of a scam?"
            )
            if item.get("subject"):
                st.write(f"**Title:** {item['subject']}")
            st.write(item.get("message", ""))

        else:
            st.markdown("### 📘 Message Scenario")
            st.write(item.get("message", ""))

        try:
            picked = st.radio(
                "How would you classify this?",
                ["Phishing", "Safe"],
                index=None,
                key=f"scenario_{idx}"
            )
        except TypeError:
            picked = st.radio(
                "How would you classify this?",
                ["Phishing", "Safe"],
                key=f"scenario_{idx}"
            )

        col1, col2 = st.columns(2)
        if col1.button("✅ Submit", use_container_width=True):
            if picked is None:
                st.warning("Please choose **Phishing** or **Safe** before submitting.")
            else:
                correct = item["answer"]
                is_correct = (picked == correct)

                if is_correct:
                    msg = f"Correct! ⭐ This scenario is **{correct}**."
                    game["score"] += 1
                    game["stars"] += 1
                else:
                    msg = f"Not quite. This scenario is actually **{correct}**."

                explanation = explain_scenario(item, picked)

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

    # ---------- QUIZ MODE ----------
    elif item["type"] == "quiz":
        st.subheader("🧠 Knowledge Check")
        st.write(item["question"])
        opts = item.get("options", [])
        ans  = item.get("answer")

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
                    "explanation": None
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
            st.info("No results yet. Complete Learn + THAT'S PHISHY to see your progress here.")
            return
        for r in rows[:12]:
            when = r.get("created_at", "—")
            st.write(
                f"• **{when}** — {r.get('level','?')} — "
                f"Score: **{r.get('score','?')}/{r.get('total','?')}** "
                f"({r.get('mode','game')})"
            )
    except Exception:
        st.error("Could not load results right now. Please try again later.")

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
    "Navigation",
    ["Home", "Learn", "Phishy or safe?", "Results", "AI Assistant", "Account"]
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
elif page == "THAT'S PHISHY":
    page_game(st.session_state.level)
elif page == "Results":
    page_results()
elif page == "AI Assistant":
    page_ai()
elif page == "Account":
    page_account()
