import streamlit as st
import json

st.set_page_config(page_title="Phishing Awareness", page_icon="🛡️", layout="centered")

# ---- tiny quiz helper ----
def run_quiz(path, key):
    with open(path, "r", encoding="utf-8") as f:
        quiz = json.load(f)

    if f"{key}_submitted" not in st.session_state:
        st.session_state[f"{key}_submitted"] = False
        st.session_state[f"{key}_score"] = 0
        st.session_state[f"{key}_total"] = len(quiz)

    score = 0
    st.header("📝 Quiz")
    for i, q in enumerate(quiz):
        st.subheader(f"{i+1}. {q['question']}")
        choice = st.radio("Choose an answer:", q["options"], index=None, key=f"{key}_{i}")
        if st.session_state[f"{key}_submitted"]:
            correct = q["options"][q["answer"]]
            if choice == correct:
                st.success("✅ Correct")
                score += 1
            else:
                st.error(f"❌ Correct: **{correct}**")

    if st.button("Submit", key=f"{key}_submit"):
        st.session_state[f"{key}_submitted"] = True
        st.session_state[f"{key}_score"] = score
        st.success(f"Score: {score}/{len(quiz)}")

# ---- pages ----
page = st.sidebar.radio("Navigate", ["Home", "Pre-Quiz", "Learn", "Post-Quiz", "Results"])

if page == "Home":
    st.title("Phishing Awareness (Thesis Prototype)")
    st.write("Welcome! Use the sidebar to take the pre-quiz, read quick lessons, and take the post-quiz.")
    st.info("AI checker & database will be added after this basic version runs.")

elif page == "Pre-Quiz":
    run_quiz("quizzes/pre.json", "pre")

elif page == "Learn":
    st.title("📚 Quick Lessons")
    st.write("Short cards to help you spot phishing.")
    try:
        cards = json.load(open("content/cards.json", "r", encoding="utf-8"))
        for c in cards:
            with st.expander("📌 " + c["title"]):
                st.write(c["body"])
                if c.get("example"):
                    st.code(c["example"])
    except FileNotFoundError:
        st.warning("Learning cards not found yet. We'll add them next.")

elif page == "Post-Quiz":
    run_quiz("quizzes/post.json", "post")

elif page == "Results":
    st.title("Your Results")
    pre = st.session_state.get("pre_score")
    post = st.session_state.get("post_score")
    total_pre = st.session_state.get("pre_total")
    total_post = st.session_state.get("post_total")

    if pre is None or post is None:
        st.info("Take the Pre-Quiz and Post-Quiz to see your results.")
    else:
        st.write(f"Pre: **{pre}/{total_pre}**")
        st.write(f"Post: **{post}/{total_post}**")
        try:
            pre_pct = pre / total_pre if total_pre else 0
            post_pct = post / total_post if total_post else 0
            st.metric("Improvement", f"{(post_pct - pre_pct)*100:.1f}%")
        except Exception:
            st.write("Complete both quizzes first.")
