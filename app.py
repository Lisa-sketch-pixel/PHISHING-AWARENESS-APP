import streamlit as st
from supabase import create_client
import json

# ==========================
# Supabase Client Setup
# ==========================
url = st.secrets["supabase"]["url"]
key = st.secrets["supabase"]["anon_key"]
supabase = create_client(url, key)

# ==========================
# Helper Functions
# ==========================
def load_json(file_path):
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.error(f"File not found: {file_path}")
        return []

def require_auth():
    """Ensure user is logged in before accessing private pages"""
    if "user" not in st.session_state:
        st.warning("🔐 Please log in to continue.")
        login_page()
        st.stop()

def go(page):
    """Simple navigation control"""
    st.session_state["page"] = page

# ==========================
# Auth Pages
# ==========================
def login_page():
    st.title("🔐 Login / Sign Up")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_pass")
        if st.button("Login"):
            try:
                user = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state["user"] = user.user
                st.success("✅ Logged in successfully!")
                go("Home")
            except Exception as e:
                st.error(f"Login failed: {e}")

    with tab2:
        email = st.text_input("Email", key="signup_email")
        password = st.text_input("Password", type="password", key="signup_pass")
        if st.button("Create Account"):
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.success("🎉 Account created! Please check your email to verify.")
            except Exception as e:
                st.error(f"Sign-up failed: {e}")

# ==========================
# Pages
# ==========================

def home_section():
    st.title("🏠 Cybersecurity Awareness System & Threat Simulator")
    st.write(
        """
        Welcome to the Cybersecurity Awareness System & Threat Simulator!  
        Learn how to identify phishing threats, take quizzes, and test your instincts with real-life simulations.  
        """
    )

def learn_section():
    st.title("📚 Learn About Phishing")

    st.info("Here you’ll learn the basics of phishing, red flags, and protection techniques.")
    basic_cards = load_json("content/cards_basic.json")

    for card in basic_cards:
        with st.expander(card["title"]):
            st.write(card["content"])

    st.success("✅ You’ve completed the learning section!")

    if "learn_viewed" not in st.session_state:
        st.session_state["learn_viewed"] = True

def quiz_section():
    require_auth()

    if not st.session_state.get("learn_viewed", False):
        st.title("🔒 Quiz Locked")
        st.info("Visit **Learn** and click ***'I've reviewed the basics'*** to unlock the quiz.")
        if st.button("Go to Learn"):
            go("Learn")
        st.stop()

    st.title("🧠 Main Quiz")
    st.caption("Answer all questions, then submit for explanations. Correct answers earn ⭐.")

    quiz = load_json("quizzes/main.json")
    if not quiz:
        st.warning("⚠️ No quiz data found (quizzes/main.json).")
        return

    score = 0
    for q in quiz:
        st.subheader(q["question"])
        ans = st.radio("Choose one:", q["options"], index=None, key=f"ans_{q['id']}")
        st.write("")

        if ans == q["answer"]:
            score += 1

    if st.button("Submit Quiz"):
        st.success(f"🎉 You got {score}/{len(quiz)} correct!")

def simulate_section():
    require_auth()

    st.title("📬 Phishing Simulation")
    st.write(
        """
        In this simulation, you’ll see a mock inbox.  
        Identify which emails look suspicious or safe to practice detecting phishing attempts.
        """
    )

    simulation_data = load_json("content/simulation.json")

    for email in simulation_data:
        with st.expander(f"📧 {email['subject']}"):
            st.write(email["body"])
            choice = st.radio(
                "Is this a phishing email?",
                ["Phishing", "Safe"],
                key=f"sim_{email['id']}"
            )
            st.write("")

    if st.button("Submit Responses"):
        st.success("✅ Simulation complete! You’ll see detailed results soon.")

def results_section():
    require_auth()

    st.title("📈 Your Progress & Results")
    st.write("Track your progress, scores, and learning milestones here!")

    st.metric(label="Total Quizzes Completed", value="1")
    st.metric(label="Average Score", value="80%")
    st.metric(label="Simulations Attempted", value="2")

# ==========================
# Page Navigation
# ==========================
pages = {
    "Home": home_section,
    "Learn": learn_section,
    "Simulate": simulate_section,
    "Quiz": quiz_section,
    "Results": results_section,
}

if "page" not in st.session_state:
    st.session_state["page"] = "Home"

st.sidebar.title("🌐 Go to")
page = st.sidebar.radio("", list(pages.keys()), index=list(pages.keys()).index(st.session_state["page"]))
st.session_state["page"] = page

pages[page]()
