"""
Service Layer for Small Business Sales and Profit Analysis System
Encapsulates financial formulas, product management, transaction recording,
COGS calculations, operational expense tracking, and profitability reporting.
"""

from datetime import datetime
import sqlite3
from database import get_db_connection, EXPENSE_CATEGORIES, PRODUCT_CATEGORIES, DEFAULT_DB_FILE


class ProfitAnalyticsService:
    def __init__(self, db_path=DEFAULT_DB_FILE):
        self.db_path = db_path

    # ==========================================
    # 1. PRODUCT MANAGEMENT (Features 1, 2, 3)
    # ==========================================

    def register_product(self, product_name, cost_price, selling_price, category="General Retail"):
        """
        Registers a new product with purchase cost price and retail selling price.
        """
        name = product_name.strip()
        if not name:
            raise ValueError("Product name cannot be blank.")

        cost = float(cost_price)
        selling = float(selling_price)

        if cost <= 0:
            raise ValueError("Purchase cost price must be greater than zero.")
        if selling <= 0:
            raise ValueError("Selling price must be greater than zero.")

        cat = category.strip() if category else "General Retail"
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            try:
                cursor.execute("""
                INSERT INTO products (product_name, category, cost_price, selling_price, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?);
                """, (name, cat, round(cost, 2), round(selling, 2), now_str, now_str))
                conn.commit()
                prod_id = cursor.lastrowid
            except sqlite3.IntegrityError:
                raise ValueError(f"Product '{name}' is already registered.")

        return self.get_product_by_id(prod_id)

    def update_product_pricing(self, product_id, new_cost_price=None, new_selling_price=None):
        """
        Updates cost and selling prices for an existing product.
        """
        prod = self.get_product_by_id(product_id)
        cost = float(new_cost_price) if new_cost_price is not None else prod["cost_price"]
        selling = float(new_selling_price) if new_selling_price is not None else prod["selling_price"]

        if cost <= 0:
            raise ValueError("Cost price must be greater than zero.")
        if selling <= 0:
            raise ValueError("Selling price must be greater than zero.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            UPDATE products
            SET cost_price = ?, selling_price = ?, updated_at = ?
            WHERE product_id = ?;
            """, (round(cost, 2), round(selling, 2), now_str, product_id))
            conn.commit()

        return self.get_product_by_id(product_id)

    def get_product_by_id(self, product_id):
        """Retrieves a product by ID."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products WHERE product_id = ?;", (product_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Product ID {product_id} not found.")
            return dict(row)

    def list_products(self):
        """Returns all products in catalog."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM products ORDER BY product_id ASC;")
            return [dict(r) for r in cursor.fetchall()]

    # ==========================================
    # 2. CUSTOMER SALES & COGS (Features 4, 5, 6, 7)
    # ==========================================

    def record_sale(self, product_id, quantity, sale_date=None, unit_selling_price=None, customer_notes=None):
        """
        Records a customer sale transaction:
        - Snapshots unit cost price and selling price.
        - Calculates total revenue = quantity * unit_selling_price.
        - Calculates COGS = quantity * unit_cost_price.
        - Calculates gross profit = revenue - COGS.
        """
        product = self.get_product_by_id(product_id)
        qty = int(quantity)
        if qty <= 0:
            raise ValueError("Sale quantity must be a positive integer.")

        unit_cost = product["cost_price"]
        unit_price = float(unit_selling_price) if unit_selling_price is not None else product["selling_price"]
        if unit_price <= 0:
            raise ValueError("Unit selling price must be greater than zero.")

        # Financial Calculations
        total_revenue = round(qty * unit_price, 2)
        total_cogs = round(qty * unit_cost, 2)
        gross_profit = round(total_revenue - total_cogs, 2)

        date_val = sale_date.strip() if sale_date else datetime.today().strftime("%Y-%m-%d")
        try:
            datetime.strptime(date_val, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid sale date format. Use YYYY-MM-DD.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO sales (product_id, sale_date, quantity, unit_cost_price, unit_selling_price, total_revenue, total_cogs, gross_profit, customer_notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?);
            """, (product_id, date_val, qty, unit_cost, round(unit_price, 2), total_revenue, total_cogs, gross_profit, customer_notes.strip() if customer_notes else None, now_str))
            conn.commit()
            sale_id = cursor.lastrowid

        return self.get_sale_by_id(sale_id)

    def get_sale_by_id(self, sale_id):
        """Fetches sale record with product name joined."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT s.*, p.product_name, p.category AS product_category
            FROM sales s
            JOIN products p ON s.product_id = p.product_id
            WHERE s.sale_id = ?;
            """, (sale_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Sale ID {sale_id} not found.")
            return dict(row)

    def list_recent_sales(self, limit=30):
        """Returns recent sales transactions."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT s.*, p.product_name
            FROM sales s
            JOIN products p ON s.product_id = p.product_id
            ORDER BY s.sale_date DESC, s.sale_id DESC LIMIT ?;
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    # ==========================================
    # 3. OPERATIONAL EXPENSES (Feature 8)
    # ==========================================

    def record_operational_expense(self, expense_date, category, amount, description):
        """
        Records business operating expense (Rent, Utilities, Wages, Supplies, etc.).
        """
        try:
            datetime.strptime(expense_date.strip(), "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid expense date format. Use YYYY-MM-DD.")

        amt = float(amount)
        if amt <= 0:
            raise ValueError("Expense amount must be greater than zero.")

        cat = category.strip()
        desc = description.strip()
        if not desc:
            raise ValueError("Expense description cannot be blank.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO operational_expenses (expense_date, category, amount, description, created_at)
            VALUES (?, ?, ?, ?, ?);
            """, (expense_date.strip(), cat, round(amt, 2), desc, now_str))
            conn.commit()
            exp_id = cursor.lastrowid

        return self.get_expense_by_id(exp_id)

    def get_expense_by_id(self, expense_id):
        """Fetches operational expense by ID."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM operational_expenses WHERE expense_id = ?;", (expense_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Expense ID {expense_id} not found.")
            return dict(row)

    def list_operational_expenses(self, limit=30):
        """Returns recent operating expenses."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM operational_expenses ORDER BY expense_date DESC, expense_id DESC LIMIT ?;", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    # ==========================================
    # 4. BEST-SELLING PRODUCTS (Feature 10)
    # ==========================================

    def identify_best_selling_products(self, limit=10, rank_by="units"):
        """
        Ranks products by total units sold or total gross revenue generated.
        """
        order_col = "total_units_sold" if rank_by == "units" else "total_revenue"

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(f"""
            SELECT 
                p.product_id,
                p.product_name,
                p.category,
                COALESCE(SUM(s.quantity), 0) AS total_units_sold,
                COALESCE(SUM(s.total_revenue), 0.0) AS total_revenue,
                COALESCE(SUM(s.total_cogs), 0.0) AS total_cogs,
                COALESCE(SUM(s.gross_profit), 0.0) AS total_gross_profit
            FROM products p
            LEFT JOIN sales s ON p.product_id = s.product_id
            GROUP BY p.product_id
            HAVING total_units_sold > 0
            ORDER BY {order_col} DESC
            LIMIT ?;
            """, (limit,))
            return [dict(r) for r in cursor.fetchall()]

    # ==========================================
    # 5. FINANCIAL REPORTS & SUMMARIES (Features 9, 11, 12, 13)
    # ==========================================

    def calculate_overall_financial_summary(self):
        """
        Computes overall lifetime financials:
        - Total Revenue
        - Cost of Goods Sold (COGS)
        - Gross Profit & Gross Margin %
        - Total Operational Expenses (OPEX)
        - Total Expenses (COGS + OPEX)
        - Net Profit & Net Margin %
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # Sales aggregations
            cursor.execute("""
            SELECT 
                COUNT(*) AS total_transactions,
                COALESCE(SUM(quantity), 0) AS total_units_sold,
                COALESCE(SUM(total_revenue), 0.0) AS total_revenue,
                COALESCE(SUM(total_cogs), 0.0) AS total_cogs,
                COALESCE(SUM(gross_profit), 0.0) AS total_gross_profit
            FROM sales;
            """)
            sales_row = cursor.fetchone()

            # Operational expenses aggregation
            cursor.execute("SELECT COALESCE(SUM(amount), 0.0) AS total_opex FROM operational_expenses;")
            opex_row = cursor.fetchone()

        revenue = round(sales_row["total_revenue"], 2)
        cogs = round(sales_row["total_cogs"], 2)
        gross_profit = round(sales_row["total_gross_profit"], 2)
        opex = round(opex_row["total_opex"], 2)

        total_expenses = round(cogs + opex, 2)
        net_profit = round(gross_profit - opex, 2)

        gross_margin = round((gross_profit / revenue * 100), 2) if revenue > 0 else 0.0
        net_margin = round((net_profit / revenue * 100), 2) if revenue > 0 else 0.0

        return {
            "total_transactions": sales_row["total_transactions"],
            "total_units_sold": sales_row["total_units_sold"],
            "total_revenue": revenue,
            "total_cogs": cogs,
            "gross_profit": gross_profit,
            "gross_margin_pct": gross_margin,
            "total_operational_expenses": opex,
            "total_expenses": total_expenses,
            "net_profit": net_profit,
            "net_margin_pct": net_margin
        }

    def generate_daily_sales_report(self, target_date):
        """
        Generates day-specific sales, revenue, COGS, and gross profit breakdown.
        """
        try:
            datetime.strptime(target_date.strip(), "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid target date format. Must be YYYY-MM-DD.")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 
                s.*, p.product_name
            FROM sales s
            JOIN products p ON s.product_id = p.product_id
            WHERE s.sale_date = ?
            ORDER BY s.sale_id ASC;
            """, (target_date.strip(),))
            sales_list = [dict(r) for r in cursor.fetchall()]

        total_units = sum(s["quantity"] for s in sales_list)
        total_revenue = round(sum(s["total_revenue"] for s in sales_list), 2)
        total_cogs = round(sum(s["total_cogs"] for s in sales_list), 2)
        gross_profit = round(sum(s["gross_profit"] for s in sales_list), 2)
        margin = round((gross_profit / total_revenue * 100), 1) if total_revenue > 0 else 0.0

        return {
            "report_date": target_date.strip(),
            "transaction_count": len(sales_list),
            "units_sold": total_units,
            "total_revenue": total_revenue,
            "total_cogs": total_cogs,
            "gross_profit": gross_profit,
            "gross_margin_pct": margin,
            "sales_transactions": sales_list
        }

    def generate_monthly_financial_report(self, month_str):
        """
        Generates full P&L monthly report:
        Revenue, COGS, Gross Profit, Operating Expenses Breakdown, Net Profit, and Margins.
        """
        try:
            datetime.strptime(month_str.strip(), "%Y-%m")
        except ValueError:
            raise ValueError("Invalid month format. Must be YYYY-MM (e.g. 2026-11).")

        clean_month = month_str.strip()

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # Monthly Sales & COGS
            cursor.execute("""
            SELECT 
                COUNT(*) AS total_sales,
                COALESCE(SUM(quantity), 0) AS total_units,
                COALESCE(SUM(total_revenue), 0.0) AS revenue,
                COALESCE(SUM(total_cogs), 0.0) AS cogs,
                COALESCE(SUM(gross_profit), 0.0) AS gross_profit
            FROM sales
            WHERE sale_date LIKE ?;
            """, (f"{clean_month}%",))
            sales_row = cursor.fetchone()

            # Monthly Operating Expenses
            cursor.execute("""
            SELECT 
                category,
                SUM(amount) AS category_total
            FROM operational_expenses
            WHERE expense_date LIKE ?
            GROUP BY category
            ORDER BY category_total DESC;
            """, (f"{clean_month}%",))
            expense_rows = cursor.fetchall()

        revenue = round(sales_row["revenue"], 2)
        cogs = round(sales_row["cogs"], 2)
        gross_profit = round(sales_row["gross_profit"], 2)

        opex_breakdown = {r["category"]: round(r["category_total"], 2) for r in expense_rows}
        total_opex = round(sum(opex_breakdown.values()), 2)

        total_expenses = round(cogs + total_opex, 2)
        net_profit = round(gross_profit - total_opex, 2)

        gross_margin = round((gross_profit / revenue * 100), 1) if revenue > 0 else 0.0
        net_margin = round((net_profit / revenue * 100), 1) if revenue > 0 else 0.0

        return {
            "month": clean_month,
            "total_sales_count": sales_row["total_sales"],
            "total_units_sold": sales_row["total_units"],
            "revenue": revenue,
            "cogs": cogs,
            "gross_profit": gross_profit,
            "gross_margin_pct": gross_margin,
            "operational_expenses_total": total_opex,
            "operational_breakdown": opex_breakdown,
            "total_expenses": total_expenses,
            "net_profit": net_profit,
            "net_margin_pct": net_margin
        }
