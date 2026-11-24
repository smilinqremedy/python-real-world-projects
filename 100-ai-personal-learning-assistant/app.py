"""
Streamlit Web Interface for AI-Powered Personal Learning Assistant.
Learning dashboard, topic summarization, grounded quiz arena, and performance analytics.
"""
import streamlit as st
import tempfile
import os

from learning_engine import LearningEngine

st.set_page_config(
    page_title="AI Learning Assistant",
    page_icon="🎓",
    layout="wide"
)

st.title("🎓 AI-Powered Personal Learning Assistant")
st.markdown("Adaptive learning management, grounded quiz generation, and personalized revision intelligence.")

engine = LearningEngine()

# Session State Auth Setup
if "user" not in st.session_state:
    st.session_state.user = None

# Sidebar Authentication
st.sidebar.header("Learner Account")
if st.session_state.user is None:
    auth_mode = st.sidebar.radio("Action:", ["Login", "Register"])
    u_name = st.sidebar.text_input("Username:")
    u_pwd = st.sidebar.text_input("Password:", type="password")

    if auth_mode == "Register" and st.sidebar.button("Create Account"):
        if u_name and u_pwd:
            uid = engine.register_user(u_name, u_pwd)
            if uid:
                st.sidebar.success("Account created! Please log in.")
            else:
                st.sidebar.error("Username already taken.")
        else:
            st.sidebar.error("Enter username and password.")

    if auth_mode == "Login" and st.sidebar.button("Sign In"):
        user = engine.authenticate_user(u_name, u_pwd)
        if user:
            st.session_state.user = user
            st.sidebar.success(f"Welcome, {user['username']}!")
            st.rerun()
        else:
            st.sidebar.error("Invalid credentials.")
else:
    st.sidebar.write(f"Logged in as: **{st.session_state.user['username']}**")
    if st.sidebar.button("Sign Out"):
        st.session_state.user = None
        st.rerun()

user = st.session_state.user

if not user:
    st.info("👋 Welcome! Please log in or register via the sidebar to access your personalized learning space.")
    st.stop()

uid = user["id"]
tabs = st.tabs([
    "📊 Study Dashboard",
    "📚 Upload Study Material",
    "🎯 Take Quiz",
    "📈 Performance & Weak Topics",
    "📘 Architecture & Guide"
])

# ---------------- Tab 1: Study Dashboard ---------------- #
with tabs[0]:
    st.subheader(f"Welcome back, {user['username']}!")
    subjects = engine.get_subjects(uid)
    topics = engine.get_topics(uid)
    weak = engine.identify_weak_topics(uid)

    col1, col2, col3 = st.columns(3)
    col1.metric("Enrolled Subjects", len(subjects))
    col2.metric("Learning Topics", len(topics))
    col3.metric("Weak Topics Flagged", len(weak), delta=-len(weak) if weak else 0, delta_color="inverse")

    st.markdown("---")
    st.write("### 📌 Personalized Revision Schedule")
    recs = engine.get_revision_recommendations(uid)
    if recs:
        for r in recs:
            st.warning(f"⚠️ **{r['subject']} → {r['topic']}** (Avg Score: `{r['avg_score']}%`): {r['recommendation']}")
    else:
        st.success("🎉 Great job! No weak topics detected. All recent quiz averages meet or exceed the 70% threshold.")

