"""
Synthetic Multi-Source Security Operations Center (SOC) Telemetry.
Simulates authentication events, web server access logs, and network firewall streams.
"""

SYNTHETIC_AUTH_LOGS = [
    {"timestamp": "2026-11-23 09:00:00", "ip_address": "10.0.1.15", "username": "alice", "action": "LOGIN_SUCCESS", "message": "Kerberos TGT issued"},
    {"timestamp": "2026-11-23 09:02:10", "ip_address": "10.0.1.20", "username": "bob", "action": "LOGIN_SUCCESS", "message": "SSH public key accepted"},
    # Brute Force / Spraying Attack from 198.51.100.77
    {"timestamp": "2026-11-23 09:10:01", "ip_address": "198.51.100.77", "username": "root", "action": "LOGIN_FAIL", "message": "Invalid password"},
    {"timestamp": "2026-11-23 09:10:15", "ip_address": "198.51.100.77", "username": "admin", "action": "LOGIN_FAIL", "message": "Invalid password"},
    {"timestamp": "2026-11-23 09:10:32", "ip_address": "198.51.100.77", "username": "administrator", "action": "LOGIN_FAIL", "message": "Invalid password"},
    {"timestamp": "2026-11-23 09:10:48", "ip_address": "198.51.100.77", "username": "guest", "action": "LOGIN_FAIL", "message": "Account disabled"},
    {"timestamp": "2026-11-23 09:11:05", "ip_address": "198.51.100.77", "username": "service_account", "action": "LOGIN_FAIL", "message": "Invalid password"},
    {"timestamp": "2026-11-23 09:11:20", "ip_address": "198.51.100.77", "username": "backup", "action": "LOGIN_FAIL", "message": "Invalid password"},
    # Initial Access Compromise from 203.0.113.50
    {"timestamp": "2026-11-23 09:25:30", "ip_address": "203.0.113.50", "username": "dev_operator", "action": "LOGIN_SUCCESS", "message": "VPN session authenticated"}
]

SYNTHETIC_WEB_LOGS = [
    {"timestamp": "2026-11-23 09:05:00", "ip_address": "10.0.1.15", "method": "GET", "path": "/dashboard/index.html", "status_code": 200, "bytes": 4500},
    {"timestamp": "2026-11-23 09:06:12", "ip_address": "10.0.1.20", "method": "GET", "path": "/api/v1/profile", "status_code": 200, "bytes": 1200},
    # Reconnaissance probe from 203.0.113.50 leading to auth
    {"timestamp": "2026-11-23 09:22:15", "ip_address": "203.0.113.50", "method": "GET", "path": "/admin/config.php", "status_code": 403, "bytes": 512},
    {"timestamp": "2026-11-23 09:23:40", "ip_address": "203.0.113.50", "method": "GET", "path": "/api/v1/auth/tokens", "status_code": 200, "bytes": 3200}
]

SYNTHETIC_FIREWALL_LOGS = [
    {"timestamp": "2026-11-23 09:07:00", "src_ip": "10.0.1.15", "dst_ip": "8.8.8.8", "dst_port": 53, "action": "ACCEPT", "bytes": 120},
    {"timestamp": "2026-11-23 09:08:15", "src_ip": "10.0.1.20", "dst_ip": "192.30.255.113", "dst_port": 443, "action": "ACCEPT", "bytes": 14500},
    # High-Volume Exfiltration connection following 203.0.113.50 compromise
    {"timestamp": "2026-11-23 09:30:00", "src_ip": "203.0.113.50", "dst_ip": "185.220.101.99", "dst_port": 443, "action": "ACCEPT", "bytes": 4500000}
]
