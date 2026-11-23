"""
Command-Line Interface for Security Log Correlation & Threat Hunting Tool.
"""
import sys
from threat_hunter import ThreatHunter
from synthetic_soc_data import SYNTHETIC_AUTH_LOGS, SYNTHETIC_WEB_LOGS, SYNTHETIC_FIREWALL_LOGS


def print_banner(title: str):
    print("\n" + "=" * 65)
    print(f" {title.upper()} ")
    print("=" * 65)


def display_threats(threats: list):
    if not threats:
        print("No correlated threats identified.")
        return

    for idx, t in enumerate(threats, 1):
        print(f"\n--- [THREAT INCIDENT #{idx}] [{t['severity'].upper()}] {t['title']} ---")
        print(f"Rule ID:         {t['rule_id']}")
        print(f"Associated IP:   {t['ip_address'] or 'N/A'}")
        print(f"Username(s):     {t['username'] or 'N/A'}")
        print(f"Timeline Window: {t['first_seen']} -> {t['last_seen']}")
        print(f"Evidence Chain:  {t['timeline_summary']}")
        print(f"SOC Notes:       {t['investigation_notes']}")


def main():
    hunter = ThreatHunter()

    while True:
        print_banner("Security Log Correlation & Threat Hunting Tool")
        print("1. Ingest Multi-Source Synthetic SOC Telemetry Stream")
        print("2. Run Log Correlation Engine Across Telemetry Sources")
        print("3. View Correlated Threat Findings")
        print("4. Search Threats by IP Address or Username")
        print("5. Reconstruct Chronological Investigation Timeline for IP")
        print("6. SOC Hunting Summary & Incident Breakdown")
        print("0. Exit")

        choice = input("\nSelect an option [0-6]: ").strip()

        if choice == "1":
            c_auth = hunter.ingest_logs(SYNTHETIC_AUTH_LOGS, "Auth")
            c_web = hunter.ingest_logs(SYNTHETIC_WEB_LOGS, "Web")
            c_fw = hunter.ingest_logs(SYNTHETIC_FIREWALL_LOGS, "Firewall")
            print(f"\nSuccessfully normalized and ingested {c_auth + c_web + c_fw} events:")
            print(f"  - Authentication Events: {c_auth}")
            print(f"  - Web Access Logs:       {c_web}")
            print(f"  - Firewall Flow Records: {c_fw}")

        elif choice == "2":
            print("\nRunning multi-source cross-correlation rules...")
            findings = hunter.run_correlation()
            print(f"Correlation completed: {len(findings)} multi-stage attack patterns identified!")
            display_threats(findings)

        elif choice == "3":
            print_banner("All Correlated Threats")
            threats = hunter.search_threats()
            display_threats(threats)

        elif choice == "4":
            print_banner("Threat Hunting Search")
            ip = input("Filter by IP address (or leave blank): ").strip() or None
            user = input("Filter by Username (or leave blank): ").strip() or None
            sev = input("Filter by Severity (Critical / High / Medium): ").strip() or None
            results = hunter.search_threats(ip_address=ip, username=user, severity=sev)
            print(f"\nMatching Threats: {len(results)}")
            display_threats(results)

        elif choice == "5":
            print_banner("IP Investigation Timeline")
            ip = input("Enter target IP address (e.g. 203.0.113.50): ").strip()
            timeline = hunter.get_timeline_for_ip(ip)
            if not timeline:
                print(f"No events found for IP: '{ip}'")
            else:
                print(f"\nUnified Chronological Timeline for {ip} ({len(timeline)} events):")
                for e in timeline:
                    print(f"  [{e['timestamp']}] [{e['source_type']:<8}] {e['action']:<14} | {e['details']} (User: {e['username'] or 'N/A'})")

        elif choice == "6":
            print_banner("SOC Threat Summary")
            s = hunter.get_threat_summary()
            print(f"Total Normalized Logs in SIEM: {s['total_normalized_logs']}")
            print(f"Correlated Threat Detections:  {s['correlated_threats_identified']}")
            print("\nDetections by Severity:")
            for k, cnt in s["threats_by_severity"].items():
                print(f"  - {k}: {cnt}")

        elif choice == "0":
            print("Exiting Threat Hunting System. Stay vigilant!")
            sys.exit(0)
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