# ---------------- Tab 2: Upload Study Material ---------------- #
with tabs[1]:
    st.subheader("Add Learning Material & Generate Grounded Quiz")
    subjects = engine.get_subjects(uid)

    with st.expander("➕ Create New Subject"):
        sub_title = st.text_input("Subject Title (e.g. Artificial Intelligence):")
        sub_desc = st.text_input("Description:")
        if st.button("Add Subject"):
            if sub_title:
                engine.add_subject(uid, sub_title, sub_desc)
                st.success(f"Subject '{sub_title}' created!")
                st.rerun()

    if not subjects:
        st.info("Create a subject above to begin adding topics.")
    else:
        subj_choice = st.selectbox("Select Target Subject:", options=[s["id"] for s in subjects], format_func=lambda x: next(s["title"] for s in subjects if s["id"] == x))
        topic_title = st.text_input("Topic Title (e.g. Neural Attention Mechanisms):")
        source_mode = st.radio("Study Material Input:", ["Paste Text Notes", "Upload File (.pdf, .txt)"], horizontal=True)

        content = ""
        filename = "pasted_notes.txt"
        if source_mode == "Paste Text Notes":
            content = st.text_area("Paste Study Text:", height=200)
        else:
            up_doc = st.file_uploader("Select Study Document:", type=["txt", "pdf"])
            if up_doc:
                filename = up_doc.name
                with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(up_doc.name)[1]) as tmp:
                    tmp.write(up_doc.getvalue())
                    tmp_p = tmp.name
                try:
                    content = engine.processor.extract_text_from_file(tmp_p)
                finally:
                    if os.path.exists(tmp_p):
                        os.remove(tmp_p)

        if st.button("🚀 Process Material & Generate Quiz"):
            if not topic_title or not content.strip():
                st.error("Please provide both topic title and study text.")
            else:
                res = engine.add_topic_with_content(uid, subj_choice, topic_title, content, filename)
                st.success(f"Topic '{topic_title}' processed!")
                st.info(f"**Conceptual Summary:** {res['summary']}")
                st.write(f"Generated **{res['questions_generated']}** verifiable questions.")

# ---------------- Tab 3: Take Quiz ---------------- #
with tabs[2]:
    st.subheader("Interactive Quiz Arena")
    topics = engine.get_topics(uid)
    if not topics:
        st.info("No study topics available. Upload study materials first.")
    else:
        selected_tid = st.selectbox("Select Topic to Test:", options=[t["id"] for t in topics], format_func=lambda x: next(t["title"] for t in topics if t["id"] == x))
        q_list = engine.get_questions_for_topic(selected_tid)

        if not q_list:
            st.warning("No questions generated for this topic yet.")
        else:
            st.write(f"### Quiz: {len(q_list)} Questions")
            answers = {}
            with st.form("quiz_form"):
                for idx, q in enumerate(q_list, start=1):
                    st.write(f"**Question {idx}:** {q['question_text']}")
                    if q["question_type"] == "mcq":
                        answers[q["id"]] = st.radio(f"Select Answer for Q{idx}:", options=q["options"], key=f"q_{q['id']}")
                    else:
                        answers[q["id"]] = st.text_input(f"Your Answer for Q{idx}:", key=f"q_{q['id']}")
                    st.caption(f"Source Reference: *\"{q['source_excerpt']}\"*")
                    st.markdown("---")

                submit_quiz = st.form_submit_button("Submit Quiz for Automatic Grading")

                if submit_quiz:
                    res = engine.grade_quiz(uid, selected_tid, answers)
                    st.success(f"### Score: **{res['score_pct']}%** ({res['correct_count']}/{res['total_questions']} correct)")
                    for fb in res["feedback"]:
                        if fb["is_correct"]:
                            st.write(f"✅ **{fb['question']}** — Your answer was correct.")
                        else:
                            st.write(f"❌ **{fb['question']}** — You answered: *{fb['user_answer']}*. Correct: **{fb['correct_answer']}**")
                            st.caption(f"Explanation: {fb['explanation']}")

# ---------------- Tab 4: Performance Analytics ---------------- #
with tabs[3]:
    st.subheader("Performance Analytics & Progress Report")
    csv_report = engine.export_progress_report(uid)
    st.download_button("📥 Download Performance Report (CSV)", data=csv_report, file_name="learning_progress_report.csv", mime="text/csv")

    weak = engine.identify_weak_topics(uid)
    if weak:
        st.write("#### Topics Requiring Targeted Revision (< 70%):")
        st.table(weak)

# ---------------- Tab 5: Technical Guide ---------------- #
with tabs[4]:
    st.subheader("System Architecture & Grounded Question Generation")
    st.markdown("""
    ### Grounded Question Generation Principles
    - **No Hallucinated Facts:** Questions and distractors are synthesized exclusively from the provided source document.
    - **Definitional & Relational Parsing:** Analyzes grammatical structures to extract core assertions and concepts.
    - **Adaptive Weak-Topic Tracking:** Tracks rolling test performance and automatically prioritizes spaced repetition for concepts below 70% mastery.
    """)
