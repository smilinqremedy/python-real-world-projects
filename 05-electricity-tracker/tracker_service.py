"""
Service Layer for Electricity and Household Power Consumption Tracker
Implements mathematical calculations, consumption tracking, expense estimation,
generator expense isolation, and monthly energy reporting.
"""

import sqlite3
from datetime import datetime
from database import get_db_connection, DEFAULT_DB_FILE


class PowerTrackerService:
    def __init__(self, db_path=DEFAULT_DB_FILE):
        self.db_path = db_path

    # ==========================================
    # 1. SETTINGS & CONFIGURATION
    # ==========================================

    def get_setting(self, key, default=""):
        """Fetches a configuration setting from database."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT setting_value FROM app_settings WHERE setting_key = ?;", (key,))
            row = cursor.fetchone()
            return row["setting_value"] if row else default

    def set_setting(self, key, value):
        """Updates or sets a configuration setting."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO app_settings (setting_key, setting_value)
            VALUES (?, ?)
            ON CONFLICT(setting_key) DO UPDATE SET setting_value = excluded.setting_value;
            """, (key, str(value)))
            conn.commit()

    def get_low_units_threshold(self):
        """Returns the current low prepaid units threshold (kWh)."""
        val = self.get_setting("low_units_threshold", "20.0")
        try:
            return float(val)
        except ValueError:
            return 20.0

    # ==========================================
    # 2. PREPAID ELECTRICITY PURCHASES
    # ==========================================

    def record_prepaid_purchase(self, purchase_date, amount_paid, units_credited, token_number=None):
        """
        Records a prepaid electricity recharge.
        Calculates effective tariff rate per unit ($/kWh).
        """
        try:
            datetime.strptime(purchase_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid purchase date format. Use YYYY-MM-DD.")

        amount = float(amount_paid)
        units = float(units_credited)

        if amount <= 0:
            raise ValueError("Recharge amount must be greater than zero.")
        if units <= 0:
            raise ValueError("Units credited must be greater than zero.")

        unit_rate = round(amount / units, 4)
        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO prepaid_purchases (purchase_date, amount_paid, units_credited, unit_rate, token_number, created_at)
            VALUES (?, ?, ?, ?, ?, ?);
            """, (purchase_date, round(amount, 2), round(units, 2), unit_rate, token_number.strip() if token_number else None, now_str))
            conn.commit()
            purchase_id = cursor.lastrowid

        return self.get_purchase_by_id(purchase_id)

    def get_purchase_by_id(self, purchase_id):
        """Fetches a purchase record by ID."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM prepaid_purchases WHERE purchase_id = ?;", (purchase_id,))
            row = cursor.fetchone()
            if not row:
                raise ValueError(f"Purchase ID {purchase_id} not found.")
            return dict(row)

    def list_purchases(self):
        """Returns all electricity purchase history sorted by date descending."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM prepaid_purchases ORDER BY purchase_date DESC, purchase_id DESC;")
            return [dict(r) for r in cursor.fetchall()]

    def get_effective_electricity_rate(self):
        """
        Calculates weighted average electricity cost per kWh from purchases.
        Falls back to configured default if no purchases recorded.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT SUM(amount_paid) AS total_paid, SUM(units_credited) AS total_units FROM prepaid_purchases;")
            row = cursor.fetchone()
            if row and row["total_units"] and row["total_units"] > 0:
                return round(row["total_paid"] / row["total_units"], 4)

        fallback = self.get_setting("default_tariff_rate", "0.20")
        try:
            return float(fallback)
        except ValueError:
            return 0.20

    # ==========================================
    # 3. DAILY ELECTRICITY CONSUMPTION
    # ==========================================

    def record_daily_consumption(self, log_date, units_consumed=None, meter_reading=None, notes=None):
        """
        Records daily electricity units consumed (kWh).
        Handles direct kWh input or differential computation from consecutive meter readings.
        """
        try:
            datetime.strptime(log_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format. Must be YYYY-MM-DD.")

        final_units = None

        if units_consumed is not None:
            val = float(units_consumed)
            if val < 0:
                raise ValueError("Units consumed cannot be negative.")
            final_units = round(val, 2)
        elif meter_reading is not None:
            reading = float(meter_reading)
            if reading < 0:
                raise ValueError("Meter reading cannot be negative.")

            # Look up previous latest meter reading
            with get_db_connection(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                SELECT meter_reading FROM electricity_consumption
                WHERE log_date < ? AND meter_reading IS NOT NULL
                ORDER BY log_date DESC LIMIT 1;
                """, (log_date,))
                prev = cursor.fetchone()

                if prev and prev["meter_reading"] is not None:
                    prev_reading = prev["meter_reading"]
                    if reading < prev_reading:
                        raise ValueError(f"Current reading ({reading}) is lower than previous reading ({prev_reading}).")
                    final_units = round(reading - prev_reading, 2)
                else:
                    # First reading recorded, cannot calculate delta without prior base
                    final_units = 0.0
        else:
            raise ValueError("Either units_consumed or meter_reading must be provided.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO electricity_consumption (log_date, units_consumed, meter_reading, notes, created_at)
            VALUES (?, ?, ?, ?, ?)
            ON CONFLICT(log_date) DO UPDATE SET
                units_consumed = excluded.units_consumed,
                meter_reading = COALESCE(excluded.meter_reading, electricity_consumption.meter_reading),
                notes = COALESCE(excluded.notes, electricity_consumption.notes),
                created_at = excluded.created_at;
            """, (log_date, final_units, meter_reading, notes.strip() if notes else None, now_str))
            conn.commit()
            log_id = cursor.lastrowid

        return {
            "log_id": log_id,
            "log_date": log_date,
            "units_consumed": final_units,
            "meter_reading": meter_reading,
            "notes": notes
        }

    def list_consumption_logs(self, limit=30):
        """Returns recent daily consumption logs."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM electricity_consumption ORDER BY log_date DESC LIMIT ?;", (limit,))
            return [dict(r) for r in cursor.fetchall()]

    # ==========================================
    # 4. REMAINING UNITS & LOW UNITS ALERT
    # ==========================================

    def get_remaining_units_status(self):
        """
        Calculates remaining prepaid electricity units (Purchased - Consumed).
        Checks if units are below alert threshold and estimates days of power remaining.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT COALESCE(SUM(units_credited), 0.0) AS total_purchased FROM prepaid_purchases;")
            total_purchased = cursor.fetchone()["total_purchased"]

            cursor.execute("SELECT COALESCE(SUM(units_consumed), 0.0) AS total_consumed FROM electricity_consumption;")
            total_consumed = cursor.fetchone()["total_consumed"]

        remaining_units = round(total_purchased - total_consumed, 2)
        threshold = self.get_low_units_threshold()
        is_low = remaining_units <= threshold

        avg_daily = self.get_average_daily_consumption()["average_daily_kwh"]
        days_remaining = round(remaining_units / avg_daily, 1) if (avg_daily > 0 and remaining_units > 0) else 0.0

        return {
            "total_purchased_kwh": round(total_purchased, 2),
            "total_consumed_kwh": round(total_consumed, 2),
            "remaining_units_kwh": remaining_units,
            "threshold_kwh": threshold,
            "is_low": is_low,
            "estimated_days_remaining": days_remaining
        }

    # ==========================================
    # 5. AVERAGE CONSUMPTION & ESTIMATIONS
    # ==========================================

    def get_average_daily_consumption(self, days=30):
        """
        Calculates the average daily electricity consumption over the last N tracked days.
        """
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT units_consumed FROM electricity_consumption
            ORDER BY log_date DESC LIMIT ?;
            """, (days,))
            rows = cursor.fetchall()

        if not rows:
            return {"tracked_days": 0, "total_kwh": 0.0, "average_daily_kwh": 0.0}

        total_kwh = sum(r["units_consumed"] for r in rows)
        count = len(rows)
        avg_kwh = round(total_kwh / count, 2)

        return {
            "tracked_days": count,
            "total_kwh": round(total_kwh, 2),
            "average_daily_kwh": avg_kwh
        }

    def estimate_monthly_electricity_expenses(self):
        """
        Projects monthly energy expenses for both Grid and Generator based on historical daily averages.
        """
        avg_data = self.get_average_daily_consumption(days=30)
        avg_daily_kwh = avg_data["average_daily_kwh"]
        tariff_rate = self.get_effective_electricity_rate()

        # Grid monthly projection (30 days)
        projected_monthly_kwh = round(avg_daily_kwh * 30, 2)
        estimated_grid_cost = round(projected_monthly_kwh * tariff_rate, 2)

        # Generator monthly projection based on average daily fuel expenses
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT SUM(total_cost) AS total_gen_cost, COUNT(DISTINCT expense_date) AS gen_days
            FROM generator_expenses;
            """)
            gen_row = cursor.fetchone()

        gen_total = gen_row["total_gen_cost"] or 0.0
        gen_days = gen_row["gen_days"] or 0
        avg_daily_gen_cost = round(gen_total / gen_days, 2) if gen_days > 0 else 0.0
        estimated_generator_cost = round(avg_daily_gen_cost * 30, 2)

        total_monthly_projection = round(estimated_grid_cost + estimated_generator_cost, 2)

        return {
            "average_daily_kwh": avg_daily_kwh,
            "tariff_rate_per_kwh": tariff_rate,
            "projected_monthly_kwh": projected_monthly_kwh,
            "estimated_grid_cost": estimated_grid_cost,
            "estimated_generator_cost": estimated_generator_cost,
            "total_estimated_monthly_expense": total_monthly_projection
        }

    # ==========================================
    # 6. GENERATOR FUEL EXPENSE TRACKING
    # ==========================================

    def record_generator_fuel(self, expense_date, liters_bought, cost_per_liter, fuel_type="Petrol", run_hours=None, notes=None):
        """
        Records a generator fuel purchase separately from grid electricity.
        """
        try:
            datetime.strptime(expense_date, "%Y-%m-%d")
        except ValueError:
            raise ValueError("Invalid date format. Must be YYYY-MM-DD.")

        liters = float(liters_bought)
        rate = float(cost_per_liter)

        if liters <= 0:
            raise ValueError("Liters bought must be greater than zero.")
        if rate <= 0:
            raise ValueError("Cost per liter must be greater than zero.")

        total_cost = round(liters * rate, 2)
        hours = float(run_hours) if run_hours is not None else None
        if hours is not None and hours < 0:
            raise ValueError("Run hours cannot be negative.")

        now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            INSERT INTO generator_expenses (expense_date, fuel_type, liters_bought, cost_per_liter, total_cost, run_hours, notes, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?);
            """, (expense_date, fuel_type.strip(), round(liters, 2), round(rate, 2), total_cost, hours, notes.strip() if notes else None, now_str))
            conn.commit()
            fuel_id = cursor.lastrowid

        return {
            "fuel_id": fuel_id,
            "expense_date": expense_date,
            "fuel_type": fuel_type,
            "liters_bought": liters,
            "cost_per_liter": rate,
            "total_cost": total_cost,
            "run_hours": hours,
            "notes": notes
        }

    def list_generator_expenses(self):
        """Returns all generator expenses sorted by date descending."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM generator_expenses ORDER BY expense_date DESC, fuel_id DESC;")
            return [dict(r) for r in cursor.fetchall()]

    def get_generator_summary(self):
        """Calculates total generator fuel statistics."""
        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
            SELECT 
                COALESCE(SUM(liters_bought), 0.0) AS total_liters,
                COALESCE(SUM(total_cost), 0.0) AS total_spend,
                COALESCE(SUM(run_hours), 0.0) AS total_run_hours,
                COUNT(*) AS total_entries
            FROM generator_expenses;
            """)
            row = cursor.fetchone()

        total_liters = round(row["total_liters"], 2)
        total_spend = round(row["total_spend"], 2)
        total_hours = round(row["total_run_hours"], 2)
        avg_rate = round(total_spend / total_liters, 2) if total_liters > 0 else 0.0
        burn_rate = round(total_liters / total_hours, 2) if total_hours > 0 else 0.0

        return {
            "total_entries": row["total_entries"],
            "total_liters": total_liters,
            "total_spend": total_spend,
            "total_run_hours": total_hours,
            "average_cost_per_liter": avg_rate,
            "liters_per_hour": burn_rate
        }

    # ==========================================
    # 7. MONTHLY ENERGY REPORT
    # ==========================================

    def generate_monthly_energy_report(self, month_str):
        """
        Generates a consolidated monthly energy report for month (YYYY-MM).
        Analyzes grid consumption vs. generator expenses.
        """
        try:
            datetime.strptime(month_str, "%Y-%m")
        except ValueError:
            raise ValueError("Invalid month format. Must be YYYY-MM (e.g. 2026-11).")

        with get_db_connection(self.db_path) as conn:
            cursor = conn.cursor()

            # Grid Purchases in month
            cursor.execute("""
            SELECT COALESCE(SUM(amount_paid), 0.0) AS grid_spend,
                   COALESCE(SUM(units_credited), 0.0) AS units_bought
            FROM prepaid_purchases WHERE purchase_date LIKE ?;
            """, (f"{month_str}%",))
            purchase_data = cursor.fetchone()

            # Grid Consumption in month
            cursor.execute("""
            SELECT COALESCE(SUM(units_consumed), 0.0) AS units_consumed,
                   COUNT(log_date) AS days_logged
            FROM electricity_consumption WHERE log_date LIKE ?;
            """, (f"{month_str}%",))
            consumption_data = cursor.fetchone()

            # Generator expenses in month
            cursor.execute("""
            SELECT COALESCE(SUM(total_cost), 0.0) AS gen_spend,
                   COALESCE(SUM(liters_bought), 0.0) AS liters_bought,
                   COALESCE(SUM(run_hours), 0.0) AS run_hours
            FROM generator_expenses WHERE expense_date LIKE ?;
            """, (f"{month_str}%",))
            gen_data = cursor.fetchone()

        grid_spend = round(purchase_data["grid_spend"], 2)
        units_bought = round(purchase_data["units_bought"], 2)
        units_consumed = round(consumption_data["units_consumed"], 2)
        days_logged = consumption_data["days_logged"]
        avg_daily_kwh = round(units_consumed / days_logged, 2) if days_logged > 0 else 0.0

        gen_spend = round(gen_data["gen_spend"], 2)
        liters_bought = round(gen_data["liters_bought"], 2)
        run_hours = round(gen_data["run_hours"], 2)

        total_energy_expense = round(grid_spend + gen_spend, 2)

        grid_share_pct = round((grid_spend / total_energy_expense * 100), 1) if total_energy_expense > 0 else 0.0
        gen_share_pct = round((gen_spend / total_energy_expense * 100), 1) if total_energy_expense > 0 else 0.0

        return {
            "month": month_str,
            "grid_spend": grid_spend,
            "units_bought_kwh": units_bought,
            "units_consumed_kwh": units_consumed,
            "days_logged": days_logged,
            "avg_daily_kwh": avg_daily_kwh,
            "generator_spend": gen_spend,
            "liters_bought": liters_bought,
            "generator_run_hours": run_hours,
            "total_energy_expense": total_energy_expense,
            "grid_share_pct": grid_share_pct,
            "generator_share_pct": gen_share_pct
        }
