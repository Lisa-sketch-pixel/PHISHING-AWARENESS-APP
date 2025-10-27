import streamlit as st
from supabase import create_client
from datetime import datetime
import json
import os
from openai import OpenAI

# ==============================
# 1️⃣  Load Secrets
# ==============================
SUPABASE_URL = st.secrets["supabase"]["url"]
SUPABASE_KEY = st.secrets["supabase"]["key"]
OPENAI_KEY = st.secrets["openai"]["api_key"]

supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
client = OpenAI(api_key=OPENAI_KEY)

# ==============================
# 2️⃣  Helper Functions
# ==============================
def load_json(path):
    try:
        with open(path, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        st.warning(f"⚠️ Missing or unreadable file: {path} — {e}")
        return []

def save_simulation_result(user_email, score, total):
    try:
        result = supabase.table("simulation_results").insert({
            "email": user_email,
            "score": score,
            "total": total,
            "created_at": datetime.utcnow().isoformat()
        }).execute()
        if result.data:
            st.success("✅ Simulation results saved successfully!")
        else:
            st.warning("⚠️ Unable to save results (check Supabase policy).")
    except Exception as e:
        st.error(f"Error saving simulation results: {e}")

def generate_ai_response(prompt):
    try:
        completion = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful cybersecurity tutor."},
                {"role": "user", "content": prompt}
            ]
        )
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"AI error: {e}")
        return None

# ==============================
# 3️⃣  Navigation Setup
# ==============================
st.sidebar.title("🌐 Navigation")
menu = st.sidebar.radio("Go to page:", ["Home", "Learn", "Quiz", "Simulate", "Results", "AI Assistant", "Account"])

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user" not in st.session_state:
    st.session_state.user = None

# ==============================
# 4️⃣  Authentication
# ==============================
if not st.session_state.logged_in:
    st.title("🔐 Login / Sign Up")
    tabs = st.tabs(["Login", "Sign Up"])

    with tabs[0]:
        email = st.text_input("Email")
        password = st.text_input("Password", type="password")
        if st.button("Login"):
            try:
                user = supabase.auth.sign_in_with_password({
                    "email": email,
                    "password": password
                })
                st.session_state.logged_in = True
                st.session_state.user = email
                st.success(f"Welcome back, {email}!")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

    with tabs[1]:
        new_email = st.text_input("New Email")
        new_password = st.text_input("Create Password", type="password")
        if st.button("Create Account"):
            try:
                user = supabase.auth.sign_up({
                    "email": new_email,
                    "password": new_password
                })
                st.success("🎉 Account created! Please verify your email before logging in.")
            except Exception as e:
                st.error(f"Sign-up failed: {e}")
    st.stop()

# ==============================
# 5️⃣  Main Pages
# ==============================
st.sidebar.markdown(f"**Logged in as:** {st.session_state.user}")
if st.sidebar.button("🚪 Log Out"):
    st.session_state.logged_in = False
    st.session_state.user = None
    st.experimental_rerun()

# ------------------------------
# 🏠 Home
# ------------------------------
if menu == "Home":
    st.title("🏠 Cybersecurity Awareness System")
    st.write("Welcome to your Phishing Awareness & Threat Simulation App!")
    st.info("Use the sidebar to navigate between learning, simulations, and AI support.")

# ------------------------------
# 📘 Learn
# ------------------------------
elif menu == "Learn":
    st.title("📚 Learn the Basics")

    st.info("Below are lessons explaining phishing tricks and how to stay safe online.")
    basic_cards = load_json("content/cards_basic.json")
    adv_cards = load_json("content/cards_advanced.json")

    with st.expander("🔹 Basic Lessons"):
        for card in basic_cards:
            st.subheader(card.get("title", "No Title"))
            st.write(card.get("content", "No details yet."))

    with st.expander("🔸 Advanced Lessons"):
        for card in adv_cards:
            st.subheader(card.get("title", "No Title"))
            st.write(card.get("content", "No details yet."))

# ------------------------------
# 🧠 Quiz
# ------------------------------
elif menu == "Quiz":
    st.title("🧩 Phishing Awareness Quiz")
    quiz_data = load_json("quizzes/main.json")

    if quiz_data:
        score = 0
        for i, q in enumerate(quiz_data):
            st.markdown(f"**Q{i+1}. {q['question']}**")
            answer = st.radio("", q["options"], key=f"quiz_{i}")
            if answer == q["answer"]:
                score += 1
        if st.button("Submit Quiz"):
            st.success(f"✅ You got {score}/{len(quiz_data)} correct!")
    else:
        st.warning("⚠️ No quiz data found!")

# ------------------------------
# ✉️ Simulate
# ------------------------------
elif menu == "Simulate":
    st.title("📨 Phishing Simulation")
    st.write("Below are mock emails. Identify if each is Phishing or Safe.")

    sim_data = load_json("content/sim_templates.json")
    if sim_data:
        user_answers = {}
        for i, mail in enumerate(sim_data):
            st.markdown(f"**Email {i+1}:** {mail['text']}")
            choice = st.radio(f"Is this email a phishing attempt?", ["Phishing", "Safe"], key=f"sim_{i}")
            user_answers[i] = (choice == "Phishing")

        if st.button("Submit Responses"):
            correct = sum(1 for i, mail in enumerate(sim_data)
                          if user_answers[i] == (mail["label"] == "Phishing"))
            st.success(f"✅ You identified {correct}/{len(sim_data)} emails correctly!")
            save_simulation_result(st.session_state.user, correct, len(sim_data))
    else:
        st.warning("⚠️ Missing simulation templates in 'content/sim_templates.json'.")

# ------------------------------
# 📊 Results
# ------------------------------
elif menu == "Results":
    st.title("📊 Your Progress")
    try:
        data = supabase.table("simulation_results").select("*").eq("email", st.session_state.user).execute()
        if data.data:
            for row in data.data:
                st.write(f"**Score:** {row['score']}/{row['total']} on {row['created_at']}")
        else:
            st.info("No simulation results found yet.")
    except Exception as e:
        st.error(f"Error loading results: {e}")

# ------------------------------
# 🤖 AI Assistant
# ------------------------------
elif menu == "AI Assistant":
    st.title("🤖 Cybersecurity AI Assistant")
    prompt = st.text_area("Ask the AI about phishing, cybersecurity, or best practices:")
    if st.button("Ask AI"):
        if prompt.strip():
            response = generate_ai_response(prompt)
            if response:
                st.markdown(f"**AI:** {response}")
        else:
            st.warning("Please enter a question.")

# ------------------------------
# ⚙️ Account
# ------------------------------
elif menu == "Account":
    st.title("👤 Account Settings")
    st.write(f"Email: {st.session_state.user}")
    st.info("Feature expansion coming soon!")
