"""
Financial calculation and Nigerian tax estimation service layer.
"""
from datetime import datetime, date
import csv
import json
import os
import re
import secrets
from database import get_connection, init_db
from pdf_exporter import PDFDocument

STATUTORY_DISCLAIMER = (
    "DISCLAIMER: This calculation is an indicative estimate for planning purposes only and does NOT "
    "constitute an official tax assessment or legal advice. Final tax liabilities must be assessed "
    "and filed with the Federal Inland Revenue Service (FIRS) or State Internal Revenue Service (SIRS) "
    "in accordance with applicable tax laws."
)


class NigerianFinanceService:
    def __init__(self, db_path=None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    # ==================== Business Registration ====================

    def register_business(self, business_name: str, rc_number: str, tin: str,
                          business_type: str, sector: str, contact_email: str,
                          contact_phone: str, address: str = None,
                          currency: str = "NGN", currency_symbol: str = "₦") -> int:
        """Register or update business information."""
        business_name = business_name.strip()
        rc_number = rc_number.strip().upper()
        tin = tin.strip().upper() if tin else None
        business_type = business_type.strip()
        sector = sector.strip()
        contact_email = contact_email.strip().lower()
        contact_phone = contact_phone.strip()

        if not business_name or not rc_number or not sector:
            raise ValueError("Business name, RC/BN number, and industry sector are required.")

        valid_types = ("Sole Proprietorship", "Partnership", "Limited Liability Company (LLC)", "Enterprise")
        if business_type not in valid_types:
            raise ValueError(f"Business type must be one of: {', '.join(valid_types)}")

        if not re.match(r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$", contact_email):
            raise ValueError(f"Invalid contact email address: {contact_email}")

        conn = self._get_connection()
        try:
            with conn:
                existing = conn.execute("SELECT id FROM business_info LIMIT 1").fetchone()
                if existing:
                    conn.execute(
                        """
                        UPDATE business_info
                        SET business_name = ?, rc_number = ?, tin = ?, business_type = ?,
                            sector = ?, contact_email = ?, contact_phone = ?, address = ?,
                            currency = ?, currency_symbol = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE id = ?
                        """,
                        (business_name, rc_number, tin, business_type, sector, contact_email,
                         contact_phone, address, currency, currency_symbol, existing["id"]),
                    )
                    return existing["id"]
                else:
                    cursor = conn.execute(
                        """
                        INSERT INTO business_info (
                            business_name, rc_number, tin, business_type, sector,
                            contact_email, contact_phone, address, currency, currency_symbol
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (business_name, rc_number, tin, business_type, sector,
                         contact_email, contact_phone, address, currency, currency_symbol),
                    )
                    return cursor.lastrowid
        finally:
            conn.close()

    def get_business_info(self) -> dict:
        """Retrieve registered business information or default fallback."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM business_info ORDER BY id DESC LIMIT 1").fetchone()
            if row:
                return dict(row)
            return {
                "business_name": "Unregistered Nigerian Business",
                "rc_number": "RC-PENDING",
                "tin": "TIN-PENDING",
                "business_type": "Limited Liability Company (LLC)",
                "sector": "General Commerce",
                "contact_email": "finance@business.ng",
                "contact_phone": "+2348000000000",
                "currency": "NGN",
                "currency_symbol": "₦",
            }
        finally:
            conn.close()

    # ==================== Configurable Tax Rules ====================

    def get_tax_rules(self) -> dict:
        """Retrieve currently active tax configuration parameters."""
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM tax_rules WHERE is_active = 1 LIMIT 1").fetchone()
            if row:
                return dict(row)
            # Default fallbacks per Nigerian Finance Act
            return {
                "rule_name": "Nigeria Finance Act Baseline",
                "small_turnover_threshold": 25000000.0,
                "medium_turnover_threshold": 100000000.0,
                "small_cit_rate": 0.0,
                "medium_cit_rate": 0.20,
                "large_cit_rate": 0.30,
                "education_tax_rate": 0.03,
                "vat_rate": 0.075,
                "minimum_tax_rate": 0.005,
                "wht_standard_rate": 0.05,
            }
        finally:
            conn.close()

    def update_tax_rules(self, small_turnover: float, medium_turnover: float,
                         small_cit: float, medium_cit: float, large_cit: float,
                         education_tax: float, vat: float, minimum_tax: float) -> bool:
        """Configure and customize tax rates and thresholds."""
        if small_turnover < 0 or medium_turnover < small_turnover:
            raise ValueError("Turnover thresholds must be positive, and medium threshold must exceed small threshold.")
        for rate, name in [
            (small_cit, "Small CIT rate"), (medium_cit, "Medium CIT rate"),
            (large_cit, "Large CIT rate"), (education_tax, "Education tax rate"),
            (vat, "VAT rate"), (minimum_tax, "Minimum tax rate")
        ]:
            if not (0.0 <= rate <= 1.0):
                raise ValueError(f"{name} must be a valid percentage between 0.0 and 1.0.")

        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    UPDATE tax_rules
                    SET small_turnover_threshold = ?, medium_turnover_threshold = ?,
                        small_cit_rate = ?, medium_cit_rate = ?, large_cit_rate = ?,
                        education_tax_rate = ?, vat_rate = ?, minimum_tax_rate = ?,
                        updated_at = CURRENT_TIMESTAMP
                    WHERE is_active = 1
                    """,
                    (small_turnover, medium_turnover, small_cit, medium_cit,
                     large_cit, education_tax, vat, minimum_tax),
                )
                return True
        finally:
            conn.close()

    # ==================== Sales & Revenue Recording ====================

    def record_sale(self, sale_date: str, category: str, description: str,
                    gross_amount: float, customer_name: str = None,
                    vat_applied: bool = False, payment_method: str = "Bank Transfer") -> str:
        """
        Record a daily sales revenue entry with validation.
        Validates date format, positive amounts, and calculates VAT if applicable.
        """
        gross_amount = float(gross_amount)
        if gross_amount <= 0:
            raise ValueError("Sales gross amount must be strictly greater than zero.")

        try:
            datetime.strptime(sale_date.strip(), "%Y-%m-%d")
        except ValueError:
            raise ValueError("Sale date must follow 'YYYY-MM-DD' format.")

        valid_categories = ("Product Sales", "Services Rendered", "Wholesale", "Consulting", "Commission", "Other Revenue")
        if category not in valid_categories:
            raise ValueError(f"Category must be one of: {', '.join(valid_categories)}")

        tax_rules = self.get_tax_rules()
        vat_rate = tax_rules.get("vat_rate", 0.075)

        if vat_applied:
            # Gross includes VAT: VAT = Gross - (Gross / (1 + vat_rate))
            net_amount = round(gross_amount / (1 + vat_rate), 2)
            vat_amount = round(gross_amount - net_amount, 2)
        else:
            net_amount = round(gross_amount, 2)
            vat_amount = 0.0

        today_str = datetime.now().strftime("%Y%m%d")
        seq = secrets.randbelow(9000) + 1000
        sale_ref = f"SAL-{today_str}-{seq}"

        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO sales_transactions (
                        sale_ref, sale_date, customer_name, category, description,
                        gross_amount, vat_applied, vat_amount, net_amount, payment_method
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (sale_ref, sale_date, customer_name, category, description.strip(),
                     gross_amount, 1 if vat_applied else 0, vat_amount, net_amount, payment_method),
                )
                return sale_ref
        finally:
            conn.close()

    # ==================== Expense Recording ====================

    def record_expense(self, expense_date: str, category: str, expense_type: str,
                       description: str, amount: float, vendor_name: str = None,
                       is_tax_deductible: bool = True, receipt_ref: str = None) -> str:
        """
        Record a business expense with categorization and tax deductibility classification.
        Expense Types:
          - 'COGS': Direct Cost of Goods Sold (inventory, raw materials, direct packaging)
          - 'Operating': Operational overhead (rent, salaries, utilities, marketing, maintenance)
          - 'Capital': Capital equipment, machinery, long-term assets
        """
        amount = float(amount)
        if amount <= 0:
            raise ValueError("Expense amount must be strictly greater than zero.")

        try:
            datetime.strptime(expense_date.strip(), "%Y-%m-%d")
        except ValueError:
            raise ValueError("Expense date must follow 'YYYY-MM-DD' format.")

        valid_types = ("COGS", "Operating", "Capital")
        if expense_type not in valid_types:
            raise ValueError(f"Expense type must be one of: {', '.join(valid_types)}")

        if not description or not description.strip():
            raise ValueError("Expense description is required.")

        today_str = datetime.now().strftime("%Y%m%d")
        seq = secrets.randbelow(9000) + 1000
        expense_ref = f"EXP-{today_str}-{seq}"

        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO expense_transactions (
                        expense_ref, expense_date, vendor_name, category, expense_type,
                        description, amount, is_tax_deductible, receipt_ref
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (expense_ref, expense_date, vendor_name, category.strip(), expense_type,
                     description.strip(), amount, 1 if is_tax_deductible else 0, receipt_ref),
                )
                return expense_ref
        finally:
            conn.close()

    # ==================== Revenue & Profit Calculations ====================

    def calculate_total_revenue(self, start_date: str = None, end_date: str = None) -> dict:
        """
        Calculate gross revenue and net sales revenue over a specified time window.
        Separates revenue from profit.
        """
        conn = self._get_connection()
        try:
            where_clauses = []
            params = []
            if start_date:
                where_clauses.append("sale_date >= ?")
                params.append(start_date)
            if end_date:
                where_clauses.append("sale_date <= ?")
                params.append(end_date)

            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            row = conn.execute(
                f"""
                SELECT count(*) as total_sales_count,
                       coalesce(sum(gross_amount), 0.0) as total_gross_revenue,
                       coalesce(sum(net_amount), 0.0) as total_net_revenue,
                       coalesce(sum(vat_amount), 0.0) as total_vat_collected
                FROM sales_transactions {where_str}
                """,
                params,
            ).fetchone()

            by_cat = conn.execute(
                f"""
                SELECT category, count(*) as count, coalesce(sum(gross_amount), 0.0) as revenue
                FROM sales_transactions {where_str}
                GROUP BY category ORDER BY revenue DESC
                """,
                params,
            ).fetchall()

            res = dict(row)
            res["by_category"] = [dict(c) for c in by_cat]
            return res
        finally:
            conn.close()

    def calculate_operating_expenses(self, start_date: str = None, end_date: str = None) -> dict:
        """
        Calculate total operating expenses and expense breakdowns by type and category.
        """
        conn = self._get_connection()
        try:
            where_clauses = []
            params = []
            if start_date:
                where_clauses.append("expense_date >= ?")
                params.append(start_date)
            if end_date:
                where_clauses.append("expense_date <= ?")
                params.append(end_date)

            where_str = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            # By expense type
            type_rows = conn.execute(
                f"""
                SELECT expense_type, coalesce(sum(amount), 0.0) as total
                FROM expense_transactions {where_str}
                GROUP BY expense_type
                """,
                params,
            ).fetchall()

            totals_by_type = {"COGS": 0.0, "Operating": 0.0, "Capital": 0.0}
            for tr in type_rows:
                totals_by_type[tr["expense_type"]] = tr["total"]

            # Deductible total
            deductible_row = conn.execute(
                f"""
                SELECT coalesce(sum(amount), 0.0) as total_deductible
                FROM expense_transactions {where_str} {'AND' if where_str else 'WHERE'} is_tax_deductible = 1
                """,
                params,
            ).fetchone()

            # By category
            cat_rows = conn.execute(
                f"""
                SELECT category, expense_type, coalesce(sum(amount), 0.0) as total
                FROM expense_transactions {where_str}
                GROUP BY category, expense_type ORDER BY total DESC
                """,
                params,
            ).fetchall()

            return {
                "cogs": totals_by_type["COGS"],
                "operating_expenses": totals_by_type["Operating"],
                "capital_expenses": totals_by_type["Capital"],
                "total_expenses": sum(totals_by_type.values()),
                "total_tax_deductible": deductible_row["total_deductible"] if deductible_row else 0.0,
                "by_category": [dict(c) for c in cat_rows],
            }
        finally:
            conn.close()

    def calculate_profit_and_loss(self, start_date: str = None, end_date: str = None) -> dict:
        """
        Perform complete P&L analysis strictly separating revenue, COGS, gross profit,
        operating expenses, and net profit.
        """
        rev_data = self.calculate_total_revenue(start_date, end_date)
        exp_data = self.calculate_operating_expenses(start_date, end_date)

        total_revenue = rev_data["total_gross_revenue"]
        cogs = exp_data["cogs"]
        gross_profit = total_revenue - cogs
        gross_margin_percent = round((gross_profit / total_revenue) * 100, 2) if total_revenue > 0 else 0.0

        operating_expenses = exp_data["operating_expenses"]
        net_profit = gross_profit - operating_expenses
        net_margin_percent = round((net_profit / total_revenue) * 100, 2) if total_revenue > 0 else 0.0

        return {
            "period_start": start_date or "All History",
            "period_end": end_date or "Present",
            "total_revenue": total_revenue,
            "cogs": cogs,
            "gross_profit": gross_profit,
            "gross_margin_percent": gross_margin_percent,
            "operating_expenses": operating_expenses,
            "capital_expenses": exp_data["capital_expenses"],
            "net_profit": net_profit,
            "net_margin_percent": net_margin_percent,
            "total_expenses": exp_data["total_expenses"],
            "vat_collected": rev_data["total_vat_collected"],
        }

    # ==================== Monthly Financial Summaries ====================

    def generate_monthly_financial_summary(self, year: int = None, month: int = None) -> list[dict]:
        """
        Generate monthly financial summaries with revenue, expenses, gross and net margins.
        """
        conn = self._get_connection()
        try:
            where_sale = ""
            where_exp = ""
            params_sale = []
            params_exp = []

            if year and month:
                pattern = f"{year:04d}-{month:02d}%"
                where_sale = "WHERE sale_date LIKE ?"
                where_exp = "WHERE expense_date LIKE ?"
                params_sale = [pattern]
                params_exp = [pattern]
            elif year:
                pattern = f"{year:04d}%"
                where_sale = "WHERE sale_date LIKE ?"
                where_exp = "WHERE expense_date LIKE ?"
                params_sale = [pattern]
                params_exp = [pattern]

            sales_by_month = conn.execute(
                f"""
                SELECT strftime('%Y-%m', sale_date) as month,
                       coalesce(sum(gross_amount), 0.0) as revenue
                FROM sales_transactions {where_sale}
                GROUP BY month ORDER BY month DESC
                """,
                params_sale,
            ).fetchall()

            exp_by_month = conn.execute(
                f"""
                SELECT strftime('%Y-%m', expense_date) as month,
                       coalesce(sum(CASE WHEN expense_type = 'COGS' THEN amount ELSE 0 END), 0.0) as cogs,
                       coalesce(sum(CASE WHEN expense_type = 'Operating' THEN amount ELSE 0 END), 0.0) as opex,
                       coalesce(sum(CASE WHEN expense_type = 'Capital' THEN amount ELSE 0 END), 0.0) as capex,
                       coalesce(sum(amount), 0.0) as total_expenses
                FROM expense_transactions {where_exp}
                GROUP BY month ORDER BY month DESC
                """,
                params_exp,
            ).fetchall()

            exp_dict = {row["month"]: dict(row) for row in exp_by_month}
            all_months = sorted(list(set([r["month"] for r in sales_by_month] + list(exp_dict.keys()))), reverse=True)

            summaries = []
            sales_dict = {row["month"]: row["revenue"] for row in sales_by_month}

            for m in all_months:
                rev = sales_dict.get(m, 0.0)
                exp = exp_dict.get(m, {"cogs": 0.0, "opex": 0.0, "capex": 0.0, "total_expenses": 0.0})
                cogs = exp["cogs"]
                opex = exp["opex"]
                gross_p = rev - cogs
                net_p = gross_p - opex

                summaries.append({
                    "month": m,
                    "revenue": rev,
                    "cogs": cogs,
                    "gross_profit": gross_p,
                    "gross_margin": round((gross_p / rev) * 100, 2) if rev > 0 else 0.0,
                    "operating_expenses": opex,
                    "capital_expenses": exp["capex"],
                    "net_profit": net_p,
                    "net_margin": round((net_p / rev) * 100, 2) if rev > 0 else 0.0,
                })

            return summaries
        finally:
            conn.close()

    # ==================== Nigerian Tax Estimation Engine ====================

    def estimate_tax_obligations(self, start_date: str = None, end_date: str = None,
                                 period_label: str = "Annual Review") -> dict:
        """
        Estimate corporate and small business tax obligations in Nigeria using configurable rules.
        Explicitly displays calculation assumptions and attaches statutory non-assessment disclaimer.
        """
        pnl = self.calculate_profit_and_loss(start_date, end_date)
        tax_rules = self.get_tax_rules()

        turnover = pnl["total_revenue"]
        cogs = pnl["cogs"]
        gross_profit = pnl["gross_profit"]
        opex = pnl["operating_expenses"]
        net_profit = pnl["net_profit"]

        # Assessable Profit is net profit before tax (assuming all recorded operating expenses are deductible)
        assessable_profit = max(0.0, net_profit)

        # 1. Companies Income Tax (CIT) Tier Classification
        small_thresh = tax_rules["small_turnover_threshold"]
        med_thresh = tax_rules["medium_turnover_threshold"]
        small_cit_rate = tax_rules["small_cit_rate"]
        med_cit_rate = tax_rules["medium_cit_rate"]
        large_cit_rate = tax_rules["large_cit_rate"]

        assumptions = []

        if turnover <= small_thresh:
            tier = "Small Company"
            cit_rate = small_cit_rate
            assumptions.append(
                f"Classified as 'Small Company' (Annual Turnover ₦{turnover:,.2f} <= ₦{small_thresh:,.2f} threshold)."
            )
            assumptions.append(
                f"Eligible for {cit_rate * 100:.1f}% CIT rate under Nigeria Finance Act incentives for small businesses."
            )
        elif turnover <= med_thresh:
            tier = "Medium Company"
            cit_rate = med_cit_rate
            assumptions.append(
                f"Classified as 'Medium Company' (Turnover ₦{turnover:,.2f} between ₦{small_thresh:,.2f} and ₦{med_thresh:,.2f})."
            )
            assumptions.append(f"Subject to medium company CIT rate of {cit_rate * 100:.1f}%.")
        else:
            tier = "Large Company"
            cit_rate = large_cit_rate
            assumptions.append(f"Classified as 'Large Company' (Turnover ₦{turnover:,.2f} > ₦{med_thresh:,.2f}).")
            assumptions.append(f"Subject to standard corporate CIT rate of {cit_rate * 100:.1f}%.")

        estimated_cit = round(assessable_profit * cit_rate, 2)

        # 2. Tertiary Education Tax (EDT / TETFund)
        # 3% of assessable profit for registered Nigerian companies
        edt_rate = tax_rules["education_tax_rate"]
        estimated_edt = round(assessable_profit * edt_rate, 2)
        assumptions.append(
            f"Tertiary Education Trust Fund (EDT) estimated at {edt_rate * 100:.1f}% on assessable profit (₦{assessable_profit:,.2f})."
        )

        # 3. Minimum Tax
        # Applicable where turnover > 25M and CIT is 0 or less than 0.5% of gross turnover
        min_tax_rate = tax_rules["minimum_tax_rate"]
        calculated_min_tax = round(turnover * min_tax_rate, 2) if turnover > small_thresh else 0.0

        if turnover > small_thresh and estimated_cit < calculated_min_tax:
            assumptions.append(
                f"Minimum Tax provision evaluated: Turnover exceeds ₦{small_thresh:,.2f}. Minimum tax of {min_tax_rate*100:.2f}% (₦{calculated_min_tax:,.2f}) exceeds standard CIT."
            )
            effective_cit = calculated_min_tax
            estimated_min_tax_display = calculated_min_tax
        else:
            effective_cit = estimated_cit
            estimated_min_tax_display = 0.0
            if turnover <= small_thresh:
                assumptions.append("Exempt from Minimum Tax assessment as gross turnover is below ₦25,000,000.")

        # 4. Value Added Tax (VAT)
        vat_collected = pnl["vat_collected"]
        assumptions.append(
            f"Value Added Tax (VAT) position: ₦{vat_collected:,.2f} collected on qualifying customer transactions at standard {tax_rules['vat_rate']*100:.1f}%."
        )

        # 5. General Accounting Assumptions
        assumptions.append(
            "Assumes all claimed business expenses satisfy the statutory Wholly, Exclusively, Necessarily, and Reasonably (WENR) incurred standard."
        )
        assumptions.append(
            "Capital allowances, loss relief carryforwards, and balancing charges require official audited financial statements."
        )

        total_estimated_tax = round(effective_cit + estimated_edt + vat_collected, 2)

        result = {
            "period_label": period_label,
            "period_start": start_date or "All History",
            "period_end": end_date or "Present",
            "company_tier": tier,
            "turnover": turnover,
            "cogs": cogs,
            "gross_profit": gross_profit,
            "operating_expenses": opex,
            "net_profit": net_profit,
            "assessable_profit": assessable_profit,
            "cit_rate_applied": cit_rate,
            "estimated_cit": estimated_cit,
            "estimated_edt": estimated_edt,
            "estimated_minimum_tax": estimated_min_tax_display,
            "estimated_vat_collected": vat_collected,
            "estimated_total_tax": total_estimated_tax,
            "assumptions": assumptions,
            "disclaimer": STATUTORY_DISCLAIMER,
        }

        # Save estimation record into database history
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO tax_estimates (
                        period_label, period_start, period_end, total_turnover,
                        cost_of_goods_sold, gross_profit, operating_expenses, net_profit,
                        taxable_profit, cit_rate_applied, estimated_cit, estimated_edt,
                        estimated_vat_collected, estimated_minimum_tax, estimated_total_tax,
                        assumptions, disclaimer
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        period_label, result["period_start"], result["period_end"], turnover,
                        cogs, gross_profit, opex, net_profit, assessable_profit,
                        cit_rate, estimated_cit, estimated_edt, vat_collected,
                        estimated_min_tax_display, total_estimated_tax,
                        json.dumps(assumptions), STATUTORY_DISCLAIMER
                    ),
                )
        finally:
            conn.close()

        return result

    # ==================== Export to CSV & PDF ====================

    def export_financials_to_csv(self, file_path: str, start_date: str = None, end_date: str = None) -> str:
        """Export comprehensive transaction records and monthly summaries to CSV format."""
        conn = self._get_connection()
        try:
            os.makedirs(os.path.dirname(os.path.abspath(file_path)), exist_ok=True)
            with open(file_path, mode="w", newline="", encoding="utf-8") as f:
                writer = csv.writer(f)

                # Header & Disclaimer
                writer.writerow(["NIGERIAN BUSINESS FINANCIAL STATEMENT & TAX ESTIMATION"])
                writer.writerow(["STATUTORY NOTICE", STATUTORY_DISCLAIMER])
                writer.writerow([])

                # Sales Section
                writer.writerow(["--- SALES & REVENUE TRANSACTIONS ---"])
                writer.writerow(["Sale Ref", "Date", "Customer", "Category", "Description", "Gross (NGN)", "VAT (NGN)", "Net (NGN)", "Payment Method"])

                where_s = []
                params_s = []
                if start_date:
                    where_s.append("sale_date >= ?")
                    params_s.append(start_date)
                if end_date:
                    where_s.append("sale_date <= ?")
                    params_s.append(end_date)
                w_str_s = f"WHERE {' AND '.join(where_s)}" if where_s else ""

                sales = conn.execute(f"SELECT * FROM sales_transactions {w_str_s} ORDER BY sale_date DESC", params_s).fetchall()
                for s in sales:
                    writer.writerow([
                        s["sale_ref"], s["sale_date"], s["customer_name"] or "-", s["category"],
                        s["description"], f"{s['gross_amount']:.2f}", f"{s['vat_amount']:.2f}",
                        f"{s['net_amount']:.2f}", s["payment_method"]
                    ])

                writer.writerow([])

                # Expenses Section
                writer.writerow(["--- BUSINESS EXPENSES ---"])
                writer.writerow(["Expense Ref", "Date", "Vendor", "Category", "Type", "Description", "Amount (NGN)", "Tax Deductible"])
                where_e = []
                params_e = []
                if start_date:
                    where_e.append("expense_date >= ?")
                    params_e.append(start_date)
                if end_date:
                    where_e.append("expense_date <= ?")
                    params_e.append(end_date)
                w_str_e = f"WHERE {' AND '.join(where_e)}" if where_e else ""

                expenses = conn.execute(f"SELECT * FROM expense_transactions {w_str_e} ORDER BY expense_date DESC", params_e).fetchall()
                for e in expenses:
                    writer.writerow([
                        e["expense_ref"], e["expense_date"], e["vendor_name"] or "-", e["category"],
                        e["expense_type"], e["description"], f"{e['amount']:.2f}",
                        "YES" if e["is_tax_deductible"] else "NO"
                    ])

                writer.writerow([])

                # P&L Summary
                pnl = self.calculate_profit_and_loss(start_date, end_date)
                writer.writerow(["--- FINANCIAL PERFORMANCE SUMMARY ---"])
                writer.writerow(["Metric", "Amount (NGN)", "Percentage"])
                writer.writerow(["Total Revenue", f"{pnl['total_revenue']:.2f}", "100.0%"])
                writer.writerow(["Cost of Goods Sold (COGS)", f"{pnl['cogs']:.2f}", "-"])
                writer.writerow(["Gross Profit", f"{pnl['gross_profit']:.2f}", f"{pnl['gross_margin_percent']}%"])
                writer.writerow(["Operating Expenses", f"{pnl['operating_expenses']:.2f}", "-"])
                writer.writerow(["Net Profit Before Tax", f"{pnl['net_profit']:.2f}", f"{pnl['net_margin_percent']}%"])

            return file_path
        finally:
            conn.close()

    def export_financials_to_pdf(self, file_path: str, start_date: str = None,
                                 end_date: str = None, period_label: str = "Financial Year") -> str:
        """Export comprehensive statement and tax estimations to PDF format."""
        business = self.get_business_info()
        pnl = self.calculate_profit_and_loss(start_date, end_date)
        tax = self.estimate_tax_obligations(start_date, end_date, period_label=period_label)

        pdf_doc = PDFDocument()
        return pdf_doc.create_report_pdf(
            file_path=file_path,
            business=business,
            financial_summary=pnl,
            tax_estimate=tax,
            assumptions=tax["assumptions"],
            disclaimer=STATUTORY_DISCLAIMER
        )
