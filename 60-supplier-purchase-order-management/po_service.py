"""
Business logic and service layer for Supplier Purchase Order Management.
Manages supplier accounts, product inventory, purchase orders, partial deliveries,
atomic inventory increments, and payments.
"""
from datetime import datetime, date
import secrets
from typing import Optional, Dict, List, Any
from database import get_connection, init_db


class POWorkflowError(Exception):
    """Raised when a purchase order transition violates business rules."""
    pass


class POService:
    def __init__(self, db_path=None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    # ==================== Supplier Management ====================

    def register_supplier(self, supplier_code: str, company_name: str, contact_name: str,
                          email: str, phone: str, address: Optional[str] = None) -> int:
        supplier_code = supplier_code.strip().upper()
        company_name = company_name.strip()
        contact_name = contact_name.strip()
        email = email.strip().lower()
        phone = phone.strip()

        if not supplier_code or not company_name:
            raise ValueError("Supplier code and company name are required.")

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO suppliers (supplier_code, company_name, contact_name, email, phone, address)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (supplier_code, company_name, contact_name, email, phone, address)
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                raise ValueError(f"Supplier code '{supplier_code}' already exists.")
            raise
        finally:
            conn.close()

    def list_suppliers(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM suppliers ORDER BY company_name ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Product Catalog & Inventory ====================

    def add_product(self, sku: str, name: str, unit_cost: float, initial_stock: int = 0,
                    reorder_level: int = 10, category: str = "General") -> int:
        sku = sku.strip().upper()
        name = name.strip()
        unit_cost = float(unit_cost)
        initial_stock = int(initial_stock)
        reorder_level = int(reorder_level)

        if not sku or not name:
            raise ValueError("Product SKU and name are required.")
        if unit_cost < 0:
            raise ValueError("Unit cost cannot be negative.")
        if initial_stock < 0 or reorder_level < 0:
            raise ValueError("Stock counts cannot be negative.")

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO products (sku, name, category, unit_cost, stock_quantity, reorder_level)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (sku, name, category, unit_cost, initial_stock, reorder_level)
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint" in str(e):
                raise ValueError(f"Product SKU '{sku}' already exists.")
            raise
        finally:
            conn.close()

    def list_products(self) -> List[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM products ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def get_low_stock_products(self) -> List[Dict[str, Any]]:
        """Identify items where stock quantity is at or below reorder level."""
        conn = self._get_connection()
        try:
            rows = conn.execute(
                """
                SELECT * FROM products
                WHERE stock_quantity <= reorder_level
                ORDER BY stock_quantity ASC
                """
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Purchase Order Lifecycle ====================

    def create_purchase_order(self, supplier_code: str, order_date: Optional[str] = None,
                              expected_date: Optional[str] = None, notes: Optional[str] = None) -> str:
        supplier_code = supplier_code.strip().upper()
        conn = self._get_connection()
        try:
            with conn:
                supplier = conn.execute(
                    "SELECT id FROM suppliers WHERE supplier_code = ?", (supplier_code,)
                ).fetchone()
                if not supplier:
                    raise ValueError(f"Supplier '{supplier_code}' not found.")

                o_date = order_date or date.today().strftime("%Y-%m-%d")
                today_tag = datetime.now().strftime("%Y%m%d")
                po_num = f"PO-{today_tag}-{secrets.randbelow(9000)+1000}"

                conn.execute(
                    """
                    INSERT INTO purchase_orders (po_number, supplier_id, order_date, expected_date, status, notes)
                    VALUES (?, ?, ?, ?, 'Draft', ?)
                    """,
                    (po_num, supplier["id"], o_date, expected_date, notes)
                )
                return po_num
        finally:
            conn.close()

    def add_po_item(self, po_number: str, sku: str, quantity: int, unit_cost: Optional[float] = None) -> int:
        """
        Add a line item to a PO. STRICT RULE: Allowed only when PO is in Draft status.
        """
        po_number = po_number.strip().upper()
        sku = sku.strip().upper()
        quantity = int(quantity)
        if quantity <= 0:
            raise ValueError("Quantity ordered must be greater than zero.")

        conn = self._get_connection()
        try:
            with conn:
                po = conn.execute("SELECT id, status FROM purchase_orders WHERE po_number = ?", (po_number,)).fetchone()
                if not po:
                    raise ValueError(f"Purchase Order '{po_number}' not found.")
                if po["status"] != "Draft":
                    raise POWorkflowError(f"Cannot modify PO items: PO '{po_number}' is in '{po["status"]}' status (Draft only).")

                prod = conn.execute("SELECT id, unit_cost FROM products WHERE sku = ?", (sku,)).fetchone()
                if not prod:
                    raise ValueError(f"Product '{sku}' not found.")

                cost = float(unit_cost) if unit_cost is not None else float(prod["unit_cost"])
                subtotal = round(quantity * cost, 2)

                cursor = conn.execute(
                    """
                    INSERT INTO po_items (po_id, product_id, quantity_ordered, unit_cost, quantity_received, subtotal)
                    VALUES (?, ?, ?, ?, 0, ?)
                    """,
                    (po["id"], prod["id"], quantity, cost, subtotal)
                )

                # Update PO total_amount
                conn.execute(
                    """
                    UPDATE purchase_orders
                    SET total_amount = (SELECT coalesce(sum(subtotal), 0) FROM po_items WHERE po_id = ?),
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (po["id"], po["id"])
                )
                return cursor.lastrowid
        finally:
            conn.close()

    def approve_purchase_order(self, po_number: str) -> bool:
        """Transitions PO from Draft to Approved."""
        po_number = po_number.strip().upper()
        conn = self._get_connection()
        try:
            with conn:
                po = conn.execute("SELECT id, status FROM purchase_orders WHERE po_number = ?", (po_number,)).fetchone()
                if not po:
                    raise ValueError(f"Purchase Order '{po_number}' not found.")
                if po["status"] != "Draft":
                    raise POWorkflowError(f"Cannot approve PO: PO is already '{po['status']}'.")

                # Verify PO has at least 1 item
                item_count = conn.execute("SELECT count(*) FROM po_items WHERE po_id = ?", (po["id"],)).fetchone()[0]
                if item_count == 0:
                    raise POWorkflowError(f"Cannot approve empty PO. Add at least one item first.")

                conn.execute(
                    "UPDATE purchase_orders SET status = 'Approved', updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (po["id"],)
                )
                return True
        finally:
            conn.close()

    def cancel_purchase_order(self, po_number: str, reason: Optional[str] = None) -> bool:
        """Cancel an order unless already Completed."""
        po_number = po_number.strip().upper()
        conn = self._get_connection()
        try:
            with conn:
                po = conn.execute("SELECT id, status FROM purchase_orders WHERE po_number = ?", (po_number,)).fetchone()
                if not po:
                    raise ValueError(f"Purchase Order '{po_number}' not found.")
                if po["status"] == "Completed":
                    raise POWorkflowError("Cannot cancel an order that has already been Completed.")

                conn.execute(
                    """
                    UPDATE purchase_orders
                    SET status = 'Cancelled', notes = coalesce(notes, '') || ' [Cancelled: ' || ? || ']',
                        updated_at = CURRENT_TIMESTAMP
                    WHERE id = ?
                    """,
                    (reason or "Cancelled by user", po["id"])
                )
                return True
        finally:
            conn.close()

    # ==================== Physical Delivery & Inventory Receipt ====================

    def receive_delivery(self, po_number: str, sku: str, quantity_delivered: int,
                         received_by: str, delivery_date: Optional[str] = None,
                         notes: Optional[str] = None) -> Dict[str, Any]:
        """
        Record physical arrival of goods from a supplier.
        TRANSACTION CRITICAL:
          1. Enforces PO status (Approved or Partially Delivered).
          2. Updates item received quantity.
          3. Atomically increases warehouse product stock quantity.
          4. Logs delivery record.
          5. Checks if PO is fully fulfilled -> Updates PO to 'Completed' or 'Partially Delivered'.
        """
        po_number = po_number.strip().upper()
        sku = sku.strip().upper()
        quantity_delivered = int(quantity_delivered)
        received_by = received_by.strip()
        d_date = delivery_date or date.today().strftime("%Y-%m-%d")

        if quantity_delivered <= 0:
            raise ValueError("Delivered quantity must be greater than zero.")
        if not received_by:
            raise ValueError("Receiving personnel name is required.")

        conn = self._get_connection()
        try:
            with conn:  # Begins atomic database transaction
                # 1. Validate PO status
                po = conn.execute("SELECT id, status FROM purchase_orders WHERE po_number = ?", (po_number,)).fetchone()
                if not po:
                    raise ValueError(f"Purchase Order '{po_number}' not found.")
                if po["status"] not in ("Approved", "Partially Delivered"):
                    raise POWorkflowError(
                        f"Cannot receive delivery: PO '{po_number}' status is '{po['status']}'. Must be Approved or Partially Delivered."
                    )

                # 2. Find matching PO item & product
                prod = conn.execute("SELECT id, name, stock_quantity FROM products WHERE sku = ?", (sku,)).fetchone()
                if not prod:
                    raise ValueError(f"Product '{sku}' not found.")

                item = conn.execute(
                    "SELECT id, quantity_ordered, quantity_received FROM po_items WHERE po_id = ? AND product_id = ?",
                    (po["id"], prod["id"])
                ).fetchone()
                if not item:
                    raise ValueError(f"Product '{sku}' is not on Purchase Order '{po_number}'.")

                remaining_expected = item["quantity_ordered"] - item["quantity_received"]
                if quantity_delivered > remaining_expected:
                    raise POWorkflowError(
                        f"Over-delivery rejected: Received {quantity_delivered} but only {remaining_expected} remaining on this PO item."
                    )

                # 3. Update PO Item received count
                new_received = item["quantity_received"] + quantity_delivered
                conn.execute(
                    "UPDATE po_items SET quantity_received = ? WHERE id = ?",
                    (new_received, item["id"])
                )

                # 4. Atomically increment warehouse stock
                conn.execute(
                    "UPDATE products SET stock_quantity = stock_quantity + ? WHERE id = ?",
                    (quantity_delivered, prod["id"])
                )

                # 5. Insert delivery log
                conn.execute(
                    """
                    INSERT INTO delivery_logs (po_item_id, quantity_delivered, delivery_date, received_by, notes)
                    VALUES (?, ?, ?, ?, ?)
                    """,
                    (item["id"], quantity_delivered, d_date, received_by, notes)
                )

                # 6. Evaluate all items on PO to determine new status
                all_items = conn.execute(
                    "SELECT quantity_ordered, quantity_received FROM po_items WHERE po_id = ?", (po["id"],)
                ).fetchall()

                all_completed = all(i["quantity_received"] >= i["quantity_ordered"] for i in all_items)
                new_status = "Completed" if all_completed else "Partially Delivered"

                conn.execute(
                    "UPDATE purchase_orders SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                    (new_status, po["id"])
                )

                # Fetch updated stock count
                updated_stock = conn.execute("SELECT stock_quantity FROM products WHERE id = ?", (prod["id"],)).fetchone()[0]

                return {
                    "po_number": po_number,
                    "sku": sku,
                    "product_name": prod["name"],
                    "quantity_delivered": quantity_delivered,
                    "total_received_for_item": new_received,
                    "ordered_quantity": item["quantity_ordered"],
                    "updated_warehouse_stock": updated_stock,
                    "po_status": new_status,
                }
        finally:
            conn.close()

    # ==================== Supplier Payments & Balance ====================

    def record_payment(self, supplier_code: str, amount: float, payment_method: str = "Bank Transfer",
                       po_number: Optional[str] = None, notes: Optional[str] = None) -> Dict[str, Any]:
        supplier_code = supplier_code.strip().upper()
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Payment amount must be greater than zero.")

        conn = self._get_connection()
        try:
            with conn:
                sup = conn.execute("SELECT id, company_name FROM suppliers WHERE supplier_code = ?", (supplier_code,)).fetchone()
                if not sup:
                    raise ValueError(f"Supplier '{supplier_code}' not found.")

                po_id = None
                if po_number:
                    po = conn.execute("SELECT id FROM purchase_orders WHERE po_number = ?", (po_number.strip().upper(),)).fetchone()
                    if po:
                        po_id = po["id"]

                today_str = datetime.now().strftime("%Y%m%d")
                pay_ref = f"SPAY-{today_str}-{secrets.randbelow(9000)+1000}"

                conn.execute(
                    """
                    INSERT INTO supplier_payments (supplier_id, po_id, payment_ref, amount, payment_method, payment_date, notes)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                    """,
                    (sup["id"], po_id, pay_ref, amount, payment_method, date.today().strftime("%Y-%m-%d"), notes)
                )

                return {
                    "payment_ref": pay_ref,
                    "supplier": sup["company_name"],
                    "amount": amount,
                    "payment_method": payment_method,
                }
        finally:
            conn.close()

    def get_supplier_statement(self, supplier_code: str) -> Dict[str, Any]:
        supplier_code = supplier_code.strip().upper()
        conn = self._get_connection()
        try:
            sup = conn.execute("SELECT * FROM suppliers WHERE supplier_code = ?", (supplier_code,)).fetchone()
            if not sup:
                raise ValueError(f"Supplier '{supplier_code}' not found.")

            # Total invoiced from approved/partially delivered/completed POs
            total_ordered = conn.execute(
                """
                SELECT coalesce(sum(total_amount), 0)
                FROM purchase_orders
                WHERE supplier_id = ? AND status IN ('Approved', 'Partially Delivered', 'Completed')
                """,
                (sup["id"],)
            ).fetchone()[0]

            total_paid = conn.execute(
                "SELECT coalesce(sum(amount), 0) FROM supplier_payments WHERE supplier_id = ?",
                (sup["id"],)
            ).fetchone()[0]

            balance_due = round(total_ordered - total_paid, 2)

            pos = conn.execute(
                """
                SELECT po_number, order_date, status, total_amount
                FROM purchase_orders
                WHERE supplier_id = ?
                ORDER BY order_date DESC
                """,
                (sup["id"],)
            ).fetchall()

            payments = conn.execute(
                """
                SELECT payment_ref, payment_date, amount, payment_method
                FROM supplier_payments
                WHERE supplier_id = ?
                ORDER BY payment_date DESC
                """,
                (sup["id"],)
            ).fetchall()

            return {
                "supplier_code": supplier_code,
                "company_name": sup["company_name"],
                "total_orders_value": round(total_ordered, 2),
                "total_paid": round(total_paid, 2),
                "outstanding_balance": balance_due,
                "orders": [dict(p) for p in pos],
                "payments": [dict(pay) for pay in payments],
            }
        finally:
            conn.close()

    # ==================== PO Details & Analytics ====================

    def get_po_details(self, po_number: str) -> Dict[str, Any]:
        po_number = po_number.strip().upper()
        conn = self._get_connection()
        try:
            po = conn.execute(
                """
                SELECT p.*, s.supplier_code, s.company_name as supplier_name, s.email as supplier_email, s.phone as supplier_phone
                FROM purchase_orders p
                JOIN suppliers s ON p.supplier_id = s.id
                WHERE p.po_number = ?
                """,
                (po_number,)
            ).fetchone()
            if not po:
                raise ValueError(f"Purchase Order '{po_number}' not found.")

            data = dict(po)
            items = conn.execute(
                """
                SELECT pi.*, pr.sku, pr.name as product_name
                FROM po_items pi
                JOIN products pr ON pi.product_id = pr.id
                WHERE pi.po_id = ?
                """,
                (data["id"],)
            ).fetchall()
            data["items"] = [dict(i) for i in items]

            deliveries = conn.execute(
                """
                SELECT dl.*, pr.sku, pr.name as product_name
                FROM delivery_logs dl
                JOIN po_items pi ON dl.po_item_id = pi.id
                JOIN products pr ON pi.product_id = pr.id
                WHERE pi.po_id = ?
                ORDER BY dl.delivery_date DESC
                """,
                (data["id"],)
            ).fetchall()
            data["deliveries"] = [dict(d) for d in deliveries]

            return data
        finally:
            conn.close()

    def get_purchasing_summary(self) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            total_pos = conn.execute("SELECT count(*) FROM purchase_orders").fetchone()[0]
            status_counts = conn.execute("SELECT status, count(*) as count FROM purchase_orders GROUP BY status").fetchall()
            status_dict = {r["status"]: r["count"] for r in status_counts}

            total_spend = conn.execute(
                "SELECT coalesce(sum(total_amount), 0) FROM purchase_orders WHERE status IN ('Approved', 'Partially Delivered', 'Completed')"
            ).fetchone()[0]

            low_stock_count = conn.execute("SELECT count(*) FROM products WHERE stock_quantity <= reorder_level").fetchone()[0]

            return {
                "total_purchase_orders": total_pos,
                "status_breakdown": status_dict,
                "total_committed_spend": round(total_spend, 2),
                "low_stock_items_count": low_stock_count,
            }
        finally:
            conn.close()
