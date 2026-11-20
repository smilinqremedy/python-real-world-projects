"""
Interactive Command-Line Interface for Job Recruitment and Applicant Tracking System.
"""
import sys
import os
from recruitment_service import RecruitmentService, AccessControlError, VALID_APPLICATION_STATUSES


def print_banner(title: str):
    print("\n" + "=" * 75)
    print(f"  {title.upper()}")
    print("=" * 75)


def seed_demo_data(service: RecruitmentService):
    """Seed sample recruitment agency data."""
    try:
        # Create users
        service.register_user(None, "ADM-001", "admin", "AdminPass123!", "Agency Super Admin", "admin@apexrecruitment.ng", "admin")
        admin_u = service.authenticate_user("admin", "AdminPass123!")

        service.register_user(admin_u, "REC-101", "recruiter.ngozi", "RecruitPass123!", "Ngozi Okafor", "ngozi@apexrecruitment.ng", "recruiter")
        service.register_user(admin_u, "HM-201", "hm.khalid", "ManagerPass123!", "Khalid Danjuma", "khalid@paydirect.ng", "hiring_manager")

        rec_u = service.authenticate_user("recruiter.ngozi", "RecruitPass123!")

        # Register companies
        service.register_company(rec_u, "COMP-101", "PayDirect Financial Technologies Ltd", "Fintech & Payments", "Femi Bakare", "hr@paydirect.ng", "+2348021112233", "Victoria Island, Lagos", "https://paydirect.ng")
        service.register_company(rec_u, "COMP-102", "Sahel Cloud Logistics", "Logistics & Supply Chain", "Amina Yusuf", "talent@sahelcloud.ng", "+2348032223344", "Central Business District, Abuja", "https://sahelcloud.ng")

        # Create vacancies
        service.create_vacancy(
            rec_u, "VAC-2026-101", "COMP-101", "Senior Python Backend Engineer", "Core Engineering",
            "Hybrid", "Lagos, Nigeria", 4.0, "Python, FastAPI, PostgreSQL, Docker, Redis",
            "Build robust transaction payment settlement pipelines.",
            "4+ years Python backend experience, microservices, unit testing.",
            salary_min=12000000.0, salary_max=18000000.0, closing_date="2026-12-31"
        )

        service.create_vacancy(
            rec_u, "VAC-2026-102", "COMP-102", "DevOps & Cloud Infrastructure Engineer", "DevOps & SRE",
            "Remote", "Abuja / Remote", 3.0, "AWS, Terraform, Kubernetes, Docker, CI/CD",
            "Manage multi-region Kubernetes clusters and infrastructure automation.",
            "3+ years cloud infrastructure experience with AWS and Terraform.",
            salary_min=10000000.0, salary_max=15000000.0, closing_date="2026-12-31"
        )

        # Register candidates
        c1 = service.register_candidate("Tunde Adeleke", "tunde.adeleke@example.com", "+2348051234567", "Lagos", "Senior Python Developer", 5.5, "Python, Django, FastAPI, PostgreSQL, Docker, AWS", "B.Sc Computer Science", "https://linkedin.com/in/tundeadel")
        c2 = service.register_candidate("Fatima Bello", "fatima.bello@example.com", "+2348067890123", "Abuja", "DevOps Engineer", 4.0, "AWS, Kubernetes, Terraform, Docker, Python, Linux", "B.Eng Electrical Engineering", "https://linkedin.com/in/fatimabello")
        c3 = service.register_candidate("Emeka Nwosu", "emeka.nwosu@example.com", "+2348098765432", "Enugu", "Junior Fullstack Developer", 1.5, "JavaScript, React, Node.js, HTML, CSS", "HND Computer Science", "https://linkedin.com/in/emekanwosu")

        # Apply to vacancies
        app1_ref = service.apply_to_vacancy(c1, "VAC-2026-101", "Excited to apply for the Senior Python Backend role. Over 5 years experience building scalable payment solutions.")
        app2_ref = service.apply_to_vacancy(c2, "VAC-2026-102", "Passionate about cloud reliability engineering and Terraform automation.")

        # Upload demo CVs
        dummy_cv_1 = b"Tunde Adeleke CV - Senior Python Backend Engineer - Skills: Python, FastAPI, Docker, SQL"
        dummy_cv_2 = b"Fatima Bello CV - Cloud DevOps Engineer - Skills: AWS, Kubernetes, Terraform, CI/CD"
        service.upload_candidate_cv(app1_ref, "Tunde_Adeleke_Resume.pdf", dummy_cv_1)
        service.upload_candidate_cv(app2_ref, "Fatima_Bello_Resume.docx", dummy_cv_2)

        # Status progression & Interview
        service.update_application_status(rec_u, app1_ref, "Under Review", "Profile matches technical criteria")
        service.update_application_status(rec_u, app1_ref, "Shortlisted", "Shortlisted for first round interview")

        int_ref = service.schedule_interview(rec_u, app1_ref, "Technical Interview", "2026-11-25 14:00", "Khalid Danjuma (Hiring Manager)", "https://meet.google.com/xyz-rec-demo")

        # Record interview feedback
        hm_u = service.authenticate_user("hm.khalid", "ManagerPass123!")
        service.record_interview_feedback(
            hm_u, int_ref, rating_overall=5, technical_score=5, communication_score=4, problem_solving_score=5,
            strengths="Exceptional grasp of concurrency, database locking, and asynchronous Python.",
            areas_for_improvement="Could gain more familiarity with GraphQL interfaces.",
            recommendation="Strong Hire",
            notes="Strong candidate for our senior payment infrastructure team."
        )

        service.update_application_status(rec_u, app1_ref, "Accepted", "Offer extended and accepted!")

    except Exception:
        pass


