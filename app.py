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
    """Load JSON file safely and handle missing files."""
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            return json.load(f)
    except FileNotFoundError:
        st.warning(f"⚠️ Missing file: {file_path}")
        return []
    except json.JSONDecodeError:
        st.error(f"❌ Invalid JSON format in {file_path}")
        return []

def go(page):
    """Simple navigation control."""
    st.session_state["page"] = page

def require_auth():
    """Ensure user is logged in before accessing private pages."""
    if "user" not in st.session_state or not st.session_state["user"]:
        st.warning("🔐 Please log in to access this section.")
        login_page()
        st.stop()

# ==========================
# Auth Pages
# ==========================
def login_page():
    st.title("🔐 Login / Sign Up")
    tab1, tab2 = st.tabs(["Login", "Sign Up"])

    # --- LOGIN TAB ---
    with tab1:
        email = st.text_input("Email", key="login_email")
        password = st.text_input("Password", type="password", key="login_password")
        if st.button("Login"):
            try:
                res = supabase.auth.sign_in_with_password({"email": email, "password": password})
                st.session_state["user"] = res.user
                st.success(f"✅ Welcome back, {res.user.email}!")
                go("Home")
                st.rerun()
            except Exception as e:
                st.error(f"Login failed: {e}")

    # --- SIGNUP TAB ---
    with tab2:
        email = st.text_input("New Email", key="signup_email")
        password = st.text_input("Create Password", type="password", key="signup_password")
        if st.button("Create Account"):
            try:
                supabase.auth.sign_up({"email": email, "password": password})
                st.success("🎉 Account created! Please check your email to verify before logging in.")
            except Exception as e:
                st.error(f"Sign-up failed: {e}")

# ==========================
# Content Pages
# ==========================
def home_section():
    st.title("🏠 Cybersecurity Awareness System & Threat Simulator")
    st.write(
        """
        Welcome to the Cybersecurity Awareness System & Threat Simulator!  
        Learn how to identify phishing threats, take quizzes, and test your instincts with real-life simulations.  
        """
    )
    st.info("Use the sidebar to explore sections like **Learn**, **Simulate**, and **Quiz**.")

def learn_section():
    st.title("📚 Learn About Phishing")
    st.info("Here you’ll learn the basics of phishing, red flags, and protection techniques.")

    basic_cards = load_json("content/cards_basic.json")

    if not basic_cards:
        st.warning("⚠️ No learning cards found. Please add content to content/cards_basic.json.")
        return

    for card in basic_cards:
        title = card.get("title", "Untitled Section")
        content = card.get("content", "No details available for this topic yet.")
        with st.expander(title):
            st.write(content)

    st.success("✅ You’ve completed the learning section!")
    st.session_state["learn_viewed"] = True

def quiz_section():
    require_auth()

    if not st.session_state.get("learn_viewed", False):
        st.title("🔒 Quiz Locked")
        st.info("Please complete the learning section before attempting the quiz.")
        if st.button("Go to Learn"):
            go("Learn")
            st.rerun()
        st.stop()

    st.title("🧠 Phishing Awareness Quiz")
    st.caption("Answer all questions carefully and earn stars for correct answers.")

    quiz = load_json("quizzes/main.json")
    if not quiz:
        st.warning("⚠️ No quiz data found. Please add content to quizzes/main.json.")
        return

    score = 0
    for q in quiz:
        question = q.get("question", "Untitled Question")
        options = q.get("options", [])
        answer = q.get("answer", "")
        st.subheader(question)
        choice = st.radio("Choose one:", options, index=None, key=f"quiz_{q.get('id', '')}")
        st.write("")
        if choice == answer:
            score += 1

    if st.button("Submit Quiz"):
        st.success(f"🎉 You got {score}/{len(quiz)} correct!")

def simulate_section():
    require_auth()
    st.title("📬 Phishing Simulation")
    st.write("Identify which emails look suspicious to test your instincts.")

    simulation_data = load_json("content/simulation.json")

    if not simulation_data:
        st.warning("⚠️ No simulation emails found. Please add content to content/simulation.json.")
        return

    for email in simulation_data:
        subject = email.get("subject", "No Subject")
        body = email.get("body", "No email content provided.")
        with st.expander(f"📧 {subject}"):
            st.write(body)
            choice = st.radio(
                "Is this email a phishing attempt?",
                ["Phishing", "Safe"],
                key=f"sim_{email.get('id', '')}"
            )
            st.write("")

    if st.button("Submit Responses"):
        st.success("✅ Simulation complete! Great job practicing your detection skills.")

def results_section():
    require_auth()
    st.title("📈 Your Progress & Results")
    st.write("Track your achievements, quiz scores, and completed simulations here.")
    st.metric("Total Quizzes Completed", "1")
    st.metric("Average Score", "80%")
    st.metric("Simulations Attempted", "2")

# ==========================
# Sidebar & Navigation
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

# --- User Info and Logout ---
if "user" in st.session_state and st.session_state["user"]:
    user_email = st.session_state["user"].email
    st.sidebar.caption(f"👤 Logged in as: {user_email}")
    if st.sidebar.button("🚪 Log Out"):
        supabase.auth.sign_out()
        st.session_state["user"] = None
        st.success("You’ve been logged out.")
        st.rerun()
else:
    st.sidebar.caption("Not signed in")

# --- Render the selected page ---
pages[page]()
