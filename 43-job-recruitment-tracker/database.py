"""
Database initialization and schema definition for Job Recruitment and Applicant Tracking System.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "recruitment_tracker.db")


def get_connection(db_path=None):
    """Establish SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    """Initialize database tables, foreign keys, and indexes."""
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        -- Users & Roles (Admin, Recruiter, Hiring Manager)
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id TEXT UNIQUE NOT NULL,
            username TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            salt TEXT NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            role TEXT CHECK(role IN ('admin', 'recruiter', 'hiring_manager')) NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Client Companies
        CREATE TABLE IF NOT EXISTS companies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            company_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            industry TEXT NOT NULL,
            contact_person TEXT NOT NULL,
            email TEXT NOT NULL,
            phone TEXT NOT NULL,
            location TEXT NOT NULL,
            website TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Job Vacancies
        CREATE TABLE IF NOT EXISTS vacancies (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            vacancy_code TEXT UNIQUE NOT NULL,
            company_id INTEGER REFERENCES companies(id) ON DELETE CASCADE NOT NULL,
            title TEXT NOT NULL,
            department TEXT NOT NULL,
            employment_type TEXT CHECK(employment_type IN ('Full-time', 'Part-time', 'Contract', 'Remote', 'Hybrid')) NOT NULL,
            location TEXT NOT NULL,
            salary_min REAL CHECK(salary_min >= 0),
            salary_max REAL CHECK(salary_max >= salary_min),
            min_years_experience REAL DEFAULT 0.0 CHECK(min_years_experience >= 0),
            required_skills TEXT NOT NULL,
            job_description TEXT NOT NULL,
            requirements TEXT NOT NULL,
            status TEXT CHECK(status IN ('Open', 'Closed', 'On Hold')) DEFAULT 'Open',
            created_by INTEGER REFERENCES users(id) ON DELETE SET NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            closing_date TEXT
        );

        -- Job Applicants / Candidates
        CREATE TABLE IF NOT EXISTS candidates (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            candidate_code TEXT UNIQUE NOT NULL,
            full_name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            location TEXT NOT NULL,
            current_title TEXT,
            years_experience REAL NOT NULL CHECK(years_experience >= 0),
            skills TEXT NOT NULL,
            education_level TEXT,
            linkedin_portfolio TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Uploaded CV Documents (Local file storage metadata)
        CREATE TABLE IF NOT EXISTS cv_documents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            file_ref TEXT UNIQUE NOT NULL,
            candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE NOT NULL,
            original_filename TEXT NOT NULL,
            stored_filename TEXT NOT NULL,
            file_path TEXT NOT NULL,
            file_type TEXT NOT NULL CHECK(file_type IN ('pdf', 'docx', 'doc', 'txt')),
            file_size_bytes INTEGER NOT NULL CHECK(file_size_bytes > 0),
            checksum_sha256 TEXT NOT NULL,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Job Applications
        CREATE TABLE IF NOT EXISTS applications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_ref TEXT UNIQUE NOT NULL,
            vacancy_id INTEGER REFERENCES vacancies(id) ON DELETE CASCADE NOT NULL,
            candidate_id INTEGER REFERENCES candidates(id) ON DELETE CASCADE NOT NULL,
            cv_id INTEGER REFERENCES cv_documents(id) ON DELETE SET NULL,
            status TEXT CHECK(status IN ('Submitted', 'Under Review', 'Shortlisted', 'Interview Scheduled', 'Accepted', 'Rejected')) DEFAULT 'Submitted',
            cover_letter TEXT,
            applied_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            UNIQUE(vacancy_id, candidate_id) -- Prevents duplicate applications for same vacancy
        );

        -- Application Status Transition History
        CREATE TABLE IF NOT EXISTS application_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            application_id INTEGER REFERENCES applications(id) ON DELETE CASCADE NOT NULL,
            old_status TEXT,
            new_status TEXT NOT NULL,
            changed_by_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            notes TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Scheduled Interviews
        CREATE TABLE IF NOT EXISTS interviews (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interview_ref TEXT UNIQUE NOT NULL,
            application_id INTEGER REFERENCES applications(id) ON DELETE CASCADE NOT NULL,
            round_name TEXT CHECK(round_name IN ('Phone Screen', 'Technical Interview', 'Behavioral Interview', 'Panel Interview', 'Final Round')) NOT NULL,
            scheduled_datetime TEXT NOT NULL,
            interviewer_name TEXT NOT NULL,
            interviewer_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            meeting_link_or_location TEXT NOT NULL,
            status TEXT CHECK(status IN ('Scheduled', 'Completed', 'Rescheduled', 'Cancelled')) DEFAULT 'Scheduled',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Interview Evaluation & Feedback
        CREATE TABLE IF NOT EXISTS interview_feedback (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            interview_id INTEGER REFERENCES interviews(id) ON DELETE CASCADE NOT NULL,
            interviewer_user_id INTEGER REFERENCES users(id) ON DELETE SET NULL,
            interviewer_name TEXT NOT NULL,
            rating_overall INTEGER CHECK(rating_overall >= 1 AND rating_overall <= 5),
            technical_score INTEGER CHECK(technical_score >= 1 AND technical_score <= 5),
            communication_score INTEGER CHECK(communication_score >= 1 AND communication_score <= 5),
            problem_solving_score INTEGER CHECK(problem_solving_score >= 1 AND problem_solving_score <= 5),
            strengths TEXT NOT NULL,
            areas_for_improvement TEXT NOT NULL,
            recommendation TEXT CHECK(recommendation IN ('Strong Hire', 'Hire', 'Hold', 'Reject')) NOT NULL,
            notes TEXT,
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        -- Indexes for query optimization
        CREATE INDEX IF NOT EXISTS idx_vacancies_company ON vacancies(company_id);
        CREATE INDEX IF NOT EXISTS idx_applications_candidate ON applications(candidate_id);
        CREATE INDEX IF NOT EXISTS idx_applications_vacancy ON applications(vacancy_id);
        CREATE INDEX IF NOT EXISTS idx_applications_status ON applications(status);
        CREATE INDEX IF NOT EXISTS idx_history_app ON application_history(application_id);
        CREATE INDEX IF NOT EXISTS idx_interviews_app ON interviews(application_id);
        """)
    conn.close()
