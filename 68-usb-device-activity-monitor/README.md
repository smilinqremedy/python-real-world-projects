# Project 68: USB Device Activity Monitoring & Audit System

A defensive endpoint security monitoring system engineered to record USB removable media connection and disconnection events, maintain an approved hardware allowlist, detect unauthorized thumb drives and rogue BadUSB devices, and maintain an immutable historical audit trail in SQLite.

## Defensive Objectives

Removable media represents significant enterprise risks:
1. **Unauthorized Data Exfiltration**: Malicious insiders copying sensitive corporate files to personal thumb drives.
2. **Malware Introduction**: Uncontrolled external drives introducing ransomware, trojans, or worm propagation (e.g. Stuxnet vectors).
3. **BadUSB & Keystroke Injection**: Microcontroller devices (e.g. USB Rubber Ducky) mimicking human keyboards to inject automated shell commands upon insertion.

## Features

- **Granular Device Identification**: Tracks Hardware Serial Numbers, Vendor Names, Product Models, Vendor IDs (VID), and Product IDs (PID).
- **Approved Device Allowlist**: Security administrators register authorized company-issued encrypted drives (e.g. Kingston IronKey).
- **Real-Time Anomaly & Intrusion Alerts**: Automatically generates high/critical severity alerts when an unauthorized device is plugged into any corporate workstation or server.
- **Connection & Disconnection Lifecycle**: Logs both insertion and removal events with exact timestamps and hostnames.
- **Cross-Platform Event Simulation**: Built-in synthetic event replay simulator allowing full validation without requiring physical USB ports or elevated root privileges.

## Database Schema

- `approved_devices`: Registered company serial numbers, hardware models, VIDs/PIDs, and authorizing officers.
- `device_events`: Insertion/removal event ledger capturing timestamps, hostnames, usernames, serial numbers, and compliance statuses.
- `device_alerts`: Incident log for all unauthorized device connection attempts.

## Running the Application

Launch the interactive CLI:

```bash
cd 68-usb-device-activity-monitor
python3 main.py
```

Choose Option `1` to run the synthetic USB activity simulation and observe how authorized vs unauthorized devices are evaluated.

## Running Unit Tests

Execute the automated test suite:

```bash
python3 -m unittest test_usb_monitor.py -v
```
