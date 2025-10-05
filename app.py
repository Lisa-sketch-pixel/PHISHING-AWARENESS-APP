import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="Phishing Awareness", page_icon="🛡️", layout="centered")

# -----------------------
# Session state
# -----------------------
def init_state():
    defaults = {
        "learn_viewed": False,
        "quiz_submitted": False,
        "quiz_score": 0,
        "quiz_total": 0,
        "stars": 0,                 # gamification currency
        "badge": None,              # Bronze / Silver / Gold
        "nav": "Home"               # internal router for CTA buttons
    }
    for k,v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_state()

# -----------------------
# Styling (simple)
# -----------------------
HERO_CSS = """
<style>
.hero {
  background: radial-gradient(110% 140% at 10% 10%, #ffffff 0%, #f6f7ff 35%, #eef1ff 60%, #e7ecff 100%);
  padding: 28px 22px;
  border-radius: 20px;
  border: 1px solid #eef;
  box-shadow: 0 8px 24px rgba(40,60,120,0.07);
}
.kpis { display:flex; gap:16px; flex-wrap:wrap; margin-top:8px; }
.kpi {
  flex:1 1 160px; background:#fff; border:1px solid #f0f2ff; border-radius:14px;
  padding:12px 14px; text-align:center;
}
.star-big { font-size: 26px; }
.cta button { margin-right:8px; }
.small-muted { color:#6b7280; font-size:13px; }
.badge-pill {
  display:inline-block; padding:6px 10px; border-radius:999px; font-size:12px; font-weight:600;
  border:1px solid #e5e7eb; background:#fff;
}
</style>
"""
st.markdown(HERO_CSS, unsafe_allow_html=True)

