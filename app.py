import streamlit as st
import json
from pathlib import Path

st.set_page_config(page_title="Phishing Awareness", page_icon="🛡️", layout="centered")

# -----------------------
# Session state
# -----------------------
def init_state():
    defaults = {
        "learn_viewed": False,   # flipped after confirming basic learning
        "quiz_submitted": False,
        "quiz_score": 0,
        "quiz_total": 0,
        "stars": 0,              # gamification currency
        "badge": None,           # Bronze / Silver / Gold
        "nav": "Home"            # for internal nav buttons
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_state()

# -----------------------
# Styling (NEW Home CSS)
# -----------------------
HERO_CSS = """
<style>
:root{
  --brand:#4f46e5;           /* indigo-600 */
  --brand-soft:#eef2ff;      /* indigo-50 */
  --ink:#0f172a;             /* slate-900 */
  --muted:#6b7280;
}
.hero {
  position: relative;
  background: radial-gradient(120% 160% at 10% 10%, #ffffff 0%, #f6f7ff 35%, #eef1ff 60%, #e7ecff 100%);
  padding: 36px 28px;
  border-radius: 22px;
  border: 1px solid #eef;
  box-shadow: 0 10px 26px rgba(40,60,120,0.08);
  overflow: hidden;
}
.hero:after{
  content:"";
  position:absolute; right:-80px; top:-80px;
  width:220px; height:220px; border-radius:50%;
  background: conic-gradient(from 180deg at 50% 50%, #c7d2fe, #e0e7ff, #c7d2fe);
  filter: blur(18px); opacity:.6;
}
.hero h1{ margin:0 0 6px 0; font-size: 1.65rem; color: var(--ink);}
.hero p{ margin:2px 0 0 0; color: var(--muted); }
.kpis { display:flex; gap:14px; flex-wrap:wrap; margin-top:14px; }
.kpi {
  flex:1 1 180px; background:#fff; border:1px solid #f0f2ff; border-radius:14px;
  padding:12px 14px; text-align:center;
}
.kpi .value{ font-size:20px; font-weight:700; color: var(--ink); }
.kpi .label{ font-size:12px; color: var(--muted); }
.pills { display:flex; gap:8px; margin-top:10px; flex-wrap:wrap; }
.pill { background:var(--brand-soft); color:var(--brand); border:1px solid #e0e7ff; padding:6px 10px; border-radius:999px; font-weight:600; font-size:12px; }
.cta-row { display:flex; gap:10px; flex-wrap:wrap; margin-top:14px; }
.cta-btn {
  border:1px solid #dbe2ff; background:#fff; padding:10px 14px; border-radius:12px; font-weight:600;
}
.cta-primary {
  background:var(--brand); color:#fff; border:1px solid var(--brand);
}
.feature-grid{ display:grid; grid-template-columns: repeat(auto-fit, minmax(210px,1fr)); gap:12px; margin-top:14px;}
.feature{
  background:#fff; border:1px solid #f0f2ff; border-radius:14px; padding:12px 14px;
}
.feature h4{ margin:0 0 6px 0; font-size: 14px;}
.feature p{ margin:0; font-size: 13px; color: var(--muted); }
.divider { height:1px; background:#eef2ff; margin: 12px 0; }
.small-muted { color:#6b7280; font-size:13px; }
</style>
"""
st.markdown(HERO_CSS, unsafe_allow_html=True)

# -----------------------
# Helpers & Data loaders
# -----------------------
def go(page: str):
    st.session_state["nav"] = page
    st.rerun()

def award_stars(n: int):
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

def load_json(path: str):
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []

def load_quiz():
    return load_json("quizzes/main.json")

def show_learning_cards(cards: list, prefix: str):
    """
    Render learning cards with optional Quick Check.
    prefix ensures unique Streamlit widget keys per tab (basic/advanced).
    """
    if not cards:
        st.warning("No learning cards found.")
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

            qc = c.get("check")
            if qc:
                st.write("---")
                st.write("**Quick Check**")
                choice = st.radio(qc["question"], qc["options"], index=None, key=f"{prefix}_q_{i}")
                if st.button("Check", key=f"{prefix}_btn_{i}"):
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

# -----------------------
# Sections (Home UPDATED)
# -----------------------
def home_section():
    stars = st.session_state["stars"]
    badge = st.session_state["badge"] or "—"
    score = f"{st.session_state['quiz_score']}/{st.session_state['quiz_total']}" if st.session_state["quiz_submitted"] else "—"

    st.markdown(f"""
<div class='hero'>
  <h1>🛡️ Learn to Spot Phishing — Fast</h1>
  <p>Start with quick lessons (Basic or Advanced), then take a short quiz. Earn <b>stars</b>, unlock badges, and build real-world instincts — no jargon.</p>

  <div class='kpis'>
    <div class='kpi'><div class='value'>⭐ {stars}</div><div class='label'>Stars earned</div></div>
    <div class='kpi'><div class='value'>{badge}</div><div class='label'>Current badge</div></div>
    <div class='kpi'><div class='value'>{score}</div><div class='label'>Latest quiz score</div></div>
  </div>

  <div class='pills'>
    <div class='pill'>Beginner-friendly</div>
    <div class='pill'>Instant feedback</div>
    <div class='pill'>Earnable rewards</div>
    <div class='pill'>Short & practical</div>
  </div>

  <div class='cta-row'>
    <button class='cta-btn cta-primary' onclick="window.parent.postMessage({{type:'streamlit:rerunScript'}}, '*')">Let's start</button>
    <button class='cta-btn' onclick="window.parent.postMessage({{type:'streamlit:setComponentValue', key:'nav', value:'Learn'}}, '*')">Browse lessons</button>
  </div>
</div>
""", unsafe_allow_html=True)

    # Real nav via Streamlit
    c1, c2, c3 = st.columns([1,1,1])
    with c1:
        if st.button("📚 Start Learning"):
            go("Learn")
    with c2:
        if st.button("📝 Take the Quiz"):
            go("Quiz")
    with c3:
        if st.button("📈 See Results"):
            go("Results")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    st.subheader("Why this works")
    st.markdown(
        "- **Micro-lessons** teach common scam tactics in minutes.\n"
        "- **Quick Checks** and the quiz give **instant feedback**.\n"
        "- **Rewards** (⭐ & badges) keep it fun — and yes, we celebrate with balloons 🎈.\n"
        "- Designed for **everyone** — no technical background needed."
    )

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)

    st.subheader("What’s inside")
    st.markdown("""
<div class='feature-grid'>
  <div class='feature'>
    <h4>📚 Basic Lessons</h4>
    <p>Plain-language tips: urgency tricks, passwords, attachments, what to do if you clicked.</p>
  </div>
  <div class='feature'>
    <h4>🧠 Advanced Lessons</h4>
    <p>Look-alike domains, header clues, QR (quishing), and spear-phishing.</p>
  </div>
  <div class='feature'>
    <h4>📝 Short Quiz</h4>
    <p>Beginner-friendly questions with explanations. Earn ⭐ for correct answers.</p>
  </div>
  <div class='feature'>
    <h4>🏅 Badges</h4>
    <p>Bronze, Silver, Gold. Level up as you learn.</p>
  </div>
</div>
""", unsafe_allow_html=True)

    st.caption("Tip: You can jump into **Basic** or **Advanced** from the Learn page anytime.")
    if stars == 0:
        st.toast("Start with Basic lessons — easy stars are waiting ⭐")

