"""
Command-Line Interface for AI Facial Recognition Attendance System.
"""
import argparse
import sys
import os
from PIL import Image
from attendance_service import AttendanceService
from reporter import AttendanceReporter


def main():
    parser = argparse.ArgumentParser(description="AI Facial Recognition Attendance System")
    parser.add_argument("--create-admin", nargs=2, metavar=("USERNAME", "PASSWORD"), help="Create admin user")
    parser.add_argument("--create-session", nargs=3, metavar=("CODE", "NAME", "DATE"), help="Create attendance session")
    parser.add_argument("--register-participant", nargs=4, metavar=("ID", "NAME", "DEPT", "EMAIL"), help="Register participant")
    parser.add_argument("--photo", type=str, help="Photo for participant enrollment or checkin")
    parser.add_argument("--opt-out-bio", action="store_true", help="Opt out of biometrics (manual only)")
    parser.add_argument("--checkin-face", nargs=2, metavar=("SESSION_CODE", "PHOTO_PATH"), help="Check in via face")
    parser.add_argument("--checkin-manual", nargs=2, metavar=("SESSION_CODE", "EMP_ID"), help="Check in manually")
    parser.add_argument("--report", type=str, help="Generate report for session code")
    parser.add_argument("--export-csv", type=str, help="Export session records to CSV file")

    args = parser.parse_args()
    service = AttendanceService()
    reporter = AttendanceReporter()

    if args.create_admin:
        u, p = args.create_admin
        ok = service.create_user(u, p, role="admin", actor="cli_admin")
        print("Admin user created successfully!" if ok else f"User '{u}' already exists.")
        return

    if args.create_session:
        code, name, date = args.create_session
        ok = service.create_session(code, name, date, created_by="cli_admin")
        print(f"Session '{code}' created." if ok else f"Session '{code}' already exists.")
        return

    if args.register_participant:
        pid, name, dept, email = args.register_participant
        face_img = None
        if not args.opt_out_bio:
            if not args.photo or not os.path.exists(args.photo):
                print("Error: Photo is required for biometric registration unless --opt-out-bio is specified.")
                sys.exit(1)
            face_img = Image.open(args.photo)

        res = service.register_participant(
            employee_id=pid,
            full_name=name,
            department=dept,
            email=email,
            consent_granted=True,
            opt_in_biometrics=not args.opt_out_bio,
            face_image=face_img,
            actor="cli_admin"
        )
        print("Registration result:", res)
        return

    if args.checkin_face:
        session, photo_path = args.checkin_face
        if not os.path.exists(photo_path):
            print(f"Photo file not found: {photo_path}")
            sys.exit(1)
        img = Image.open(photo_path)
        res = service.record_attendance_by_face(session, img, actor="kiosk")
        print("Check-in result:", res)
        return

    if args.checkin_manual:
        session, emp_id = args.checkin_manual
        res = service.record_attendance_manual(session, emp_id, verified_by="admin")
        print("Manual check-in result:", res)
        return

    if args.report:
        recs = reporter.get_session_attendance(args.report)
        print(f"Attendance for Session '{args.report}' ({len(recs)} records):")
        for r in recs:
            print(f"  [{r['timestamp']}] {r['employee_id']} - {r['full_name']} ({r['method']}, Status: {r['status']})")
        if args.export_csv:
            reporter.export_to_csv(recs, args.export_csv)
            print(f"Exported to {args.export_csv}")
        return

    parser.print_help()


if __name__ == "__main__":
    main()
