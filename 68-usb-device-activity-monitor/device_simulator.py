"""
Synthetic USB Device Event Stream for Endpoint Activity Simulation.
Simulates insertion and removal of corporate allowlisted flash drives,
unauthorized personal thumb drives, and rogue HID/storage devices.
"""

SIMULATED_EVENTS = [
    # 1. Authorized Company Encrypted Flash Drive Insertion
    {
        "event_type": "CONNECTED",
        "serial_number": "CORP-KINGSTON-98214",
        "vendor_name": "Kingston Technology",
        "product_name": "DataTraveler Vault Privacy",
        "vendor_id": "0951",
        "product_id": "1666",
        "device_type": "Encrypted Mass Storage",
        "host": "WS-FINANCE-01",
        "user": "CORP\\adeleke",
        "timestamp": "2026-11-23 08:45:10"
    },
    # 2. Unauthorized Personal Flash Drive Insertion (Flagged)
    {
        "event_type": "CONNECTED",
        "serial_number": "SANDISK-CRUZER-X992",
        "vendor_name": "SanDisk",
        "product_name": "Cruzer Blade 32GB",
        "vendor_id": "0781",
        "product_id": "5567",
        "device_type": "Mass Storage",
        "host": "WS-HR-03",
        "user": "CORP\\nwosu",
        "timestamp": "2026-11-23 09:15:22"
    },
    # 3. Unauthorized Device Disconnected
    {
        "event_type": "DISCONNECTED",
        "serial_number": "SANDISK-CRUZER-X992",
        "vendor_name": "SanDisk",
        "product_name": "Cruzer Blade 32GB",
        "vendor_id": "0781",
        "product_id": "5567",
        "device_type": "Mass Storage",
        "host": "WS-HR-03",
        "user": "CORP\\nwosu",
        "timestamp": "2026-11-23 09:22:04"
    },
    # 4. Rogue Keystroke Injection / BadUSB Hardware Insertion (Flagged Critical)
    {
        "event_type": "CONNECTED",
        "serial_number": "DUCKY-V2-88129",
        "vendor_name": "Hak5",
        "product_name": "USB Rubber Ducky HID / Mass Storage",
        "vendor_id": "03eb",
        "product_id": "2403",
        "device_type": "Compound HID / Storage",
        "host": "SRV-DC-01",
        "user": "LOCAL\\operator",
        "timestamp": "2026-11-23 09:40:15"
    }
]
