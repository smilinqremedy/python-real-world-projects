"""
Core Attendance Service Layer.
Enforces informed consent, biometric matching, duplicate prevention,
manual alternative access, and administrative override corrections.
"""
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import sqlite3
import numpy as np
from PIL import Image

import database
from auth import hash_password, verify_password
from biometrics import (
    extract_face_embedding,
    match_embedding_against_gallery,
    BiometricConsentError
)


class AttendanceService:
    def __init__(self, db_path: str = database.DEFAULT_DB_PATH):
        self.db_path = db_path
        database.init_db(self.db_path)

    # ---------------- User Management & Auth ---------------- #

    def create_user(self, username: str, password: str, role: str = "operator", actor: str = "system") -> bool:
        """Creates a new administrative or operator user."""
        pwd_hash, pwd_salt = hash_password(password)
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")
        try:
            with database.get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO users (username, password_hash, password_salt, role, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (username, pwd_hash, pwd_salt, role, ts))
                conn.commit()
            database.log_audit_event(actor, "USER_CREATED", f"Created user {username} with role {role}", self.db_path)
            return True
        except sqlite3.IntegrityError:
            return False

    def authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        """Authenticates user credentials and returns user details or None."""
        with database.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
            row = cursor.fetchone()
            if row and verify_password(password, row["password_hash"], row["password_salt"]):
                database.log_audit_event(username, "AUTH_LOGIN_SUCCESS", "User logged in", self.db_path)
                return {"id": row["id"], "username": row["username"], "role": row["role"]}
        database.log_audit_event(username, "AUTH_LOGIN_FAILED", "Failed login attempt", self.db_path)
        return None

    # ---------------- Participant Registration & Consent ---------------- #

    def register_participant(
        self,
        employee_id: str,
        full_name: str,
        department: str,
        email: str,
        consent_granted: bool,
        opt_in_biometrics: bool,
        face_image: Optional[Image.Image] = None,
        actor: str = "admin"
    ) -> Dict[str, Any]:
        """
        Registers a participant with informed consent compliance.
        If opt_in_biometrics is False, registers for manual alternative attendance without collecting face embeddings.
        If consent_granted is False, registration is strictly rejected.
        """
        if not consent_granted:
            raise BiometricConsentError(
                "Registration rejected: Informed consent is legally and ethically mandatory for enrollment."
            )

        embedding_blob = None
        if opt_in_biometrics:
            if face_image is None:
                raise ValueError("Biometric opt-in requires a valid face image during enrollment.")
            emb = extract_face_embedding(face_image)
            embedding_blob = database.serialize_embedding(emb)

        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        try:
            with database.get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO participants (
                        employee_id, full_name, department, email, consent_granted,
                        consent_timestamp, opt_in_biometrics, biometric_embedding, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    employee_id, full_name, department, email, 1 if consent_granted else 0,
                    ts, 1 if opt_in_biometrics else 0, embedding_blob, ts
                ))
                conn.commit()
                pid = cursor.lastrowid

            details = f"Enrolled participant {full_name} ({employee_id}), BiometricOptIn={opt_in_biometrics}"
            database.log_audit_event(actor, "PARTICIPANT_REGISTERED", details, self.db_path)

            return {
                "success": True,
                "participant_id": pid,
                "employee_id": employee_id,
                "opt_in_biometrics": opt_in_biometrics
            }
        except sqlite3.IntegrityError:
            return {"success": False, "error": f"Participant with Employee ID '{employee_id}' already exists."}

    # ---------------- Session Management ---------------- #

    def create_session(self, session_code: str, session_name: str, session_date: str, created_by: str) -> bool:
        """Creates a named attendance session (e.g. MORNING_2026_11_24)."""
        try:
            with database.get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO attendance_sessions (session_code, session_name, session_date, created_by)
                    VALUES (?, ?, ?, ?)
                """, (session_code, session_name, session_date, created_by))
                conn.commit()
            database.log_audit_event(created_by, "SESSION_CREATED", f"Created session {session_code} - {session_name}", self.db_path)
            return True
        except sqlite3.IntegrityError:
            return False

    def get_session_by_code(self, session_code: str) -> Optional[Dict[str, Any]]:
        with database.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM attendance_sessions WHERE session_code = ?", (session_code,))
            row = cursor.fetchone()
            return dict(row) if row else None

    # ---------------- Attendance Recording ---------------- #

    def get_consenting_biometric_gallery(self) -> List[Tuple[int, str, np.ndarray]]:
        """Retrieves active participants who consented and opted into biometric matching."""
        gallery = []
        with database.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, full_name, biometric_embedding FROM participants
                WHERE is_active = 1 AND consent_granted = 1 AND opt_in_biometrics = 1 AND biometric_embedding IS NOT NULL
            """)
            rows = cursor.fetchall()
            for r in rows:
                emb = database.deserialize_embedding(r["biometric_embedding"])
                gallery.append((r["id"], r["full_name"], emb))
        return gallery

    def record_attendance_by_face(
        self,
        session_code: str,
        face_image: Image.Image,
        actor: str = "system"
    ) -> Dict[str, Any]:
        """
        Extracts facial embedding from query image, matches against gallery,
        and records attendance. Prevents duplicate session check-ins.
        """
        session = self.get_session_by_code(session_code)
        if not session:
            return {"success": False, "error": f"Session '{session_code}' does not exist."}
        if not session["is_open"]:
            return {"success": False, "error": f"Session '{session_code}' is closed."}

        query_emb = extract_face_embedding(face_image)
        gallery = self.get_consenting_biometric_gallery()

        if not gallery:
            return {"success": False, "error": "No consenting biometric participants registered in database."}

        match = match_embedding_against_gallery(query_emb, gallery, similarity_threshold=0.82)
        if not match:
            database.log_audit_event(actor, "ATTENDANCE_MATCH_FAILED", f"No match for session {session_code}", self.db_path)
            return {"success": False, "error": "Face not recognized or similarity score below verified threshold."}

        pid, name, score = match
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        try:
            with database.get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO attendance_records (
                        session_id, participant_id, timestamp, date, method, confidence_score, verified_by
                    ) VALUES (?, ?, ?, ?, 'facial_biometric', ?, ?)
                """, (session["id"], pid, ts, session["session_date"], score, actor))
                conn.commit()
                rec_id = cursor.lastrowid

            log_msg = f"Check-in verified for {name} (ID: {pid}), Session: {session_code}, Confidence: {score}"
            database.log_audit_event(actor, "ATTENDANCE_RECORDED", log_msg, self.db_path)

            return {
                "success": True,
                "record_id": rec_id,
                "participant_id": pid,
                "participant_name": name,
                "method": "facial_biometric",
                "confidence_score": score,
                "timestamp": ts
            }
        except sqlite3.IntegrityError:
            # UNIQUE(session_id, participant_id) triggered
            return {
                "success": False,
                "error": f"Duplicate attendance: {name} is already checked in for session '{session_code}'."
            }

    def record_attendance_manual(
        self,
        session_code: str,
        employee_id: str,
        verified_by: str,
        notes: str = "Manual alternative check-in"
    ) -> Dict[str, Any]:
        """
        Manual attendance alternative for non-consenting participants or administrative check-in.
        Prevents duplicate check-in.
        """
        session = self.get_session_by_code(session_code)
        if not session:
            return {"success": False, "error": f"Session '{session_code}' does not exist."}

        with database.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id, full_name FROM participants WHERE employee_id = ?", (employee_id,))
            p = cursor.fetchone()

        if not p:
            return {"success": False, "error": f"Participant with Employee ID '{employee_id}' not found."}

        pid = p["id"]
        name = p["full_name"]
        ts = datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M:%S UTC")

        try:
            with database.get_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO attendance_records (
                        session_id, participant_id, timestamp, date, method, verified_by, notes
                    ) VALUES (?, ?, ?, ?, 'manual_alternative', ?, ?)
                """, (session["id"], pid, ts, session["session_date"], verified_by, notes))
                conn.commit()
                rec_id = cursor.lastrowid

            database.log_audit_event(
                verified_by, "ATTENDANCE_MANUAL_RECORDED",
                f"Manual check-in for {name} ({employee_id}), Session: {session_code}", self.db_path
            )
            return {
                "success": True,
                "record_id": rec_id,
                "participant_id": pid,
                "participant_name": name,
                "method": "manual_alternative",
                "timestamp": ts
            }
        except sqlite3.IntegrityError:
            return {
                "success": False,
                "error": f"Duplicate attendance: {name} is already checked in for session '{session_code}'."
            }

    # ---------------- Admin Override & Correction ---------------- #

    def correct_attendance_record(
        self,
        record_id: int,
        new_status: str,
        justification: str,
        admin_user: str
    ) -> bool:
        """Allows administrators to correct or amend attendance with mandatory audit justification."""
        if not justification or len(justification.strip()) < 5:
            raise ValueError("A documented administrative justification is required for attendance correction.")

        with database.get_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM attendance_records WHERE id = ?", (record_id,))
            rec = cursor.fetchone()
            if not rec:
                return False

            old_status = rec["status"]
            cursor.execute("""
                UPDATE attendance_records
                SET status = ?, notes = notes || ' | Correction by ' || ? || ': ' || ?
                WHERE id = ?
            """, (new_status, admin_user, justification, record_id))
            conn.commit()

        database.log_audit_event(
            admin_user, "ATTENDANCE_CORRECTED",
            f"Record {record_id} changed from {old_status} to {new_status}. Justification: {justification}",
            self.db_path
        )
        return True
