"""
Command-Line Interface for AI Personal Learning Assistant.
"""
import argparse
import sys
import os
import database

from learning_engine import LearningEngine
from content_processor import ContentProcessor


def main():
    parser = argparse.ArgumentParser(description="AI Personal Learning Assistant")
    parser.add_argument("--register-user", nargs=2, metavar=("USERNAME", "PASSWORD"), help="Register a learner account")
    parser.add_argument("--add-subject", nargs=3, metavar=("USERNAME", "TITLE", "DESCRIPTION"), help="Add a learning subject")
    parser.add_argument("--upload-material", nargs=4, metavar=("USERNAME", "SUBJECT_TITLE", "TOPIC_TITLE", "FILE_PATH"), help="Upload study material")
    parser.add_argument("--weak-topics", type=str, metavar="USERNAME", help="List weak topics for user")
    parser.add_argument("--export-report", nargs=2, metavar=("USERNAME", "OUTPUT_CSV"), help="Export progress report")

    args = parser.parse_args()
    engine = LearningEngine()

    if args.register_user:
        u, p = args.register_user
        uid = engine.register_user(u, p)
        print(f"User '{u}' registered successfully (ID: {uid})." if uid else f"Username '{u}' already taken.")
        return

    if args.add_subject:
        u, title, desc = args.add_subject
        with database.get_connection(engine.db_path) as conn:
            user = conn.execute("SELECT id FROM users WHERE username = ?", (u,)).fetchone()
        if not user:
            print(f"User '{u}' not found.", file=sys.stderr)
            sys.exit(1)

        sid = engine.add_subject(user["id"], title, desc)
        print(f"Subject '{title}' created (ID: {sid})." if sid else f"Subject '{title}' already exists.")
        return

    if args.upload_material:
        u, s_title, t_title, fpath = args.upload_material
        if not os.path.exists(fpath):
            print(f"File not found: {fpath}", file=sys.stderr)
            sys.exit(1)

        with database.get_connection(engine.db_path) as conn:
            user = conn.execute("SELECT id FROM users WHERE username = ?", (u,)).fetchone()
            if not user:
                print(f"User '{u}' not found.", file=sys.stderr)
                sys.exit(1)
            subject = conn.execute("SELECT id FROM subjects WHERE user_id = ? AND title = ?", (user["id"], s_title)).fetchone()
            if not subject:
                print(f"Subject '{s_title}' not found.", file=sys.stderr)
                sys.exit(1)

        content = engine.processor.extract_text_from_file(fpath)
        res = engine.add_topic_with_content(user["id"], subject["id"], t_title, content, os.path.basename(fpath))
        print(f"Topic '{t_title}' created successfully!")
        print(f"Summary: {res['summary']}")
        print(f"Questions Generated: {res['questions_generated']}")
        return

    if args.weak_topics:
        u = args.weak_topics
        with database.get_connection(engine.db_path) as conn:
            user = conn.execute("SELECT id FROM users WHERE username = ?", (u,)).fetchone()
        if not user:
            print(f"User '{u}' not found.", file=sys.stderr)
            sys.exit(1)

        weak = engine.identify_weak_topics(user["id"])
        print(f"Weak Topics for '{u}' ({len(weak)} flagged):")
        for w in weak:
            print(f"  - [{w['subject_title']}] {w['topic_title']}: Average Score = {w['avg_score']:.1f}%")
        return

    if args.export_report:
        u, out_csv = args.export_report
        with database.get_connection(engine.db_path) as conn:
            user = conn.execute("SELECT id FROM users WHERE username = ?", (u,)).fetchone()
        if not user:
            print(f"User '{u}' not found.", file=sys.stderr)
            sys.exit(1)

        engine.export_progress_report(user["id"], out_csv)
        print(f"Progress report exported to: {out_csv}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
