# =========================================================
# CYBERSECURITY AWARENESS SYSTEM & THREAT SIMULATOR
# Final integrated version — Streamlit + Supabase + OpenAI
# Author: Layla
# =========================================================

import streamlit as st
import json
from datetime import datetime
from supabase import create_client
import openai

# ---------------------------------------------------------
# PAGE CONFIG
# ---------------------------------------------------------
st.set_page_config(
    page_title="Cybersecurity Awareness & Threat Simulator",
    page_icon="🛡️",
    layout="wide",
)

# ---------------------------------------------------------
# LOAD SECRETS SAFELY
# ---------------------------------------------------------
# Your Streamlit -> Settings -> Secrets MUST look like:
# [supabase]
# url = "https://flrvzxeypjzbfbftyrit.supabase.co"
# key = "your anon key here"
#
# [openai]
# api_key = "sk-proj-....your key...."
#
# DO NOT change the key names below unless you also change secrets.
try:
    SUPABASE_URL = st.secrets["supabase"]["url"]
    SUPABASE_KEY = st.secrets["supabase"]["key"]
    OPENAI_API_KEY = st.secrets["openai"]["api_key"]
except KeyError as e:
    st.error(f"Missing key in Streamlit secrets: {e}")
    st.stop()

# ---------------------------------------------------------
# INIT CLIENTS
# ---------------------------------------------------------
try:
    supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
except Exception as e:
    st.error(f"Failed to connect to Supabase: {e}")
    st.stop()

try:
    openai.api_key = OPENAI_API_KEY
except Exception as e:
    st.error(f"Failed to configure OpenAI: {e}")
    st.stop()

# ---------------------------------------------------------
# SMALL HELPERS
# ---------------------------------------------------------
def load_json(file_path: str):
    """
    Safely load static JSON content (lessons, quiz data, simulation emails).
    Returns [] if file missing or invalid, instead of crashing the app.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.warning(f"⚠️ Missing file: {file_path}")
        return []
    except json.JSONDecodeError:
        st.error(f"❌ Invalid JSON format in {file_path}")
        return []

def go(page_name: str):
    """Update which page should render."""
    st.session_state["page"] = page_name

def require_auth():
    """Block access if user not logged in."""
    if "user" not in st.session_state or not st.session_state["user"]:
        st.warning("🔐 Please log in to access this section.")
        login_page(show_only_login=True)
        st.stop()

def current_user_id():
    """Return the logged-in user's UUID (or None)."""
    if "user" in st.session_state and st.session_state["user"]:
        return st.session_state["user"].id
    return None

# ---------------------------------------------------------
# AI SUPPORT
# ---------------------------------------------------------
def get_ai_feedback(prompt_text: str):
    """
    Ask OpenAI to generate personalized cybersecurity guidance.
    Used after quiz/simulation AND in the AI Assistant page.
    """
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",  # model choice for cost/speed
            messages=[
                {
                    "role": "system",
                    "content": (
                        "You are a friendly, practical cybersecurity mentor. "
                        "You explain phishing and online safety in simple, non-scary language. "
                        "You give short, direct tips and examples."
                    ),
                },
                {
                    "role": "user",
                    "content": prompt_text,
                },
            ],
            max_tokens=220,
            temperature=0.7,
        )
        return response["choices"][0]["message"]["content"]
    except Exception as e:
        st.error(f"AI error: {e}")
        return None

