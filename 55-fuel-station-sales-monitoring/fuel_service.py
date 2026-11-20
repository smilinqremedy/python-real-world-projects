"""
Fuel station sales, delivery tracking, and tank stock reconciliation service using Decimal arithmetic.
"""
from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP
import secrets
from database import get_connection, init_db

TWO_PLACES = Decimal("0.01")
THREE_PLACES = Decimal("0.001")


def to_decimal(val, places=TWO_PLACES) -> Decimal:
    """Convert any numeric/string value to quantized Decimal."""
    if isinstance(val, Decimal):
        d = val
    else:
        d = Decimal(str(val).strip())
    return d.quantize(places, rounding=ROUND_HALF_UP)


class FuelStationService:
    def __init__(self, db_path=None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    # ==================== Product & Tank Configuration ====================

    def register_product(self, product_code: str, name: str, unit_price: float | str | Decimal) -> int:
        product_code = product_code.strip().upper()
        name = name.strip()
        price_dec = to_decimal(unit_price)

        if price_dec <= Decimal("0"):
            raise ValueError("Unit price must be strictly positive.")

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    """
                    INSERT INTO fuel_products (product_code, name, unit_price)
                    VALUES (?, ?, ?)
                    """,
                    (product_code, name, str(price_dec)),
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Product '{product_code}' is already registered.")
            raise
        finally:
            conn.close()

    def register_tank(self, tank_code: str, product_code: str, capacity_litres: float | str | Decimal,
                      initial_volume: float | str | Decimal = "0.0") -> int:
        tank_code = tank_code.strip().upper()
        product_code = product_code.strip().upper()
        cap_dec = to_decimal(capacity_litres)
        vol_dec = to_decimal(initial_volume)

        if cap_dec <= Decimal("0"):
            raise ValueError("Tank capacity must be strictly positive.")
        if vol_dec < Decimal("0"):
            raise ValueError("Initial volume cannot be negative.")
        if vol_dec > cap_dec:
            raise ValueError("Initial volume cannot exceed tank capacity.")

        conn = self._get_connection()
        try:
            with conn:
                prod = conn.execute("SELECT id FROM fuel_products WHERE product_code = ?", (product_code,)).fetchone()
                if not prod:
                    raise ValueError(f"Product code '{product_code}' not found.")

                cursor = conn.execute(
                    """
                    INSERT INTO storage_tanks (tank_code, product_id, capacity_litres, current_volume_litres)
                    VALUES (?, ?, ?, ?)
                    """,
                    (tank_code, prod["id"], str(cap_dec), str(vol_dec)),
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Tank code '{tank_code}' already exists.")
            raise
        finally:
            conn.close()

    def list_tanks(self) -> list[dict]:
        conn = self._get_connection()
        try:
            rows = conn.execute(
                """
                SELECT t.*, p.product_code, p.name as product_name, p.unit_price
                FROM storage_tanks t
                JOIN fuel_products p ON t.product_id = p.id
                ORDER BY t.tank_code ASC
                """
            ).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Fuel Deliveries ====================

    def record_delivery(self, tank_code: str, supplier_name: str, quantity_litres: float | str | Decimal,
                        unit_cost: float | str | Decimal, delivery_date: str = None, waybill: str = None) -> str:
        tank_code = tank_code.strip().upper()
        qty_dec = to_decimal(quantity_litres)
        cost_dec = to_decimal(unit_cost)

        if qty_dec <= Decimal("0"):
            raise ValueError("Delivered quantity must be strictly greater than zero.")
        if cost_dec <= Decimal("0"):
            raise ValueError("Unit cost must be strictly greater than zero.")

        if not delivery_date:
            delivery_date = datetime.now().strftime("%Y-%m-%d")

        total_cost_dec = to_decimal(qty_dec * cost_dec)

        conn = self._get_connection()
        try:
            with conn:
                tank = conn.execute("SELECT id, capacity_litres, current_volume_litres FROM storage_tanks WHERE tank_code = ?", (tank_code,)).fetchone()
                if not tank:
                    raise ValueError(f"Tank '{tank_code}' not found.")

                cap = Decimal(tank["capacity_litres"])
                curr_vol = Decimal(tank["current_volume_litres"])
                if curr_vol + qty_dec > cap:
                    raise ValueError(f"Delivery of {qty_dec}L exceeds tank capacity. Current volume: {curr_vol}L, Capacity: {cap}L.")

                today_str = datetime.now().strftime("%Y%m%d")
                seq = secrets.randbelow(9000) + 1000
                deliv_ref = f"DEL-{today_str}-{seq}"

                conn.execute(
                    """
                    INSERT INTO fuel_deliveries (
                        delivery_ref, tank_id, supplier_name, waybill_number,
                        quantity_litres, unit_cost, total_cost, delivery_date
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (deliv_ref, tank["id"], supplier_name.strip(), waybill, str(qty_dec), str(cost_dec), str(total_cost_dec), delivery_date),
                )

                # Replenish current volume
                new_vol = to_decimal(curr_vol + qty_dec)
                conn.execute("UPDATE storage_tanks SET current_volume_litres = ? WHERE id = ?", (str(new_vol), tank["id"]))
                return deliv_ref
        finally:
            conn.close()

    # ==================== Pump Sales Recording ====================

    def record_pump_sale(self, tank_code: str, pump_id: str, opening_meter: float | str | Decimal,
                         closing_meter: float | str | Decimal, sale_date: str = None) -> str:
        tank_code = tank_code.strip().upper()
        m_start = to_decimal(opening_meter)
        m_end = to_decimal(closing_meter)

        if m_end < m_start:
            raise ValueError(f"Closing meter reading ({m_end}) cannot be less than opening meter ({m_start}).")

        litres_sold_dec = to_decimal(m_end - m_start)
        if litres_sold_dec <= Decimal("0"):
            raise ValueError("No fuel dispensed. Litres sold must be greater than zero.")

        if not sale_date:
            sale_date = datetime.now().strftime("%Y-%m-%d")

        conn = self._get_connection()
        try:
            with conn:
                tank = conn.execute(
                    """
                    SELECT t.id, t.current_volume_litres, p.unit_price
                    FROM storage_tanks t
                    JOIN fuel_products p ON t.product_id = p.id
                    WHERE t.tank_code = ?
                    """,
                    (tank_code,),
                ).fetchone()
                if not tank:
                    raise ValueError(f"Tank '{tank_code}' not found.")

                curr_vol = Decimal(tank["current_volume_litres"])
                unit_price = Decimal(tank["unit_price"])
                total_rev = to_decimal(litres_sold_dec * unit_price)

                today_str = datetime.now().strftime("%Y%m%d")
                seq = secrets.randbelow(9000) + 1000
                sale_ref = f"SAL-{today_str}-{seq}"

                conn.execute(
                    """
                    INSERT INTO pump_sales (
                        sale_ref, tank_id, pump_id, sale_date, opening_meter,
                        closing_meter, litres_sold, unit_price, total_revenue
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (sale_ref, tank["id"], pump_id.strip(), sale_date, str(m_start), str(m_end), str(litres_sold_dec), str(unit_price), str(total_rev)),
                )

                # Deduct from estimated volume
                new_vol = to_decimal(max(Decimal("0"), curr_vol - litres_sold_dec))
                conn.execute("UPDATE storage_tanks SET current_volume_litres = ? WHERE id = ?", (str(new_vol), tank["id"]))
                return sale_ref
        finally:
            conn.close()

    # ==================== Tank Dip Reconciliation & Discrepancy Detection ====================

    def reconcile_tank(self, tank_code: str, recon_date: str, opening_dip: float | str | Decimal,
                       actual_closing_dip: float | str | Decimal) -> dict:
        """
        Perform physical dip reconciliation using Decimal calculations:
        Expected Closing Stock = Opening Dip + Deliveries Received - Pump Sales
        Discrepancy = Actual Physical Closing Dip - Expected Closing Stock
        """
        tank_code = tank_code.strip().upper()
        open_dip_dec = to_decimal(opening_dip)
        actual_close_dec = to_decimal(actual_closing_dip)

        if open_dip_dec < Decimal("0") or actual_close_dec < Decimal("0"):
            raise ValueError("Dip readings cannot be negative.")

        conn = self._get_connection()
        try:
            with conn:
                tank = conn.execute("SELECT id FROM storage_tanks WHERE tank_code = ?", (tank_code,)).fetchone()
                if not tank:
                    raise ValueError(f"Tank '{tank_code}' not found.")

                # Calculate total deliveries for that tank and date
                deliv_row = conn.execute(
                    "SELECT quantity_litres FROM fuel_deliveries WHERE tank_id = ? AND delivery_date = ?",
                    (tank["id"], recon_date),
                ).fetchall()
                deliv_total = sum((Decimal(r["quantity_litres"]) for r in deliv_row), Decimal("0.0"))

                # Calculate total pump sales for that tank and date
                sales_row = conn.execute(
                    "SELECT litres_sold, total_revenue FROM pump_sales WHERE tank_id = ? AND sale_date = ?",
                    (tank["id"], recon_date),
                ).fetchall()
                sales_total = sum((Decimal(r["litres_sold"]) for r in sales_row), Decimal("0.0"))
                revenue_total = sum((Decimal(r["total_revenue"]) for r in sales_row), Decimal("0.0"))

                # Expected Closing = Opening + Deliveries - Sales
                expected_close_dec = to_decimal(open_dip_dec + deliv_total - sales_total)
                discrepancy_dec = to_decimal(actual_close_dec - expected_close_dec)

                # Evaluate discrepancy tolerance
                # Industry rule: allowable evaporation/handling variance is +/- 0.5% of total throughput
                throughput = max(Decimal("1.0"), deliv_total + sales_total)
                variance_ratio = abs(discrepancy_dec) / throughput

                if abs(discrepancy_dec) <= Decimal("5.0"):
                    status = "Balanced"
                elif variance_ratio <= Decimal("0.005"):
                    status = "Acceptable Normal Variance"
                elif discrepancy_dec < Decimal("0"):
                    status = "Significant Shortage / Leakage"
                else:
                    status = "Unaccounted Gain / Meter Overfill"

                today_str = datetime.now().strftime("%Y%m%d")
                seq = secrets.randbelow(9000) + 1000
                recon_ref = f"RCN-{today_str}-{seq}"

                conn.execute(
                    """
                    INSERT INTO tank_reconciliations (
                        recon_ref, tank_id, reconciliation_date, opening_dip_litres,
                        deliveries_received_litres, pump_sales_litres, expected_closing_litres,
                        actual_closing_dip_litres, discrepancy_litres, discrepancy_status, total_revenue
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """,
                    (
                        recon_ref, tank["id"], recon_date, str(open_dip_dec),
                        str(deliv_total), str(sales_total), str(expected_close_dec),
                        str(actual_close_dec), str(discrepancy_dec), status, str(revenue_total)
                    ),
                )

                # Reset tank's physical volume to verified dip reading
                conn.execute(
                    "UPDATE storage_tanks SET current_volume_litres = ?, last_reconciled_date = ? WHERE id = ?",
                    (str(actual_close_dec), recon_date, tank["id"]),
                )

                return {
                    "recon_ref": recon_ref,
                    "tank_code": tank_code,
                    "date": recon_date,
                    "opening_dip": open_dip_dec,
                    "deliveries": deliv_total,
                    "pump_sales": sales_total,
                    "expected_closing": expected_close_dec,
                    "actual_closing": actual_close_dec,
                    "discrepancy": discrepancy_dec,
                    "status": status,
                    "total_revenue": revenue_total,
                }
        finally:
            conn.close()

    # ==================== Reporting ====================

    def generate_daily_report(self, report_date: str = None) -> dict:
        if not report_date:
            report_date = datetime.now().strftime("%Y-%m-%d")

        conn = self._get_connection()
        try:
            sales = conn.execute(
                """
                SELECT p.product_code, p.name as product_name,
                       sum(CAST(ps.litres_sold AS REAL)) as total_litres,
                       sum(CAST(ps.total_revenue AS REAL)) as total_rev
                FROM pump_sales ps
                JOIN storage_tanks t ON ps.tank_id = t.id
                JOIN fuel_products p ON t.product_id = p.id
                WHERE ps.sale_date = ?
                GROUP BY p.id
                """,
                (report_date,),
            ).fetchall()

            recons = conn.execute(
                """
                SELECT tr.*, t.tank_code, p.name as product_name
                FROM tank_reconciliations tr
                JOIN storage_tanks t ON tr.tank_id = t.id
                JOIN fuel_products p ON t.product_id = p.id
                WHERE tr.reconciliation_date = ?
                """,
                (report_date,),
            ).fetchall()

            total_litres_sold = sum((Decimal(str(s["total_litres"])) for s in sales), Decimal("0.0"))
            total_revenue = sum((Decimal(str(s["total_rev"])) for s in sales), Decimal("0.0"))

            return {
                "date": report_date,
                "total_litres_sold": total_litres_sold,
                "total_revenue": total_revenue,
                "product_breakdown": [dict(s) for s in sales],
                "tank_reconciliations": [dict(r) for r in recons],
            }
        finally:
            conn.close()
