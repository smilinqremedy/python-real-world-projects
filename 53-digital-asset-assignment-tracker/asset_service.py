"""
Service layer and business logic for Digital Asset & Equipment Assignment Tracker.
"""
from datetime import datetime, date
import secrets
from database import get_connection, init_db


class AssetAssignmentError(Exception):
    """Raised when an asset assignment violates business rules."""
    pass


class AssetTrackerService:
    def __init__(self, db_path=None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    # ==================== Employee Registration ====================

    def register_employee(self, employee_id: str, full_name: str, email: str, department: str, designation: str) -> int:
        employee_id = employee_id.strip().upper()
        full_name = full_name.strip()
        email = email.strip().lower()
        dept = department.strip()
        desig = designation.strip()

        if not employee_id or not full_name or not email or not dept:
            raise ValueError("Employee ID, full name, email, and department are required.")

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO employees (employee_id, full_name, email, department, designation)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (employee_id, full_name, email, dept, desig),
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError("Employee ID or email already registered.")
            raise
        finally:
            conn.close()

    def list_employees(self) -> list[dict]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM employees WHERE is_active = 1 ORDER BY full_name ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Asset Registration ====================

    def register_asset(self, asset_tag: str, name: str, category: str, serial_number: str,
                       purchase_date: str, purchase_cost: float, model_number: str = None,
                       condition: str = "New") -> int:
        asset_tag = asset_tag.strip().upper()
        name = name.strip()
        category = category.strip()
        serial_number = serial_number.strip().upper()
        condition = condition.strip().capitalize()

        if not asset_tag or not name or not category or not serial_number:
            raise ValueError("Asset tag, name, category, and serial number are required.")

        if purchase_cost < 0:
            raise ValueError("Purchase cost cannot be negative.")

        valid_conditions = ("New", "Good", "Fair", "Damaged", "Broken")
        if condition not in valid_conditions:
            raise ValueError(f"Condition must be one of: {', '.join(valid_conditions)}")

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO assets (
                        asset_tag, name, category, model_number, serial_number,
                        purchase_date, purchase_cost, current_condition, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Available')
                    """,
                    (asset_tag, name, category, model_number, serial_number, purchase_date, purchase_cost, condition),
                )
                asset_id = cursor.lastrowid

                # Initial condition log
                conn.execute(
                    """
                    INSERT INTO asset_condition_logs (asset_id, previous_condition, new_condition, action, notes)
                    VALUES (?, NULL, ?, 'Registration', 'Initial asset onboarding')
                    """,
                    (asset_id, condition),
                )
                return asset_id
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Asset tag '{asset_tag}' or serial number '{serial_number}' is already registered.")
            raise
        finally:
            conn.close()

    def get_asset(self, asset_tag: str) -> dict:
        conn = self._get_connection()
        try:
            row = conn.execute(
                """
                SELECT a.*, e.full_name as holder_name, e.employee_id as holder_emp_id, e.department as holder_dept
                FROM assets a
                LEFT JOIN employees e ON a.current_holder_id = e.id
                WHERE a.asset_tag = ?
                """,
                (asset_tag.strip().upper(),),
            ).fetchone()
            if not row:
                raise ValueError(f"Asset with tag '{asset_tag}' not found.")
            return dict(row)
        finally:
            conn.close()

    def list_assets(self, status: str = None) -> list[dict]:
        conn = self._get_connection()
        try:
            sql = """
            SELECT a.*, e.full_name as holder_name, e.employee_id as holder_emp_id, e.department as holder_dept
            FROM assets a
            LEFT JOIN employees e ON a.current_holder_id = e.id
            """
            params = []
            if status:
                sql += " WHERE a.status = ?"
                params.append(status)
            sql += " ORDER BY a.asset_tag ASC"

            rows = conn.execute(sql, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Asset Assignment & Return ====================

    def assign_asset(self, asset_tag: str, employee_id: str, assigned_date: str = None,
                     expected_return_date: str = None, notes: str = None) -> str:
        """
        Assign an asset to an employee.
        CRITICAL BUSINESS RULE: Prevents an already-assigned or unavailable asset from being assigned.
        """
        asset_tag = asset_tag.strip().upper()
        employee_id = employee_id.strip().upper()

        if not assigned_date:
            assigned_date = datetime.now().strftime("%Y-%m-%d")

        conn = self._get_connection()
        try:
            with conn:
                asset = conn.execute(
                    "SELECT id, asset_tag, status, current_condition FROM assets WHERE asset_tag = ?",
                    (asset_tag,),
                ).fetchone()
                if not asset:
                    raise ValueError(f"Asset '{asset_tag}' not found.")

                if asset["status"] != "Available":
                    raise AssetAssignmentError(
                        f"Cannot assign asset '{asset_tag}': Current status is '{asset['status']}'. It must be returned or made Available first."
                    )

                emp = conn.execute(
                    "SELECT id, full_name, is_active FROM employees WHERE employee_id = ?",
                    (employee_id,),
                ).fetchone()
                if not emp:
                    raise ValueError(f"Employee '{employee_id}' not found.")
                if not emp["is_active"]:
                    raise AssetAssignmentError(f"Employee '{employee_id}' is inactive and cannot be assigned assets.")

                today_str = datetime.now().strftime("%Y%m%d")
                seq = secrets.randbelow(9000) + 1000
                asg_ref = f"ASG-{today_str}-{seq}"

                # Create assignment
                conn.execute(
                    """
                    INSERT INTO asset_assignments (
                        assignment_ref, asset_id, employee_id, assigned_date,
                        expected_return_date, condition_at_assignment, status, notes
                    ) VALUES (?, ?, ?, ?, ?, ?, 'Active', ?)
                    """,
                    (asg_ref, asset["id"], emp["id"], assigned_date, expected_return_date, asset["current_condition"], notes),
                )

                # Update asset status & holder
                conn.execute(
                    "UPDATE assets SET status = 'Assigned', current_holder_id = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (emp["id"], asset["id"]),
                )

                # Log condition / status change
                conn.execute(
                    """
                    INSERT INTO asset_condition_logs (asset_id, previous_condition, new_condition, action, recorded_by, notes)
                    VALUES (?, ?, ?, 'Assignment', ?, ?)
                    """,
                    (asset["id"], asset["current_condition"], asset["current_condition"], f"Assigned to {emp['full_name']} ({employee_id})", notes),
                )

                return asg_ref
        finally:
            conn.close()

    def return_asset(self, assignment_ref: str, return_date: str = None,
                     condition_at_return: str = "Good", notes: str = None) -> bool:
        """
        Record return of an assigned asset, update its condition, and restore availability.
        """
        assignment_ref = assignment_ref.strip().upper()
        if not return_date:
            return_date = datetime.now().strftime("%Y-%m-%d")

        valid_conditions = ("New", "Good", "Fair", "Damaged", "Broken")
        if condition_at_return not in valid_conditions:
            raise ValueError(f"Condition must be one of: {', '.join(valid_conditions)}")

        conn = self._get_connection()
        try:
            with conn:
                asg = conn.execute(
                    """
                    SELECT a.*, ast.id as asset_db_id, ast.asset_tag, ast.current_condition
                    FROM asset_assignments a
                    JOIN assets ast ON a.asset_id = ast.id
                    WHERE a.assignment_ref = ?
                    """,
                    (assignment_ref,),
                ).fetchone()
                if not asg:
                    raise ValueError(f"Assignment '{assignment_ref}' not found.")
                if asg["status"] == "Returned":
                    raise AssetAssignmentError(f"Assignment '{assignment_ref}' is already marked as returned.")

                # Determine new asset status: if condition is Damaged or Broken, mark as Damaged
                new_asset_status = "Damaged" if condition_at_return in ("Damaged", "Broken") else "Available"

                # Mark assignment returned
                conn.execute(
                    """
                    UPDATE asset_assignments
                    SET returned_date = ?, condition_at_return = ?, status = 'Returned', notes = coalesce(?, notes)
                    WHERE id = ?
                    """,
                    (return_date, condition_at_return, notes, asg["id"]),
                )

                # Update asset
                conn.execute(
                    """
                    UPDATE assets
                    SET status = ?, current_condition = ?, current_holder_id = NULL, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (new_asset_status, condition_at_return, asg["asset_db_id"]),
                )

                # Log condition change
                conn.execute(
                    """
                    INSERT INTO asset_condition_logs (asset_id, previous_condition, new_condition, action, notes)
                    VALUES (?, ?, ?, 'Return', ?)
                    """,
                    (asg["asset_db_id"], asg["current_condition"], condition_at_return, f"Returned via {assignment_ref}. {notes or ''}"),
                )
                return True
        finally:
            conn.close()

    def report_asset_status(self, asset_tag: str, new_status: str, new_condition: str = None, notes: str = None) -> bool:
        """Manually mark asset as Damaged, Under Repair, Lost / Missing, or Retired."""
        asset_tag = asset_tag.strip().upper()
        valid_statuses = ("Available", "Under Repair", "Damaged", "Lost / Missing", "Retired")
        if new_status not in valid_statuses:
            raise ValueError(f"Status must be one of: {', '.join(valid_statuses)}")

        conn = self._get_connection()
        try:
            with conn:
                asset = conn.execute("SELECT id, status, current_condition FROM assets WHERE asset_tag = ?", (asset_tag,)).fetchone()
                if not asset:
                    raise ValueError(f"Asset '{asset_tag}' not found.")

                cond = new_condition or asset["current_condition"]
                conn.execute(
                    """
                    UPDATE assets
                    SET status = ?, current_condition = ?, current_holder_id = CASE WHEN ? IN ('Lost / Missing', 'Retired', 'Under Repair') THEN NULL ELSE current_holder_id END,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (new_status, cond, new_status, asset["id"]),
                )

                conn.execute(
                    """
                    INSERT INTO asset_condition_logs (asset_id, previous_condition, new_condition, action, notes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (asset["id"], asset["current_condition"], cond, f"Status Update -> {new_status}", notes),
                )
                return True
        finally:
            conn.close()

    # ==================== Asset History & Allocation Reports ====================

    def get_asset_history(self, asset_tag: str) -> dict:
        asset_tag = asset_tag.strip().upper()
        conn = self._get_connection()
        try:
            asset = self.get_asset(asset_tag)

            assignments = conn.execute(
                """
                SELECT a.*, e.full_name as employee_name, e.employee_id, e.department
                FROM asset_assignments a
                JOIN employees e ON a.employee_id = e.id
                WHERE a.asset_id = ?
                ORDER BY a.assigned_date DESC
                """,
                (asset["id"],),
            ).fetchall()

            condition_logs = conn.execute(
                "SELECT * FROM asset_condition_logs WHERE asset_id = ? ORDER BY timestamp DESC",
                (asset["id"],),
            ).fetchall()

            asset["assignments"] = [dict(a) for a in assignments]
            asset["condition_logs"] = [dict(c) for c in condition_logs]
            return asset
        finally:
            conn.close()

    def generate_allocation_report(self) -> dict:
        conn = self._get_connection()
        try:
            total = conn.execute("SELECT count(*) FROM assets").fetchone()[0]

            by_status = conn.execute(
                "SELECT status, count(*) as count FROM assets GROUP BY status"
            ).fetchall()

            by_category = conn.execute(
                "SELECT category, count(*) as total, sum(CASE WHEN status = 'Assigned' THEN 1 ELSE 0 END) as assigned_count FROM assets GROUP BY category"
            ).fetchall()

            by_dept = conn.execute(
                """
                SELECT e.department, count(a.id) as assigned_assets
                FROM assets a
                JOIN employees e ON a.current_holder_id = e.id
                WHERE a.status = 'Assigned'
                GROUP BY e.department
                ORDER BY assigned_assets DESC
                """
            ).fetchall()

            damaged_or_missing = conn.execute(
                "SELECT asset_tag, name, category, status, current_condition FROM assets WHERE status IN ('Damaged', 'Lost / Missing', 'Under Repair')"
            ).fetchall()

            return {
                "total_assets": total,
                "by_status": [dict(s) for s in by_status],
                "by_category": [dict(c) for c in by_category],
                "by_department": [dict(d) for d in by_dept],
                "damaged_or_missing": [dict(dm) for dm in damaged_or_missing],
            }
        finally:
            conn.close()
