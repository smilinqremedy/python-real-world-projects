"""
Command-Line Interface for Security Incident Response Management System.
"""
import sys
from incident_service import IncidentResponseService, RBACPermissionError, IncidentWorkflowError


def print_banner(title: str):
    print("\n" + "=" * 65)
    print(f" {title.upper()} ")
    print("=" * 65)


def seed_demo(service: IncidentResponseService):
    try:
        u_admin = service.create_user("ciso_admin", "Folake Adeleke (CISO)", "Admin", "admin@secops.ng")
        u_lead = service.create_user("lead_emeka", "Emeka Nwosu (Lead IR)", "Lead", "emeka@secops.ng")
        u_analyst = service.create_user("analyst_zainab", "Zainab Bello (SOC Analyst)", "Analyst", "zainab@secops.ng")

        inc1 = service.create_incident(
            title="Credential Spraying Attack on VPN Gateway",
            description="Repeated failed authentications across multiple AD accounts originating from bulletproof VPS.",
            severity="High",
            category="Unauthorized Access",
            created_by_id=u_analyst
        )
        service.assign_lead_investigator(inc1, lead_user_id=u_lead, acting_user_id=u_admin)
        service.transition_status(inc1, "Investigating", u_analyst, "IP blocks applied at firewall edge.")
        service.add_evidence(inc1, u_analyst, "Log", "syslog:/var/log/auth.log", "VPN gateway authentication failure logs")

        print(f"Demo data seeded successfully! Sample Incident: {inc1}")
    except Exception as e:
        print(f"Note: Seed data or error: {e}")


def main():
    service = IncidentResponseService()

    while True:
        print_banner("Security Incident Response Management")
        print("1. Create User Account (Analyst, Lead, Admin)")
        print("2. List Users")
        print("3. Register New Security Incident")
        print("4. View Incident Details & Timeline")
        print("5. Assign Lead Investigator (Lead / Admin only)")
        print("6. Transition Incident Status (Reported -> Closed)")
        print("7. Add Investigation Note")
        print("8. Attach Evidence Reference")
        print("9. Incident Response SOC Metrics Dashboard")
        print("10. Seed Demo Data")
        print("0. Exit")

        choice = input("\nSelect an option [0-10]: ").strip()

        if choice == "1":
            print_banner("Create User")
            uname = input("Username: ").strip()
            fname = input("Full Name: ").strip()
            role = input("Role (Analyst / Lead / Admin) [Analyst]: ").strip() or "Analyst"
            email = input("Email: ").strip()
            try:
                uid = service.create_user(uname, fname, role, email)
                print(f"User created successfully! (ID: {uid})")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "2":
            print_banner("User Directory")
            users = service.list_users()
            for u in users:
                print(f"[ID: {u['id']}] {u['full_name']} (@{u['username']}) | Role: {u['role']} | Email: {u['email']}")

        elif choice == "3":
            print_banner("Register Incident")
            title = input("Title: ").strip()
            desc = input("Description: ").strip()
            sev = input("Severity (Low, Medium, High, Critical) [High]: ").strip() or "High"
            print("Categories: Phishing, Malware, Data Breach, Unauthorized Access, DDoS, Insider Threat, System Compromise")
            cat = input("Category: ").strip()
            try:
                uid = int(input("Reporting User ID: ").strip())
                ref = service.create_incident(title, desc, sev, cat, uid)
                print(f"\n[SUCCESS] Incident registered! Reference: {ref}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "4":
            print_banner("Incident Details")
            ref = input("Enter Incident Reference (e.g. INC-2026-1234): ").strip()
            try:
                inc = service.get_incident_details(ref)
                print(f"\nReference:    {inc['incident_ref']}")
                print(f"Title:        {inc['title']}")
                print(f"Severity:     {inc['severity']} | Category: {inc['category']}")
                print(f"Status:       {inc['status']}")
                print(f"Reported By:  {inc['creator_name']} on {inc['created_at']}")
                print(f"Lead Analyst: {inc['lead_analyst_name'] or 'Unassigned'}")
                print(f"Description:  {inc['description']}")

                print("\nInvestigation Notes:")
                if not inc["notes"]:
                    print("  No notes recorded yet.")
                else:
                    for n in inc["notes"]:
                        print(f"  [{n['created_at']}] {n['author_name']} ({n['author_role']}): {n['note_text']}")

                print("\nEvidence Items:")
                if not inc["evidence"]:
                    print("  No evidence items attached.")
                else:
                    for e in inc["evidence"]:
                        sha_str = f" | SHA256: {e['sha256'][:16]}..." if e['sha256'] else ""
                        print(f"  [{e['evidence_type']}] {e['reference_locator']} - {e['description']}{sha_str}")

                print("\nAudit Trail & Timeline:")
                for t in inc["timeline"]:
                    print(f"  [{t['timestamp']}] {t['actor_name']}: {t['action']} ({t['previous_state'] or 'None'} -> {t['new_state'] or 'None'})")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "5":
            print_banner("Assign Lead Investigator")
            ref = input("Incident Reference: ").strip()
            try:
                lead_id = int(input("Target Lead Analyst User ID: ").strip())
                actor_id = int(input("Acting User ID (Lead/Admin): ").strip())
                service.assign_lead_investigator(ref, lead_id, actor_id)
                print("Lead analyst assigned successfully!")
            except RBACPermissionError as pe:
                print(f"RBAC ERROR: {pe}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "6":
            print_banner("Transition Incident Status")
            ref = input("Incident Reference: ").strip()
            print("Status Options: Investigating, Contained, Eradicated, Recovered, Closed")
            st = input("New Status: ").strip()
            note = input("Resolution Note (optional): ").strip() or None
            try:
                actor_id = int(input("Acting User ID: ").strip())
                service.transition_status(ref, st, actor_id, note)
                print(f"Incident {ref} transitioned to status: {st}")
            except (RBACPermissionError, IncidentWorkflowError) as we:
                print(f"WORKFLOW / RBAC ERROR: {we}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "7":
            print_banner("Add Investigation Note")
            ref = input("Incident Reference: ").strip()
            note = input("Note Text: ").strip()
            try:
                uid = int(input("Author User ID: ").strip())
                service.add_note(ref, uid, note)
                print("Note added to incident file.")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "8":
            print_banner("Attach Evidence Reference")
            ref = input("Incident Reference: ").strip()
            print("Evidence Types: Log, File Hash, Network PCAP, Memory Dump, Disk Image, Screenshot, Email Artifact")
            etype = input("Evidence Type: ").strip()
            loc = input("Reference Locator (Path / URI / Ticket): ").strip()
            desc = input("Description: ").strip()
            sha = input("SHA-256 Hash (optional): ").strip() or None
            try:
                uid = int(input("Acting User ID: ").strip())
                service.add_evidence(ref, uid, etype, loc, desc, sha)
                print("Evidence reference attached and recorded in audit log.")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "9":
            print_banner("SOC Incident Metrics")
            m = service.get_incident_metrics()
            print(f"Total Logged Incidents: {m['total_incidents']}")
            print("\nBy Status:")
            for s, c in m["by_status"].items():
                print(f"  - {s}: {c}")
            print("\nBy Severity:")
            for sv, c in m["by_severity"].items():
                print(f"  - {sv}: {c}")
            print("\nBy Threat Category:")
            for cat, c in m["by_category"].items():
                print(f"  - {cat}: {c}")

        elif choice == "10":
            seed_demo(service)

        elif choice == "0":
            print("Exiting Incident Response System. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice.")


if __name__ == "__main__":
    main()
