"""
Command-Line Interface for USB Device Activity Monitoring & Audit System.
"""
import sys
from usb_monitor import USBMonitorService
from device_simulator import SIMULATED_EVENTS


def print_banner(title: str):
    print("\n" + "=" * 65)
    print(f" {title.upper()} ")
    print("=" * 65)


def display_alerts(alerts: list):
    if not alerts:
        print("No USB security alerts logged.")
        return

    for idx, a in enumerate(alerts, 1):
        print(f"\n[ALERT #{idx}] [{a['severity'].upper()}] {a['alert_type']}")
        print(f"  Timestamp: {a['timestamp']}")
        print(f"  Host/User: {a['host']} ({a['user']})")
        print(f"  Hardware:  SN: {a['serial_number']}")
        print(f"  Details:   {a['details']}")


def run_simulation(service: USBMonitorService):
    print(f"\nReplaying {len(SIMULATED_EVENTS)} simulated USB connection/disconnection events...")
    alert_count = 0
    for ev in SIMULATED_EVENTS:
        res = service.process_event(
            event_type=ev["event_type"],
            serial_number=ev["serial_number"],
            vendor_name=ev["vendor_name"],
            product_name=ev["product_name"],
            vendor_id=ev["vendor_id"],
            product_id=ev["product_id"],
            host=ev["host"],
            user=ev["user"],
            device_type=ev["device_type"],
            timestamp=ev["timestamp"]
        )
        status_tag = "[ALLOWED]" if res["is_approved"] else "[ALERT / UNAUTHORIZED]"
        print(f"  {ev['event_type']:<12} {ev['vendor_name']} {ev['product_name']} ({ev['serial_number']}) -> {status_tag}")
        if res["alert_triggered"]:
            alert_count += 1

    print(f"\nSimulation complete: {alert_count} unauthorized device alerts generated.")


def main():
    service = USBMonitorService()

    while True:
        print_banner("USB Device Monitoring & Allowlist System")
        print("1. Run Synthetic USB Activity Simulation")
        print("2. Add Approved Device to Organization Allowlist")
        print("3. List Approved Devices")
        print("4. Log Manual Connection / Disconnection Event")
        print("5. View Security Alerts")
        print("6. View Device Connection Event Audit History")
        print("7. Executive Audit & Compliance Summary")
        print("0. Exit")

        choice = input("\nSelect an option [0-7]: ").strip()

        if choice == "1":
            run_simulation(service)

        elif choice == "2":
            print_banner("Add Approved Device")
            sn = input("Device Serial Number (e.g. CORP-KNG-1234): ").strip()
            vname = input("Vendor Name (e.g. Kingston): ").strip()
            pname = input("Product Model (e.g. IronKey Vault 64GB): ").strip()
            vid = input("Vendor ID / VID (e.g. 0951): ").strip()
            pid = input("Product ID / PID (e.g. 1666): ").strip()
            admin = input("Approving Officer [SecOps Lead]: ").strip() or "SecOps Lead"
            try:
                row_id = service.add_approved_device(sn, vname, pname, vid, pid, admin)
                print(f"Device allowlisted successfully! (ID: {row_id})")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "3":
            print_banner("Approved Device Allowlist")
            devices = service.list_approved_devices()
            if not devices:
                print("No approved devices registered. All USB connections will be flagged.")
            else:
                for d in devices:
                    print(f"[{d['serial_number']}] {d['vendor_name']} - {d['product_name']} (VID:{d['vendor_id']} PID:{d['product_id']}) | Approved by {d['approved_by']}")

        elif choice == "4":
            print_banner("Log Device Event")
            etype = input("Event Type (CONNECTED / DISCONNECTED) [CONNECTED]: ").strip().upper() or "CONNECTED"
            sn = input("Device Serial Number: ").strip()
            vname = input("Vendor Name: ").strip()
            pname = input("Product Name: ").strip()
            vid = input("Vendor ID: ").strip()
            pid = input("Product ID: ").strip()
            host = input("Target Hostname (e.g. WS-FINANCE-02): ").strip()
            user = input("Username: ").strip()
            dtype = input("Device Type [Mass Storage]: ").strip() or "Mass Storage"
            try:
                res = service.process_event(etype, sn, vname, pname, vid, pid, host, user, dtype)
                if res["alert_triggered"]:
                    print("\n[SECURITY ALERT TRIGGERED] Unauthorized device insertion logged!")
                else:
                    print("\n[COMPLIANT] Device authorized or disconnection logged safely.")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "5":
            print_banner("Security Alerts")
            alerts = service.get_alerts()
            display_alerts(alerts)

        elif choice == "6":
            print_banner("Event Audit Ledger")
            events = service.get_event_history()
            for e in events:
                app_str = "AUTHORIZED" if e["is_approved"] else "UNAUTHORIZED"
                print(f"[{e['timestamp']}] {e['event_type']} on {e['host']} by {e['user']} | SN: {e['serial_number']} ({app_str})")

        elif choice == "7":
            print_banner("Audit Summary")
            s = service.get_audit_summary()
            print(f"Total USB Events Logged:     {s['total_events_logged']}")
            print(f"Approved Connections:        {s['approved_connections']}")
            print(f"Unauthorized Connections:    {s['unauthorized_connections']}")
            print(f"Security Alerts Generated:   {s['security_alerts_generated']}")
            if s["top_unauthorized_devices"]:
                print("\nMost Frequently Plugged Unauthorized Devices:")
                for d in s["top_unauthorized_devices"]:
                    print(f"  - SN: {d['serial_number']} ({d['vendor_name']} {d['product_name']}) -> {d['count']} attempt(s)")

        elif choice == "0":
            print("Exiting USB Monitor. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid option.")


if __name__ == "__main__":
    main()
