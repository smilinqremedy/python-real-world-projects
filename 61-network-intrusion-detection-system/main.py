"""
Command-Line Interface for Network Intrusion Detection System (NIDS).
"""
import sys
from detector import NIDSEngine, DetectionRules
from traffic_simulator import generate_synthetic_stream


def print_banner(title: str):
    print("\n" + "=" * 65)
    print(f" {title.upper()} ")
    print("=" * 65)


def run_simulation(engine: NIDSEngine):
    print("\nGenerating and analyzing synthetic authorized lab packet stream...")
    packets = generate_synthetic_stream()
    total_alerts = 0
    for pkt in packets:
        alerts = engine.process_scapy_packet(pkt)
        total_alerts += len(alerts)

    print(f"Analysis complete: Processed {len(packets)} packets. Generated {total_alerts} security alerts.")


def main():
    rules = DetectionRules()
    engine = NIDSEngine(rules=rules)

    while True:
        print_banner("Network Intrusion Detection System (NIDS)")
        print("1. Run Synthetic Lab Traffic Simulation")
        print("2. View Security Alerts")
        print("3. View Alerts Filtered by Severity (High / Critical)")
        print("4. Network Traffic & Incident Summary")
        print("5. View Configured Detection Rules")
        print("0. Exit")

        choice = input("\nSelect an option [0-5]: ").strip()

        if choice == "1":
            run_simulation(engine)

        elif choice == "2":
            print_banner("Security Alert Incident Log")
            alerts = engine.get_alerts()
            if not alerts:
                print("No alerts logged. System is quiet.")
            else:
                for a in alerts:
                    print(f"[{a['datetime_str']}] [{a['severity'].upper()}] {a['alert_type']}")
                    print(f"  Source: {a['src_ip']} -> Destination: {a['dst_ip'] or 'N/A'}")
                    print(f"  Rule: {a['rule_triggered']} | Details: {a['description']}\n")

        elif choice == "3":
            sev = input("Enter severity to filter (Low, Medium, High, Critical) [High]: ").strip().capitalize() or "High"
            print_banner(f"Alerts with Severity: {sev}")
            alerts = engine.get_alerts(severity=sev)
            if not alerts:
                print(f"No {sev} alerts found.")
            else:
                for a in alerts:
                    print(f"[{a['datetime_str']}] {a['alert_type']} | From: {a['src_ip']} | {a['description']}")

        elif choice == "4":
            print_banner("Traffic & Security Overview")
            summary = engine.get_traffic_summary()
            print(f"Total Packets Inspected:    {summary['total_packets_inspected']}")
            print(f"Total Security Alerts:      {summary['total_alerts_generated']}")
            print("\nAlerts by Severity:")
            for s, cnt in summary["alerts_by_severity"].items():
                print(f"  - {s}: {cnt}")
            print("\nTop Active Source IPs:")
            for ip in summary["top_active_ips"]:
                print(f"  - {ip['src_ip']}: {ip['count']} events")

        elif choice == "5":
            print_banner("Configured Detection Rules")
            print(f"Port Scan Threshold:       {rules.port_scan_threshold} distinct ports in {rules.scan_window_seconds}s")
            print(f"Packet Burst Threshold:     {rules.packet_burst_threshold} packets in {rules.burst_window_seconds}s")
            print(f"Traffic Volume Threshold:   {rules.volume_threshold_bytes:,} bytes in {rules.volume_window_seconds}s")
            print(f"Monitored Suspicious Ports: {list(rules.suspicious_ports.keys())}")
            print(f"Blocked Malicious IPs:      {list(rules.blocked_ips)}")

        elif choice == "0":
            print("Exiting NIDS. Stay secure!")
            sys.exit(0)
        else:
            print("Invalid option. Please choose 0 to 5.")


if __name__ == "__main__":
    main()