def handle_register_company(service: RecruitmentService, user: dict):
    print_banner("Register Employer Company")
    try:
        code = input("Company Code (e.g. COMP-103): ").strip()
        name = input("Company Name: ").strip()
        ind = input("Industry / Sector: ").strip()
        contact = input("Contact Person Name: ").strip()
        email = input("Contact Email: ").strip()
        phone = input("Contact Phone: ").strip()
        loc = input("Office Location (City, State): ").strip()
        web = input("Website URL (optional): ").strip() or None

        service.register_company(user, code, name, ind, contact, email, phone, loc, web)
        print(f"\n[SUCCESS] Company '{name}' registered successfully.")
    except (ValueError, AccessControlError) as e:
        print(f"\n[ERROR] {e}")


def handle_create_vacancy(service: RecruitmentService, user: dict):
    print_banner("Create Job Vacancy")
    try:
        vcode = input("Vacancy Code (e.g. VAC-2026-103): ").strip()
        ccode = input("Company Code (e.g. COMP-101): ").strip()
        title = input("Job Title: ").strip()
        dept = input("Department: ").strip()
        emp_type = input("Employment Type (Full-time / Part-time / Contract / Remote / Hybrid): ").strip()
        loc = input("Location: ").strip()
        exp = float(input("Minimum Years of Experience required (e.g. 3.0): ").strip())
        skills = input("Required Skills (comma-separated): ").strip()
        desc = input("Job Description: ").strip()
        reqs = input("Job Requirements: ").strip()
        smin = float(input("Minimum Annual Salary (₦) [0]: ").strip() or "0")
        smax = float(input("Maximum Annual Salary (₦) [0]: ").strip() or "0")
        cdate = input("Closing Date (YYYY-MM-DD, optional): ").strip() or None

        service.create_vacancy(user, vcode, ccode, title, dept, emp_type, loc, exp, skills, desc, reqs, smin, smax, cdate)
        print(f"\n[SUCCESS] Vacancy '{title}' created successfully under reference: {vcode}")
    except (ValueError, AccessControlError) as e:
        print(f"\n[ERROR] {e}")


def handle_list_vacancies(service: RecruitmentService):
    print_banner("Active Job Vacancies")
    vacancies = service.list_vacancies()
    if not vacancies:
        print("No job vacancies currently registered.")
        return

    print(f"{'Code':<14} {'Job Title':<32} {'Company':<25} {'Type':<10} {'Min Exp'}")
    print("-" * 88)
    for v in vacancies:
        print(f"{v['vacancy_code']:<14} {v['title']:<32} {v['company_name']:<25} {v['employment_type']:<10} {v['min_years_experience']} yrs")
    print("-" * 88)


