"""
Database schema for Automated Job Application Email Assistant.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "job_applications.db")


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            recruitment_email TEXT NOT NULL,
            industry TEXT,
            website TEXT,
            notes TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE NOT NULL,
            title TEXT NOT NULL,
            job_url TEXT,
            salary_range TEXT,
            status TEXT CHECK(status IN ('Saved', 'Drafting', 'Applied', 'Interviewing', 'Rejected', 'Offer')) DEFAULT 'Saved',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS email_templates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            subject_template TEXT NOT NULL,
            body_template TEXT NOT NULL,
            is_default INTEGER DEFAULT 0 CHECK(is_default IN (0, 1))
        );

        CREATE TABLE IF NOT EXISTS sent_applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vacancy_id INTEGER REFERENCES vacancies(id) ON DELETE SET NULL,
            company_name TEXT NOT NULL,
            recipient_email TEXT NOT NULL,
            job_title TEXT NOT NULL,
            subject TEXT NOT NULL,
            body TEXT NOT NULL,
            cv_filename TEXT,
            cv_path TEXT,
            status TEXT CHECK(status IN ('Sent', 'Follow-up Needed', 'Interviewing', 'Rejected', 'Offer')) DEFAULT 'Sent',
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            notes TEXT
        );

        -- Insert standard default templates if empty
        INSERT OR IGNORE INTO email_templates (id, name, subject_template, body_template, is_default)
        VALUES (
            1,
            'Standard Application',
            'Application for {job_title} - {candidate_name}',
            'Dear {recruiter_name},\n\nI am writing to express my strong interest in the {job_title} position at {company}.\n\nWith {years_experience} years of experience in software engineering and hands-on expertise in {candidate_skills}, I have successfully built and delivered reliable, high-performing systems. I admire {company}''s mission and would be thrilled to contribute to your engineering goals.\n\nPlease find my resume attached for your review. I look forward to the opportunity to discuss how my background aligns with your requirements.\n\nWarm regards,\n{candidate_name}\n{candidate_phone} | {candidate_email}',
            1
        );

        INSERT OR IGNORE INTO email_templates (id, name, subject_template, body_template, is_default)
        VALUES (
            2,
            'Senior Technical Role',
            '{candidate_name} - {job_title} Application',
            'Dear Hiring Team at {company},\n\nI am writing to apply for the {job_title} role at {company}. Over the past {years_experience}+ years, I have architected and maintained production services using {candidate_skills}.\n\nI specialize in clean architecture, database optimization, and scalable backend services. Having followed {company}''s recent milestones, I am eager to bring this engineering discipline to your team.\n\nMy complete CV is attached. I welcome the opportunity to discuss my qualifications further.\n\nBest regards,\n{candidate_name}\n{candidate_email} | {candidate_phone}',
            0
        );

        INSERT OR IGNORE INTO email_templates (id, name, subject_template, body_template, is_default)
        VALUES (
            3,
            'Application Follow-up',
            'Following up on Application for {job_title} - {candidate_name}',
            'Dear {recruiter_name},\n\nI hope this email finds you well. I am following up on my application for the {job_title} role at {company} submitted recently.\n\nI remain very enthusiastic about the opportunity to join {company} and contribute my expertise in {candidate_skills}.\n\nPlease let me know if any additional details or references are required.\n\nThank you for your time and consideration.\n\nSincerely,\n{candidate_name}\n{candidate_email}',
            0
        );
        """)
    conn.close()
