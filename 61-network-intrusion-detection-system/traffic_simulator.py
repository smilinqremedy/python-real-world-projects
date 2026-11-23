"""
Synthetic Traffic Generator for NIDS Lab Testing.
Generates safe Scapy packet streams simulating legitimate traffic
and defensive test cases (port scans, connection bursts, suspicious ports, blacklisted IPs).
"""
import time
from typing import List
from scapy.layers.inet import IP, TCP, UDP, ICMP
from scapy.packet import Raw


def generate_synthetic_stream() -> List:
    packets = []
    base_time = time.time()

    # 1. Normal Web & DNS Traffic (Host: 192.168.1.50)
    for i in range(5):
        pkt_dns = IP(src="192.168.1.50", dst="8.8.8.8") / UDP(sport=54321 + i, dport=53) / Raw(load=b"dns_query_example")
        pkt_dns.time = base_time + (i * 0.2)
        pkt_http = IP(src="192.168.1.50", dst="93.184.216.34") / TCP(sport=50000 + i, dport=443, flags="PA") / Raw(load=b"tls_client_hello")
        pkt_http.time = base_time + 0.1 + (i * 0.2)
        packets.extend([pkt_dns, pkt_http])

    # 2. Port Scan Attack Simulation (Host: 192.168.1.199 probing 8 target ports)
    scan_ports = [21, 22, 23, 25, 80, 443, 3389, 8080]
    for idx, p in enumerate(scan_ports):
        scan_pkt = IP(src="192.168.1.199", dst="192.168.1.10") / TCP(sport=40000 + idx, dport=p, flags="S")
        scan_pkt.time = base_time + 1.0 + (idx * 0.05)
        packets.append(scan_pkt)

    # 3. Connection Attempt to Known Suspicious Port (Port 4444 - Metasploit Default)
    suspicious_pkt = IP(src="192.168.1.77", dst="192.168.1.10") / TCP(sport=49152, dport=4444, flags="S")
    suspicious_pkt.time = base_time + 2.0
    packets.append(suspicious_pkt)

    # 4. Packet Burst / DoS Simulation (Host: 192.168.1.88 sending 18 rapid packets)
    for i in range(18):
        burst_pkt = IP(src="192.168.1.88", dst="192.168.1.10") / TCP(sport=30000 + i, dport=80, flags="S")
        burst_pkt.time = base_time + 2.5 + (i * 0.02)
        packets.append(burst_pkt)

    # 5. Known Blacklisted Threat Actor IP (198.51.100.45)
    threat_pkt = IP(src="198.51.100.45", dst="192.168.1.10") / TCP(sport=12345, dport=80, flags="S")
    threat_pkt.time = base_time + 3.0
    packets.append(threat_pkt)

    return packets
