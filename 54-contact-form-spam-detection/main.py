"""
Interactive CLI for Website Contact Form Spam Detection System.
"""
import sys
from spam_service import SpamDetectionService


def print_banner(title: str):
    print("\n" + "=" * 70)
    print(f"  {title.upper()}")
    print("=" * 70)


def seed_demo_data(service: SpamDetectionService):
    try:
        service.submit_contact_form(
            "Dr. Tunde Fashola", "tunde.fashola@healthcare.ng",
            "Inquiry on Telemedicine API Integration",
            "Good day team, our clinic is interested in connecting our electronic health record software with your lab API. Could you share your technical documentation and sandbox access credentials?",
            "102.89.23.11"
        )
        service.submit_contact_form(
            "Crypto Winner Bot", "bot9921@freemail.ru",
            "URGENT: Claim your prize bitcoin investment giveaway",
            "Congratulations! Your email has won our crypto giveaway. Claim your prize now: http://spam-crypto.ru/claim or check http://fast-money.biz and http://bonus-btc.top",
            "185.220.101.5"
        )
        service.submit_contact_form(
            "SEO Rank Masters", "alex@seorankboost.xyz",
            "Boost your website ranking on Google First Page",
            "Hello webmaster, we provide guaranteed seo backlink service to boost your website ranking on google first page in 7 days! Visit our website at https://backlinks.xyz",
            "194.26.29.100"
        )
    except Exception:
        pass


def handle_submit(service: SpamDetectionService):
    print_banner("Submit Contact Form")
    try:
        name = input("Your Name: ").strip()
        email = input("Your Email Address: ").strip()
        subject = input("Subject: ").strip()
        print("Enter Message (press Enter when done):")
        msg = input("> ").strip()
        ip = input("Simulated Client IP Address [192.168.1.105]: ").strip() or "192.168.1.105"

        res = service.submit_contact_form(name, email, subject, msg, ip)
        print(f"\n[SUBMISSION RECORDED] Reference: {res['submission_ref']}")
        print(f"Classification : {res['classification'].upper()} (Spam Score: {res['spam_score']}/100)")
        print(f"Masked IP Log  : {res['masked_ip']}")
        if res["triggered_rules"]:
            print("Triggered Detection Rules:")
            for r in res["triggered_rules"]:
                print(f"  - {r}")
        if res["classification"] == "Suspicious":
            print("\n[NOTE] Message was NOT deleted; safely queued for administrator review.")
    except ValueError as e:
        print(f"\n[VALIDATION ERROR] {e}")


def handle_list_submissions(service: SpamDetectionService):
    print_banner("Contact Form Submissions")
    print("Filter: 1. All  2. Suspicious Only  3. Genuine Only")
    f_choice = input("Choice (1-3) [1]: ").strip() or "1"
    f_map = {"1": None, "2": "Suspicious", "3": "Genuine"}
    classification = f_map.get(f_choice)

    subs = service.list_submissions(classification=classification)
    if not subs:
        print("No submissions found.")
        return

    print(f"\n{'Ref':<18} {'Sender':<20} {'Subject':<25} {'Score':<7} {'Class':<12} {'Review Status'}")
    print("-" * 95)
    for s in subs:
        print(f"{s['submission_ref']:<18} {s['sender_name'][:18]:<20} {s['subject'][:23]:<25} {s['spam_score']:<7} {s['classification']:<12} {s['admin_status']}")


def handle_admin_review(service: SpamDetectionService):
    print_banner("Administrator Review Queue")
    pending = service.list_submissions(admin_status="Pending Review")
    if not pending:
        print("No submissions currently pending review.")
        return

    print(f"Found {len(pending)} submission(s) pending review:\n")
    for s in pending:
        print(f"[{s['submission_ref']}] From: {s['sender_name']} <{s['email']}> | Score: {s['spam_score']}/100 | Class: {s['classification']}")
        print(f"  Subject: {s['subject']}")
        print(f"  Message: {s['message'][:120]}...")
        if s.get("triggered_rules"):
            print(f"  Flags  : {', '.join(s['triggered_rules'])}")
        print("-" * 70)

    ref = input("\nEnter Submission Ref to Review (or press Enter to return): ").strip()
    if ref:
        print("Select Review Decision: 1. Confirm Genuine  2. Confirm Spam")
        d_choice = input("Choice (1-2): ").strip()
        decision = "Confirmed Genuine" if d_choice == "1" else "Confirmed Spam"
        try:
            service.review_submission(ref, decision)
            print(f"\n[SUCCESS] Submission {ref} updated to '{decision}'.")
        except ValueError as e:
            print(f"\n[ERROR] {e}")


def handle_stats(service: SpamDetectionService):
    print_banner("Spam Detection & Form Activity Statistics")
    stats = service.get_spam_statistics()
    print(f"\nTotal Submissions Ingested : {stats['total_submissions']}")
    print(f"Genuine Messages           : {stats['genuine_count']}")
    print(f"Suspicious Messages Flagged: {stats['suspicious_count']} ({stats['spam_rate_percent']}%)")
    print(f"Average Spam Score         : {stats['average_spam_score']} / 100")
    print(f"Pending Administrator Review: {stats['pending_review_count']}")
    print(f"Confirmed Spam Audit Count : {stats['confirmed_spam_count']}")


def main():
    service = SpamDetectionService()
    seed_demo_data(service)

    while True:
        print_banner("Website Contact Form Spam Detection System")
        print("1. Submit Contact Form Message")
        print("2. View Submissions & Classifications")
        print("3. Administrator Review Queue (Approve / Confirm Spam)")
        print("4. View Spam Statistics & Analytics")
        print("5. Exit")

        choice = input("\nSelect an option (1-5): ").strip()
        if choice == "1":
            handle_submit(service)
        elif choice == "2":
            handle_list_submissions(service)
        elif choice == "3":
            handle_admin_review(service)
        elif choice == "4":
            handle_stats(service)
        elif choice == "5":
            print("Goodbye!")
            sys.exit(0)


if __name__ == "__main__":
    main()
