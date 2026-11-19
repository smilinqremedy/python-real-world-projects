"""
Business logic and accounting operations for Microfinance Loan Management System.
"""

from datetime import datetime, date
import calendar
import uuid
from typing import List, Dict, Any, Optional
from database import get_connection, init_db


def add_months(sourcedate: date, months: int) -> date:
    month = sourcedate.month - 1 + months
    year = sourcedate.year + month // 12
    month = month % 12 + 1
    day = min(sourcedate.day, calendar.monthrange(year, month)[1])
    return date(year, month, day)


class LoanService:
    def __init__(self, db_path: Optional[str] = None):
        self.db_path = db_path
        init_db(self.db_path)

    def register_borrower(self, code: str, name: str, phone: str,
                          email: str = "", monthly_income: float = 0.0) -> Dict[str, Any]:
        b_code = code.strip().upper()
        name = name.strip()
        phone = phone.strip()

        if not b_code or not name or not phone:
            raise ValueError("Borrower code, name, and phone cannot be empty.")
        if monthly_income < 0:
            raise ValueError("Monthly income cannot be negative.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    INSERT INTO borrowers (borrower_code, name, phone, email, monthly_income)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (b_code, name, phone, email.strip(), round(monthly_income, 2))
                )
                return {
                    "id": cursor.lastrowid,
                    "borrower_code": b_code,
                    "name": name,
                    "phone": phone,
                    "email": email.strip(),
                    "monthly_income": round(monthly_income, 2)
                }
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Borrower with code '{b_code}' already exists.")
            raise
        finally:
            conn.close()

    def create_loan_application(self, borrower_code: str, principal: float,
                                annual_interest_rate: float, period_months: int,
                                application_date_str: Optional[str] = None) -> Dict[str, Any]:
        if principal <= 0:
            raise ValueError("Principal loan amount must be greater than zero.")
        if annual_interest_rate < 0:
            raise ValueError("Interest rate cannot be negative.")
        if period_months <= 0:
            raise ValueError("Repayment period must be at least 1 month.")

        app_date = application_date_str.strip() if application_date_str else str(date.today())
        try:
            parsed_app_date = datetime.strptime(app_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Application date must be in YYYY-MM-DD format.")

        # Financial formulas
        total_interest = round(principal * (annual_interest_rate / 100.0) * (period_months / 12.0), 2)
        total_payable = round(principal + total_interest, 2)
        monthly_installment = round(total_payable / period_months, 2)

        loan_ref = f"LN-{uuid.uuid4().hex[:6].upper()}"

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, name FROM borrowers WHERE borrower_code = ?", (borrower_code.strip().upper(),))
                borrower = cursor.fetchone()
                if not borrower:
                    raise ValueError(f"Borrower '{borrower_code}' does not exist. Cannot approve loan for nonexistent borrower.")

                cursor.execute(
                    """
                    INSERT INTO loans (loan_reference, borrower_id, principal_amount, interest_rate_percent,
                                       repayment_period_months, total_interest, total_payable,
                                       monthly_installment, status, application_date)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Applied', ?)
                    """,
                    (loan_ref, borrower["id"], round(principal, 2), round(annual_interest_rate, 2),
                     period_months, total_interest, total_payable, monthly_installment, str(parsed_app_date))
                )
        finally:
            conn.close()

        return self.get_loan_details(loan_ref)

    def decide_loan_application(self, loan_reference: str, decision: str,
                                decision_date_str: Optional[str] = None) -> Dict[str, Any]:
        ref = loan_reference.strip().upper()
        dec = decision.strip().capitalize()
        if dec not in ["Approved", "Rejected"]:
            raise ValueError("Decision must be 'Approved' or 'Rejected'.")

        d_date = decision_date_str.strip() if decision_date_str else str(date.today())
        try:
            parsed_date = datetime.strptime(d_date, "%Y-%m-%d").date()
        except ValueError:
            raise ValueError("Decision date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id, status, repayment_period_months FROM loans WHERE loan_reference = ?", (ref,))
                loan = cursor.fetchone()
                if not loan:
                    raise ValueError(f"Loan reference '{ref}' not found.")
                if loan["status"] != "Applied":
                    raise ValueError(f"Cannot decide on loan '{ref}' because current status is '{loan['status']}'.")

                if dec == "Approved":
                    due_date = str(add_months(parsed_date, loan["repayment_period_months"]))
                    cursor.execute(
                        "UPDATE loans SET status = 'Active', approval_date = ?, due_date = ? WHERE id = ?",
                        (str(parsed_date), due_date, loan["id"])
                    )
                else:
                    cursor.execute("UPDATE loans SET status = 'Rejected' WHERE id = ?", (loan["id"],))
        finally:
            conn.close()

        return self.get_loan_details(ref)

    def calculate_repayment_schedule(self, loan_reference: str) -> List[Dict[str, Any]]:
        loan = self.get_loan_details(loan_reference)
        start_date = datetime.strptime(loan["approval_date"] or loan["application_date"], "%Y-%m-%d").date()
        months = loan["repayment_period_months"]
        installment = loan["monthly_installment"]

        schedule = []
        running_balance = loan["total_payable"]
        for i in range(1, months + 1):
            installment_due_date = str(add_months(start_date, i))
            paid_amount = min(installment, running_balance)
            running_balance = max(0.0, round(running_balance - paid_amount, 2))
            schedule.append({
                "installment_number": i,
                "due_date": installment_due_date,
                "installment_amount": installment,
                "remaining_balance_after": running_balance
            })
        return schedule

    def record_repayment(self, loan_reference: str, amount: float,
                         payment_date_str: Optional[str] = None, payment_method: str = "Bank Transfer",
                         notes: str = "") -> Dict[str, Any]:
        ref = loan_reference.strip().upper()
        if amount <= 0:
            raise ValueError("Repayment amount must be greater than zero.")

        p_date = payment_date_str.strip() if payment_date_str else str(date.today())
        try:
            datetime.strptime(p_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Payment date must be in YYYY-MM-DD format.")

        conn = get_connection(self.db_path)
        try:
            with conn:
                cursor = conn.cursor()
                cursor.execute(
                    """
                    SELECT id, status, total_payable, amount_repaid
                    FROM loans
                    WHERE loan_reference = ?
                    """,
                    (ref,)
                )
                loan = cursor.fetchone()
                if not loan:
                    raise ValueError(f"Loan reference '{ref}' not found.")
                if loan["status"] not in ["Active", "Defaulted"]:
                    raise ValueError(f"Cannot record repayment for loan with status '{loan['status']}'.")

                total_payable = float(loan["total_payable"])
                amount_repaid = float(loan["amount_repaid"])
                outstanding = round(total_payable - amount_repaid, 2)

                if outstanding <= 0:
                    raise ValueError(f"Loan '{ref}' is already fully repaid.")

                payment_ref = f"REP-{uuid.uuid4().hex[:6].upper()}"
                excess_ref = None
                excess_amount = 0.0

                if round(amount, 2) > outstanding:
                    # Explicit excess transaction handling requirement:
                    # "Do not allow repayments exceeding the outstanding balance without explicitly recording the excess as a separate transaction."
                    excess_amount = round(amount - outstanding, 2)
                    applied_amount = outstanding
                    new_repaid = total_payable
                    new_status = "Repaid"

                    excess_ref = f"EXC-{uuid.uuid4().hex[:6].upper()}"
                    cursor.execute(
                        """
                        INSERT INTO excess_payments (excess_reference, loan_id, excess_amount, payment_date, notes)
                        VALUES (?, ?, ?, ?, ?)
                        """,
                        (excess_ref, loan["id"], excess_amount, p_date, f"Excess on repayment {payment_ref}")
                    )
                else:
                    applied_amount = round(amount, 2)
                    new_repaid = round(amount_repaid + applied_amount, 2)
                    new_status = "Repaid" if new_repaid >= total_payable else loan["status"]

                cursor.execute(
                    """
                    INSERT INTO repayments (payment_reference, loan_id, amount, payment_date, payment_method, notes)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (payment_ref, loan["id"], applied_amount, p_date, payment_method.strip(), notes.strip())
                )

                cursor.execute(
                    "UPDATE loans SET amount_repaid = ?, status = ? WHERE id = ?",
                    (new_repaid, new_status, loan["id"])
                )
        finally:
            conn.close()

        res = self.get_loan_details(ref)
        res["latest_payment_ref"] = payment_ref
        res["excess_logged"] = excess_amount
        res["excess_reference"] = excess_ref
        return res

    def get_loan_details(self, loan_reference: str) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT l.*, b.borrower_code, b.name as borrower_name, b.phone as borrower_phone, b.monthly_income
                FROM loans l
                JOIN borrowers b ON l.borrower_id = b.id
                WHERE l.loan_reference = ?
                """,
                (loan_reference.strip().upper(),)
            )
            loan = cursor.fetchone()
            if not loan:
                raise ValueError(f"Loan reference '{loan_reference}' not found.")

            cursor.execute(
                """
                SELECT payment_reference, amount, payment_date, payment_method, notes
                FROM repayments
                WHERE loan_id = ?
                ORDER BY payment_date ASC, id ASC
                """,
                (loan["id"],)
            )
            repayments = [dict(r) for r in cursor.fetchall()]

            cursor.execute(
                """
                SELECT excess_reference, excess_amount, payment_date, notes
                FROM excess_payments
                WHERE loan_id = ?
                ORDER BY id ASC
                """,
                (loan["id"],)
            )
            excesses = [dict(r) for r in cursor.fetchall()]

            res = dict(loan)
            res["repayments"] = repayments
            res["excess_records"] = excesses
            res["outstanding_balance"] = max(0.0, round(float(loan["total_payable"]) - float(loan["amount_repaid"]), 2))
            return res
        finally:
            conn.close()

    def get_overdue_loans(self, as_of_date_str: Optional[str] = None) -> List[Dict[str, Any]]:
        target_date = datetime.strptime(as_of_date_str.strip(), "%Y-%m-%d").date() if as_of_date_str else date.today()
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute(
                """
                SELECT l.*, b.borrower_code, b.name as borrower_name, b.phone as borrower_phone
                FROM loans l
                JOIN borrowers b ON l.borrower_id = b.id
                WHERE l.status = 'Active' AND l.due_date IS NOT NULL AND l.due_date < ?
                ORDER BY l.due_date ASC
                """,
                (str(target_date),)
            )
            rows = cursor.fetchall()
            overdue = []
            for r in rows:
                d = dict(r)
                d["outstanding_balance"] = max(0.0, round(float(r["total_payable"]) - float(r["amount_repaid"]), 2))
                due_d = datetime.strptime(r["due_date"], "%Y-%m-%d").date()
                d["days_overdue"] = (target_date - due_d).days
                overdue.append(d)
            return overdue
        finally:
            conn.close()

    def list_loans(self, status_filter: Optional[str] = None) -> List[Dict[str, Any]]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            query = """
                SELECT l.*, b.borrower_code, b.name as borrower_name
                FROM loans l
                JOIN borrowers b ON l.borrower_id = b.id
            """
            params = []
            if status_filter:
                query += " WHERE l.status = ?"
                params.append(status_filter.capitalize())
            query += " ORDER BY l.id DESC"
            cursor.execute(query, params)
            results = []
            for r in cursor.fetchall():
                d = dict(r)
                d["outstanding_balance"] = max(0.0, round(float(r["total_payable"]) - float(r["amount_repaid"]), 2))
                results.append(d)
            return results
        finally:
            conn.close()

    def generate_loan_performance_report(self) -> Dict[str, Any]:
        conn = get_connection(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM loans")
            total_applications = cursor.fetchone()[0]

            cursor.execute(
                """
                SELECT COUNT(*), COALESCE(SUM(principal_amount), 0),
                       COALESCE(SUM(total_interest), 0),
                       COALESCE(SUM(total_payable), 0),
                       COALESCE(SUM(amount_repaid), 0)
                FROM loans
                WHERE status IN ('Active', 'Repaid', 'Defaulted')
                """
            )
            stats = cursor.fetchone()
            disbursed_count = stats[0]
            total_principal = float(stats[1])
            total_interest = float(stats[2])
            total_expected = float(stats[3])
            total_recovered = float(stats[4])

            cursor.execute("SELECT COUNT(*) FROM loans WHERE status = 'Repaid'")
            fully_repaid_count = cursor.fetchone()[0]

            today_str = str(date.today())
            cursor.execute("SELECT COUNT(*) FROM loans WHERE status = 'Active' AND due_date < ?", (today_str,))
            overdue_count = cursor.fetchone()[0]

            recovery_rate = (total_recovered / total_expected * 100) if total_expected > 0 else 0.0

            return {
                "total_applications": total_applications,
                "disbursed_loans_count": disbursed_count,
                "fully_repaid_loans": fully_repaid_count,
                "overdue_loans_count": overdue_count,
                "total_principal_disbursed": round(total_principal, 2),
                "total_interest_expected": round(total_interest, 2),
                "total_expected_recovery": round(total_expected, 2),
                "total_capital_recovered": round(total_recovered, 2),
                "outstanding_portfolio_balance": max(0.0, round(total_expected - total_recovered, 2)),
                "recovery_rate_percent": round(recovery_rate, 1)
            }
        finally:
            conn.close()
