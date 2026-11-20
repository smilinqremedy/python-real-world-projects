"""
Pharmacy Service and Business Logic for Hospital Pharmacy Prescription Management.
"""
from datetime import datetime, date
import re
import secrets
from database import get_connection, init_db


class PrescriptionError(Exception):
    """Raised when an operation on a prescription is invalid or violates constraints."""
    pass


class InsufficientStockError(PrescriptionError):
    """Raised when attempting to dispense more medicine than is available in stock."""
    pass


class PharmacyService:
    def __init__(self, db_path=None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    # ==================== Patient Registration ====================

    def register_patient(self, patient_id: str, full_name: str, date_of_birth: str,
                         gender: str, phone: str, email: str = None, allergies: str = "None reported") -> int:
        patient_id = patient_id.strip().upper()
        full_name = full_name.strip()
        dob = date_of_birth.strip()
        gender = gender.strip().capitalize()
        phone = phone.strip()
        email = email.strip().lower() if email else None
        allergies = allergies.strip() if allergies else "None reported"

        if not patient_id or not full_name or not phone:
            raise ValueError("Patient ID, full name, and phone number are required.")

        try:
            dob_parsed = datetime.strptime(dob, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Date of birth must follow 'YYYY-MM-DD' format.")

        if dob_parsed >= date.today():
            raise ValueError("Date of birth must be a past date.")

        if gender not in ("M", "F", "Other"):
            raise ValueError("Gender must be 'M', 'F', or 'Other'.")

        if email and not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", email):
            raise ValueError(f"Invalid email format: {email}")

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO patients (patient_id, full_name, date_of_birth, gender, phone, email, allergies)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (patient_id, full_name, dob, gender, phone, email, allergies),
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Patient ID '{patient_id}' already registered.")
            raise
        finally:
            conn.close()

    def get_patient(self, patient_id: str) -> dict:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM patients WHERE patient_id = ?", (patient_id.strip().upper(),)).fetchone()
            if not row:
                raise ValueError(f"Patient '{patient_id}' not found.")
            return dict(row)
        finally:
            conn.close()

    # ==================== Doctor Registration ====================

    def register_doctor(self, doctor_id: str, full_name: str, specialization: str,
                        license_number: str, phone: str, email: str = None) -> int:
        doctor_id = doctor_id.strip().upper()
        full_name = full_name.strip()
        spec = specialization.strip()
        lic = license_number.strip().upper()
        phone = phone.strip()
        email = email.strip().lower() if email else None

        if not doctor_id or not full_name or not spec or not lic or not phone:
            raise ValueError("Doctor ID, full name, specialization, license number, and phone are required.")

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO doctors (doctor_id, full_name, specialization, license_number, phone, email)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (doctor_id, full_name, spec, lic, phone, email),
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Doctor ID or license number already registered.")
            raise
        finally:
            conn.close()

    # ==================== Medicine Inventory Management ====================

    def add_medicine(self, medicine_id: str, name: str, dosage_form: str, strength: str,
                     stock_quantity: int, unit_price: float, reorder_level: int = 10,
                     manufacturer: str = None) -> int:
        medicine_id = medicine_id.strip().upper()
        name = name.strip()
        dosage_form = dosage_form.strip()
        strength = strength.strip()

        if stock_quantity < 0:
            raise ValueError("Stock quantity cannot be negative.")
        if unit_price < 0:
            raise ValueError("Unit price cannot be negative.")
        if reorder_level < 0:
            raise ValueError("Reorder level cannot be negative.")

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO medicines (
                        medicine_id, name, dosage_form, strength, stock_quantity,
                        unit_price, reorder_level, manufacturer
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (medicine_id, name, dosage_form, strength, stock_quantity, unit_price, reorder_level, manufacturer),
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Medicine ID '{medicine_id}' already registered.")
            raise
        finally:
            conn.close()

    def update_stock(self, medicine_id: str, quantity_delta: int) -> int:
        """Add to or reduce stock of a medicine."""
        medicine_id = medicine_id.strip().upper()
        conn = self._get_connection()
        try:
            with conn:
                med = conn.execute("SELECT stock_quantity FROM medicines WHERE medicine_id = ?", (medicine_id,)).fetchone()
                if not med:
                    raise ValueError(f"Medicine '{medicine_id}' not found.")

                new_stock = med["stock_quantity"] + quantity_delta
                if new_stock < 0:
                    raise ValueError(f"Cannot reduce stock below zero. Current stock: {med['stock_quantity']}.")

                conn.execute(
                    "UPDATE medicines SET stock_quantity = ?, updated_at = CURRENT_TIMESTAMP WHERE medicine_id = ?",
                    (new_stock, medicine_id),
                )
                return new_stock
        finally:
            conn.close()

    def get_medicine(self, medicine_id: str) -> dict:
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM medicines WHERE medicine_id = ?", (medicine_id.strip().upper(),)).fetchone()
            if not row:
                raise ValueError(f"Medicine '{medicine_id}' not found.")
            return dict(row)
        finally:
            conn.close()

    def list_medicines(self, low_stock_only: bool = False) -> list[dict]:
        conn = self._get_connection()
        try:
            if low_stock_only:
                rows = conn.execute("SELECT * FROM medicines WHERE stock_quantity <= reorder_level ORDER BY stock_quantity ASC").fetchall()
            else:
                rows = conn.execute("SELECT * FROM medicines ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Prescriptions Management ====================

    def create_prescription(self, patient_id: str, doctor_id: str, diagnosis: str,
                            prescribed_date: str = None, notes: str = None) -> str:
        patient_id = patient_id.strip().upper()
        doctor_id = doctor_id.strip().upper()
        diagnosis = diagnosis.strip()

        if not diagnosis:
            raise ValueError("Diagnosis is required for prescription.")

        if prescribed_date:
            try:
                datetime.strptime(prescribed_date.strip(), "%Y-%m-%d")
            except ValueError:
                raise ValueError("Prescribed date must be 'YYYY-MM-DD'.")
        else:
            prescribed_date = datetime.now().strftime("%Y-%m-%d")

        conn = self._get_connection()
        try:
            with conn:
                p = conn.execute("SELECT id FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
                if not p:
                    raise ValueError(f"Patient '{patient_id}' does not exist.")

                d = conn.execute("SELECT id, is_active FROM doctors WHERE doctor_id = ?", (doctor_id,)).fetchone()
                if not d:
                    raise ValueError(f"Doctor '{doctor_id}' does not exist.")
                if not d["is_active"]:
                    raise PrescriptionError(f"Doctor '{doctor_id}' is currently inactive and cannot issue prescriptions.")

                today_str = datetime.now().strftime("%Y%m%d")
                seq = secrets.randbelow(9000) + 1000
                rx_ref = f"RX-{today_str}-{seq}"

                conn.execute(
                    """
                    INSERT INTO prescriptions (prescription_ref, patient_id, doctor_id, diagnosis, status, prescribed_date, notes)
                    VALUES (?, ?, ?, ?, 'Pending', ?, ?)
                    """,
                    (rx_ref, p["id"], d["id"], diagnosis, prescribed_date, notes),
                )
                return rx_ref
        finally:
            conn.close()

    def add_prescription_item(self, prescription_ref: str, medicine_id: str,
                              quantity_prescribed: int, dosage_instructions: str,
                              duration_days: int) -> int:
        prescription_ref = prescription_ref.strip().upper()
        medicine_id = medicine_id.strip().upper()
        dosage_instructions = dosage_instructions.strip()

        if quantity_prescribed <= 0:
            raise ValueError("Prescribed quantity must be greater than zero.")
        if duration_days <= 0:
            raise ValueError("Duration days must be greater than zero.")
        if not dosage_instructions:
            raise ValueError("Dosage instructions are required.")

        conn = self._get_connection()
        try:
            with conn:
                rx = conn.execute("SELECT id, status FROM prescriptions WHERE prescription_ref = ?", (prescription_ref,)).fetchone()
                if not rx:
                    raise PrescriptionError(f"Prescription '{prescription_ref}' not found.")
                if rx["status"] != "Pending":
                    raise PrescriptionError(f"Cannot add items to prescription with status '{rx['status']}'.")

                med = conn.execute("SELECT id FROM medicines WHERE medicine_id = ?", (medicine_id,)).fetchone()
                if not med:
                    raise ValueError(f"Medicine '{medicine_id}' not found.")

                cursor = conn.execute(
                    """
                    INSERT INTO prescription_items (
                        prescription_id, medicine_id, quantity_prescribed,
                        dosage_instructions, duration_days, status
                    ) VALUES (?, ?, ?, ?, ?, 'Pending')
                    """,
                    (rx["id"], med["id"], quantity_prescribed, dosage_instructions, duration_days),
                )
                return cursor.lastrowid
        finally:
            conn.close()

    def check_prescription_availability(self, prescription_ref: str) -> dict:
        """
        Check medicine availability in inventory against prescribed quantities.
        Identifies any shortages or out-of-stock items.
        """
        prescription_ref = prescription_ref.strip().upper()
        conn = self._get_connection()
        try:
            rx = conn.execute("SELECT id, status FROM prescriptions WHERE prescription_ref = ?", (prescription_ref,)).fetchone()
            if not rx:
                raise PrescriptionError(f"Prescription '{prescription_ref}' not found.")

            items = conn.execute(
                """
                SELECT pi.id, pi.quantity_prescribed, pi.dosage_instructions, pi.duration_days,
                       m.medicine_id, m.name as medicine_name, m.dosage_form, m.strength,
                       m.stock_quantity, m.unit_price
                FROM prescription_items pi
                JOIN medicines m ON pi.medicine_id = m.id
                WHERE pi.prescription_id = ?
                """,
                (rx["id"],),
            ).fetchall()

            if not items:
                raise PrescriptionError("Prescription has no prescribed medication items.")

            all_available = True
            item_statuses = []
            total_estimated_cost = 0.0

            for it in items:
                available = it["stock_quantity"] >= it["quantity_prescribed"]
                deficit = max(0, it["quantity_prescribed"] - it["stock_quantity"])
                if not available:
                    all_available = False

                cost = round(it["quantity_prescribed"] * it["unit_price"], 2)
                total_estimated_cost += cost

                item_statuses.append({
                    "item_id": it["id"],
                    "medicine_id": it["medicine_id"],
                    "medicine_name": it["medicine_name"],
                    "strength": it["strength"],
                    "prescribed_qty": it["quantity_prescribed"],
                    "available_qty": it["stock_quantity"],
                    "is_available": available,
                    "deficit": deficit,
                    "unit_price": it["unit_price"],
                    "subtotal": cost,
                })

            return {
                "prescription_ref": prescription_ref,
                "status": rx["status"],
                "can_dispense": all_available and rx["status"] == "Pending",
                "items": item_statuses,
                "total_estimated_cost": total_estimated_cost,
            }
        finally:
            conn.close()

    def dispense_prescription(self, prescription_ref: str, pharmacist_name: str, notes: str = None) -> dict:
        """
        Record dispensing of a prescription.
        CRITICAL: Strictly prevents dispensing if ANY medicine has insufficient stock.
        Atomically updates medicine inventory, prescription status, and creates dispense record.
        """
        prescription_ref = prescription_ref.strip().upper()
        pharmacist_name = pharmacist_name.strip()
        if not pharmacist_name:
            raise ValueError("Pharmacist name is required.")

        conn = self._get_connection()
        try:
            with conn:
                rx = conn.execute(
                    "SELECT id, status, patient_id FROM prescriptions WHERE prescription_ref = ?",
                    (prescription_ref,),
                ).fetchone()
                if not rx:
                    raise PrescriptionError(f"Prescription '{prescription_ref}' not found.")
                if rx["status"] == "Dispensed":
                    raise PrescriptionError(f"Prescription '{prescription_ref}' has already been dispensed.")
                if rx["status"] == "Cancelled":
                    raise PrescriptionError(f"Cannot dispense cancelled prescription '{prescription_ref}'.")

                # Fetch items
                items = conn.execute(
                    """
                    SELECT pi.id, pi.quantity_prescribed, m.id as medicine_db_id,
                           m.medicine_id, m.name, m.stock_quantity, m.unit_price
                    FROM prescription_items pi
                    JOIN medicines m ON pi.medicine_id = m.id
                    WHERE pi.prescription_id = ?
                    """,
                    (rx["id"],),
                ).fetchall()

                if not items:
                    raise PrescriptionError("Prescription has no medication items to dispense.")

                # Validate stock for all items BEFORE performing updates
                shortages = []
                total_amount = 0.0
                for it in items:
                    if it["stock_quantity"] < it["quantity_prescribed"]:
                        shortages.append(
                            f"{it['name']} ({it['medicine_id']}): requested {it['quantity_prescribed']}, available {it['stock_quantity']}"
                        )
                    total_amount += round(it["quantity_prescribed"] * it["unit_price"], 2)

                if shortages:
                    raise InsufficientStockError(
                        f"Cannot dispense prescription {prescription_ref}. Insufficient stock for: {'; '.join(shortages)}."
                    )

                # Generate dispense reference
                today_str = datetime.now().strftime("%Y%m%d")
                seq = secrets.randbelow(9000) + 1000
                dispense_ref = f"DSP-{today_str}-{seq}"

                cursor = conn.execute(
                    """
                    INSERT INTO dispense_records (dispense_ref, prescription_id, pharmacist_name, total_amount, notes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (dispense_ref, rx["id"], pharmacist_name, total_amount, notes),
                )
                dispense_id = cursor.lastrowid

                dispensed_items_details = []
                for it in items:
                    subtotal = round(it["quantity_prescribed"] * it["unit_price"], 2)

                    # Decrement inventory stock
                    conn.execute(
                        "UPDATE medicines SET stock_quantity = stock_quantity - ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                        (it["quantity_prescribed"], it["medicine_db_id"]),
                    )

                    # Record dispensed line item
                    conn.execute(
                        """
                        INSERT INTO dispense_items (dispense_id, medicine_id, quantity_dispensed, unit_price, subtotal)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (dispense_id, it["medicine_db_id"], it["quantity_prescribed"], it["unit_price"], subtotal),
                    )

                    dispensed_items_details.append({
                        "medicine_id": it["medicine_id"],
                        "name": it["name"],
                        "quantity": it["quantity_prescribed"],
                        "subtotal": subtotal,
                    })

                # Mark prescription items and prescription as Dispensed
                conn.execute("UPDATE prescription_items SET status = 'Dispensed' WHERE prescription_id = ?", (rx["id"],))
                conn.execute("UPDATE prescriptions SET status = 'Dispensed' WHERE id = ?", (rx["id"],))

                return {
                    "dispense_ref": dispense_ref,
                    "prescription_ref": prescription_ref,
                    "pharmacist_name": pharmacist_name,
                    "total_amount": total_amount,
                    "items": dispensed_items_details,
                    "dispensed_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                }
        finally:
            conn.close()

    def cancel_prescription(self, prescription_ref: str, reason: str = None) -> bool:
        prescription_ref = prescription_ref.strip().upper()
        conn = self._get_connection()
        try:
            with conn:
                rx = conn.execute("SELECT id, status FROM prescriptions WHERE prescription_ref = ?", (prescription_ref,)).fetchone()
                if not rx:
                    raise PrescriptionError(f"Prescription '{prescription_ref}' not found.")
                if rx["status"] == "Dispensed":
                    raise PrescriptionError("Cannot cancel an already dispensed prescription.")

                conn.execute(
                    "UPDATE prescriptions SET status = 'Cancelled', notes = coalesce(?, notes) WHERE id = ?",
                    (f"Cancelled: {reason}" if reason else "Cancelled", rx["id"]),
                )
                return True
        finally:
            conn.close()

    def get_prescription(self, prescription_ref: str) -> dict:
        prescription_ref = prescription_ref.strip().upper()
        conn = self._get_connection()
        try:
            row = conn.execute(
                """
                SELECT rx.*, p.patient_id, p.full_name as patient_name, p.phone as patient_phone,
                       p.allergies as patient_allergies, d.doctor_id, d.full_name as doctor_name,
                       d.specialization as doctor_specialization
                FROM prescriptions rx
                JOIN patients p ON rx.patient_id = p.id
                JOIN doctors d ON rx.doctor_id = d.id
                WHERE rx.prescription_ref = ?
                """,
                (prescription_ref,),
            ).fetchone()
            if not row:
                raise PrescriptionError(f"Prescription '{prescription_ref}' not found.")

            rx_data = dict(row)
            items = conn.execute(
                """
                SELECT pi.*, m.medicine_id, m.name as medicine_name, m.dosage_form, m.strength, m.unit_price, m.stock_quantity
                FROM prescription_items pi
                JOIN medicines m ON pi.medicine_id = m.id
                WHERE pi.prescription_id = ?
                """,
                (rx_data["id"],),
            ).fetchall()
            rx_data["items"] = [dict(i) for i in items]

            # Check if dispensed
            dispense = conn.execute(
                "SELECT * FROM dispense_records WHERE prescription_id = ?", (rx_data["id"],)
            ).fetchone()
            rx_data["dispense_record"] = dict(dispense) if dispense else None

            return rx_data
        finally:
            conn.close()

    def get_patient_prescription_history(self, patient_id: str) -> list[dict]:
        patient_id = patient_id.strip().upper()
        conn = self._get_connection()
        try:
            p = conn.execute("SELECT id FROM patients WHERE patient_id = ?", (patient_id,)).fetchone()
            if not p:
                raise ValueError(f"Patient '{patient_id}' not found.")

            rows = conn.execute(
                """
                SELECT rx.prescription_ref, rx.prescribed_date, rx.diagnosis, rx.status,
                       d.full_name as doctor_name, d.specialization,
                       count(pi.id) as item_count
                FROM prescriptions rx
                JOIN doctors d ON rx.doctor_id = d.id
                LEFT JOIN prescription_items pi ON rx.id = pi.prescription_id
                WHERE rx.patient_id = ?
                GROUP BY rx.id
                ORDER BY rx.prescribed_date DESC
                """,
                (p["id"],),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Dispensing Reports ====================

    def generate_daily_dispensing_report(self, target_date: str = None) -> dict:
        if target_date:
            try:
                datetime.strptime(target_date.strip(), "%Y-%m-%d")
            except ValueError:
                raise ValueError("Target date must be 'YYYY-MM-DD'.")
            date_filter = f"{target_date.strip()}%"
        else:
            date_filter = f"{datetime.now().strftime('%Y-%m-%d')}%"

        conn = self._get_connection()
        try:
            summary = conn.execute(
                """
                SELECT count(*) as total_dispenses,
                       coalesce(sum(total_amount), 0.0) as total_revenue
                FROM dispense_records
                WHERE dispensed_at LIKE ?
                """,
                (date_filter,),
            ).fetchone()

            items_dispensed = conn.execute(
                """
                SELECT m.medicine_id, m.name, m.dosage_form, m.strength,
                       sum(di.quantity_dispensed) as total_units,
                       sum(di.subtotal) as total_cost
                FROM dispense_items di
                JOIN dispense_records dr ON di.dispense_id = dr.id
                JOIN medicines m ON di.medicine_id = m.id
                WHERE dr.dispensed_at LIKE ?
                GROUP BY m.id
                ORDER BY total_units DESC
                """,
                (date_filter,),
            ).fetchall()

            low_stock = conn.execute(
                "SELECT medicine_id, name, stock_quantity, reorder_level FROM medicines WHERE stock_quantity <= reorder_level ORDER BY stock_quantity ASC"
            ).fetchall()

            return {
                "report_date": target_date or datetime.now().strftime("%Y-%m-%d"),
                "total_dispenses": summary["total_dispenses"],
                "total_revenue": summary["total_revenue"],
                "items_dispensed": [dict(i) for i in items_dispensed],
                "low_stock_alerts": [dict(m) for m in low_stock],
            }
        finally:
            conn.close()