def handle_register_candidate(service: RecruitmentService):
    print_banner("Register Job Applicant")
    try:
        name = input("Full Name: ").strip()
        email = input("Email Address: ").strip()
        phone = input("Phone Number: ").strip()
        loc = input("Current Location: ").strip()
        title = input("Current Job Title: ").strip()
        exp = float(input("Years of Professional Experience (e.g. 4.5): ").strip())
        skills = input("Key Skills (comma-separated, e.g. Python, SQL, Docker): ").strip()
        edu = input("Education Level (e.g. B.Sc Computer Science): ").strip() or None
        link = input("LinkedIn / Portfolio URL (optional): ").strip() or None

        ccode = service.register_candidate(name, email, phone, loc, title, exp, skills, edu, link)
        print(f"\n[SUCCESS] Candidate registered! Unique Candidate Code: {ccode}")
    except ValueError as e:
        print(f"\n[ERROR] {e}")


def handle_submit_application(service: RecruitmentService):
    print_banner("Submit Job Application")
    try:
        cand_code = input("Candidate Code (e.g. CND-2026-XXXX): ").strip()
        vac_code = input("Vacancy Code (e.g. VAC-2026-101): ").strip()
        letter = input("Cover Letter / Summary Note (optional): ").strip() or None

        app_ref = service.apply_to_vacancy(cand_code, vac_code, letter)
        print(f"\n[SUCCESS] Application recorded! Unique Reference Number: {app_ref}")

        upload_cv_now = input("Upload CV document now? (y/n) [y]: ").strip().lower()
        if upload_cv_now != "n":
            cv_path = input("Enter path to CV file (.pdf, .docx, .doc, .txt): ").strip()
            if os.path.exists(cv_path):
                with open(cv_path, "rb") as f:
                    data = f.read()
                meta = service.upload_candidate_cv(app_ref, os.path.basename(cv_path), data)
                print(f"[SUCCESS] CV uploaded successfully (Ref: {meta['file_ref']}, Type: {meta['file_type'].upper()})")
            else:
                print("[WARNING] Specified file not found. You can upload the CV later.")
    except (ValueError, FileNotFoundError) as e:
        print(f"\n[ERROR] {e}")


def handle_search_candidates(service: RecruitmentService):
    print_banner("Search Candidates by Skills & Experience")
    print("NOTE: Compliant with ethical recruitment standards. Candidate evaluation is strictly")
    print("based on technical skills, verified experience, and structured interview scores.")

    skills = input("\nEnter Skill Keywords (e.g. Python, AWS, Docker) [Enter for all]: ").strip() or None
    exp_str = input("Minimum Years of Experience (e.g. 3.0) [Enter for any]: ").strip()
    min_exp = float(exp_str) if exp_str else None
    loc = input("Location (e.g. Lagos, Abuja, Remote) [Enter for any]: ").strip() or None

    results = service.search_candidates(skill_query=skills, min_years_exp=min_exp, location=loc)
    if not results:
        print("No candidates matching the criteria.")
        return

    print(f"\nFound {len(results)} candidate(s):")
    print("-" * 90)
    print(f"{'Code':<14} {'Name':<22} {'Current Title':<24} {'Exp (Yrs)':<10} {'Skills'}")
    print("-" * 90)
    for c in results:
        skills_summary = c['skills'][:28] + "..." if len(c['skills']) > 28 else c['skills']
        print(f"{c['candidate_code']:<14} {c['full_name']:<22} {c['current_title']:<24} {c['years_experience']:<10} {skills_summary}")
    print("-" * 90)


def handle_update_status(service: RecruitmentService, user: dict):
    print_banner("Update Application Status")
    try:
        app_ref = input("Application Reference (e.g. APP-2026-XXXX): ").strip()
        print("\nAvailable Statuses:")
        for idx, s in enumerate(VALID_APPLICATION_STATUSES, 1):
            print(f"  {idx}. {s}")
        s_choice = input(f"Select New Status (1-{len(VALID_APPLICATION_STATUSES)}): ").strip()
        try:
            new_status = VALID_APPLICATION_STATUSES[int(s_choice) - 1]
        except (IndexError, ValueError):
            print("[ERROR] Invalid choice.")
            return

        notes = input("Status Transition Notes / Reason: ").strip() or None
        service.update_application_status(user, app_ref, new_status, notes)
        print(f"\n[SUCCESS] Application {app_ref} status transitioned to '{new_status}'.")
    except (ValueError, AccessControlError) as e:
        print(f"\n[ERROR] {e}")


