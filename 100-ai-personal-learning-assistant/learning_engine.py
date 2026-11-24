"""
Core Learning Engine and Analytics Service.
Manages user progress, quiz grading, weak topic diagnosis,
revision recommendations, and CSV report export.
"""
import os
import csv
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import sqlite3

import database
from auth import hash_password, verify_password
from content_processor import ContentProcessor, GeneratedQuestion


class LearningEngine:
    def __init__(self, db_path: str = database.DEFAULT_DB_PATH):
        self.db_path = db_path
        database.init_db(self.db_path)
        self.processor = ContentProcessor()

    # ---------------- User Management ---------------- #

    def register_user(self, username: str, password: str) -> Optional[int]:
        pwd_hash, pwd_salt = hash_password(password)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        try:
            with database.get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, password_hash, password_salt, created_at)
                    VALUES (?, ?, ?, ?)
                """, (username, pwd_hash, pwd_salt, ts))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        with database.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row and verify_password(password, row["password_hash"], row["password_salt"]):
                return {"id": row["id"], "username": row["username"]}
        return None

    # ---------------- Subject & Topic Management ---------------- #

    def add_subject(self, user_id: int, title: str, description: str = "") -> Optional[int]:
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        try:
            with database.get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO subjects (user_id, title, description, created_at)
                    VALUES (?, ?, ?, ?)
                """, (user_id, title, description, ts))
                conn.commit()
                return cursor.lastrowid
        except sqlite3.IntegrityError:
            return None

    def get_subjects(self, user_id: int) -> List[Dict[str, Any]]:
        with database.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM subjects WHERE user_id = ? ORDER BY id ASC", (user_id,))
            return [dict(r) for r in cursor.fetchall()]

    def add_topic_with_content(
        self,
        user_id: int,
        subject_id: int,
        title: str,
        content: str,
        source_filename: str = "manual_entry.txt"
    ) -> Dict[str, Any]:
        """
        Creates a learning topic, generates conceptual summary,
        synthesizes grounded questions, and saves to database.
        """
        summary = self.processor.generate_topic_summary(content)
        questions = self.processor.generate_grounded_questions(content, num_questions=4)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        with database.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO topics (subject_id, user_id, title, content_text, summary, source_filename, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (subject_id, user_id, title, content, summary, source_filename, ts))
            topic_id = cursor.lastrowid

            # Save generated questions
            for q in questions:
                cursor.execute("""
                    INSERT INTO questions (
                        topic_id, question_text, question_type, options_json,
                        correct_answer, explanation, source_excerpt
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    topic_id, q.question_text, q.question_type,
                    json.dumps(q.options), q.correct_answer, q.explanation, q.source_excerpt
                ))
            conn.commit()

        return {
            "topic_id": topic_id,
            "title": title,
            "summary": summary,
            "questions_generated": len(questions)
        }

    def get_topics(self, user_id: int, subject_id: Optional[int] = None) -> List[Dict[str, Any]]:
        with database.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            if subject_id:
                cursor.execute("SELECT * FROM topics WHERE user_id = ? AND subject_id = ? ORDER BY id ASC", (user_id, subject_id))
            else:
                cursor.execute("SELECT * FROM topics WHERE user_id = ? ORDER BY id ASC", (user_id,))
            return [dict(r) for r in cursor.fetchall()]

    def get_questions_for_topic(self, topic_id: int) -> List[Dict[str, Any]]:
        with database.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM questions WHERE topic_id = ? ORDER BY id ASC", (topic_id,))
            rows = cursor.fetchall()
            result = []
            for r in rows:
                d = dict(r)
                d["options"] = json.loads(d["options_json"]) if d["options_json"] else []
                result.append(d)
            return result

    # ---------------- Quiz Grading & Performance ---------------- #

    def grade_quiz(
        self,
        user_id: int,
        topic_id: int,
        user_answers: Dict[int, str]
    ) -> Dict[str, Any]:
        """
        Grades submitted quiz answers against ground truth.
        Computes score, updates quiz_attempts, and updates revision alerts.
        """
        questions = self.get_questions_for_topic(topic_id)
        if not questions:
            return {"error": "No questions found for this topic."}

        correct_count = 0
        feedback = []

        for q in questions:
            qid = q["id"]
            user_ans = user_answers.get(qid, "").strip()
            correct_ans = q["correct_answer"].strip()

            is_correct = False
            if q["question_type"] == "mcq":
                is_correct = (user_ans.lower() == correct_ans.lower())
            else:
                # Short answer: flexible case-insensitive match or substring
                is_correct = (user_ans.lower() in correct_ans.lower() or correct_ans.lower() in user_ans.lower()) and len(user_ans) > 1

            if is_correct:
                correct_count += 1

            feedback.append({
                "question_id": qid,
                "question": q["question_text"],
                "user_answer": user_ans,
                "correct_answer": correct_ans,
                "is_correct": is_correct,
                "explanation": q["explanation"]
            })

        score_pct = round((correct_count / len(questions)) * 100.0, 1)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        with database.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO quiz_attempts (user_id, topic_id, score_pct, total_questions, correct_count, completed_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (user_id, topic_id, score_pct, len(questions), correct_count, ts))

            # Revision scheduling
            if score_pct < 70.0:
                cursor.execute("""
                    INSERT INTO revision_recommendations (user_id, topic_id, priority, reason, created_at)
                    VALUES (?, ?, 'HIGH', 'Recent quiz score below 70% threshold', ?)
                """, (user_id, topic_id, ts))
            conn.commit()

        return {
            "score_pct": score_pct,
            "total_questions": len(questions),
            "correct_count": correct_count,
            "feedback": feedback
        }

    def identify_weak_topics(self, user_id: int, threshold_pct: float = 70.0) -> List[Dict[str, Any]]:
        """
        Identifies learning topics where the user's average quiz performance is below threshold.
        """
        with database.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    t.id as topic_id,
                    t.title as topic_title,
                    s.title as subject_title,
                    AVG(a.score_pct) as avg_score,
                    COUNT(a.id) as attempts_count
                FROM topics t
                JOIN subjects s ON t.subject_id = s.id
                LEFT JOIN quiz_attempts a ON t.id = a.topic_id AND a.user_id = ?
                WHERE t.user_id = ?
                GROUP BY t.id
                HAVING avg_score IS NOT NULL AND avg_score < ?
                ORDER BY avg_score ASC
            """, (user_id, user_id, threshold_pct))
            rows = cursor.fetchall()
            return [dict(r) for r in rows]

    def get_revision_recommendations(self, user_id: int) -> List[Dict[str, Any]]:
        """Retrieves active revision recommendations for weak topics."""
        weak = self.identify_weak_topics(user_id)
        recommendations = []
        for w in weak:
            recommendations.append({
                "topic_id": w["topic_id"],
                "topic": w["topic_title"],
                "subject": w["subject_title"],
                "avg_score": round(w["avg_score"], 1),
                "attempts": w["attempts_count"],
                "recommendation": f"Review key summaries and retake quiz for '{w['topic_title']}'."
            })
        return recommendations

    def export_progress_report(self, user_id: int, output_csv: Optional[str] = None) -> str:
        """Exports user learning progress and quiz attempt history to CSV."""
        with database.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT
                    s.title as subject,
                    t.title as topic,
                    COALESCE(AVG(a.score_pct), 0) as average_score,
                    COUNT(a.id) as attempts,
                    CASE
                        WHEN AVG(a.score_pct) >= 85 THEN 'Mastered'
                        WHEN AVG(a.score_pct) >= 70 THEN 'Proficient'
                        WHEN COUNT(a.id) = 0 THEN 'Unattempted'
                        ELSE 'Needs Revision'
                    END as mastery_status
                FROM topics t
                JOIN subjects s ON t.subject_id = s.id
                LEFT JOIN quiz_attempts a ON t.id = a.topic_id AND a.user_id = ?
                WHERE t.user_id = ?
                GROUP BY t.id
                ORDER BY s.title ASC, t.title ASC
            """, (user_id, user_id))
            rows = [dict(r) for r in cursor.fetchall()]

        import io
        buf = io.StringIO()
        writer = csv.DictWriter(buf, fieldnames=["subject", "topic", "average_score", "attempts", "mastery_status"])
        writer.writeheader()
        for r in rows:
            r["average_score"] = round(r["average_score"], 1)
            writer.writerow(r)

        csv_str = buf.getvalue()
        if output_csv:
            os.makedirs(os.path.dirname(os.path.abspath(output_csv)), exist_ok=True)
            with open(output_csv, "w", encoding="utf-8") as f:
                f.write(csv_str)

        return csv_str
