"""
Automated unit tests for USB Device Activity Monitoring & Audit System.
"""
import unittest
import os
import tempfile
from usb_monitor import USBMonitorService
from device_simulator import SIMULATED_EVENTS


class TestUSBMonitor(unittest.TestCase):
    def setUp(self):
        self.temp_db = tempfile.NamedTemporaryFile(suffix=".db", delete=False)
        self.db_path = self.temp_db.name
        self.temp_db.close()
        self.service = USBMonitorService(self.db_path)

        # Seed approved company device
        self.service.add_approved_device(
            serial_number="CORP-KINGSTON-98214",
            vendor_name="Kingston Technology",
            product_name="DataTraveler Vault",
            vendor_id="0951",
            product_id="1666",
            approved_by="IT Security Admin"
        )

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_approved_device_registration_and_duplicate_check(self):
        devices = self.service.list_approved_devices()
        self.assertEqual(len(devices), 1)
        self.assertEqual(devices[0]["serial_number"], "CORP-KINGSTON-98214")

        with self.assertRaises(ValueError):
            self.service.add_approved_device(
                "CORP-KINGSTON-98214", "Kingston", "Duplicate", "0951", "1666"
            )

    def test_approved_device_connection_allowed_without_alert(self):
        res = self.service.process_event(
            event_type="CONNECTED",
            serial_number="CORP-KINGSTON-98214",
            vendor_name="Kingston Technology",
            product_name="DataTraveler Vault",
            vendor_id="0951",
            product_id="1666",
            host="WS-01",
            user="CORP\\user1"
        )
        self.assertTrue(res["is_approved"])
        self.assertFalse(res["alert_triggered"])
        self.assertEqual(len(self.service.get_alerts()), 0)

    def test_unauthorized_device_connection_generates_alert(self):
        res = self.service.process_event(
            event_type="CONNECTED",
            serial_number="ROGUE-THUMB-5544",
            vendor_name="Generic",
            product_name="Flash Drive",
            vendor_id="1234",
            product_id="5678",
            host="WS-HR-02",
            user="CORP\\unauthorized_user",
            device_type="Mass Storage"
        )
        self.assertFalse(res["is_approved"])
        self.assertTrue(res["alert_triggered"])

        alerts = self.service.get_alerts()
        self.assertEqual(len(alerts), 1)
        self.assertEqual(alerts[0]["alert_type"], "UNAUTHORIZED_USB_DEVICE")
        self.assertEqual(alerts[0]["severity"], "Critical")
        self.assertEqual(alerts[0]["serial_number"], "ROGUE-THUMB-5544")

    def test_disconnection_event_logged_safely(self):
        res = self.service.process_event(
            event_type="DISCONNECTED",
            serial_number="ROGUE-THUMB-5544",
            vendor_name="Generic",
            product_name="Flash Drive",
            vendor_id="1234",
            product_id="5678",
            host="WS-HR-02",
            user="CORP\\unauthorized_user"
        )
        self.assertEqual(res["event_type"], "DISCONNECTED")
        self.assertFalse(res["alert_triggered"])

    def test_simulated_stream_and_audit_summary(self):
        for ev in SIMULATED_EVENTS:
            self.service.process_event(
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

        summary = self.service.get_audit_summary()
        self.assertEqual(summary["total_events_logged"], 4)
        self.assertEqual(summary["approved_connections"], 1)
        self.assertEqual(summary["unauthorized_connections"], 2)
        self.assertEqual(summary["security_alerts_generated"], 2)
        self.assertGreaterEqual(len(summary["top_unauthorized_devices"]), 2)


if __name__ == "__main__":
    unittest.main()
