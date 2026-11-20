"""
Interactive CLI for Automated Job Application Email Assistant.
"""
import sys
import os
from assistant_service import EmailAssistantService


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)


def seed_demo_data(service: EmailAssistantService):
    try:
        c1 = service.add_company("PayStack Payments Ltd", "careers@paystack.com", "FinTech", "https://paystack.com")
        c2 = service.add_company("Flutterwave Technologies", "recruitment@flutterwavego.com", "FinTech & Payments", "https://flutterwave.com")
        c3 = service.add_company("Kuda Microfinance Bank", "jobs@kuda.com", "Digital Banking", "https://kuda.com")

        service.add_vacancy(c1, "Senior Python Backend Engineer", "https://paystack.com/careers/senior-python", "₦14,000,000 - ₦18,000,000")
        service.add_vacancy(c2, "DevOps & Infrastructure Architect", "https://flutterwave.com/careers/devops", "₦15,000,000 - ₦20,000,000")
        service.add_vacancy(c3, "API Integration Specialist", "https://kuda.com/careers/api-spec", "₦10,000,000 - ₦13,000,000")
    except Exception:
        pass


def handle_add_company(service: EmailAssistantService):
    print_banner("Add Employer / Recruitment Contact")
    try:
        name = input("Company Name: ").strip()
        email = input("Recruitment Email Address: ").strip()
        ind = input("Industry (e.g. FinTech, Healthcare): ").strip() or None
        web = input("Website URL (optional): ").strip() or None
        notes = input("Notes (optional): ").strip() or None

        cid = service.add_company(name, email, ind, web, notes)
        print(f"\n[SUCCESS] Company '{name}' added (ID: {cid}).")
    except ValueError as e:
        print(f"\n[ERROR] {e}")


def handle_add_vacancy(service: EmailAssistantService):
    print_banner("Add Job Vacancy")
    comps = service.list_companies()
    if not comps:
        print("Please add a company contact first.")
        return

    print("Select Company:")
    for c in comps:
        print(f"  [{c['id']}] {c['name']} ({c['recruitment_email']})")

    try:
        cid = int(input("\nEnter Company ID: ").strip())
        title = input("Job Title: ").strip()
        url = input("Job Listing URL (optional): ").strip() or None
        salary = input("Salary Range (optional): ").strip() or None

        vid = service.add_vacancy(cid, title, url, salary)
        print(f"\n[SUCCESS] Vacancy '{title}' saved (ID: {vid}).")
    except ValueError as e:
        print(f"\n[ERROR] {e}")


def handle_generate_and_send(service: EmailAssistantService):
    print_banner("Generate, Preview & Send Application Email")
    vacs = service.list_vacancies()
    if not vacs:
        print("No job vacancies available.")
        return

    print("Select Target Vacancy:")
    for v in vacs:
        print(f"  [{v['id']}] {v['title']} at {v['company_name']} ({v['recruitment_email']}) - Status: {v['status']}")

    try:
        vid = int(input("\nEnter Vacancy ID: ").strip())
        templates = service.list_templates()
        print("\nSelect Email Template:")
        for t in templates:
            print(f"  [{t['id']}] {t['name']}")
        tid = int(input("Enter Template ID [1]: ").strip() or "1")

        print("\nEnter Your Profile Details:")
        c_name = input("Your Full Name: ").strip() or "Applicant"
        c_exp = input("Years of Experience [4]: ").strip() or "4"
        c_skills = input("Key Technical Skills [Python, SQL, System Architecture]: ").strip() or "Python, SQL, System Architecture"
        c_phone = input("Your Phone Number: ").strip() or "+2348000000000"
        c_email = input("Your Email Address: ").strip() or "applicant@example.com"
        rec_name = input("Recruiter / Contact Person Name [Hiring Team]: ").strip() or "Hiring Team"
        cv_path = input("Path to CV / Resume File (or Enter to skip): ").strip() or None

        profile = {
            "candidate_name": c_name,
            "years_experience": c_exp,
            "candidate_skills": c_skills,
            "candidate_phone": c_phone,
            "candidate_email": c_email,
            "recruiter_name": rec_name,
        }

        # MANDATORY PREVIEW
        preview = service.preview_application(vid, tid, profile, cv_path)

        print("\n" + "=" * 70)
        print("  APPLICATION EMAIL PREVIEW (REVIEW CAREFULLY)")
        print("=" * 70)
        print(f"To         : {preview['recipient_email']}")
        print(f"Company    : {preview['company_name']}")
        print(f"Position   : {preview['job_title']}")
        print(f"Subject    : {preview['subject']}")
        print(f"Attachment : {preview['cv_filename'] or 'None'}")
        print("-" * 70)
        print("EMAIL BODY:")
        print(preview['body'])
        print("=" * 70)

        # STRICT CONFIRMATION GATE
        confirm = input("\nDo you confirm and authorize sending this email? (yes/no): ").strip().lower()
        if confirm == "yes":
            res = service.send_confirmed_application(preview, user_confirmed=True, dry_run=True)
            print(f"\n[SUCCESS] {res['message']}")
            print(f"Mode: {res['mode']} | Recipient: {res['recipient']}")
        else:
            print("\n[CANCELLED] Email was NOT sent. Application remained untouched.")

    except (ValueError, FileNotFoundError, PermissionError) as e:
        print(f"\n[ERROR] {e}")


def handle_reports(service: EmailAssistantService):
    print_banner("Applications Activity Report")
    rep = service.get_applications_report()
    print(f"\nTotal Applications Submitted: {rep['total_applications']}")

    if rep["by_status"]:
        print("\nStatus Breakdown:")
        for s in rep["by_status"]:
            print(f"  * {s['status']:<18}: {s['count']}")

    if rep["recent_applications"]:
        print(f"\n{'Date':<18} {'Company':<22} {'Position':<26} {'Status'}")
        print("-" * 75)
        for r in rep["recent_applications"]:
            print(f"{r['sent_at'][:16]:<18} {r['company_name'][:20]:<22} {r['job_title'][:24]:<26} {r['status']}")


def main():
    service = EmailAssistantService()
    seed_demo_data(service)

    while True:
        print_banner("Job Application Email Assistant")
        print("1. View Saved Vacancies")
        print("2. Add Target Company")
        print("3. Add Job Vacancy")
        print("4. Generate, Preview & Send Application Email")
        print("5. View Applications Activity & Status Report")
        print("6. Exit")

        choice = input("\nSelect option (1-6): ").strip()
        if choice == "1":
            vacs = service.list_vacancies()
            print(f"\n{'ID':<5} {'Company':<22} {'Position':<30} {'Status':<12} {'Email'}")
            print("-" * 85)
            for v in vacs:
                print(f"{v['id']:<5} {v['company_name']:<22} {v['title']:<30} {v['status']:<12} {v['recruitment_email']}")
        elif choice == "2":
            handle_add_company(service)
        elif choice == "3":
            handle_add_vacancy(service)
        elif choice == "4":
            handle_generate_and_send(service)
        elif choice == "5":
            handle_reports(service)
        elif choice == "6":
            print("Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
