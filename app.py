import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="Phishing Awareness", page_icon="🛡️", layout="centered")

# -----------------------
# Session state helpers
# -----------------------
def init_state():
    defaults = {
        "learn_viewed": False,       # flipped to True after user opens at least 1 card
        "quiz_submitted": False,     # becomes True after quiz is submitted
        "quiz_score": 0,
        "quiz_total": 0,
        "badge_learner": False,
        "badge_quizzer": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# -----------------------
# Sidebar: navigation + progress
# -----------------------
st.sidebar.title("🧭 Navigation")
page = st.sidebar.radio("", ["Home", "Learn", "Quiz", "Results"])

# Simple progress calc
steps_done = int(st.session_state["learn_viewed"]) + int(st.session_state["quiz_submitted"])
st.sidebar.progress(steps_done/2)  # Learn (1/2), Quiz (2/2)

# Badges
with st.sidebar.expander("🏅 Badges"):
    st.write("• Beginner Learner ✅" if st.session_state["badge_learner"] else "• Beginner Learner ⬜")
    st.write("• Quiz Challenger ✅" if st.session_state["badge_quizzer"] else "• Quiz Challenger ⬜")


# -----------------------
# Utilities
# -----------------------
def load_cards():
    p = Path("content/cards.json")
    if not p.exists():
        return []
    return json.loads(p.read_text(encoding="utf-8"))

def load_quiz():
    p = Path("quizzes/main.json")  # single main quiz
    return json.loads(p.read_text(encoding="utf-8"))

def learn_section():
    st.title("📚 Learn the Basics (Start Here)")
    st.caption("Short, friendly cards. Open at least one card to unlock the quiz.")

    cards = load_cards()
    if not cards:
        st.warning("No learning cards found yet (content/cards.json). Add them and reload.")
        return

    opened_any = False
    for c in cards:
        with st.expander(f"📌 {c['title']}"):
            opened_any = True
            st.write(c["body"])
            if c.get("example"):
                st.code(c["example"])
            if c.get("tips"):
                st.write("**Tips:**")
                for tip in c["tips"]:
                    st.write("•", tip)

    # If user opened an expander on the page load, mark as viewed.
    # (Streamlit doesn't directly tell which expander opened; using a button to confirm)
    st.divider()
    if st.button("I’ve reviewed the basics"):
        st.session_state["learn_viewed"] = True
        st.session_state["badge_learner"] = True
        st.success("Great! You can now take the quiz.")
        st.balloons()

def quiz_section():
    # Gate: require Learn first
    if not st.session_state["learn_viewed"]:
        st.title("🔒 Quiz Locked")
        st.info("Please visit **Learn** first and click **“I’ve reviewed the basics”** to unlock the quiz.")
        return

    st.title("📝 Main Quiz")
    st.caption("Answer each question, then submit at the end for instant feedback.")

    quiz = load_quiz()
    score = 0

    # Show questions
    for q in quiz:
        st.subheader(q["question"])
        choice = st.radio("Choose one:", q["options"], index=None, key=f"ans_{q['id']}")
        st.write("")  # spacing

    # Submit button
    if st.button("Submit Quiz"):
        # Grade
        for q in quiz:
            choice = st.session_state.get(f"ans_{q['id']}")
            correct = q["options"][q["answer"]]
            is_ok = (choice == correct)
            score += int(is_ok)
            with st.expander(f"Review: {q['question']}"):
                st.write("Your answer:", f"**{choice}**" if choice else "_No answer_")
                st.write("Correct:", f"**{correct}**")
                if q.get("explanation"):
                    st.info(q["explanation"])

        st.session_state["quiz_submitted"] = True
        st.session_state["quiz_score"] = score
        st.session_state["quiz_total"] = len(quiz)
        st.session_state["badge_quizzer"] = True

        st.success(f"Score: {score}/{len(quiz)}")
        st.toast("Quiz submitted! Check the Results page for your summary.")

def results_section():
    st.title("📈 Your Results")
    if not st.session_state["quiz_submitted"]:
        st.info("Take the quiz to see your results here.")
        return

    score = st.session_state["quiz_score"]
    total = st.session_state["quiz_total"]
    pct = (score/total)*100 if total else 0.0

    st.metric("Final Score", f"{score}/{total}")
    st.progress(pct/100)
    if pct >= 80:
        st.success("Great job! You’re well on your way to spotting phishing.")
    elif pct >= 50:
        st.info("Good start. Review the cards again to sharpen your eye.")
    else:
        st.warning("No stress — revisit the Learn section and try again!")

    st.divider()
    st.caption("(Later we’ll add per-topic breakdown and saving to database here.)")


# -----------------------
# Pages
# -----------------------
if page == "Home":
    st.title("🛡️ Phishing Awareness — Thesis Prototype")
    st.write(
        "Welcome! Start with **Learn**, then take the **Quiz**, and view your **Results**. "
        "This tool uses simple language and examples to help anyone spot phishing."
    )

    # Mini status
    col1, col2 = st.columns(2)
    with col1:
        st.metric("Learn viewed", "Yes" if st.session_state["learn_viewed"] else "No")
    with col2:
        label = f"{st.session_state['quiz_score']}/{st.session_state['quiz_total']}" if st.session_state["quiz_submitted"] else "—"
        st.metric("Quiz score", label)

elif page == "Learn":
    learn_section()

elif page == "Quiz":
    quiz_section()

elif page == "Results":
    results_section()
