"""
Database schema for Website Contact Form Spam Detection System.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "spam_detection.db")


def get_connection(db_path=None):
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS form_submissions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            submission_ref TEXT UNIQUE NOT NULL,
            sender_name TEXT NOT NULL,
            email TEXT NOT NULL,
            subject TEXT NOT NULL,
            message TEXT NOT NULL,
            ip_hash TEXT NOT NULL,
            masked_ip TEXT NOT NULL,
            spam_score INTEGER NOT NULL CHECK(spam_score >= 0 AND spam_score <= 100),
            classification TEXT CHECK(classification IN ('Genuine', 'Suspicious')) NOT NULL,
            triggered_rules TEXT, -- JSON array of triggered detection rules
            admin_status TEXT CHECK(admin_status IN ('Pending Review', 'Confirmed Genuine', 'Confirmed Spam')) DEFAULT 'Pending Review',
            submitted_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            reviewed_at TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS spam_keywords (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL, -- Financial, SEO, Phishing, Adult, Crypto
            pattern TEXT UNIQUE NOT NULL,
            weight INTEGER NOT NULL CHECK(weight > 0)
        );

        CREATE INDEX IF NOT EXISTS idx_submissions_class ON form_submissions(classification);
        CREATE INDEX IF NOT EXISTS idx_submissions_status ON form_submissions(admin_status);
        CREATE INDEX IF NOT EXISTS idx_submissions_ip ON form_submissions(ip_hash);
        CREATE INDEX IF NOT EXISTS idx_submissions_date ON form_submissions(submitted_at);

        -- Standard baseline spam keywords and weights
        INSERT OR IGNORE INTO spam_keywords (category, pattern, weight) VALUES
            ('Financial', 'claim your prize', 35),
            ('Financial', 'make money fast', 30),
            ('Financial', 'wire transfer', 25),
            ('Financial', 'bank beneficiary', 35),
            ('Financial', 'inheritance fund', 40),
            ('Crypto', 'crypto giveaway', 35),
            ('Crypto', 'bitcoin investment', 30),
            ('Crypto', 'wallet recovery', 35),
            ('SEO', 'boost your website ranking', 25),
            ('SEO', 'first page on google', 25),
            ('SEO', 'seo backlink service', 30),
            ('Phishing', 'account suspended verify password', 45),
            ('Phishing', 'urgent action required click here', 35),
            ('Adult', 'online casino free spins', 30);
        """)
    conn.close()
