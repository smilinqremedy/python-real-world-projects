"""
Business logic and service operations for the Online Examination Management System.
"""
from datetime import datetime, timedelta
import re
from database import get_connection, init_db


class ExamService:
    def __init__(self, db_path=None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    @staticmethod
    def _validate_email(email):
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, email.strip()):
            raise ValueError(f"Invalid email format: {email}")

    # ==================== User Management ====================

    def register_user(self, user_id, name, email, role):
        user_id = user_id.strip().upper()
        name = name.strip()
        email = email.strip().lower()
        role = role.strip().lower()

        if not user_id or not name or not email:
            raise ValueError("User ID, name, and email are required.")
        if role not in ("student", "teacher", "admin"):
            raise ValueError("Role must be 'student', 'teacher', or 'admin'.")
        self._validate_email(email)

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO users (user_id, name, email, role) VALUES (?, ?, ?, ?)",
                    (user_id, name, email, role)
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError("User ID or email already registered.")
            raise
        finally:
            conn.close()

    def get_user_by_user_id(self, user_id):
        conn = self._get_connection()
        try:
            row = conn.execute(
                "SELECT * FROM users WHERE user_id = ?",
                (user_id.strip().upper(),)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_users_by_role(self, role):
        conn = self._get_connection()
        try:
            rows = conn.execute(
                "SELECT * FROM users WHERE role = ? ORDER BY name ASC",
                (role.strip().lower(),)
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Subject Management ====================

    def create_subject(self, code, title, description="", teacher_user_id=None):
        code = code.strip().upper()
        title = title.strip()
        if not code or not title:
            raise ValueError("Subject code and title are required.")

        conn = self._get_connection()
        try:
            teacher_id = None
            if teacher_user_id:
                t_row = conn.execute(
                    "SELECT id, role FROM users WHERE user_id = ?",
                    (teacher_user_id.strip().upper(),)
                ).fetchone()
                if not t_row:
                    raise ValueError(f"Teacher {teacher_user_id} not found.")
                if t_row["role"] not in ("teacher", "admin"):
                    raise ValueError("Assigned subject creator must be a teacher or admin.")
                teacher_id = t_row["id"]

            with conn:
                cursor = conn.execute(
                    "INSERT INTO subjects (code, title, description, teacher_id) VALUES (?, ?, ?, ?)",
                    (code, title, description.strip(), teacher_id)
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Subject code '{code}' already exists.")
            raise
        finally:
            conn.close()

    def list_subjects(self):
        conn = self._get_connection()
        try:
            rows = conn.execute("""
                SELECT s.*, u.name as teacher_name
                FROM subjects s
                LEFT JOIN users u ON s.teacher_id = u.id
                ORDER BY s.code ASC
            """).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Examination Setup ====================

    def create_exam(self, exam_code, subject_code, title, duration_minutes,
                    passing_score=50.0, start_window=None, end_window=None,
                    created_by_user_id=None):
        exam_code = exam_code.strip().upper()
        subject_code = subject_code.strip().upper()
        title = title.strip()

        if not exam_code or not title:
            raise ValueError("Exam code and title are required.")
        if duration_minutes <= 0:
            raise ValueError("Duration must be a positive integer in minutes.")
        if not (0 <= passing_score <= 100):
            raise ValueError("Passing score must be between 0 and 100%.")

        if start_window and end_window:
            start_dt = datetime.fromisoformat(start_window)
            end_dt = datetime.fromisoformat(end_window)
            if start_dt >= end_dt:
                raise ValueError("Exam start window must be before end window.")

        conn = self._get_connection()
        try:
            sub = conn.execute("SELECT id FROM subjects WHERE code = ?", (subject_code,)).fetchone()
            if not sub:
                raise ValueError(f"Subject '{subject_code}' not found.")
            subject_id = sub["id"]

            creator_id = None
            if created_by_user_id:
                u = conn.execute("SELECT id FROM users WHERE user_id = ?", (created_by_user_id.strip().upper(),)).fetchone()
                if u:
                    creator_id = u["id"]

            with conn:
                cursor = conn.execute("""
                    INSERT INTO exams (
                        exam_code, subject_id, title, duration_minutes,
                        passing_score, start_window, end_window, created_by
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (exam_code, subject_id, title, duration_minutes,
                      passing_score, start_window, end_window, creator_id))
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Exam code '{exam_code}' already exists.")
            raise
        finally:
            conn.close()

    def publish_exam(self, exam_code):
        conn = self._get_connection()
        try:
            with conn:
                exam = conn.execute("SELECT id FROM exams WHERE exam_code = ?", (exam_code.strip().upper(),)).fetchone()
                if not exam:
                    raise ValueError(f"Exam '{exam_code}' not found.")
                q_count = conn.execute("SELECT COUNT(*) as cnt FROM questions WHERE exam_id = ?", (exam["id"],)).fetchone()["cnt"]
                if q_count == 0:
                    raise ValueError(f"Cannot publish exam '{exam_code}' with no questions.")
                conn.execute("UPDATE exams SET is_published = 1 WHERE id = ?", (exam["id"],))
        finally:
            conn.close()

    def add_question(self, exam_code, question_number, question_text,
                     option_a, option_b, option_c, option_d,
                     correct_option, points=1.0):
        exam_code = exam_code.strip().upper()
        correct_option = correct_option.strip().upper()
        if correct_option not in ("A", "B", "C", "D"):
            raise ValueError("Correct option must be 'A', 'B', 'C', or 'D'.")
        if points <= 0:
            raise ValueError("Question points must be greater than zero.")
        if not question_text.strip():
            raise ValueError("Question text cannot be blank.")
        if not option_a.strip() or not option_b.strip() or not option_c.strip() or not option_d.strip():
            raise ValueError("All 4 options (A, B, C, D) must have text.")

        conn = self._get_connection()
        try:
            exam = conn.execute("SELECT id, is_published FROM exams WHERE exam_code = ?", (exam_code,)).fetchone()
            if not exam:
                raise ValueError(f"Exam '{exam_code}' not found.")
            if exam["is_published"]:
                raise ValueError("Cannot modify questions for an already published exam.")

            with conn:
                cursor = conn.execute("""
                    INSERT INTO questions (
                        exam_id, question_number, question_text,
                        option_a, option_b, option_c, option_d,
                        correct_option, points
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    exam["id"], question_number, question_text.strip(),
                    option_a.strip(), option_b.strip(), option_c.strip(), option_d.strip(),
                    correct_option, points
                ))
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Question number {question_number} already exists for this exam.")
            raise
        finally:
            conn.close()

    def get_exam_questions(self, exam_code, include_correct=False):
        conn = self._get_connection()
        try:
            exam = conn.execute("SELECT id FROM exams WHERE exam_code = ?", (exam_code.strip().upper(),)).fetchone()
            if not exam:
                raise ValueError(f"Exam '{exam_code}' not found.")

            rows = conn.execute("""
                SELECT id, question_number, question_text, option_a, option_b, option_c, option_d,
                       correct_option, points
                FROM questions
                WHERE exam_id = ?
                ORDER BY question_number ASC
            """, (exam["id"],)).fetchall()

            questions = []
            for r in rows:
                q = dict(r)
                if not include_correct:
                    q.pop("correct_option")
                questions.append(q)
            return questions
        finally:
            conn.close()

    # ==================== Assignments & Candidate Access ====================

    def assign_exam_to_student(self, exam_code, student_user_id):
        exam_code = exam_code.strip().upper()
        student_user_id = student_user_id.strip().upper()

        conn = self._get_connection()
        try:
            exam = conn.execute("SELECT id, is_published FROM exams WHERE exam_code = ?", (exam_code,)).fetchone()
            if not exam:
                raise ValueError(f"Exam '{exam_code}' not found.")

            student = conn.execute("SELECT id, role FROM users WHERE user_id = ?", (student_user_id,)).fetchone()
            if not student:
                raise ValueError(f"Student '{student_user_id}' not found.")
            if student["role"] != "student":
                raise ValueError(f"User '{student_user_id}' is not a student (role: {student['role']}).")

            with conn:
                cursor = conn.execute("""
                    INSERT INTO exam_assignments (exam_id, student_id, status)
                    VALUES (?, ?, 'assigned')
                """, (exam["id"], student["id"]))
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Student {student_user_id} is already assigned to exam {exam_code}.")
            raise
        finally:
            conn.close()

    def authorize_retake(self, exam_code, student_user_id):
        exam_code = exam_code.strip().upper()
        student_user_id = student_user_id.strip().upper()

        conn = self._get_connection()
        try:
            exam = conn.execute("SELECT id FROM exams WHERE exam_code = ?", (exam_code,)).fetchone()
            student = conn.execute("SELECT id FROM users WHERE user_id = ?", (student_user_id,)).fetchone()
            if not exam or not student:
                raise ValueError("Exam or Student not found.")

            with conn:
                updated = conn.execute("""
                    UPDATE exam_assignments
                    SET retake_authorized = 1, status = 'assigned'
                    WHERE exam_id = ? AND student_id = ?
                """, (exam["id"], student["id"])).rowcount
                if updated == 0:
                    raise ValueError("Student is not assigned to this exam.")
        finally:
            conn.close()

    def list_assigned_exams(self, student_user_id):
        student_user_id = student_user_id.strip().upper()
        conn = self._get_connection()
        try:
            student = conn.execute("SELECT id FROM users WHERE user_id = ?", (student_user_id,)).fetchone()
            if not student:
                raise ValueError(f"Student '{student_user_id}' not found.")

            rows = conn.execute("""
                SELECT ea.id as assignment_id, ea.status as assignment_status, ea.retake_authorized,
                       e.exam_code, e.title as exam_title, e.duration_minutes, e.passing_score,
                       e.start_window, e.end_window, e.is_published, s.code as subject_code, s.title as subject_title
                FROM exam_assignments ea
                JOIN exams e ON ea.exam_id = e.id
                JOIN subjects s ON e.subject_id = s.id
                WHERE ea.student_id = ?
                ORDER BY e.created_at DESC
            """, (student["id"],)).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Exam Sitting & Workflow ====================

    def start_exam(self, student_user_id, exam_code, current_time=None):
        student_user_id = student_user_id.strip().upper()
        exam_code = exam_code.strip().upper()
        now = current_time or datetime.now()

        conn = self._get_connection()
        try:
            student = conn.execute("SELECT id, role FROM users WHERE user_id = ?", (student_user_id,)).fetchone()
            if not student:
                raise ValueError(f"Student '{student_user_id}' not found.")
            if student["role"] != "student":
                raise ValueError(f"User '{student_user_id}' is not a student.")

            exam = conn.execute("""
                SELECT id, exam_code, title, duration_minutes, is_published, start_window, end_window
                FROM exams WHERE exam_code = ?
            """, (exam_code,)).fetchone()
            if not exam:
                raise ValueError(f"Exam '{exam_code}' not found.")
            if not exam["is_published"]:
                raise ValueError(f"Exam '{exam_code}' has not been published yet.")

            # Validate time window
            now_iso = now.isoformat()
            if exam["start_window"] and now_iso < exam["start_window"]:
                raise ValueError(f"Examination has not opened yet. Starts at {exam['start_window']}.")
            if exam["end_window"] and now_iso > exam["end_window"]:
                raise ValueError(f"Examination window has closed on {exam['end_window']}.")

            # Check assignment
            assignment = conn.execute("""
                SELECT id, status, retake_authorized
                FROM exam_assignments
                WHERE exam_id = ? AND student_id = ?
            """, (exam["id"], student["id"])).fetchone()

            if not assignment:
                raise ValueError(f"Student '{student_user_id}' is not assigned to exam '{exam_code}'.")

            if assignment["status"] == "completed" and not assignment["retake_authorized"]:
                raise ValueError(f"Student has already completed this examination and retake is not authorized.")

            # Check if active in_progress session exists
            active_session = conn.execute("""
                SELECT id, expires_at FROM exam_sessions
                WHERE assignment_id = ? AND status = 'in_progress'
            """, (assignment["id"],)).fetchone()

            if active_session:
                # If still active and not expired
                if datetime.fromisoformat(active_session["expires_at"]) > now:
                    return {
                        "session_id": active_session["id"],
                        "exam_code": exam_code,
                        "expires_at": active_session["expires_at"],
                        "resumed": True
                    }
                else:
                    # Auto-close expired session
                    self._auto_submit_session_internal(conn, active_session["id"], now)

            # Calculate session expiry
            duration = timedelta(minutes=exam["duration_minutes"])
            expires_at = now + duration
            if exam["end_window"]:
                end_dt = datetime.fromisoformat(exam["end_window"])
                if expires_at > end_dt:
                    expires_at = end_dt

            with conn:
                cursor = conn.execute("""
                    INSERT INTO exam_sessions (
                        assignment_id, exam_id, student_id, started_at, expires_at, status
                    ) VALUES (?, ?, ?, ?, ?, 'in_progress')
                """, (assignment["id"], exam["id"], student["id"], now.isoformat(), expires_at.isoformat()))
                session_id = cursor.lastrowid

                conn.execute("""
                    UPDATE exam_assignments
                    SET status = 'in_progress', retake_authorized = 0
                    WHERE id = ?
                """, (assignment["id"],))

            return {
                "session_id": session_id,
                "exam_code": exam_code,
                "expires_at": expires_at.isoformat(),
                "resumed": False
            }
        finally:
            conn.close()

    def answer_question(self, session_id, question_number, selected_option, current_time=None):
        selected_option = selected_option.strip().upper()
        if selected_option not in ("A", "B", "C", "D"):
            raise ValueError("Answer option must be A, B, C, or D.")
        now = current_time or datetime.now()

        conn = self._get_connection()
        try:
            session = conn.execute("""
                SELECT s.id, s.exam_id, s.status, s.expires_at
                FROM exam_sessions s
                WHERE s.id = ?
            """, (session_id,)).fetchone()
            if not session:
                raise ValueError(f"Exam session #{session_id} not found.")

            if session["status"] != "in_progress":
                raise ValueError(f"Session is {session['status']} and cannot accept answers.")

            # Check if time expired
            expires_dt = datetime.fromisoformat(session["expires_at"])
            if now > expires_dt:
                self._auto_submit_session_internal(conn, session_id, now)
                raise ValueError("Examination duration has expired. Session has been automatically submitted.")

            # Find question
            q = conn.execute("""
                SELECT id FROM questions
                WHERE exam_id = ? AND question_number = ?
            """, (session["exam_id"], question_number)).fetchone()
            if not q:
                raise ValueError(f"Question #{question_number} not found for this exam.")

            with conn:
                conn.execute("""
                    INSERT INTO student_answers (session_id, question_id, selected_option, answered_at)
                    VALUES (?, ?, ?, ?)
                    ON CONFLICT(session_id, question_id) DO UPDATE SET
                        selected_option = excluded.selected_option,
                        answered_at = excluded.answered_at
                """, (session_id, q["id"], selected_option, now.isoformat()))
            return True
        finally:
            conn.close()

    def submit_exam(self, session_id, current_time=None):
        now = current_time or datetime.now()
        conn = self._get_connection()
        try:
            session = conn.execute("""
                SELECT s.id, s.exam_id, s.status, s.expires_at, s.assignment_id
                FROM exam_sessions s
                WHERE s.id = ?
            """, (session_id,)).fetchone()
            if not session:
                raise ValueError(f"Exam session #{session_id} not found.")

            if session["status"] != "in_progress":
                raise ValueError(f"Session is already {session['status']}.")

            expires_dt = datetime.fromisoformat(session["expires_at"])
            is_auto = (now > expires_dt)
            status = "auto_submitted" if is_auto else "submitted"

            return self._grade_and_close_session(conn, session_id, status, now)
        finally:
            conn.close()

    def _auto_submit_session_internal(self, conn, session_id, now):
        self._grade_and_close_session(conn, session_id, "auto_submitted", now)

    def _grade_and_close_session(self, conn, session_id, final_status, now):
        session = conn.execute("""
            SELECT s.*, e.passing_score
            FROM exam_sessions s
            JOIN exams e ON s.exam_id = e.id
            WHERE s.id = ?
        """, (session_id,)).fetchone()

        questions = conn.execute("""
            SELECT id, correct_option, points
            FROM questions
            WHERE exam_id = ?
        """, (session["exam_id"],)).fetchall()

        total_points = sum(q["points"] for q in questions)
        earned_score = 0.0

        with conn:
            for q in questions:
                ans = conn.execute("""
                    SELECT id, selected_option
                    FROM student_answers
                    WHERE session_id = ? AND question_id = ?
                """, (session_id, q["id"])).fetchone()

                if ans and ans["selected_option"] == q["correct_option"]:
                    is_correct = 1
                    pts = q["points"]
                    earned_score += pts
                else:
                    is_correct = 0
                    pts = 0.0

                if ans:
                    conn.execute("""
                        UPDATE student_answers
                        SET is_correct = ?, points_awarded = ?
                        WHERE id = ?
                    """, (is_correct, pts, ans["id"]))

            percentage = round((earned_score / total_points * 100) if total_points > 0 else 0.0, 2)
            passed = 1 if percentage >= session["passing_score"] else 0

            conn.execute("""
                UPDATE exam_sessions
                SET submitted_at = ?, status = ?, score = ?,
                    total_points = ?, percentage = ?, passed = ?
                WHERE id = ?
            """, (now.isoformat(), final_status, earned_score, total_points, percentage, passed, session_id))

            conn.execute("""
                UPDATE exam_assignments
                SET status = 'completed'
                WHERE id = ?
            """, (session["assignment_id"],))

        return {
            "session_id": session_id,
            "status": final_status,
            "score": earned_score,
            "total_points": total_points,
            "percentage": percentage,
            "passed": bool(passed)
        }

    # ==================== Results & Analytics Reports ====================

    def get_session_result(self, session_id):
        conn = self._get_connection()
        try:
            session = conn.execute("""
                SELECT s.*, e.exam_code, e.title as exam_title, e.passing_score,
                       sub.code as subject_code, sub.title as subject_title,
                       u.user_id as student_code, u.name as student_name, u.email as student_email
                FROM exam_sessions s
                JOIN exams e ON s.exam_id = e.id
                JOIN subjects sub ON e.subject_id = sub.id
                JOIN users u ON s.student_id = u.id
                WHERE s.id = ?
            """, (session_id,)).fetchone()
            if not session:
                raise ValueError(f"Session #{session_id} not found.")

            answers = conn.execute("""
                SELECT q.question_number, q.question_text, q.option_a, q.option_b,
                       q.option_c, q.option_d, q.correct_option, q.points as max_points,
                       sa.selected_option, sa.is_correct, sa.points_awarded
                FROM questions q
                LEFT JOIN student_answers sa ON q.id = sa.question_id AND sa.session_id = ?
                WHERE q.exam_id = ?
                ORDER BY q.question_number ASC
            """, (session_id, session["exam_id"])).fetchall()

            result = dict(session)
            result["passed"] = bool(result["passed"])
            result["answers"] = [dict(a) for a in answers]
            return result
        finally:
            conn.close()

    def generate_exam_report(self, exam_code):
        exam_code = exam_code.strip().upper()
        conn = self._get_connection()
        try:
            exam = conn.execute("""
                SELECT e.*, s.code as subject_code, s.title as subject_title
                FROM exams e
                JOIN subjects s ON e.subject_id = s.id
                WHERE e.exam_code = ?
            """, (exam_code,)).fetchone()
            if not exam:
                raise ValueError(f"Exam '{exam_code}' not found.")

            total_assigned = conn.execute(
                "SELECT COUNT(*) as cnt FROM exam_assignments WHERE exam_id = ?",
                (exam["id"],)
            ).fetchone()["cnt"]

            completed_sessions = conn.execute("""
                SELECT s.score, s.percentage, s.passed, s.status, u.user_id, u.name
                FROM exam_sessions s
                JOIN users u ON s.student_id = u.id
                WHERE s.exam_id = ? AND s.status IN ('submitted', 'auto_submitted')
                ORDER BY s.score DESC
            """, (exam["id"],)).fetchall()

            total_sat = len(completed_sessions)
            passed_count = sum(1 for s in completed_sessions if s["passed"])
            failed_count = total_sat - passed_count
            pass_rate = round((passed_count / total_sat * 100) if total_sat > 0 else 0.0, 2)

            scores = [s["percentage"] for s in completed_sessions]
            avg_score = round(sum(scores) / total_sat, 2) if total_sat > 0 else 0.0
            highest_score = max(scores) if scores else 0.0
            lowest_score = min(scores) if scores else 0.0

            # Question difficulty analytics
            questions = conn.execute("""
                SELECT q.id, q.question_number, q.question_text, q.points,
                       COUNT(sa.id) as total_answers,
                       COALESCE(SUM(sa.is_correct), 0) as correct_answers
                FROM questions q
                LEFT JOIN student_answers sa ON q.id = sa.question_id
                WHERE q.exam_id = ?
                GROUP BY q.id
                ORDER BY q.question_number ASC
            """, (exam["id"],)).fetchall()

            question_stats = []
            for q in questions:
                ans_cnt = q["total_answers"]
                corr_cnt = q["correct_answers"]
                accuracy = round((corr_cnt / ans_cnt * 100) if ans_cnt > 0 else 0.0, 2)
                question_stats.append({
                    "question_number": q["question_number"],
                    "question_text": q["question_text"],
                    "points": q["points"],
                    "total_answered": ans_cnt,
                    "correct_count": corr_cnt,
                    "accuracy_pct": accuracy
                })

            return {
                "exam_code": exam["exam_code"],
                "exam_title": exam["title"],
                "subject": f"{exam['subject_code']} - {exam['subject_title']}",
                "total_assigned": total_assigned,
                "total_sat": total_sat,
                "passed_count": passed_count,
                "failed_count": failed_count,
                "pass_rate_pct": pass_rate,
                "average_score_pct": avg_score,
                "highest_score_pct": highest_score,
                "lowest_score_pct": lowest_score,
                "student_rankings": [dict(s) for s in completed_sessions],
                "question_analytics": question_stats
            }
        finally:
            conn.close()
