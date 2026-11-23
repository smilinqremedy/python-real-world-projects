# Project 61: Network Intrusion Detection System (NIDS)

A defensive, passive Network Intrusion Detection System (NIDS) designed for network security monitoring in an authorized lab environment. The application extracts packet metadata via **Scapy**, enforces sliding-window stateful behavioral rules, logs raw network flows, and generates categorized incident alerts into SQLite.

## How Network Packets & Intrusion Detection Work

Network communication relies on packets encapsulated into protocol layers (e.g., Ethernet $\rightarrow$ IP $\rightarrow$ TCP/UDP $\rightarrow$ Application Payload). Intrusion detection systems operate defensively by inspecting packet headers and metadata:
- **Port Scans**: An adversary probes multiple destination ports on a target host to identify listening services. NIDS tracks unique destination ports accessed by a given source IP within a sliding time window.
- **Connection Floods**: Abnormal spikes of SYN packets or high connection counts within seconds can signify Denial-of-Service (DoS) behavior.
- **Suspicious Ports**: Connection attempts to known backdoor, Trojan, or C2 listener ports (e.g., Metasploit port 4444, Back Orifice 31337) trigger immediate alerts.
- **Threat Intelligence Feeds**: Packets originating from known malicious or blacklisted IP addresses trigger high/critical alerts.

## Features

- **Passive Packet Inspection**: Safe metadata extraction from IP, TCP, UDP, and ICMP layers using Scapy.
- **Stateful Sliding-Window Anomaly Detection**:
  - Horizontal & vertical port scan detection.
  - Connection burst / DoS spike detection.
  - High-volume data exfiltration detection.
- **Threat Intel & Port Rule Matching**:
  - Flags blacklisted IP interactions.
  - Flags known backdoor/trojan communication attempts.
- **Synthetic Traffic Generator**: Includes a safe, non-destructive synthetic packet simulator allowing complete offline validation without requiring root raw socket access.
- **Event Logging & Relational Alert Database**: SQLite storage maintaining timestamped packet flows, alerts, and severity levels (`Low`, `Medium`, `High`, `Critical`).

## Database Schema

- `network_events`: Flow records capturing timestamps, source/destination IPs, protocols, ports, sizes, and TCP flags.
- `security_alerts`: Incident log recording timestamps, alert categories, severity ratings, triggering rules, descriptions, and resolution statuses.

## Dependencies

- Python 3.10+
- `scapy`

```bash
pip install scapy
```

## Running the Application

Launch the interactive CLI:

```bash
cd 61-network-intrusion-detection-system
python3 main.py
```

Choose Option `1` to run the synthetic lab traffic simulation and observe the real-time detection alerts.

## Running Unit Tests

Run the automated test suite:

```bash
python3 -m unittest test_nids.py -v
```
