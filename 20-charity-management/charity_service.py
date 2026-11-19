"""
Service layer and financial accounting logic for Donation and Charity Management System.
"""

from datetime import datetime, date
import uuid
from typing import List, Dict, Any, Optional
from database import get_connection, init_db


class CharityService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def register_donor(self, code: str, name: str, email: str, phone: str,
                       donor_type: str = "Individual") -> Dict[str, Any]:
        d_code = code.strip().upper()
        name = name.strip()
        email = email.strip().lower()
        phone = phone.strip()
        dtype = donor_type.strip().capitalize()

        if not d_code or not name or not email or not phone:
            raise ValueError("Donor code, name, email, and phone cannot be empty.")
        if dtype not in ["Individual", "Corporate", "Foundation"]:
            raise ValueError("Donor type must be 'Individual', 'Corporate', or 'Foundation'.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO donors (donor_code, name, email, phone, donor_type) VALUES (?, ?, ?, ?, ?)",
                    (d_code, name, email, phone, dtype)
                )
                return {
                    "id": cursor.lastrowid,
                    "donor_code": d_code,
                    "name": name,
                    "email": email,
                    "phone": phone,
                    "donor_type": dtype
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Donor with code '{d_code}' already exists.")
            raise
        finally:
            conn.close()

    def create_campaign(self, code: str, name: str, description: str,
                        target_amount: float, start_date_str: str, end_date_str: str) -> Dict[str, Any]:
        c_code = code.strip().upper()
        name = name.strip()
        desc = description.strip()

        if not c_code or not name or not desc:
            raise ValueError("Campaign code, name, and description cannot be empty.")
        if target_amount <= 0:
            raise ValueError("Campaign target amount must be greater than zero.")

        try:
            d_start = datetime.strptime(start_date_str.strip(), "%Y-%m-%d").date()
            d_end = datetime.strptime(end_date_str.strip(), "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Campaign dates must be in YYYY-MM-DD format.")

        if d_start > d_end:
            raise ValueError("Campaign start date cannot be later than end date.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO campaigns (campaign_code, name, description, target_amount, start_date, end_date, status)
                    VALUES (?, ?, ?, ?, ?, ?, 'Active')
                    """,
                    (c_code, name, desc, round(target_amount, 2), str(d_start), str(d_end))
                )
                return {
                    "id": cursor.lastrowid,
                    "campaign_code": c_code,
                    "name": name,
                    "description": desc,
                    "target_amount": round(target_amount, 2),
                    "start_date": str(d_start),
                    "end_date": str(d_end),
                    "status": "Active"
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Campaign with code '{c_code}' already exists.")
            raise
        finally:
            conn.close()

    def record_donation(self, donor_code: str, campaign_code: str, amount: float,
                        payment_method: str = "Bank Transfer", donation_date_str: Optional[str] = None,
                        notes: str = "") -> Dict[str, Any]:
        if amount <= 0:
            raise ValueError("Donation amount must be greater than zero.")

        d_date = donation_date_str.strip() if donation_date_str else str(date.today())
        try:
            datetime.strptime(d_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Donation date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM donors WHERE donor_code = ?", (donor_code.strip().upper(),))
                donor = cursor.fetchone()
                if not donor:
                    raise ValueError(f"Donor '{donor_code}' not found.")

                cursor.execute("SELECT id, name, status FROM campaigns WHERE campaign_code = ?", (campaign_code.strip().upper(),))
                camp = cursor.fetchone()
                if not camp:
                    raise ValueError(f"Campaign '{campaign_code}' not found.")
                if camp["status"] != "Active":
                    raise ValueError(f"Cannot accept donations for campaign '{camp['name']}' (Status is {camp['status']}).")

                receipt_ref = f"DON-{uuid.uuid4().hex[:6].upper()}"
                cursor.execute(
                    """
                    INSERT INTO donations (receipt_reference, donor_id, campaign_id, amount, donation_date, payment_method, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (receipt_ref, donor["id"], camp["id"], round(amount, 2), d_date, payment_method.strip(), notes.strip())
                )
                return {
                    "receipt_reference": receipt_ref,
                    "donor_name": donor["name"],
                    "campaign_name": camp["name"],
                    "amount": round(amount, 2),
                    "donation_date": d_date,
                    "payment_method": payment_method.strip()
                }
        finally:
            conn.close()

    def get_campaign_balance(self, campaign_code: str) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT id, campaign_code, name, target_amount, status FROM campaigns WHERE campaign_code = ?", (campaign_code.strip().upper(),))
            camp = cursor.fetchone()
            if not camp:
                raise ValueError(f"Campaign '{campaign_code}' not found.")

            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM donations WHERE campaign_id = ?", (camp["id"],))
            total_raised = float(cursor.fetchone()[0])

            cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM disbursements WHERE campaign_id = ?", (camp["id"],))
            total_disbursed = float(cursor.fetchone()[0])

            available_balance = round(total_raised - total_disbursed, 2)
            progress_pct = (total_raised / camp["target_amount"] * 100) if camp["target_amount"] > 0 else 0.0

            return {
                "campaign_code": camp["campaign_code"],
                "name": camp["name"],
                "target_amount": round(camp["target_amount"], 2),
                "total_raised": round(total_raised, 2),
                "total_disbursed": round(total_disbursed, 2),
                "available_balance": available_balance,
                "progress_percentage": round(progress_pct, 1),
                "status": camp["status"]
            }
        finally:
            conn.close()

    def record_disbursement(self, campaign_code: str, recipient: str, purpose: str,
                            amount: float, disbursement_date_str: Optional[str] = None,
                            notes: str = "") -> Dict[str, Any]:
        if amount <= 0:
            raise ValueError("Disbursement amount must be greater than zero.")
        recip = recipient.strip()
        purp = purpose.strip()
        if not recip or not purp:
            raise ValueError("Recipient and purpose cannot be empty.")

        d_date = disbursement_date_str.strip() if disbursement_date_str else str(date.today())
        try:
            datetime.strptime(d_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Disbursement date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM campaigns WHERE campaign_code = ?", (campaign_code.strip().upper(),))
                camp = cursor.fetchone()
                if not camp:
                    raise ValueError(f"Campaign '{campaign_code}' not found.")

                cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM donations WHERE campaign_id = ?", (camp["id"],))
                total_raised = float(cursor.fetchone()[0])

                cursor.execute("SELECT COALESCE(SUM(amount), 0) FROM disbursements WHERE campaign_id = ?", (camp["id"],))
                total_disbursed = float(cursor.fetchone()[0])

                current_balance = round(total_raised - total_disbursed, 2)

                # Strict balance gate: Fund distributions cannot exceed available campaign balance
                if round(amount, 2) > current_balance:
                    raise ValueError(f"Disbursement rejected! Amount (${amount:.2f}) exceeds available campaign balance (${current_balance:.2f}).")

                disb_ref = f"DIS-{uuid.uuid4().hex[:6].upper()}"
                cursor.execute(
                    """
                    INSERT INTO disbursements (disbursement_reference, campaign_id, recipient, purpose, amount, disbursement_date, approval_notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (disb_ref, camp["id"], recip, purp, round(amount, 2), d_date, notes.strip())
                )
                remaining = round(current_balance - amount, 2)
                return {
                    "disbursement_reference": disb_ref,
                    "campaign_name": camp["name"],
                    "recipient": recip,
                    "purpose": purp,
                    "amount": round(amount, 2),
                    "disbursement_date": d_date,
                    "remaining_balance": remaining
                }
        finally:
            conn.close()

    def list_campaigns(self) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT campaign_code FROM campaigns ORDER BY id ASC")
            codes = [r["campaign_code"] for r in cursor.fetchall()]
        finally:
            conn.close()

        return [self.get_campaign_balance(c) for c in codes]

    def generate_financial_report(self) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM donations")
            don_count, total_donations = cursor.fetchone()

            cursor.execute("SELECT COUNT(*), COALESCE(SUM(amount), 0) FROM disbursements")
            disb_count, total_disbursed = cursor.fetchone()

            net_treasury = round(float(total_donations) - float(total_disbursed), 2)

            cursor.execute(
                """
                SELECT d.name as donor_name, d.donor_type, COUNT(dn.id) as donations_count, SUM(dn.amount) as total_contributed
                FROM donors d
                JOIN donations dn ON d.id = dn.donor_id
                GROUP BY d.id
                ORDER BY total_contributed DESC
                LIMIT 5
                """
            )
            top_donors = [dict(r) for r in cursor.fetchall()]
        finally:
            conn.close()

        campaigns = self.list_campaigns()

        return {
            "total_donations_count": don_count,
            "total_funds_raised": round(float(total_donations), 2),
            "total_disbursements_count": disb_count,
            "total_funds_distributed": round(float(total_disbursed), 2),
            "net_treasury_balance": net_treasury,
            "campaign_summaries": campaigns,
            "top_donors": top_donors
        }
