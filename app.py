import streamlit as st
from supabase import create_client
import streamlit as st
import json, csv, io, re, random
from pathlib import Path
from typing import List, Dict, Any
import streamlit as st
from supabase import create_client, Client

# --- Initialize Supabase client ---
@st.cache_resource
def get_supabase() -> Client:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["anon_key"]
    return create_client(url, key)

# --- Maintain auth state ---
def ensure_auth_state():
    if "sb_session" not in st.session_state:
        st.session_state["sb_session"] = None
    if "user" not in st.session_state:
        st.session_state["user"] = None
# --- Signup Form ---
def signup_form():
    st.subheader("🆕 Create an Account")
    email = st.text_input("Email", key="signup_email")
    password = st.text_input("Password", type="password", key="signup_password")
    full_name = st.text_input("Full Name", key="signup_name")

    if st.button("Sign Up"):
        sb = get_supabase()
        try:
            res = sb.auth.sign_up({
                "email": email,
                "password": password,
                "options": {"data": {"full_name": full_name}}
            })
            st.success("✅ Account created successfully! Please check your email to verify before logging in.")
        except Exception as e:
            st.error(f"Signup failed: {e}")


# --- Login Form ---
def login_form():
    st.subheader("🔐 Login to Your Account")
    email = st.text_input("Email", key="login_email")
    password = st.text_input("Password", type="password", key="login_password")

    if st.button("Login"):
        sb = get_supabase()
        try:
            res = sb.auth.sign_in_with_password({
                "email": email,
                "password": password
            })
            st.session_state["sb_session"] = res.session
            st.session_state["user"] = res.user
            st.success(f"✅ Logged in as {res.user.email}")
            st.rerun()
        except Exception as e:
            st.error(f"Login failed: {e}")


# --- Logout Button ---
def logout_button():
    if st.session_state.get("user") and st.button("🚪 Log Out"):
        sb = get_supabase()
        sb.auth.sign_out()
        st.session_state["user"] = None
        st.session_state["sb_session"] = None
        st.success("You’ve been logged out.")
        st.rerun()
def require_auth():
    ensure_auth_state()
    if not st.session_state["user"]:
        tab1, tab2 = st.tabs(["🔐 Login", "🆕 Sign Up"])
        with tab1:
            login_form()
        with tab2:
            signup_form()
        st.stop()  # stop loading rest of the page if not logged in

# --- Supabase connection test ---
try:
    url = st.secrets["supabase"]["url"]
    key = st.secrets["supabase"]["anon_key"]
    supabase = create_client(url, key)
    st.success(f"✅ Connected to Supabase project: {url}")
except Exception as e:
    st.error(f"❌ Could not connect to Supabase: {e}")

st.set_page_config(page_title="Cybersecurity Awareness System & Threat Simulator", page_icon="🛡️", layout="centered")