# -----------------------
# Data loaders
# -----------------------
def load_cards():
    p = Path("content/cards.json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []

def load_quiz():
    p = Path("quizzes/main.json")
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []

# -----------------------
# Utils
# -----------------------
def award_stars(n):
    st.session_state["stars"] = max(0, st.session_state["stars"] + int(n))

def update_badge():
    s = st.session_state["stars"]
    if s >= 25:
        st.session_state["badge"] = "Gold"
    elif s >= 15:
        st.session_state["badge"] = "Silver"
    elif s >= 8:
        st.session_state["badge"] = "Bronze"
    else:
        st.session_state["badge"] = None

def go(page):
    st.session_state["nav"] = page
    st.rerun()

# -----------------------
# Sections
# -----------------------
def home_section():
    st.markdown("""
<div class='hero'>
  <h2>🛡️ Phishing Awareness — Learn, Play, Improve</h2>
  <p class='small-muted'>Quick lessons first, then a short quiz. Earn <b>stars</b>, unlock <span class='badge-pill'>Bronze</span>, <span class='badge-pill'>Silver</span>, or <span class='badge-pill'>Gold</span> badges. Perfect for beginners — no jargon.</p>
  <div class='kpis'>
    <div class='kpi'><div class='star-big'>⭐</div><div><b>{stars}</b> Stars</div></div>
    <div class='kpi'>Badge<br><b>{badge}</b></div>
    <div class='kpi'>Quiz Score<br><b>{score}</b></div>
  </div>
</div>
""".format(
        stars=st.session_state["stars"],
        badge=(st.session_state["badge"] or "—"),
        score=(f"{st.session_state['quiz_score']}/{st.session_state['quiz_total']}" if st.session_state["quiz_submitted"] else "—")
    ), unsafe_allow_html=True)

    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("📚 Start Learning"):
            go("Learn")
    with c2:
        if st.button("📝 Go to Quiz"):
            go("Quiz")
    with c3:
        if st.button("📈 View Results"):
            go("Results")

    st.write("")
    st.write("**How it works**")
    st.markdown("""
- Open a few short **Learn** cards. Each card has a tiny **Quick Check** — get it right to earn a ⭐.
- Take the **Quiz** (beginner-friendly). Each correct answer adds more ⭐.
- See your **Results**, total ⭐, and your **badge**.
""")

def learn_section():
    st.title("📚 Learn the Basics (Start Here)")
    st.caption("Open the cards. Each card has a tiny Quick Check — answer correctly to earn a ⭐.")
    cards = load_cards()
    if not cards:
        st.warning("No learning cards found yet (content/cards.json).")
        return

    earned_now = 0
    for i, c in enumerate(cards):
        with st.expander(f"📌 {c['title']}"):
            st.write(c["body"])
            if c.get("example"):
                st.code(c["example"])
            if c.get("tips"):
                st.write("**Tips:**")
                for tip in c["tips"]:
                    st.write("•", tip)

            # Quick check (mini question per card)
            qc = c.get("check")
            if qc:
                st.write("---")
                st.write("**Quick Check**")
                choice = st.radio(qc["question"], qc["options"], index=None, key=f"lc_{i}")
                if st.button("Check", key=f"lc_btn_{i}"):
                    correct = qc["options"][qc["answer"]]
                    if choice == correct:
                        st.success("✅ Correct! +1 ⭐")
                        award_stars(1)
                        earned_now += 1
                    else:
                        st.error(f"❌ Correct answer: {correct}")
                    if qc.get("explanation"):
                        st.info(qc["explanation"])

    if earned_now > 0:
        update_badge()
        st.balloons()

    # unlock quiz after viewing learn (or answering at least one)
    st.write("")
    if st.button("I’ve reviewed the basics"):
        st.session_state["learn_viewed"] = True
        st.success("Great! The quiz is unlocked.")
        st.balloons()

def quiz_section():
    if not st.session_state["learn_viewed"]:
        st.title("🔒 Quiz Locked")
        st.info("Visit **Learn** first and click **“I’ve reviewed the basics”** to unlock the quiz.")
        if st.button("Go to Learn"):
            go("Learn")
        return

    st.title("📝 Main Quiz")
    st.caption("Answer then submit to see explanations. Correct answers earn ⭐.")
    quiz = load_quiz()
    if not quiz:
        st.warning("No quiz found (quizzes/main.json).")
        return

    for q in quiz:
        st.subheader(q["question"])
        st.radio("Choose one:", q["options"], index=None, key=f"ans_{q['id']}")
        st.write("")

    if st.button("Submit Quiz"):
        score = 0
        stars_now = 0
        for q in quiz:
            choice = st.session_state.get(f"ans_{q['id']}")
            correct = q["options"][q["answer"]]
            ok = (choice == correct)
            score += int(ok)
            stars_now += int(ok)  # 1 star per correct
            with st.expander(f"Review: {q['question']}"):
                st.write("Your answer:", f"**{choice}**" if choice else "_No answer_")
                st.write("Correct:", f"**{correct}**")
                if q.get("explanation"):
                    st.info(q["explanation"])

        st.session_state["quiz_submitted"] = True
        st.session_state["quiz_score"] = score
        st.session_state["quiz_total"] = len(quiz)

        if stars_now > 0:
            award_stars(stars_now)
            update_badge()
        st.success(f"Score: {score}/{len(quiz)}  |  ⭐ earned: {stars_now}")

        # celebrate!
        if score == len(quiz):
            st.balloons()
        elif score >= max(3, len(quiz)//2):
            st.toast("Nice work! Keep going ⭐")
        else:
            st.toast("Good start — check the Learn cards and try again!")

def results_section():
    st.title("📈 Your Results & Rewards")
    colA, colB, colC = st.columns(3)
    with colA:
        st.metric("Stars", st.session_state["stars"])
    with colB:
        score = f"{st.session_state['quiz_score']}/{st.session_state['quiz_total']}" if st.session_state["quiz_submitted"] else "—"
        st.metric("Quiz Score", score)
    with colC:
        st.metric("Badge", st.session_state["badge"] or "—")

    if st.session_state["quiz_submitted"]:
        pct = (st.session_state["quiz_score"]/st.session_state["quiz_total"])*100 if st.session_state["quiz_total"] else 0
        st.progress(pct/100)
        if st.session_state["badge"] == "Gold":
            st.success("🥇 Gold — Elite Phish Spotter! You’re crushing it.")
        elif st.session_state["badge"] == "Silver":
            st.info("🥈 Silver — Strong awareness. A little more practice for Gold!")
        elif st.session_state["badge"] == "Bronze":
            st.info("🥉 Bronze — Great start! Keep learning and earn more ⭐.")
        else:
            st.write("Keep learning and quizzing to unlock a badge!")

    st.write("")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📚 Learn More"):
            go("Learn")
    with c2:
        if st.button("📝 Retake Quiz"):
            st.session_state["quiz_submitted"] = False
            st.session_state["quiz_score"] = 0
            st.session_state["quiz_total"] = 0
            go("Quiz")

# -----------------------
# Router (sidebar or internal)
# -----------------------
# You can keep your old sidebar radio if you like.
# Here we'll mirror the internal nav for a clean experience.
page = st.sidebar.radio("🧭 Navigation", ["Home", "Learn", "Quiz", "Results"], index=["Home","Learn","Quiz","Results"].index(st.session_state["nav"]))

if page != st.session_state["nav"]:
    st.session_state["nav"] = page

if st.session_state["nav"] == "Home":
    home_section()
elif st.session_state["nav"] == "Learn":
    learn_section()
elif st.session_state["nav"] == "Quiz":
    quiz_section()
elif st.session_state["nav"] == "Results":
    results_section()