def handle_view_application(service: RecruitmentService):
    print_banner("View Application Details & History")
    app_ref = input("Enter Application Reference (e.g. APP-2026-XXXX): ").strip()
    try:
        app = service.get_application_details(app_ref)
        print(f"\nApplication Reference : {app['application_ref']}")
        print(f"Current Status        : {app['status']}")
        print(f"Candidate Name        : {app['candidate_name']} ({app['candidate_code']})")
        print(f"Candidate Email       : {app['candidate_email']} | Phone: {app['candidate_phone']}")
        print(f"Experience & Skills   : {app['years_experience']} yrs | {app['skills']}")
        print(f"Target Vacancy        : {app['job_title']} ({app['vacancy_code']}) at {app['company_name']}")
        print(f"CV Document           : {app.get('original_filename') or 'No CV uploaded'}")
        if app.get("cover_letter"):
            print(f"Cover Letter Note     : {app['cover_letter']}")

        print("\n--- Status Transition Timeline ---")
        for h in app["history"]:
            actor = f"by {h['actor_name']} ({h['actor_role']})" if h['actor_name'] else ""
            print(f"[{h['timestamp']}] {h.get('old_status') or 'Start'} -> {h['new_status']} {actor}")
            if h.get("notes"):
                print(f"  Note: {h['notes']}")

        if app.get("interviews"):
            print("\n--- Scheduled Interviews ---")
            for i in app["interviews"]:
                print(f"[{i['scheduled_datetime']}] Ref: {i['interview_ref']} | Round: {i['round_name']} | Status: {i['status']}")

    except ValueError as e:
        print(f"\n[ERROR] {e}")


def handle_schedule_interview(service: RecruitmentService, user: dict):
    print_banner("Schedule Interview")
    try:
        app_ref = input("Application Reference (e.g. APP-2026-XXXX): ").strip()
        print("\nInterview Rounds: 1. Phone Screen  2. Technical Interview  3. Behavioral Interview  4. Panel Interview  5. Final Round")
        r_choice = input("Select Round (1-5) [2]: ").strip() or "2"
        r_map = {"1": "Phone Screen", "2": "Technical Interview", "3": "Behavioral Interview", "4": "Panel Interview", "5": "Final Round"}
        round_name = r_map.get(r_choice, "Technical Interview")

        sdate = input("Scheduled Date & Time (YYYY-MM-DD HH:MM): ").strip()
        iname = input("Interviewer Name: ").strip()
        loc = input("Meeting Link / Location: ").strip()

        iref = service.schedule_interview(user, app_ref, round_name, sdate, iname, loc)
        print(f"\n[SUCCESS] Interview scheduled with Ref: {iref}")
        print("Application status automatically moved to 'Interview Scheduled'.")
    except (ValueError, AccessControlError) as e:
        print(f"\n[ERROR] {e}")


def handle_record_feedback(service: RecruitmentService, user: dict):
    print_banner("Record Interview Feedback")
    try:
        iref = input("Interview Reference (e.g. INT-2026-XXXX): ").strip()
        r_overall = int(input("Overall Rating (1-5): ").strip())
        r_tech = int(input("Technical Competency Score (1-5): ").strip())
        r_comm = int(input("Communication Score (1-5): ").strip())
        r_prob = int(input("Problem Solving Score (1-5): ").strip())
        strengths = input("Candidate Strengths: ").strip()
        improvements = input("Areas for Improvement: ").strip()

        print("\nRecommendation: 1. Strong Hire  2. Hire  3. Hold  4. Reject")
        rec_choice = input("Select (1-4) [2]: ").strip() or "2"
        rec_map = {"1": "Strong Hire", "2": "Hire", "3": "Hold", "4": "Reject"}
        recommendation = rec_map.get(rec_choice, "Hire")

        notes = input("Additional Feedback Notes (optional): ").strip() or None

        fid = service.record_interview_feedback(user, iref, r_overall, r_tech, r_comm, r_prob, strengths, improvements, recommendation, notes)
        print(f"\n[SUCCESS] Interview evaluation saved (Feedback #{fid})! Status marked as Completed.")
    except (ValueError, AccessControlError) as e:
        print(f"\n[ERROR] {e}")