# -----------------------
# Session state
# -----------------------
def init_state():
    defaults = {
        "learn_viewed": False,
        "quiz_submitted": False,
        "quiz_score": 0,
        "quiz_total": 0,
        "stars": 0,
        "badge": None,
        "nav": "Home",
        # simulation
        "sim_inbox": None,
        "sim_answers": {},
        "sim_submitted": False,
        "sim_score": 0,
        "sim_history": [],   # append dicts for export
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v
init_state()

# -----------------------
# Styling (Home)
# -----------------------
HERO_CSS = """
<style>
:root{
  --brand:#4f46e5; --brand-soft:#eef2ff; --ink:#0f172a; --muted:#6b7280;
}
.hero { position:relative; background: radial-gradient(120% 160% at 10% 10%, #ffffff 0%, #f6f7ff 35%, #eef1ff 60%, #e7ecff 100%);
  padding:36px 28px; border-radius:22px; border:1px solid #eef; box-shadow:0 10px 26px rgba(40,60,120,0.08); overflow:hidden;}
.hero:after{ content:""; position:absolute; right:-80px; top:-80px; width:220px; height:220px; border-radius:50%;
  background: conic-gradient(from 180deg at 50% 50%, #c7d2fe, #e0e7ff, #c7d2fe); filter: blur(18px); opacity:.6;}
.hero h1{ margin:0 0 6px 0; font-size:1.65rem; color:var(--ink);}
.hero p{ margin:2px 0 0 0; color:var(--muted);}
.kpis{ display:flex; gap:14px; flex-wrap:wrap; margin-top:14px;}
.kpi{ flex:1 1 180px; background:#fff; border:1px solid #f0f2ff; border-radius:14px; padding:12px 14px; text-align:center;}
.kpi .value{ font-size:20px; font-weight:700; color:var(--ink);}
.kpi .label{ font-size:12px; color:var(--muted);}
.pills{ display:flex; gap:8px; margin-top:10px; flex-wrap:wrap;}
.pill{ background:var(--brand-soft); color:var(--brand); border:1px solid #e0e7ff; padding:6px 10px; border-radius:999px; font-weight:600; font-size:12px;}
.cta-row{ display:flex; gap:10px; flex-wrap:wrap; margin-top:14px;}
.cta-btn{ border:1px solid #dbe2ff; background:#fff; padding:10px 14px; border-radius:12px; font-weight:600;}
.cta-primary{ background:var(--brand); color:#fff; border:1px solid var(--brand);}
.feature-grid{ display:grid; grid-template-columns: repeat(auto-fit, minmax(210px,1fr)); gap:12px; margin-top:14px;}
.feature{ background:#fff; border:1px solid #f0f2ff; border-radius:14px; padding:12px 14px;}
.feature h4{ margin:0 0 6px 0; font-size:14px;}
.feature p{ margin:0; font-size:13px; color:var(--muted);}
.divider{ height:1px; background:#eef2ff; margin:12px 0;}
.small-muted{ color:#6b7280; font-size:13px;}
</style>
"""
st.markdown(HERO_CSS, unsafe_allow_html=True)

# -----------------------
# Helpers & Data
# -----------------------
def go(page: str):
    st.session_state["nav"] = page
    st.rerun()

def award_stars(n: int):
    st.session_state["stars"] = max(0, st.session_state["stars"] + int(n))

def update_badge():
    s = st.session_state["stars"]
    if s >= 25: st.session_state["badge"] = "Gold"
    elif s >= 15: st.session_state["badge"] = "Silver"
    elif s >= 8: st.session_state["badge"] = "Bronze"
    else: st.session_state["badge"] = None

def load_json(path: str):
    p = Path(path)
    return json.loads(p.read_text(encoding="utf-8")) if p.exists() else []

def load_quiz():
    return load_json("quizzes/main.json")

def show_learning_cards(cards: list, prefix: str):
    if not cards:
        st.warning("No learning cards found.")
        return
    earned_now = 0
    for i, c in enumerate(cards):
        with st.expander(f"📌 {c['title']}"):
            st.write(c["body"])
            if c.get("example"): st.code(c["example"])
            if c.get("tips"):
                st.write("**Tips:**")
                for tip in c["tips"]:
                    st.write("•", tip)
            qc = c.get("check")
            if qc:
                st.write("---"); st.write("**Quick Check**")
                choice = st.radio(qc["question"], qc["options"], index=None, key=f"{prefix}_q_{i}")
                if st.button("Check", key=f"{prefix}_btn_{i}"):
                    correct = qc["options"][qc["answer"]]
                    if choice == correct:
                        st.success("✅ Correct! +1 ⭐"); award_stars(1); earned_now += 1
                    else:
                        st.error(f"❌ Correct answer: {correct}")
                    if qc.get("explanation"): st.info(qc["explanation"])
    if earned_now > 0:
        update_badge(); st.balloons()

# -----------------------
# Home
# -----------------------
def home_section():
    stars = st.session_state["stars"]
    badge = st.session_state["badge"] or "—"
    score = f"{st.session_state['quiz_score']}/{st.session_state['quiz_total']}" if st.session_state["quiz_submitted"] else "—"

    st.markdown(f"""
<div class='hero'>
  <h1>🛡️ Cybersecurity Awareness System & Threat Simulator</h1>
  <p>Quick lessons, a short quiz, and a hands-on simulation with a mock inbox. Earn <b>stars</b>, unlock badges, and build real instincts — no jargon.</p>
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
</div>
""", unsafe_allow_html=True)

    c1, c2, c3, c4 = st.columns(4)
    with c1:
        if st.button("📚 Learn"): go("Learn")
    with c2:
        if st.button("📝 Quiz"): go("Quiz")
    with c3:
        if st.button("📬 Simulate"): go("Simulate")
    with c4:
        if st.button("📈 Results"): go("Results")

    st.markdown("<div class='divider'></div>", unsafe_allow_html=True)
    st.subheader("What’s inside")
    st.markdown("""
<div class='feature-grid'>
  <div class='feature'><h4>📚 Basic Lessons</h4><p>Urgency tricks, passwords, attachments, what to do if you clicked.</p></div>
  <div class='feature'><h4>🧠 Advanced Lessons</h4><p>Look-alike domains, header clues, QR (quishing), spear-phishing.</p></div>
  <div class='feature'><h4>📝 Quiz</h4><p>Beginner-friendly questions with explanations. Earn ⭐ for correct answers.</p></div>
  <div class='feature'><h4>📬 Simulation</h4><p>Practice labeling a mock inbox. Streak bonuses, hints, and CSV export.</p></div>
</div>
""", unsafe_allow_html=True)
    if stars == 0: st.toast("Start with Basic lessons — easy stars are waiting ⭐")

# -----------------------
# Learn
# -----------------------
def learn_section():
    st.title("📚 Learn About Phishing")
    st.caption("Choose your level. Basic is beginner-friendly; Advanced is optional deeper content.")
    tab1, tab2 = st.tabs(["🟢 Basic", "🔵 Advanced"])
    with tab1:
        st.subheader("Basic Awareness")
        basic_cards = load_json("content/cards_basic.json")
        show_learning_cards(basic_cards, prefix="basic")
        if st.button("✅ I've reviewed the basics"):
            st.session_state["learn_viewed"] = True
            st.success("Great! The quiz is unlocked."); st.balloons()
    with tab2:
        st.subheader("Advanced Awareness (Optional)")
        adv_cards = load_json("content/cards_advanced.json")
        show_learning_cards(adv_cards, prefix="adv")

# -----------------------
# Quiz
# -----------------------
def quiz_section():
     require_auth()
    if not st.session_state["learn_viewed"]:
        st.title("🔒 Quiz Locked")
        st.info("Visit **Learn** and click **“I've reviewed the basics”** to unlock the quiz.")
        if st.button("Go to Learn"): go("Learn"); return
    st.title("📝 Main Quiz")
    st.caption("Answer all questions, then submit for explanations. Correct answers earn ⭐.")
    quiz = load_quiz()
    if not quiz: st.warning("No quiz found (quizzes/main.json)."); return
    for q in quiz:
        st.subheader(q["question"])
        st.radio("Choose one:", q["options"], index=None, key=f"ans_{q['id']}"); st.write("")
    if st.button("Submit Quiz"):
        score = 0; stars_now = 0
        for q in quiz:
            choice = st.session_state.get(f"ans_{q['id']}")
            correct = q["options"][q["answer"]]
            ok = (choice == correct)
            score += int(ok); stars_now += int(ok)
            with st.expander(f"Review: {q['question']}"):
                st.write("Your answer:", f"**{choice}**" if choice else "_No answer_")
                st.write("Correct:", f"**{correct}**")
                if q.get("explanation"): st.info(q["explanation"])
        st.session_state["quiz_submitted"] = True
        st.session_state["quiz_score"] = score
        st.session_state["quiz_total"] = len(quiz)
        if stars_now > 0: award_stars(stars_now); update_badge()
        st.success(f"Score: {score}/{len(quiz)}  |  ⭐ earned: {stars_now}")
        if score == len(quiz): st.balloons()
        elif score >= max(3, len(quiz)//2): st.toast("Nice work! Keep going ⭐")
        else: st.toast("Good start — check the Learn cards and try again!")

# -----------------------
# Simulation (no AI; hints only)
# -----------------------
# templates loader & inbox
def load_sim_templates():
    data = load_json("content/sim_templates.json")
    phishing = [t for t in data if t.get("label") == "phishing"]
    legit = [t for t in data if t.get("label") == "safe"]
    return phishing, legit

def synth_email(tpl: Dict[str, Any]) -> Dict[str, Any]:
    def pick(x): return random.choice(x) if isinstance(x, list) else x
    subject = tpl["subject"].format(
        brand=pick(tpl.get("brand", ["Your Bank","ParcelCo","Account Center"])),
        mins=random.choice([15, 30, 60])
    )
    body = tpl["body"].format(
        link="http://secure-check-update.com/login",
        brand=pick(tpl.get("brand", ["Your Bank","ParcelCo","Account Center"])),
        ticket=random.randint(100000, 999999),
        code=random.randint(100000, 999999),
    )
    return {
        "from": pick(tpl.get("from", ["noreply@mailer.cc"])),
        "to": "you@example.com",
        "subject": subject,
        "body": body,
        "label": tpl["label"]
    }

def make_inbox(n_total=6, ratio_phish=0.5, difficulty="Medium"):
    phish_tpls, legit_tpls = load_sim_templates()
    n_phish = int(n_total * ratio_phish)
    n_legit = n_total - n_phish
    items = []
    for _ in range(n_phish): items.append(synth_email(random.choice(phish_tpls)))
    for _ in range(n_legit): items.append(synth_email(random.choice(legit_tpls)))
    # difficulty tweaks
    if difficulty == "Hard":
        for it in items:
            it["body"] += "\n\nNote: Action required immediately."
    elif difficulty == "Easy":
        for it in items:
            it["body"] = re.sub(r"(immediately|now|minutes)", "soon", it["body"], flags=re.I)
    random.shuffle(items)
    return items

# simple hint extractor (rule-based) — does NOT predict
HINT_KEYWORDS = [
    ("verify account","Mentions verifying accounts"),
    ("update password","Suggests password update via message"),
    ("click here","Generic “click here” call-to-action"),
    ("urgent","Uses urgency wording"),
    ("suspended","Threat of suspension"),
    ("prize","Unexpected prize/reward"),
    ("billing","Billing/payment issue"),
    ("confirm now","Demands immediate confirmation"),
    ("login immediately","Pushes immediate login"),
    ("payment failed","Says payment failed"),
    ("security alert","Claims a security alert")
]
SENDER_FLAGS = [".ru",".tk",".cc","random-mailer","secure-update","mailer"]

def extract_hints(item: Dict[str, Any]) -> List[str]:
    text = f"{item.get('subject','')} {item.get('body','')}".lower()
    hints = []
    for kw, msg in HINT_KEYWORDS:
        if kw in text: hints.append(f"• {msg}.")
    sender = item.get("from","").lower()
    if any(x in sender for x in SENDER_FLAGS):
        hints.append("• Suspicious sender domain/relay.")
    if re.search(r"http[s]?://", text):
        hints.append("• Contains a link — verify independently via official site/app.")
    if re.search(r"\.(exe|scr|bat|zip)\\b", text) or "attachment" in text:
        hints.append("• Mentions risky attachment types.")
    if not hints:
        hints.append("• Check sender, tone, links, and requests for sensitive info.")
    return hints

def simulate_section():
     require_auth()
    st.title("📬 Simulation — Inbox Training")
    st.caption("Label each message as **Phishing** or **Safe**. Use **Hints** if you’re unsure (no AI yet).")

    colA, colB, colC = st.columns(3)
    with colA:
        n_total = st.selectbox("Emails to generate", [4,6,8,10], index=1)
    with colB:
        ratio = st.slider("Phishing ratio", 0.0, 1.0, 0.5, 0.1)
    with colC:
        difficulty = st.selectbox("Difficulty", ["Easy","Medium","Hard"], index=1)

    if (st.session_state["sim_inbox"] is None) or st.button("🔁 Regenerate Inbox"):
        st.session_state["sim_inbox"] = make_inbox(n_total, ratio, difficulty)
        st.session_state["sim_answers"] = {}
        st.session_state["sim_submitted"] = False
        st.session_state["sim_score"] = 0

    inbox: List[Dict[str, Any]] = st.session_state["sim_inbox"]

    # live streak tracking (resets on wrong after submit)
    streak_preview = 0

    for i, item in enumerate(inbox):
        with st.expander(f"✉️  {item['subject']} — from {item['from']}"):
            st.write(item["body"])
            cols = st.columns([1,1,2])
            with cols[0]:
                ans = st.radio("Your label", ["Phishing","Safe"], index=None, key=f"sim_ans_{i}")
                st.session_state["sim_answers"][i] = ans
            with cols[1]:
                if st.button("💡 Hints", key=f"hint_{i}"):
                    for h in extract_hints(item): st.info(h)
            with cols[2]:
                st.caption("Truth is hidden until you submit.")
            streak_preview += 1  # display only (not final)

    if st.button("Submit Labels"):
        score = 0
        stars_now = 0
        streak = 0
        wrong_examples = 0
        run_rows = []  # for export

        for i, item in enumerate(inbox):
            truth = "Phishing" if item["label"] == "phishing" else "Safe"
            chosen = st.session_state["sim_answers"].get(i)
            ok = (chosen == truth)
            score += int(ok)
            streak = streak + 1 if ok else 0
            # +1 star for correct, +1 streak bonus on every third in-a-row
            add = 1 if ok else 0
            if ok and streak > 0 and (streak % 3 == 0):
                add += 1
            stars_now += add

            with st.expander(f"Review: {item['subject']}"):
                st.write("Correct label:", f"**{truth}**")
                st.write("Your label:", f"**{chosen or 'No answer'}**")
                st.write("Reasons to consider:")
                for h in extract_hints(item):
                    st.write(h)

            if not ok: wrong_examples += 1

            run_rows.append({
                "index": i,
                "from": item["from"],
                "subject": item["subject"],
                "label_truth": truth,
                "label_user": chosen or "",
                "correct": int(ok),
                "difficulty": difficulty,
                "phish_ratio": ratio
            })

        st.session_state["sim_submitted"] = True
        st.session_state["sim_score"] = score
        if stars_now > 0: award_stars(stars_now); update_badge()

        st.success(f"You labeled {score}/{len(inbox)} correctly. ⭐ earned: {stars_now} (streak bonuses every 3 in a row!)")
        if score == len(inbox): st.balloons()
        elif wrong_examples >= 2: st.toast("Nice try—review Basic cards and practice again!")

        # save to history (session only)
        st.session_state["sim_history"].append(run_rows)

        # CSV export of this run
        csv_buf = io.StringIO()
        writer = csv.DictWriter(csv_buf, fieldnames=list(run_rows[0].keys()))
        writer.writeheader()
        writer.writerows(run_rows)
        st.download_button("⬇️ Download this run as CSV", data=csv_buf.getvalue(),
                           file_name="simulation_results.csv", mime="text/csv")

# -----------------------
# Results
# -----------------------
def results_section():
     require_auth()
    st.title("📈 Your Results & Rewards")
    colA, colB, colC = st.columns(3)
    with colA: st.metric("Stars", st.session_state["stars"])
    with colB:
        score = f"{st.session_state['quiz_score']}/{st.session_state['quiz_total']}" if st.session_state["quiz_submitted"] else "—"
        st.metric("Quiz Score", score)
    with colC: st.metric("Badge", st.session_state["badge"] or "—")

    if st.session_state["quiz_submitted"]:
        pct = (st.session_state["quiz_score"]/st.session_state["quiz_total"])*100 if st.session_state["quiz_total"] else 0
        st.progress(pct/100)
    st.write("")
    if st.session_state["sim_history"]:
        st.subheader("Recent Simulation (last run)")
        last = st.session_state["sim_history"][-1]
        correct = sum(r["correct"] for r in last)
        st.write(f"Last run: **{correct}/{len(last)}** correct")
    c1, c2 = st.columns(2)
    with c1:
        if st.button("📚 Learn More"): go("Learn")
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
    "🧭 Go to", ["Home", "Learn", "Simulate", "Quiz", "Results"],
    index=["Home","Learn","Simulate","Quiz","Results"].index(st.session_state["nav"])
)
if page != st.session_state["nav"]:
    st.session_state["nav"] = page

if st.session_state["nav"] == "Home":
    home_section()
elif st.session_state["nav"] == "Learn":
    learn_section()
elif st.session_state["nav"] == "Simulate":
    simulate_section()
elif st.session_state["nav"] == "Quiz":
    quiz_section()
elif st.session_state["nav"] == "Results":
    results_section()
