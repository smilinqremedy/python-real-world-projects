# Project 70: Security Log Correlation & Threat Hunting Tool

A Security Operations Center (SOC) threat hunting and SIEM correlation platform engineered to ingest disparate telemetry streams (authentication servers, web application reverse proxies, and network firewalls), normalize heterogeneous timestamp formats into a synchronized timeline, and correlate multi-stage attack patterns that escape single-source monitoring.

## Multi-Stage Attack Correlation Rules

Individual log sources rarely reveal sophisticated attacks in isolation:
1. **Rule 1: Password Spraying & Credential Brute Force (`BRUTE_FORCE_01`)**:
   - Detects $\ge 5$ failed authentications originating from a single IP address or targeting multiple usernames within a 5-minute window.
2. **Rule 2: Web Reconnaissance to Initial Access (`RECON_TO_ACCESS_02`)**:
   - Correlates administrative web application probing (e.g. `/admin`, SQL injection patterns, or authentication API fuzzing) from IP $X$ followed within 10 minutes by a successful login originating from the identical IP $X$.
3. **Rule 3: Compromise to High-Volume Data Exfiltration (`EXFILTRATION_03`)**:
   - Correlates an initial successful authentication followed within 15 minutes by an unusually large outbound network firewall transfer ($\ge 100,000$ bytes) destined for external infrastructure.

## Features

- **Multi-Source Ingestion & Timestamp Normalization**: Ingests authentication logs, web access logs, and firewall traffic streams across syslog, ISO 8601, and epoch timestamps.
- **Unified Entity Extraction**: Automatically extracts IPv4 addresses, usernames, HTTP methods, and status codes via regular expressions.
- **Cross-Source Chronological Timelines**: Reconstructs complete multi-stage attacker journeys across web, identity, and network boundaries for any given IP address or user.
- **Threat Hunting Filters**: Supports analyst queries filtering by IP address, targeted username, detection rule, and severity level (`Low`, `Medium`, `High`, `Critical`).
- **Synthetic SOC Dataset**: Built-in multi-source telemetry stream containing legitimate baseline operations alongside correlated multi-stage compromise scenarios.

## Database Schema

- `normalized_logs`: Normalized event records (`timestamp`, `epoch_time`, `source_type`, `ip_address`, `username`, `action`, `details`, `status_code`, `bytes_transferred`).
- `correlated_threats`: Correlated incident findings (`title`, `severity`, `rule_id`, `ip_address`, `username`, `first_seen`, `last_seen`, `event_count`, `timeline_summary`, `investigation_notes`).

## Running the Application

Launch the interactive CLI:

```bash
cd 70-security-log-correlation-threat-hunting
python3 main.py
```

Choose Option `1` to ingest the synthetic SOC telemetry stream, then Option `2` to execute cross-source correlation.

## Running Unit Tests

Execute the automated test suite:

```bash
python3 -m unittest test_threat_hunter.py -v
```
