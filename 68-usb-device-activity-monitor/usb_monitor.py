"""
USB Device Monitoring & Allowlist Enforcement Service.
Logs device insertion/removal events, matches against authorized allowlists,
and generates alerts for rogue or unknown removable media.
"""
from datetime import datetime
import logging
from typing import Optional, Dict, List, Any
from database import get_connection, init_db

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger("USBMonitor")


class USBMonitorService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    # ==================== Allowlist Management ====================

    def add_approved_device(self, serial_number: str, vendor_name: str, product_name: str,
                            vendor_id: str, product_id: str, approved_by: str = "SecOps Lead") -> int:
        serial_number = serial_number.strip().upper()
        vendor_id = vendor_id.strip().lower()
        product_id = product_id.strip().lower()

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO approved_devices (serial_number, vendor_name, product_name, vendor_id, product_id, approved_by)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (serial_number, vendor_name.strip(), product_name.strip(), vendor_id, product_id, approved_by)
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                raise ValueError(f"Device with serial '{serial_number}' is already on the allowlist.")
            raise
        finally:
            conn.close()

    def list_approved_devices(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM approved_devices ORDER BY vendor_name ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def is_device_approved(self, serial_number: str, vendor_id: Optional[str] = None,
                           product_id: Optional[str] = None) -> bool:
        """Check whether a hardware serial or VID/PID pair is authorized."""
        serial_number = serial_number.strip().upper()
        conn = self._get_connection()
        try:
            # First match exact serial number
            row = conn.execute("SELECT id FROM approved_devices WHERE serial_number = ?", (serial_number,)).fetchone()
            if row:
                return True

            # If VID and PID provided, check if authorized hardware model
            if vendor_id and product_id:
                row_vid = conn.execute(
                    "SELECT id FROM approved_devices WHERE vendor_id = ? AND product_id = ?",
                    (vendor_id.strip().lower(), product_id.strip().lower())
                ).fetchone()
                if row_vid:
                    return True

            return False
        finally:
            conn.close()

    # ==================== Event Processing ====================

    def process_event(self, event_type: str, serial_number: str, vendor_name: str,
                      product_name: str, vendor_id: str, product_id: str,
                      host: str, user: str, device_type: str = "Mass Storage",
                      timestamp: Optional[str] = None) -> Dict[str, Any]:
        """
        Record a device connection/disconnection event and trigger alerts if unapproved.
        """
        event_type = event_type.strip().upper()
        if event_type not in ("CONNECTED", "DISCONNECTED"):
            raise ValueError("Event type must be 'CONNECTED' or 'DISCONNECTED'.")

        serial_number = serial_number.strip().upper()
        ts = timestamp or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        is_approved = self.is_device_approved(serial_number, vendor_id, product_id)
        alert_triggered = False
        alert_info = None

        conn = self._get_connection()
        try:
            with conn:
                # 1. Check if unapproved connection
                if event_type == "CONNECTED" and not is_approved:
                    alert_triggered = True
                    sev = "Critical" if "storage" in device_type.lower() else "High"
                    details = f"Unapproved USB device insertion detected on host {host} by user {user}. Device: {vendor_name} {product_name} (SN: {serial_number}, VID/PID: {vendor_id}:{product_id})."
                    logger.warning(f"[USB SECURITY ALERT] {details}")

                cursor = conn.execute(
                    """
                    INSERT INTO device_events (
                        event_type, serial_number, vendor_name, product_name, vendor_id,
                        product_id, device_type, host, user, timestamp, is_approved, alert_triggered
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        event_type, serial_number, vendor_name, product_name, vendor_id,
                        product_id, device_type, host, user, ts, 1 if is_approved else 0,
                        1 if alert_triggered else 0
                    )
                )
                event_id = cursor.lastrowid

                if alert_triggered:
                    cursor_alt = conn.execute(
                        """
                        INSERT INTO device_alerts (event_id, timestamp, host, user, alert_type, severity, serial_number, details)
                        VALUES (?, ?, ?, ?, 'UNAUTHORIZED_USB_DEVICE', ?, ?, ?)
                        """,
                        (event_id, ts, host, user, sev, serial_number, details)
                    )
                    alert_info = {
                        "alert_id": cursor_alt.lastrowid,
                        "severity": sev,
                        "details": details
                    }

                return {
                    "event_id": event_id,
                    "event_type": event_type,
                    "serial_number": serial_number,
                    "is_approved": is_approved,
                    "alert_triggered": alert_triggered,
                    "alert_info": alert_info
                }
        finally:
            conn.close()

    def get_alerts(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM device_alerts ORDER BY timestamp DESC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_event_history(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM device_events ORDER BY id DESC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_audit_summary(self) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            total_events = conn.execute("SELECT count(*) FROM device_events").fetchone()[0]
            unapproved_conns = conn.execute(
                "SELECT count(*) FROM device_events WHERE event_type = 'CONNECTED' AND is_approved = 0"
            ).fetchone()[0]
            approved_conns = conn.execute(
                "SELECT count(*) FROM device_events WHERE event_type = 'CONNECTED' AND is_approved = 1"
            ).fetchone()[0]
            total_alerts = conn.execute("SELECT count(*) FROM device_alerts").fetchone()[0]

            flagged_devices = conn.execute(
                """
                SELECT serial_number, vendor_name, product_name, count(*) as count
                FROM device_events
                WHERE is_approved = 0 AND event_type = 'CONNECTED'
                GROUP BY serial_number
                ORDER BY count DESC LIMIT 5
                """
            ).fetchall()

            return {
                "total_events_logged": total_events,
                "approved_connections": approved_conns,
                "unauthorized_connections": unapproved_conns,
                "security_alerts_generated": total_alerts,
                "top_unauthorized_devices": [dict(r) for r in flagged_devices]
            }
        finally:
            conn.close()
