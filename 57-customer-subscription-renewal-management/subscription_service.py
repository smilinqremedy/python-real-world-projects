"""
Service layer for Customer Subscription & Renewal Management System.
"""
from datetime import datetime, date, timedelta
import secrets
from database import get_connection, init_db


class InvalidRenewalError(Exception):
    """Raised when a subscription renewal violates business rules."""
    pass


class SubscriptionService:
    def __init__(self, db_path=None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    # ==================== Customer Registration ====================

    def register_customer(self, customer_id: str, full_name: str, email: str, phone: str, company: str = None) -> int:
        customer_id = customer_id.strip().upper()
        full_name = full_name.strip()
        email = email.strip().lower()
        phone = phone.strip()

        if not customer_id or not full_name or not email:
            raise ValueError("Customer ID, full name, and email are required.")

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO customers (customer_id, full_name, email, phone, company)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (customer_id, full_name, email, phone, company),
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Customer ID '{customer_id}' or email already exists.")
            raise
        finally:
            conn.close()

    def list_customers(self) -> list[dict]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM customers ORDER BY full_name ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Subscription Plans ====================

    def create_plan(self, plan_code: str, name: str, billing_cycle: str, price: float, description: str = None) -> int:
        plan_code = plan_code.strip().upper()
        name = name.strip()
        billing_cycle = billing_cycle.strip().capitalize()
        price = float(price)

        if price <= 0:
            raise ValueError("Plan price must be greater than zero.")

        valid_cycles = ("Monthly", "Quarterly", "Yearly")
        if billing_cycle not in valid_cycles:
            raise ValueError(f"Billing cycle must be one of: {', '.join(valid_cycles)}")

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO subscription_plans (plan_code, name, billing_cycle, price, description)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (plan_code, name, billing_cycle, price, description),
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Plan code '{plan_code}' already exists.")
            raise
        finally:
            conn.close()

    def list_plans(self) -> list[dict]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM subscription_plans WHERE is_active = 1 ORDER BY price ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Subscription Management ====================

    @staticmethod
    def _calculate_expiry(start_date: date, billing_cycle: str) -> date:
        if billing_cycle == "Monthly":
            return start_date + timedelta(days=30)
        elif billing_cycle == "Quarterly":
            return start_date + timedelta(days=90)
        elif billing_cycle == "Yearly":
            return start_date + timedelta(days=365)
        return start_date + timedelta(days=30)

    def create_subscription(self, customer_id: str, plan_code: str, start_date_str: str = None,
                            auto_renew: bool = True) -> str:
        customer_id = customer_id.strip().upper()
        plan_code = plan_code.strip().upper()

        if start_date_str:
            try:
                s_date = datetime.strptime(start_date_str.strip(), "%Y-%m-%d").date()
            except ValueError:
                raise ValueError("Start date must be 'YYYY-MM-DD'.")
        else:
            s_date = date.today()

        conn = self._get_connection()
        try:
            with conn:
                cust = conn.execute("SELECT id FROM customers WHERE customer_id = ?", (customer_id,)).fetchone()
                if not cust:
                    raise ValueError(f"Customer '{customer_id}' not found.")

                plan = conn.execute(
                    "SELECT id, billing_cycle, price FROM subscription_plans WHERE plan_code = ? AND is_active = 1",
                    (plan_code,),
                ).fetchone()
                if not plan:
                    raise ValueError(f"Active plan '{plan_code}' not found.")

                expiry_date = self._calculate_expiry(s_date, plan["billing_cycle"])

                today_str = datetime.now().strftime("%Y%m%d")
                seq = secrets.randbelow(9000) + 1000
                sub_ref = f"SUB-{today_str}-{seq}"

                cursor = conn.execute(
                    """
                    INSERT INTO subscriptions (
                        subscription_ref, customer_id, plan_id, start_date,
                        expiry_date, status, auto_renew
                    ) VALUES (?, ?, ?, ?, ?, 'Active', ?)
                    """,
                    (sub_ref, cust["id"], plan["id"], s_date.strftime("%Y-%m-%d"),
                     expiry_date.strftime("%Y-%m-%d"), 1 if auto_renew else 0),
                )
                sub_id = cursor.lastrowid

                # Record initial payment
                pay_ref = f"PAY-{today_str}-{secrets.randbelow(9000)+1000}"
                conn.execute(
                    """
                    INSERT INTO subscription_payments (payment_ref, subscription_id, amount, payment_method, payment_date, notes)
                    VALUES (?, ?, ?, 'Credit Card', ?, 'Initial subscription payment')
                    """,
                    (pay_ref, sub_id, plan["price"], s_date.strftime("%Y-%m-%d")),
                )

                return sub_ref
        finally:
            conn.close()

    def renew_subscription(self, subscription_ref: str, amount_paid: float,
                           payment_method: str = "Credit Card") -> dict:
        """
        Renew an active, grace period, or expired subscription.
        CRITICAL BUSINESS RULE: Prevents invalid renewals (e.g. cancelled subscription, underpayment).
        """
        subscription_ref = subscription_ref.strip().upper()
        amount_paid = float(amount_paid)

        conn = self._get_connection()
        try:
            with conn:
                sub = conn.execute(
                    """
                    SELECT s.*, p.billing_cycle, p.price as plan_price, p.name as plan_name
                    FROM subscriptions s
                    JOIN subscription_plans p ON s.plan_id = p.id
                    WHERE s.subscription_ref = ?
                    """,
                    (subscription_ref,),
                ).fetchone()
                if not sub:
                    raise ValueError(f"Subscription '{subscription_ref}' not found.")

                if sub["status"] == "Cancelled":
                    raise InvalidRenewalError(
                        f"Cannot renew subscription '{subscription_ref}': The subscription is Cancelled. Customer must initiate a new subscription."
                    )

                if amount_paid < sub["plan_price"]:
                    raise InvalidRenewalError(
                        f"Underpayment rejected: Amount paid (₦{amount_paid:,.2f}) is less than plan renewal cost (₦{sub['plan_price']:,.2f})."
                    )

                current_expiry = datetime.strptime(sub["expiry_date"], "%Y-%m-%d").date()
                today = date.today()

                # If current expiry is in the future, extend from current expiry date.
                # If current expiry is in the past, extend from today.
                base_date = current_expiry if current_expiry > today else today
                new_expiry = self._calculate_expiry(base_date, sub["billing_cycle"])

                # Update subscription status to Active and set new expiry
                conn.execute(
                    """
                    UPDATE subscriptions
                    SET expiry_date = ?, status = 'Active', updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (new_expiry.strftime("%Y-%m-%d"), sub["id"]),
                )

                # Record payment
                today_str = datetime.now().strftime("%Y%m%d")
                pay_ref = f"PAY-{today_str}-{secrets.randbelow(9000)+1000}"
                conn.execute(
                    """
                    INSERT INTO subscription_payments (payment_ref, subscription_id, amount, payment_method, payment_date, notes)
                    VALUES (?, ?, ?, ?, ?, 'Subscription renewal payment')
                    """,
                    (pay_ref, sub["id"], amount_paid, payment_method, today.strftime("%Y-%m-%d")),
                )

                # Record renewal log
                conn.execute(
                    """
                    INSERT INTO renewal_logs (subscription_id, previous_expiry, new_expiry, amount_paid)
                    VALUES (?, ?, ?, ?)
                    """,
                    (sub["id"], sub["expiry_date"], new_expiry.strftime("%Y-%m-%d"), amount_paid),
                )

                return {
                    "subscription_ref": subscription_ref,
                    "previous_expiry": sub["expiry_date"],
                    "new_expiry": new_expiry.strftime("%Y-%m-%d"),
                    "amount_paid": amount_paid,
                    "payment_ref": pay_ref,
                    "status": "Active",
                }
        finally:
            conn.close()

    def cancel_subscription(self, subscription_ref: str, reason: str = None) -> bool:
        subscription_ref = subscription_ref.strip().upper()
        conn = self._get_connection()
        try:
            with conn:
                sub = conn.execute("SELECT id, status FROM subscriptions WHERE subscription_ref = ?", (subscription_ref,)).fetchone()
                if not sub:
                    raise ValueError(f"Subscription '{subscription_ref}' not found.")
                if sub["status"] == "Cancelled":
                    raise ValueError("Subscription is already cancelled.")

                conn.execute(
                    """
                    UPDATE subscriptions
                    SET status = 'Cancelled', cancellation_reason = ?, updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (reason or "Customer requested cancellation", sub["id"]),
                )
                return True
        finally:
            conn.close()

    def check_and_update_expirations(self, reference_date: date = None) -> dict:
        """
        Evaluate all active/grace period subscriptions against the reference date.
        If past expiry but <= 7 days: set to 'Grace Period'.
        If past expiry by > 7 days: set to 'Suspended'.
        """
        ref_d = reference_date or date.today()
        ref_str = ref_d.strftime("%Y-%m-%d")
        grace_threshold_str = (ref_d - timedelta(days=7)).strftime("%Y-%m-%d")

        conn = self._get_connection()
        try:
            with conn:
                # 1. Past 7 days overdue -> Suspend
                suspended = conn.execute(
                    """
                    UPDATE subscriptions
                    SET status = 'Suspended', updated_at = CURRENT_TIMESTAMP
                    WHERE status IN ('Active', 'Grace Period') AND expiry_date < ?
                    """,
                    (grace_threshold_str,),
                ).rowcount

                # 2. Past expiry but within 7 days -> Grace Period
                grace = conn.execute(
                    """
                    UPDATE subscriptions
                    SET status = 'Grace Period', updated_at = CURRENT_TIMESTAMP
                    WHERE status = 'Active' AND expiry_date < ?
                    """,
                    (ref_str,),
                ).rowcount

                return {
                    "reference_date": ref_str,
                    "newly_suspended_count": suspended,
                    "newly_grace_period_count": grace,
                }
        finally:
            conn.close()

    def get_expiring_soon(self, days_threshold: int = 7, reference_date: date = None) -> list[dict]:
        """Identify subscriptions expiring within the next N days."""
        ref_d = reference_date or date.today()
        ref_str = ref_d.strftime("%Y-%m-%d")
        target_str = (ref_d + timedelta(days=days_threshold)).strftime("%Y-%m-%d")

        conn = self._get_connection()
        try:
            rows = conn.execute(
                """
                SELECT s.*, c.full_name as customer_name, c.email as customer_email,
                       p.name as plan_name, p.price as plan_price, p.billing_cycle
                FROM subscriptions s
                JOIN customers c ON s.customer_id = c.id
                JOIN subscription_plans p ON s.plan_id = p.id
                WHERE s.status IN ('Active', 'Grace Period')
                  AND s.expiry_date >= ? AND s.expiry_date <= ?
                ORDER BY s.expiry_date ASC
                """,
                (ref_str, target_str),
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_subscription_details(self, subscription_ref: str) -> dict:
        subscription_ref = subscription_ref.strip().upper()
        conn = self._get_connection()
        try:
            row = conn.execute(
                """
                SELECT s.*, c.customer_id, c.full_name as customer_name, c.email as customer_email,
                       c.phone as customer_phone, c.company, p.plan_code, p.name as plan_name,
                       p.billing_cycle, p.price as plan_price
                FROM subscriptions s
                JOIN customers c ON s.customer_id = c.id
                JOIN subscription_plans p ON s.plan_id = p.id
                WHERE s.subscription_ref = ?
                """,
                (subscription_ref,),
            ).fetchone()
            if not row:
                raise ValueError(f"Subscription '{subscription_ref}' not found.")

            data = dict(row)
            payments = conn.execute(
                "SELECT * FROM subscription_payments WHERE subscription_id = ? ORDER BY payment_date DESC",
                (data["id"],),
            ).fetchall()
            data["payments"] = [dict(p) for p in payments]

            renewals = conn.execute(
                "SELECT * FROM renewal_logs WHERE subscription_id = ? ORDER BY renewed_at DESC",
                (data["id"],),
            ).fetchall()
            data["renewals"] = [dict(r) for r in renewals]
            return data
        finally:
            conn.close()

    # ==================== Reporting & Metrics ====================

    def generate_revenue_report(self) -> dict:
        """
        Calculate Monthly Recurring Revenue (MRR), Annual Recurring Revenue (ARR),
        subscriber counts, and total cashflow collected.
        """
        conn = self._get_connection()
        try:
            total_customers = conn.execute("SELECT count(*) FROM customers").fetchone()[0]
            status_counts = conn.execute("SELECT status, count(*) as count FROM subscriptions GROUP BY status").fetchall()
            status_dict = {r["status"]: r["count"] for r in status_counts}

            # MRR Calculation for all Active or Grace Period subscriptions
            active_subs = conn.execute(
                """
                SELECT p.billing_cycle, p.price
                FROM subscriptions s
                JOIN subscription_plans p ON s.plan_id = p.id
                WHERE s.status IN ('Active', 'Grace Period')
                """
            ).fetchall()

            mrr = 0.0
            for sub in active_subs:
                price = sub["price"]
                cycle = sub["billing_cycle"]
                if cycle == "Monthly":
                    mrr += price
                elif cycle == "Quarterly":
                    mrr += price / 3.0
                elif cycle == "Yearly":
                    mrr += price / 12.0

            mrr = round(mrr, 2)
            arr = round(mrr * 12.0, 2)

            total_collected = conn.execute("SELECT coalesce(sum(amount), 0.0) FROM subscription_payments").fetchone()[0]

            return {
                "total_customers": total_customers,
                "active_subscriptions": status_dict.get("Active", 0),
                "grace_period_subscriptions": status_dict.get("Grace Period", 0),
                "suspended_subscriptions": status_dict.get("Suspended", 0),
                "cancelled_subscriptions": status_dict.get("Cancelled", 0),
                "mrr": mrr,
                "arr": arr,
                "total_payments_collected": round(total_collected, 2),
            }
        finally:
            conn.close()
