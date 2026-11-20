"""
Unit tests for Digital Asset & Equipment Assignment Tracker.
"""
import unittest
import os
from asset_service import AssetTrackerService, AssetAssignmentError

TEST_DB = "test_asset_tracker.db"


class TestAssetTracker(unittest.TestCase):
    def setUp(self):
        self._cleanup()
        self.service = AssetTrackerService(TEST_DB)
        self.service.register_employee("EMP-01", "Alice Smith", "alice@corp.com", "Engineering", "Developer")
        self.service.register_employee("EMP-02", "Bob Jones", "bob@corp.com", "Marketing", "Specialist")
        self.service.register_asset("AST-01", "MacBook Pro 14", "Laptop", "SN-10001", "2026-01-01", 2500.0)

    def tearDown(self):
        self._cleanup()

    def _cleanup(self):
        if os.path.exists(TEST_DB):
            os.remove(TEST_DB)

    def test_duplicate_asset_prevention(self):
        with self.assertRaises(ValueError):
            self.service.register_asset("AST-01", "Another Laptop", "Laptop", "SN-99999", "2026-01-01", 2000.0)

        with self.assertRaises(ValueError):
            self.service.register_asset("AST-02", "Duplicate Serial", "Laptop", "SN-10001", "2026-01-01", 2000.0)

    def test_prevent_assigning_already_assigned_asset(self):
        # Assign to Alice
        asg_ref = self.service.assign_asset("AST-01", "EMP-01")
        self.assertTrue(asg_ref.startswith("ASG-"))

        # Check status is Assigned
        ast = self.service.get_asset("AST-01")
        self.assertEqual(ast["status"], "Assigned")
        self.assertEqual(ast["holder_name"], "Alice Smith")

        # Attempt to assign the SAME asset to Bob must be blocked
        with self.assertRaises(AssetAssignmentError) as ctx:
            self.service.assign_asset("AST-01", "EMP-02")
        self.assertIn("must be returned or made Available first", str(ctx.exception))

    def test_return_asset_restores_availability(self):
        asg_ref = self.service.assign_asset("AST-01", "EMP-01")
        self.service.return_asset(asg_ref, return_date="2026-06-01", condition_at_return="Good")

        # Asset should be Available again
        ast = self.service.get_asset("AST-01")
        self.assertEqual(ast["status"], "Available")
        self.assertIsNone(ast["current_holder_id"])

        # Now Bob can be assigned the asset
        asg_ref_2 = self.service.assign_asset("AST-01", "EMP-02")
        self.assertTrue(asg_ref_2.startswith("ASG-"))

    def test_return_damaged_asset_flags_damaged(self):
        asg_ref = self.service.assign_asset("AST-01", "EMP-01")
        self.service.return_asset(asg_ref, return_date="2026-06-01", condition_at_return="Damaged", notes="Cracked screen")

        ast = self.service.get_asset("AST-01")
        self.assertEqual(ast["status"], "Damaged")
        self.assertEqual(ast["current_condition"], "Damaged")

        # Damaged asset cannot be assigned
        with self.assertRaises(AssetAssignmentError):
            self.service.assign_asset("AST-01", "EMP-02")

    def test_asset_history_and_allocation_report(self):
        asg_ref = self.service.assign_asset("AST-01", "EMP-01")
        self.service.return_asset(asg_ref, condition_at_return="Good")

        history = self.service.get_asset_history("AST-01")
        self.assertEqual(len(history["assignments"]), 1)
        self.assertGreaterEqual(len(history["condition_logs"]), 3)

        rep = self.service.generate_allocation_report()
        self.assertEqual(rep["total_assets"], 1)


if __name__ == "__main__":
    unittest.main()