def learn_section():
    st.title("📚 Learn About Phishing")
    st.caption("Choose your level. Basic is beginner-friendly; Advanced is optional deeper content.")

    tab1, tab2 = st.tabs(["🟢 Basic", "🔵 Advanced"])

    with tab1:
        st.subheader("Basic Awareness")
        st.caption("Simple cards with quick checks. Great for first-timers.")
        basic_cards = load_json("content/cards_basic.json")
        show_learning_cards(basic_cards, prefix="basic")

        if st.button("✅ I've reviewed the basics"):
            st.session_state["learn_viewed"] = True
            st.success("Great! The quiz is unlocked.")
            st.balloons()

    with tab2:
        st.subheader("Advanced Awareness (Optional)")
        st.caption("Deeper topics like homoglyph domains, headers, QR phishing, spear-phishing.")
        adv_cards = load_json("content/cards_advanced.json")
        show_learning_cards(adv_cards, prefix="adv")

def quiz_section():
    if not st.session_state["learn_viewed"]:
        st.title("🔒 Quiz Locked")
        st.info("Please visit **Learn** and click **“I've reviewed the basics”** to unlock the quiz.")
        if st.button("Go to Learn"):
            go("Learn")
        return

    st.title("📝 Main Quiz")
    st.caption("Answer all questions, then submit for explanations. Correct answers earn ⭐.")

    quiz = load_quiz()
    if not quiz:
        st.warning("No quiz found (quizzes/main.json).")
        return

    # Render questions
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
            stars_now += int(ok)
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

        # Celebrate!
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
# Router (sidebar)
# -----------------------
page = st.sidebar.radio(
    "🧭 Go to", ["Home", "Learn", "Quiz", "Results"],
    index=["Home","Learn","Quiz","Results"].index(st.session_state["nav"])
)

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
