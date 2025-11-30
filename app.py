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
    st.warning("Supabase credentials not found in Secrets. Results will not be saved remotely in this session.")
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
    """
    Load a JSON file from content folders. If missing, return default (do NOT warn here).
    """
    default = default or []
    try:
        full = os.path.join(BASE_DIR, path)
        with open(full, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return default

# Built-in default simulations (multi-channel: email, sms, whatsapp, popup)
DEFAULT_SIMULATIONS = [
    # Beginner (email)
    {
        "channel": "email",
        "subject": "Your account has been locked — verify now",
        "sender": "support@secure-bank.com",
        "message": "Dear user,\n\nWe noticed suspicious activity on your account. Please verify your details immediately at https://secure-bank-verify.example.com to avoid suspension.\n\nSecurity Team",
        "is_phishing": True,
        "level": "beginner"
    },
    {
        "channel": "email",
        "subject": "Password change confirmation",
        "sender": "no-reply@yourbank.com",
        "message": "Hello,\n\nThis is to confirm your password was changed. If this was not you, login to the official site and reset your password.\n\nBank Team",
        "is_phishing": False,
        "level": "beginner"
    },
    # Beginner (sms)
    {
        "channel": "sms",
        "sender": "YourBank",
        "message": "Your OTP is 123456. Do not share this with anyone.",
        "is_phishing": False,
        "level": "beginner"
    },
    # Intermediate (email / HR payroll)
    {
        "channel": "email",
        "subject": "Action required: Update payroll details",
        "sender": "payroll@company-pay.com",
        "message": "Hi,\n\nPlease confirm your bank details by replying with account number and branch code to avoid payment delays.\n\nPayroll",
        "is_phishing": True,
        "level": "intermediate"
    },
    {
        "channel": "email",
        "subject": "Meeting notes attached",
        "sender": "project.manager@company.com",
        "message": "Hi team,\n\nAttached are the notes from today's meeting. Please review the PDF for your tasks.\n\nRegards",
        "is_phishing": False,
        "level": "intermediate"
    },
    # Intermediate (whatsapp)
    {
        "channel": "whatsapp",
        "sender": "+447700900123",
        "message": "Hey, this is HR, please click this link to confirm your details: http://hr-confirm.example.com",
        "is_phishing": True,
        "level": "intermediate"
    },
    # Advanced (BEC / popup)
    {
        "channel": "email",
        "subject": "Invoice #8471 overdue - urgent payment required",
        "sender": "accounts@trusted-vendor.com",
        "message": "Hi Finance,\n\nPlease process payment immediately. Note the bank details have changed (see attached PDF).\n\nRegards",
        "is_phishing": True,
        "level": "advanced"
    },
    {
        "channel": "popup",
        "subject": "WARNING: Your device is infected",
        "sender": "System Alert",
        "message": "Your device shows critical infections. Call +1-800-FAKEHELP or install our cleanup tool now.",
        "is_phishing": True,
        "level": "advanced"
    },
    {
        "channel": "email",
        "subject": "Security advisory: new phishing campaign",
        "sender": "security@company.com",
        "message": "We have detected a campaign targeting employees. Do not click links or share passwords. Report suspicious emails.",
        "is_phishing": False,
        "level": "advanced"
    }
]

# Built-in default quizzes (merged for all levels)
DEFAULT_QUIZZES = [
    # Beginner
    {"question":"What is the main purpose of a phishing attack?",
     "options":["To steal information or trick the victim into harmful actions","To test internet connection","To fix device problems","To update software"],
     "answer":"To steal information or trick the victim into harmful actions","level":"beginner"},
    {"question":"Which of the following is a common sign of a phishing email?",
     "options":["Urgent language demanding immediate action","An email from a known company domain","A long formal signature","A meeting invitation"],
     "answer":"Urgent language demanding immediate action","level":"beginner"},
    {"question":"How can you check if a link is suspicious before clicking it?",
     "options":["Hover to preview the real URL","Click it quickly to see","Ignore it","Reply to the sender"],
     "answer":"Hover to preview the real URL","level":"beginner"},
    {"question":"Which action is safest with an unexpected attachment?",
     "options":["Open it immediately","Forward to coworkers","Delete or verify separately","Save it for later"],
     "answer":"Delete or verify separately","level":"beginner"},

    # Intermediate
    {"question":"Which is an example of a look-alike domain used in phishing?",
     "options":["paypa1.com instead of paypal.com","company.com vs secure.company.com","sub.company.com","company.co.uk vs company.com"],
     "answer":"paypa1.com instead of paypal.com","level":"intermediate"},
    {"question":"What should you do if 'IT Support' email comes from a free email address?",
     "options":["Reply and ask to confirm","Click link to verify","Ignore or report as phishing","Forward to coworkers"],
     "answer":"Ignore or report as phishing","level":"intermediate"},
    {"question":"Which HR-related email is most suspicious?",
     "options":["Monthly newsletter","Urgent request to send bank details by email","Meeting invite","Timesheet reminder via official portal"],
     "answer":"Urgent request to send bank details by email","level":"intermediate"},
    {"question":"Why are unexpected attachments dangerous even if message looks professional?",
     "options":["They can contain malware or remote access tools","They slow your computer","They always contain images","They are harmless if well-written"],
     "answer":"They can contain malware or remote access tools","level":"intermediate"},
    {"question":"Which is an example of multi-channel phishing?",
     "options":["Email only","Email + SMS + call asking for OTP","Single newsletter","Calendar invite from manager"],
     "answer":"Email + SMS + call asking for OTP","level":"intermediate"},
    {"question":"What is the safest way to check a login request from an email?",
     "options":["Use the link in the email","Type the official site yourself or open the official app","Reply asking if it's real","Ignore always"],
     "answer":"Type the official site yourself or open the official app","level":"intermediate"},

    # Advanced
    {"question":"What is spear phishing?",
     "options":["Highly targeted phishing aimed at specific people or roles","Random spam to millions","SMS-only scams","A harmless internal test"],
     "answer":"Highly targeted phishing aimed at specific people or roles","level":"advanced"},
    {"question":"Business Email Compromise often tries to:",
     "options":["Request urgent payments or change banking details","Improve email deliverability","Send safe newsletters","Schedule meetings"],
     "answer":"Request urgent payments or change banking details","level":"advanced"},
    {"question":"Credential harvesting uses:",
     "options":["Fake login pages to collect usernames and passwords","Only phone calls","Physical mail","Verified portals"],
     "answer":"Fake login pages to collect usernames and passwords","level":"advanced"},
    {"question":"A fake security popup asking you to call a number is likely:",
     "options":["A scam to gain payment or remote access","AWindows update","Your antivirus support","A trusted alert from your ISP"],
     "answer":"A scam to gain payment or remote access","level":"advanced"}
]

# AI helper (OpenAI optional) — safe fallback to simple tips
def ai_summary(text: str) -> str:
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
        tips = [
            "Watch for urgency, odd sender domains, and unexpected attachments.",
            "Hover links to preview URLs. Real services do not ask for passwords or codes via messages.",
            "Verify using official apps or websites and report suspicious messages."
        ]
        return random.choice(tips)

def save_result(email, score, total, level, mode):
    if not supabase:
        return
    try:
        supabase.table("simulation_results").insert({
            "email": email or "guest@demo",
            "score": score, "total": total,
            "level": level, "mode": mode,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
    except Exception:
        pass  # silent fail so users don't see errors

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
    Build a short explanation for an item using AI or fallback tips.
    """
    correct = item.get("answer", "Safe")
    channel = item.get("channel", "email")
    short = f"Channel: {channel}\nSender: {item.get('sender','(unknown)')}\nSubject/Title: {item.get('subject','-')}\nMessage: {item.get('message','-')}"
    prompt = f"The learner classified a scenario as '{picked}', but it is actually '{correct}'.\n\n{short}\n\nGive 3 short bullet points in simple English: 1) why it's {correct} 2) what clues to watch for 3) what to do."
    return ai_summary(prompt)

# -----------------------------
# Session State defaults
# -----------------------------
if "user_email" not in st.session_state:
    st.session_state.user_email = None

if "level" not in st.session_state:
    st.session_state.level = "Beginner"

if "learn_done" not in st.session_state:
    st.session_state.learn_done = {"Beginner": False, "Intermediate": False, "Advanced": False}

if "game" not in st.session_state:
    st.session_state.game = {"bank": [], "index": 0, "score": 0, "stars": 0, "finished": False, "feedback": None}

# -----------------------------
# Auth UI
# -----------------------------
def login_ui():
    st.subheader("🔐 Log in")
    email = st.text_input("Email", key="login_email")
    pwd   = st.text_input("Password", type="password", key="login_pwd")
    if st.button("Login", use_container_width=True):
        if not supabase:
            st.error("Login currently unavailable (Supabase not configured).")
            return
        try:
            res = supabase.auth.sign_in_with_password({"email": email, "password": pwd})
            st.session_state.user_email = getattr(res.user, "email", email)
            st.success(f"Welcome back, {st.session_state.user_email}!")
        except Exception:
            st.error("Login failed. Please check credentials or try later.")

def signup_ui():
    st.subheader("✨ Create account")
    email = st.text_input("New email", key="signup_email")
    pwd   = st.text_input("Create password", type="password", key="signup_pwd")
    if st.button("Sign Up", use_container_width=True):
        if not supabase:
            st.error("Sign-up currently unavailable (Supabase not configured).")
            return
        try:
            supabase.auth.sign_up({"email": email, "password": pwd})
            st.success("Account created! Verify your email before logging in.")
        except Exception:
            st.error("Sign-up failed. Try again with a different email.")

# -----------------------------
# Content builders & bank
# -----------------------------
def load_lessons(level):
    # prefer files if present, otherwise fallback to defaults embedded in code
    if level == "Beginner":
        return load_json("content/cards_beginner.json", default=None) or [
            {"title":"What is Phishing?","content":"Phishing is a social engineering attack where a fake message pretends to be from a trusted organization to steal information or trick you into installing malware."},
            {"title":"Common Phishing Clues","content":"Urgent language, poor spelling, unknown senders, unexpected attachments, and suspicious links."},
            {"title":"Links & Fake Websites","content":"Hover links to reveal the real URL; watch for look-alike domains such as paypa1.com."},
            {"title":"Attachments & Information Requests","content":"Never share passwords or OTPs. Unexpected files (ZIP, EXE, HTML) can be dangerous."}
        ]
    elif level == "Intermediate":
        return load_json("content/cards_intermediate.json", default=None) or [
            {"title":"Look-Alike Domains & Spoofed Senders","content":"Attackers register domains that look similar and spoof display names; always check the real sender address."},
            {"title":"Fake HR & Payroll Messages","content":"Messages pretending to be HR may ask for bank details or forms—verify via official portals."},
            {"title":"Malicious Attachments in Realistic Messages","content":"Professional-looking messages may include malware-laden attachments like .zip or .exe."},
            {"title":"Multi-Channel Phishing","content":"Attacks can combine email, SMS, and phone calls to build credibility—never share OTPs."},
            {"title":"Verify Before You Act","content":"Pause and verify using official websites or known phone numbers before acting on unusual requests."}
        ]
    else:
        return load_json("content/cards_advanced.json", default=None) or [
            {"title":"Spear Phishing","content":"Highly targeted attacks using personal or company information to appear legitimate."},
            {"title":"Business Email Compromise","content":"Attackers impersonate executives or vendors to request urgent payments or change bank details."},
            {"title":"Credential Harvesting & Fake Login Pages","content":"Fake login portals capture credentials—always type the official URL in your browser."},
            {"title":"Fake 'Your Device Has a Virus' Popups","content":"These popups often trick users into calling scammers or installing remote access tools."},
            {"title":"Report & Escalate","content":"Report suspicious messages to IT/security and help improve filters."}
        ]

def build_bank_for_level(level):
    """
    Build a mixed bank of multi-channel scenarios and quiz items for the chosen level.
    Uses actual content/simulation.json and quizzes/main.json if present, otherwise falls back to DEFAULT_* lists.
    """
    level_map = {"Beginner":"beginner","Intermediate":"intermediate","Advanced":"advanced"}
    want_lvl = level_map.get(level, level).lower()

    bank = []

    # Load scenarios file if available, else use default list
    emails = load_json("content/simulation.json", default=None) or DEFAULT_SIMULATIONS

    # Filter scenarios by level (if 'level' key exists in items) OR split into thirds otherwise
    labelled = any(bool(e.get("level")) for e in emails)
    if labelled:
        for em in emails:
            el = (em.get("level") or "").lower()
            if el and want_lvl in el:
                # normalize fields
                channel = em.get("channel","email").lower()
                subj = em.get("subject","")
                sender = em.get("sender") or em.get("from") or ""
                message = em.get("message") or em.get("body") or ""
                is_phish = bool(em.get("is_phishing") or (em.get("label")=="Phishing"))
                bank.append({"type":"scenario","channel":channel,"subject":subj,"sender":sender,"message":message,"answer":"Phishing" if is_phish else "Safe"})
    else:
        # split by index three-way
        n = len(emails)
        third = max(1, n // 3)
        for i, em in enumerate(emails):
            include = False
            if level == "Beginner" and i < third:
                include = True
            elif level == "Intermediate" and third <= i < 2*third:
                include = True
            elif level == "Advanced" and i >= 2*third:
                include = True
            if include:
                channel = em.get("channel","email").lower()
                subj = em.get("subject","")
                sender = em.get("sender") or em.get("from") or ""
                message = em.get("message") or em.get("body") or ""
                is_phish = bool(em.get("is_phishing") or (em.get("label")=="Phishing"))
                bank.append({"type":"scenario","channel":channel,"subject":subj,"sender":sender,"message":message,"answer":"Phishing" if is_phish else "Safe"})

    # Load quiz file if present, else use default quizzes
    quiz = load_json("quizzes/main.json", default=None) or DEFAULT_QUIZZES
    labelled_q = any(bool(q.get("level")) for q in quiz)
    if labelled_q:
        for q in quiz:
            ql = (q.get("level") or "").lower()
            if ql and want_lvl in ql:
                bank.append({"type":"quiz","question": q.get("question","Untitled"),"options": q.get("options",[]),"answer": q.get("answer")})
    else:
        # three-way split of quiz list
        n_q = len(quiz)
        third_q = max(1, n_q // 3)
        for j, q in enumerate(quiz):
            include = False
            if level == "Beginner" and j < third_q:
                include = True
            elif level == "Intermediate" and third_q <= j < 2*third_q:
                include = True
            elif level == "Advanced" and j >= 2*third_q:
                include = True
            if include:
                bank.append({"type":"quiz","question": q.get("question","Untitled"),"options": q.get("options",[]),"answer": q.get("answer")})

    random.shuffle(bank)
    return bank

def reset_game(level):
    st.session_state.game = {"bank": build_bank_for_level(level), "index":0, "score":0, "stars":0, "finished":False, "feedback": None}

# -----------------------------
# Pages
# -----------------------------
def page_home():
    st.title("🎣 THAT'S PHISHY")
    st.caption("Interactive, gamified phishing awareness across email, SMS, WhatsApp, and fake virus popups.")
    if st.session_state.user_email:
        st.success(f"Signed in as {st.session_state.user_email}")
    else:
        st.info("You’re playing as guest. Results saved locally (and to Supabase if configured).")

def page_learn(level):
    st.header(f"📚 Learn — {level}")
    lessons = load_lessons(level)
    for c in lessons:
        with st.expander(c.get("title","Untitled")):
            st.write(c.get("content","No details."))
    st.markdown("<span class='badge'>Complete this section to unlock the game</span>", unsafe_allow_html=True)
    if st.button("✅ Mark Learn as Complete", use_container_width=True):
        st.session_state.learn_done[level] = True
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
    idx = game["index"]

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

        summary_prompt = (
            f"User finished a phishing training ({level}) with score {score}/{total}. "
            "Give 3 short, encouraging improvement tips aligned with common phishing red flags."
        )
        st.info(ai_summary(summary_prompt))
        save_result(st.session_state.user_email, score, total, level, mode="game")

        col1, col2 = st.columns(2)
        if col1.button("🔁 Play Again", use_container_width=True):
            reset_game(level); st.rerun()
        if col2.button("➡️ Next Section", use_container_width=True):
            if level == "Beginner":
                st.session_state.level = "Intermediate"
            elif level == "Intermediate":
                st.session_state.level = "Advanced"
            st.rerun()
        return

    st.write(f"**Scenario {idx+1} of {len(bank)}**")
    st.progress((idx + 1) / len(bank))
    st.markdown(f"<div class='starline'>{star_bar(min(game['stars'],10))}</div>", unsafe_allow_html=True)

    # If feedback present, show and wait for Next
    if game["feedback"] is not None:
        fb = game["feedback"]
        if fb.get("correct"):
            st.success(fb.get("message", "Correct! ⭐"))
        else:
            st.error(fb.get("message", "Not quite."))

        if fb.get("explanation"):
            st.markdown("### 🧠 Scenario Breakdown")
            st.write(fb.get("explanation"))

        if st.button("➡️ Next Scenario", use_container_width=True):
            game["index"] += 1
            game["feedback"] = None
            st.session_state.game = game
            st.rerun()
        return

    # Present current item
    item = bank[idx]

    if item["type"] == "scenario":
        ch = item.get("channel","email")
        if ch == "email":
            st.markdown("### 📧 Email Scenario")
            if item.get("sender"): st.write(f"**From:** {item['sender']}")
            if item.get("subject"): st.write(f"**Subject:** {item['subject']}")
            st.write(item.get("message",""))
        elif ch == "sms":
            st.markdown("### 📱 SMS Scenario")
            if item.get("sender"): st.write(f"**From:** {item['sender']}")
            st.write(item.get("message",""))
        elif ch == "whatsapp":
            st.markdown("### 💬 WhatsApp Scenario")
            if item.get("sender"): st.write(f"**From:** {item['sender']}")
            st.write(item.get("message",""))
        elif ch == "popup":
            st.markdown("### 🖥️ Security / Virus Alert Scenario")
            if item.get("subject"): st.write(f"**Title:** {item['subject']}")
            st.write(item.get("message",""))
        else:
            st.markdown("### 📘 Message Scenario")
            st.write(item.get("message",""))

        try:
            picked = st.radio("How would you classify this?", ["Phishing","Safe"], key=f"scenario_{idx}", index=None)
        except TypeError:
            picked = st.radio("How would you classify this?", ["Phishing","Safe"], key=f"scenario_{idx}")

        col1, col2 = st.columns(2)
        if col1.button("✅ Submit", use_container_width=True):
            if picked is None:
                st.warning("Please choose Phishing or Safe before submitting.")
            else:
                correct = item.get("answer","Safe")
                is_correct = (picked == correct)
                if is_correct:
                    msg = f"Correct! ⭐ This scenario is {correct}."
                    game["score"] += 1; game["stars"] += 1
                else:
                    msg = f"Not quite. This scenario is actually {correct}."
                explanation = explain_scenario(item, picked)
                game["feedback"] = {"correct": is_correct, "message": msg, "explanation": explanation}
                st.session_state.game = game
                st.rerun()
        if col2.button("⏭️ Skip Scenario", use_container_width=True):
            game["index"] += 1; st.session_state.game = game; st.rerun()

    elif item["type"] == "quiz":
        st.subheader("🧠 Knowledge Check")
        st.write(item.get("question",""))
        opts = item.get("options",[])
        ans = item.get("answer")
        if not opts or not ans:
            st.warning("This quiz item is incomplete; skipping.")
            game["index"] += 1; st.session_state.game = game; st.rerun(); return
        try:
            choice = st.radio("Select the best answer:", opts, key=f"quiz_{idx}", index=None)
        except TypeError:
            choice = st.radio("Select the best answer:", opts, key=f"quiz_{idx}")
        col1, col2 = st.columns(2)
        if col1.button("✅ Submit Answer", use_container_width=True):
            if choice is None:
                st.warning("Please select an answer first.")
            else:
                is_correct = (choice == ans)
                if is_correct:
                    msg = "Correct! ⭐"; game["score"] += 1; game["stars"] += 1
                else:
                    msg = f"Oops! The correct answer is: **{ans}**"
                game["feedback"] = {"correct": is_correct, "message": msg, "explanation": None}
                st.session_state.game = game
                st.rerun()
        if col2.button("⏭️ Skip Question", use_container_width=True):
            game["index"] += 1; st.session_state.game = game; st.rerun()

def page_results():
    st.header("📈 Your Results")
    who = st.session_state.user_email or "guest@demo"
    if not supabase:
        st.info("Results are stored locally in this session. Configure Supabase to save them remotely.")
        return
    try:
        q = supabase.table("simulation_results").select("*").eq("email", who).order("created_at", desc=True).execute()
        rows = getattr(q, "data", []) or []
        if not rows:
            st.info("No results yet. Complete Learn + THAT'S PHISHY to see your progress here.")
            return
        for r in rows[:12]:
            when = r.get("created_at","—")
            st.write(f"• **{when}** — {r.get('level','?')} — Score: **{r.get('score','?')}/{r.get('total','?')}** ({r.get('mode','game')})")
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
            if supabase:
                try: supabase.auth.sign_out()
                except Exception: pass
            st.session_state.user_email = None; st.rerun()
    else:
        t1, t2 = st.tabs(["Login","Sign Up"])
        with t1: login_ui()
        with t2: signup_ui()

# -----------------------------
# Sidebar Navigation (user requested)
# -----------------------------
st.sidebar.title("🌐 Navigation")
st.sidebar.selectbox("Difficulty level", ["Beginner","Intermediate","Advanced"], key="level")

if st.session_state.user_email:
    st.sidebar.caption(f"Signed in: {st.session_state.user_email}")
else:
    st.sidebar.caption("Signed in: guest (results saved as guest@demo)")

# Changed per request: remove "Phishy or Safe?" label and use neutral 'Go to:' label
page = st.sidebar.radio("Go to:", ["Home", "Learn", "THAT'S PHISHY", "Results", "AI Assistant", "Account"])

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
