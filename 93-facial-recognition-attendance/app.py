"""
Streamlit Web Interface for AI Facial Recognition Attendance System.
Enforces informed consent, ethical biometrics, manual alternatives, and audit logging.
"""
import io
import os
import streamlit as st
from PIL import Image
from attendance_service import AttendanceService
from reporter import AttendanceReporter
from biometrics import BiometricConsentError
import database

st.set_page_config(
    page_title="Facial Recognition Attendance",
    page_icon="🛡️",
    layout="wide"
)

st.title("🛡️ AI-Powered Facial Recognition Attendance System")
st.markdown("Ethical Biometrics, Informed Consent Compliance, and Multi-Modal Verification.")

service = AttendanceService()
reporter = AttendanceReporter()

# Privacy notice banner
st.info(
    "🔒 **PRIVACY & BIOMETRIC COMPLIANCE:** Raw facial photographs are never saved to disk. "
    "Only 128-dimensional irreversible mathematical vectors are stored. Participants have the right "
    "to select the manual attendance alternative at any time."
)

tabs = st.tabs([
    "📸 Check-In (Biometric / Manual)",
    "📝 Participant Registration",
    "📅 Session Manager",
    "📊 Reports & CSV Export",
    "📜 Audit Log & Ethics"
])

# ---------------- Tab 1: Check-in ---------------- #
with tabs[0]:
    st.subheader("Attendance Verification")
    session_code = st.text_input("Enter Active Session Code (e.g. DAILY_2026_11_24):", value="DEMO_SESSION")

    checkin_mode = st.radio("Verification Method:", ["📸 Facial Recognition", "✍️ Manual Alternative (Consent Opt-Out)"])

    if checkin_mode == "📸 Facial Recognition":
        img_file = st.file_uploader("Upload Face Image for Matching", type=["png", "jpg", "jpeg"])
        if st.button("Verify & Check In"):
            if not img_file:
                st.error("Please upload a facial image.")
            else:
                img = Image.open(img_file)
                res = service.record_attendance_by_face(session_code.strip(), img, actor="kiosk_operator")
                if res["success"]:
                    st.success(f"✅ Verified: **{res['participant_name']}** (Confidence: {res['confidence_score'] * 100:.1f}%)")
                    st.info(f"Recorded at `{res['timestamp']}`")
                else:
                    st.error(f"❌ {res['error']}")
    else:
        emp_id = st.text_input("Enter Employee / Participant ID:")
        notes = st.text_input("Manual Reason / Notes:", value="Manual check-in option chosen")
        if st.button("Record Manual Attendance"):
            if not emp_id:
                st.error("Please enter Employee ID.")
            else:
                res = service.record_attendance_manual(session_code.strip(), emp_id.strip(), "admin", notes)
                if res["success"]:
                    st.success(f"✅ Recorded Manual Check-In: **{res['participant_name']}**")
                else:
                    st.error(f"❌ {res['error']}")

# ---------------- Tab 2: Participant Registration ---------------- #
with tabs[1]:
    st.subheader("Register New Participant")
    with st.form("reg_form"):
        emp_id = st.text_input("Employee / Student ID (e.g. EMP-101):")
        full_name = st.text_input("Full Name:")
        dept = st.text_input("Department / Cohort:", value="Engineering")
        email = st.text_input("Email:")

        st.markdown("#### Informed Consent Declaration")
        consent_cb = st.checkbox("I confirm that the participant has reviewed the Biometric Privacy Notice and granted informed consent.")
        opt_in_bio = st.checkbox("Opt into facial biometric recognition (Uncheck for manual-only alternative).", value=True)

        face_upload = st.file_uploader("Participant Enrollment Photo (Required if opting into biometrics):", type=["png", "jpg", "jpeg"])
        submitted = st.form_submit_button("Register Participant")

        if submitted:
            if not emp_id or not full_name:
                st.error("Employee ID and Full Name are required.")
            elif not consent_cb:
                st.error("Informed consent is mandatory for registration under privacy regulations.")
            elif opt_in_bio and not face_upload:
                st.error("An enrollment face image is required when biometric recognition is opted in.")
            else:
                try:
                    face_img = Image.open(face_upload) if (opt_in_bio and face_upload) else None
                    res = service.register_participant(
                        employee_id=emp_id.strip(),
                        full_name=full_name.strip(),
                        department=dept.strip(),
                        email=email.strip(),
                        consent_granted=consent_cb,
                        opt_in_biometrics=opt_in_bio,
                        face_image=face_img,
                        actor="admin"
                    )
                    if res["success"]:
                        st.success(f"Participant **{full_name}** successfully enrolled (Biometric: {opt_in_bio})!")
                    else:
                        st.error(res["error"])
                except Exception as e:
                    st.error(f"Enrollment Error: {e}")

# ---------------- Tab 3: Session Management ---------------- #
with tabs[2]:
    st.subheader("Attendance Session Management")
    with st.form("session_form"):
        s_code = st.text_input("Session Code (Unique):", value="SESSION_001")
        s_name = st.text_input("Session Description:", value="Morning Standup / Lecture")
        s_date = st.date_input("Session Date:")
        create_btn = st.form_submit_button("Create Session")

        if create_btn:
            ok = service.create_session(s_code.strip(), s_name.strip(), str(s_date), "admin")
            if ok:
                st.success(f"Session '{s_code}' created successfully!")
            else:
                st.error(f"Session code '{s_code}' already exists.")

# ---------------- Tab 4: Reports & CSV Export ---------------- #
with tabs[3]:
    st.subheader("Attendance Reports & Analytics")
    query_session = st.text_input("Filter by Session Code:", value="DEMO_SESSION")
    if st.button("Fetch Session Report"):
        recs = reporter.get_session_attendance(query_session.strip())
        if recs:
            st.dataframe(recs)
            csv_data = reporter.export_to_csv(recs)
            st.download_button("📥 Export to CSV", data=csv_data, file_name=f"{query_session}_report.csv", mime="text/csv")
        else:
            st.info("No attendance records found for this session.")

# ---------------- Tab 5: Ethics & Audit Log ---------------- #
with tabs[4]:
    st.subheader("Security Audit Trail")
    with database.get_connection(service.db_path) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM audit_logs ORDER BY id DESC LIMIT 50")
        logs = [dict(r) for r in cursor.fetchall()]

    if logs:
        st.dataframe(logs)
    else:
        st.write("Audit log is currently empty.")