def handle_reports(service: RecruitmentService):
    print_banner("Recruitment Agency Analytics & Reports")
    rep = service.generate_recruitment_reports()
    print(f"\nTotal Registered Companies : {rep['total_companies']}")
    print(f"Total Open Vacancies       : {rep['total_vacancies']}")
    print(f"Total Candidate Pool       : {rep['total_candidates']}")
    print(f"Total Applications Processed: {rep['total_applications']}")

    print("\n--- Application Funnel Pipeline ---")
    for stage in rep["pipeline_funnel"]:
        bar = "#" * stage["count"]
        print(f"  {stage['stage']:<20}: {stage['count']:<4} {bar}")

    print("\n--- Vacancy Breakdown ---")
    for v in rep["vacancy_breakdowns"]:
        print(f"  [{v['vacancy_code']}] {v['title']} at {v['company_name']}: {v['total_applicants']} applicants (Accepted: {v['accepted_count']})")

    fs = rep["feedback_stats"]
    if fs.get("total_evaluations", 0) > 0:
        print("\n--- Interview Quality Metrics ---")
        print(f"  Total Evaluations Completed : {fs['total_evaluations']}")
        print(f"  Average Overall Rating      : {fs['avg_rating']:.1f} / 5.0")
        print(f"  Average Technical Score     : {fs['avg_technical']:.1f} / 5.0")
        print(f"  Average Communication Score : {fs['avg_communication']:.1f} / 5.0")


def main():
    service = RecruitmentService()
    seed_demo_data(service)

    current_user = None

    while True:
        if not current_user:
            print_banner("Applicant Tracking & Job Recruitment System")
            print("1. Login")
            print("2. Demo Accounts Information")
            print("3. Exit")

            choice = input("\nSelect option (1-3): ").strip()
            if choice == "1":
                uname = input("Username: ").strip()
                pwd = input("Password: ").strip()
                try:
                    current_user = service.authenticate_user(uname, pwd)
                    print(f"\n[SUCCESS] Welcome, {current_user['full_name']} [{current_user['role'].upper()}]")
                except ValueError as e:
                    print(f"\n[ERROR] {e}")
            elif choice == "2":
                print("\nDemo Accounts:")
                print("  Administrator : admin / AdminPass123!")
                print("  Recruiter     : recruiter.ngozi / RecruitPass123!")
                print("  Hiring Manager: hm.khalid / ManagerPass123!")
            elif choice == "3":
                print("Goodbye.")
                sys.exit(0)
        else:
            role = current_user["role"]
            print_banner(f"Main Menu - {current_user['full_name']} [{role.upper()}]")
            print("1. View Active Job Vacancies")
            print("2. Create Job Vacancy")
            print("3. Register Employer Company")
            print("4. Register Candidate Profile")
            print("5. Search Candidates (Skills & Experience)")
            print("6. Submit Job Application & Upload CV")
            print("7. View Application Details & Status History")
            print("8. Update Application Status")
            print("9. Schedule Interview")
            print("10. Record Interview Feedback & Scores")
            print("11. View Recruitment Funnel Analytics")
            print("12. Logout")

            choice = input("\nSelect option (1-12): ").strip()
            if choice == "1":
                handle_list_vacancies(service)
            elif choice == "2":
                handle_create_vacancy(service, current_user)
            elif choice == "3":
                handle_register_company(service, current_user)
            elif choice == "4":
                handle_register_candidate(service)
            elif choice == "5":
                handle_search_candidates(service)
            elif choice == "6":
                handle_submit_application(service)
            elif choice == "7":
                handle_view_application(service)
            elif choice == "8":
                handle_update_status(service, current_user)
            elif choice == "9":
                handle_schedule_interview(service, current_user)
            elif choice == "10":
                handle_record_feedback(service, current_user)
            elif choice == "11":
                handle_reports(service)
            elif choice == "12":
                print("Logged out.")
                current_user = None


if __name__ == "__main__":
    main()