# ---------------------------------------------------------
# SUPABASE WRITE HELPERS
# ---------------------------------------------------------
def create_profile_if_needed(user_id: str, full_name: str = ""):
    """
    We try to insert a profile row for this user.
    If it already exists (duplicate key), we silently ignore.
    """
    if not user_id:
        return
    try:
        supabase.table("profiles").insert({
            "id": user_id,
            "full_name": full_name,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        st.info("Profile created ✅")
    except Exception:
        # Most common failure case: row already exists (PRIMARY KEY conflict)
        # or RLS timing if email not verified yet.
        pass

def save_quiz_result(score: int, total_q: int, stars: int):
    """
    Save user's quiz performance into quiz_results.
    Assumes RLS is configured to allow insert where auth.uid() = user_id.
    """
    uid = current_user_id()
    if not uid:
        st.warning("You must be logged in to save your quiz results.")
        return
    try:
        supabase.table("quiz_results").insert({
            "user_id": uid,
            "score": score,
            "total_questions": total_q,
            "stars_earned": stars,
            "date_taken": datetime.utcnow().isoformat()
        }).execute()
        st.success("✅ Quiz results saved.")
    except Exception as e:
        st.error(f"Error saving quiz results: {e}")

def save_simulation_result(correct: int, total: int, difficulty: str, stars: int):
    """
    Save user's simulation performance into simulation_results.
    """
    uid = current_user_id()
    if not uid:
        st.warning("You must be logged in to save your simulation results.")
        return
    try:
        supabase.table("simulation_results").insert({
            "user_id": uid,
            "correct": correct,
            "total": total,
            "difficulty": difficulty,
            "stars_earned": stars,
            "date_taken": datetime.utcnow().isoformat()
        }).execute()
        st.success("✅ Simulation results saved.")
    except Exception as e:
        st.error(f"Error saving simulation results: {e}")

# ---------------------------------------------------------
# AUTH / ACCOUNT PAGE
# ---------------------------------------------------------
def login_page(show_only_login=False):
    """
    Sign Up + Login page.
    If show_only_login=True, only show Login tab (used when blocking access).
    """
    st.header("🔐 Account Access")

    if show_only_login:
        tabs = [("Login", True)]
    else:
        tabs = [("Login", True), ("Sign Up", False)]

    # mimic tabs manually, more control
    active_tab = st.radio(
        "Select",
        [label for label, _ in tabs],
        horizontal=True,
        key="auth_tab_choice"
    )

    if active_tab == "Login":
        st.subheader("Log In")
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login", key="login_button"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state["user"] = res.user
                st.success(f"✅ Welcome back, {res.user.email}!")
                go("Home")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

    else:
        st.subheader("Create Account")
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_password")
        full_name = st.text_input("Your Name (optional)", key="signup_name")

        st.caption(
            "After sign-up you'll get a verification link by email. "
            "You must verify before logging in."
        )

        if st.button("Sign Up", key="signup_button"):
            try:
                res = supabase.auth.sign_up({"email": email, "password": password})

                st.success("🎉 Account created! Please check your email to verify before logging in.")

                # We TRY to create profile now.
                # If email not verified yet, RLS/foreign key might block it.
                # That's okay — there's also a DB trigger we set on auth.users
                # that will insert into profiles after verification.
                if getattr(res, "user", None):
                    create_profile_if_needed(
                        user_id=res.user.id,
                        full_name=full_name.strip()
                    )
            except Exception as e:
                st.error(f"Sign-up failed: {e}")

    st.info(
        "⚠️ If you see 'email not confirmed' or redirect issues, make sure your Supabase "
        "Auth 'Site URL' and 'Redirect URLs' are set to your Streamlit app URL, "
        "and that email signups + confirmations are enabled."
    )

# ---------------------------------------------------------
# PAGE: HOME
# ---------------------------------------------------------
def home_section():
    st.header("🏠 Cybersecurity Awareness & Threat Simulator")
    st.write(
        """
        Welcome to the Cybersecurity Awareness & Threat Simulator.

        This platform helps you:
        • Understand what phishing is and how it works  
        • Practice spotting fake / malicious emails  
        • Take quizzes to test your awareness  
        • See your personal progress over time  
        • Chat with an AI cybersecurity assistant for safety tips
        """
    )

    st.success(
        "Tip: Start with **Learn** to unlock the **Quiz**. "
        "Then try **Simulate** to test yourself with real-style phishing emails."
    )

# ---------------------------------------------------------
# PAGE: LEARN
# ---------------------------------------------------------
def learn_section():
    st.header("📚 Learn the Basics")

    st.info(
        "Below are short lessons explaining phishing, common tricks, and how to protect yourself. "
        "Read through them to unlock the quiz."
    )

    lessons = load_json("content/cards_basic.json")
    if not lessons:
        st.warning("⚠️ No learning cards found. (content/cards_basic.json)")
        return

    for card in lessons:
        title = card.get("title", "Untitled Topic")
        body = card.get("content", "No details yet.")
        with st.expander(title):
            st.write(body)

    st.success("✅ Nice! You've viewed the learning content.")
    st.session_state["learn_viewed"] = True

# ---------------------------------------------------------
# PAGE: QUIZ
# ---------------------------------------------------------
def quiz_section():
    require_auth()

    # gate: must have viewed Learn first
    if not st.session_state.get("learn_viewed", False):
        st.header("🔒 Quiz Locked")
        st.info("Please complete the Learn section before attempting the quiz.")
        if st.button("Go to Learn"):
            go("Learn")
            st.rerun()
        st.stop()

    st.header("🧠 Phishing Awareness Quiz")
    st.caption("Answer all questions and earn stars for correct answers.")

    quiz_data = load_json("quizzes/main.json")
    if not quiz_data:
        st.warning("⚠️ No quiz data found. (quizzes/main.json)")
        return

    # We'll track answers in this run only (not across reruns)
    # It's fine for MVP/demo.
    score = 0
    for q in quiz_data:
        qid = q.get("id", "")
        question = q.get("question", "Untitled Question")
        options = q.get("options", [])
        answer = q.get("answer", "")

        st.subheader(question)
        choice = st.radio(
            "Choose one:",
            options,
            index=None,
            key=f"quiz_q_{qid}"
        )
        st.write("")  # spacing

        if choice == answer:
            score += 1

    if st.button("Submit Quiz", key="submit_quiz"):
        total_q = len(quiz_data)
        st.success(f"🎉 You got {score}/{total_q} correct!")
        stars = score  # 1 star per correct

        # save in Supabase
        save_quiz_result(score, total_q, stars)

        # AI feedback
        ai_text = get_ai_feedback(
            f"A learner scored {score} out of {total_q} on a phishing awareness quiz. "
            "Give supportive feedback, highlight one thing they did well, "
            "and explain one practical tip to get better at spotting phishing."
        )
        if ai_text:
            st.info(ai_text)

# ---------------------------------------------------------
# PAGE: SIMULATE
# ---------------------------------------------------------
def simulate_section():
    require_auth()

    st.header("📬 Phishing Simulation")
    st.write(
        "Below are mock emails. For each one, decide if it is 'Phishing' or 'Safe'. "
        "Trust your instincts, but also pay attention to sender, links, urgency, and tone."
    )

    sim_data = load_json("content/simulation.json")
    if not sim_data:
        st.warning("⚠️ No simulation emails found. (content/simulation.json)")
        return

    correct = 0
    total = len(sim_data)

    # We'll collect answers dynamically
    for email in sim_data:
        sim_id = email.get("id", "")
        subject = email.get("subject", "No Subject")
        body = email.get("body", "No body text.")
        is_phish = email.get("is_phishing", False)

        with st.expander(f"📧 {subject}"):
            st.write(body)
            guess = st.radio(
                "Is this email a phishing attempt?",
                ["Phishing", "Safe"],
                key=f"sim_{sim_id}"
            )

            # score logic
            if guess == "Phishing" and is_phish:
                correct += 1
            elif guess == "Safe" and not is_phish:
                correct += 1

    if st.button("Submit Responses", key="submit_sim"):
        st.success(f"✅ You identified {correct}/{total} emails correctly.")
        stars = correct  # 1 star per correct classification

        # save to Supabase
        save_simulation_result(correct, total, "Normal", stars)

        # AI feedback
        ai_text = get_ai_feedback(
            f"A learner correctly identified {correct} out of {total} simulated phishing emails. "
            "Give a short analysis of what that means and one realistic next step they should take "
            "to improve their ability to spot scams in real life."
        )
        if ai_text:
            st.info(ai_text)

# ---------------------------------------------------------
# PAGE: RESULTS / DASHBOARD
# ---------------------------------------------------------
def results_section():
    require_auth()

    st.header("📈 Your Progress")
    st.caption("These stats are private to you. We only ever show your own data.")

    uid = current_user_id()
    if not uid:
        st.error("No authenticated user ID found.")
        st.stop()

    # Pull quiz history
    try:
        quiz_resp = supabase.table("quiz_results").select("*").eq("user_id", uid).execute()
        quiz_rows = quiz_resp.data if hasattr(quiz_resp, "data") else []
    except Exception as e:
        quiz_rows = []
        st.error(f"Couldn't load quiz results: {e}")

    # Pull simulation history
    try:
        sim_resp = supabase.table("simulation_results").select("*").eq("user_id", uid).execute()
        sim_rows = sim_resp.data if hasattr(sim_resp, "data") else []
    except Exception as e:
        sim_rows = []
        st.error(f"Couldn't load simulation results: {e}")

    # Compute summary
    total_quizzes = len(quiz_rows)
    total_sims = len(sim_rows)
    if total_quizzes > 0:
        avg_score_raw = sum([r["score"] for r in quiz_rows]) / total_quizzes
        # Convert to percentage of correct answers
        avg_pct = []
        for r in quiz_rows:
            if r["total_questions"]:
                pct = (r["score"] / r["total_questions"]) * 100.0
                avg_pct.append(pct)
        avg_score_pct = round(sum(avg_pct) / len(avg_pct), 2) if avg_pct else 0.0
    else:
        avg_score_raw = 0
        avg_score_pct = 0.0

    col1, col2, col3 = st.columns(3)
    col1.metric("Total Quizzes Completed", total_quizzes)
    col2.metric("Avg Quiz Score %", f"{avg_score_pct}%")
    col3.metric("Simulations Attempted", total_sims)

    st.write("---")

    st.subheader("📝 Recent Quiz Attempts")
    if quiz_rows:
        for row in sorted(quiz_rows, key=lambda r: r["date_taken"], reverse=True)[:5]:
            ts = row["date_taken"]
            st.write(
                f"- {ts}: {row['score']}/{row['total_questions']} correct "
                f"({row['stars_earned']} ⭐)"
            )
    else:
        st.write("No quiz attempts yet.")

    st.subheader("📬 Recent Simulation Attempts")
    if sim_rows:
        for row in sorted(sim_rows, key=lambda r: r["date_taken"], reverse=True)[:5]:
            ts = row["date_taken"]
            st.write(
                f"- {ts}: {row['correct']}/{row['total']} emails identified "
                f"({row['stars_earned']} ⭐)"
            )
    else:
        st.write("No simulation attempts yet.")

# ---------------------------------------------------------
# PAGE: AI ASSISTANT
# ---------------------------------------------------------
def ai_assistant_section():
    """
    This page is a simple 'Ask the cybersecurity coach' chat.
    User types a question, AI responds.
    """
    require_auth()

    st.header("🤖 AI Cyber Coach")
    st.write(
        "Ask anything about phishing, suspicious messages, password safety, "
        "scams, fake login pages, social engineering, etc."
    )

    user_q = st.text_area(
        "Your question:",
        placeholder="Example: How do I know if a link is safe before I click it?",
        key="ai_user_q"
    )

    if st.button("Ask AI", key="ask_ai_btn"):
        if not user_q.strip():
            st.warning("Please type a question first.")
        else:
            with st.spinner("Thinking..."):
                reply = get_ai_feedback(
                    "User cybersecurity question: " + user_q.strip() +
                    "\nGive a clear, calm, real-world answer for a non-technical person."
                )
            if reply:
                st.success("AI Coach says:")
                st.write(reply)

    st.info("Note: This AI cannot see your passwords, inbox, or personal data. It only sees what you type here.")

# ---------------------------------------------------------
# SIDEBAR NAVIGATION & STATE
# ---------------------------------------------------------
PAGES = {
    "Home": home_section,
    "Learn": learn_section,
    "Quiz": quiz_section,
    "Simulate": simulate_section,
    "Results": results_section,
    "AI Assistant": ai_assistant_section,
    "Account": login_page,
}

if "page" not in st.session_state:
    st.session_state["page"] = "Home"

st.sidebar.title("🌐 Navigation")
choice = st.sidebar.radio(
    "Go to page:",
    list(PAGES.keys()),
    index=list(PAGES.keys()).index(st.session_state["page"]),
)
st.session_state["page"] = choice

# show who's logged in + logout button
if "user" in st.session_state and st.session_state["user"]:
    user_email = st.session_state["user"].email
    st.sidebar.caption(f"👤 Logged in as: {user_email}")

    if st.sidebar.button("🚪 Log Out"):
        try:
            supabase.auth.sign_out()
        except Exception:
            pass
        st.session_state["user"] = None
        st.success("You’ve been logged out.")
        st.rerun()
else:
    st.sidebar.caption("Not signed in")
    st.sidebar.write("Go to **Account** to Sign Up / Log In.")

st.sidebar.write("---")
st.sidebar.success("If you see this app, deployment is working ✅")

# ---------------------------------------------------------
# RENDER CURRENT PAGE
# ---------------------------------------------------------
PAGES[choice]()


