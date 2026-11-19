"""
Inventory Management System - Core Logic
Handles data storage, product management, purchases, sales, valuation, and reporting.
"""

import json
import os
from datetime import datetime

DATA_FILE = "inventory.json"

DEFAULT_DATA = {
    "products": [],
    "sales": [],
    "purchases": []
}


# ==========================================
# 1. STORAGE & PERSISTENCE
# ==========================================

def load_data(file_path=DATA_FILE):
    """
    Loads inventory data from a JSON file.
    Recovers with default empty structure if file is missing, empty, or corrupted.
    """
    if not os.path.exists(file_path):
        return {
            "products": [],
            "sales": [],
            "purchases": []
        }

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
            if not content:
                return {"products": [], "sales": [], "purchases": []}
            data = json.loads(content)
            if not isinstance(data, dict):
                return {"products": [], "sales": [], "purchases": []}
            if "products" not in data or not isinstance(data["products"], list):
                data["products"] = []
            if "sales" not in data or not isinstance(data["sales"], list):
                data["sales"] = []
            if "purchases" not in data or not isinstance(data["purchases"], list):
                data["purchases"] = []
            return data
    except (json.JSONDecodeError, IOError) as error:
        print(f"\n[Warning] Could not read '{file_path}' ({error}). Starting with fresh data.")
        return {"products": [], "sales": [], "purchases": []}


def save_data(data, file_path=DATA_FILE):
    """
    Saves inventory data to a JSON file with pretty formatting.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        return True
    except IOError as error:
        print(f"\n[Error] Failed to save data to '{file_path}': {error}")
        return False


# ==========================================
# 2. VALIDATION & HELPER FUNCTIONS
# ==========================================

def generate_next_id(items_list, id_key="id"):
    """
    Generates a unique incremental integer ID for any list of records.
    """
    if not items_list:
        return 1
    return max(item.get(id_key, 0) for item in items_list) + 1


def find_product_by_id(products, product_id):
    """
    Finds and returns a product dictionary by its unique ID, or None if not found.
    """
    for product in products:
        if product.get("id") == product_id:
            return product
    return None


def get_valid_int(prompt_text, min_val=0, default=None):
    """
    Prompts user for an integer, validating that it meets the minimum value constraint.
    """
    while True:
        display_prompt = f"{prompt_text} [default: {default}]: " if default is not None else f"{prompt_text}: "
        user_input = input(display_prompt).strip()

        if not user_input and default is not None:
            return default

        try:
            val = int(user_input)
            if val < min_val:
                print(f"  [Error] Value must be at least {min_val}.")
                continue
            return val
        except ValueError:
            print("  [Error] Invalid input. Please enter a valid whole number.")


def get_valid_float(prompt_text, min_val=0.01, default=None):
    """
    Prompts user for a positive float, stripping currency symbols.
    """
    while True:
        display_prompt = f"{prompt_text} [default: {default}]: " if default is not None else f"{prompt_text}: "
        user_input = input(display_prompt).strip()

        if not user_input and default is not None:
            return default

        clean_input = user_input.lstrip("$£€")
        try:
            val = float(clean_input)
            if val < min_val:
                print(f"  [Error] Value must be at least {min_val:.2f}.")
                continue
            return round(val, 2)
        except ValueError:
            print("  [Error] Invalid amount. Please enter a valid number (e.g., 19.99).")


def get_non_empty_string(prompt_text, default=None):
    """
    Prompts user for text, ensuring it is not empty.
    """
    while True:
        display_prompt = f"{prompt_text} [default: {default}]: " if default is not None else f"{prompt_text}: "
        user_input = input(display_prompt).strip()

        if not user_input and default is not None:
            return default
        if user_input:
            return user_input
        print("  [Error] Input cannot be blank.")


# ==========================================
# 3. PRODUCT MANAGEMENT (Features 1-4)
# ==========================================

def add_product(data, name, quantity, cost_price, selling_price, low_stock_threshold=5, file_path=DATA_FILE):
    """
    Adds a new product to inventory with a unique ID and saves data.
    """
    # Check for existing product with identical name
    for p in data["products"]:
        if p["name"].strip().lower() == name.strip().lower():
            print(f"\n[Warning] A product with name '{p['name']}' already exists (ID: {p['id']}).")
            confirm = input("Do you still want to add this product as a new entry? (y/n): ").strip().lower()
            if confirm != "y":
                print("Product creation cancelled.")
                return None

    new_id = generate_next_id(data["products"], id_key="id")
    product = {
        "id": new_id,
        "name": name.strip(),
        "quantity": int(quantity),
        "cost_price": round(float(cost_price), 2),
        "selling_price": round(float(selling_price), 2),
        "low_stock_threshold": int(low_stock_threshold)
    }

    data["products"].append(product)
    save_data(data, file_path)
    return product


def update_product_details(data, product_id, new_name=None, new_cost=None, new_selling=None, new_threshold=None, file_path=DATA_FILE):
    """
    Updates details for an existing product.
    """
    product = find_product_by_id(data["products"], product_id)
    if not product:
        return False, f"Product ID {product_id} not found."

    if new_name is not None and new_name.strip():
        product["name"] = new_name.strip()
    if new_cost is not None and new_cost > 0:
        product["cost_price"] = round(float(new_cost), 2)
    if new_selling is not None and new_selling > 0:
        product["selling_price"] = round(float(new_selling), 2)
    if new_threshold is not None and new_threshold >= 0:
        product["low_stock_threshold"] = int(new_threshold)

    save_data(data, file_path)
    return True, "Product updated successfully."


# ==========================================
# 4. PURCHASES / RESTOCKING (Feature 5)
# ==========================================

def record_purchase(data, product_id, quantity, unit_cost=None, file_path=DATA_FILE):
    """
    Records incoming stock for an existing product, increases its quantity,
    and logs the purchase transaction.
    """
    product = find_product_by_id(data["products"], product_id)
    if not product:
        return False, f"Product ID {product_id} does not exist."

    if quantity <= 0:
        return False, "Purchase quantity must be greater than zero."

    cost_per_unit = round(float(unit_cost), 2) if unit_cost is not None else product["cost_price"]
    total_cost = round(cost_per_unit * quantity, 2)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Increase stock
    product["quantity"] += quantity
    # Update cost price to latest purchase cost if provided
    if unit_cost is not None:
        product["cost_price"] = cost_per_unit

    purchase_id = generate_next_id(data["purchases"], id_key="purchase_id")
    purchase_entry = {
        "purchase_id": purchase_id,
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
        "unit_cost": cost_per_unit,
        "total_cost": total_cost,
        "date": now_str
    }

    data["purchases"].append(purchase_entry)
    save_data(data, file_path)
    return True, purchase_entry


# ==========================================
# 5. SALES & INVENTORY DEDUCTION (Features 6, 7, 8)
# ==========================================

def record_sale(data, product_id, quantity, file_path=DATA_FILE):
    """
    Records a product sale:
    - Validates sufficient stock (prevents sale if insufficient).
    - Automatically reduces stock.
    - Logs sale transaction with revenue and profit calculation.
    """
    product = find_product_by_id(data["products"], product_id)
    if not product:
        return False, f"Product ID {product_id} not found."

    if quantity <= 0:
        return False, "Sale quantity must be greater than zero."

    available_stock = product["quantity"]

    # Prevent sale when stock is insufficient (Feature 8)
    if available_stock < quantity:
        return False, f"Insufficient stock! Requested: {quantity}, Available in stock: {available_stock}."

    # Automatically reduce stock (Feature 7)
    product["quantity"] -= quantity

    unit_cost = product["cost_price"]
    unit_price = product["selling_price"]
    total_revenue = round(unit_price * quantity, 2)
    total_cogs = round(unit_cost * quantity, 2)
    profit = round(total_revenue - total_cogs, 2)
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    sale_id = generate_next_id(data["sales"], id_key="sale_id")
    sale_entry = {
        "sale_id": sale_id,
        "product_id": product_id,
        "product_name": product["name"],
        "quantity": quantity,
        "unit_cost": unit_cost,
        "unit_price": unit_price,
        "total_revenue": total_revenue,
        "cogs": total_cogs,
        "profit": profit,
        "date": now_str
    }

    data["sales"].append(sale_entry)
    save_data(data, file_path)
    return True, sale_entry


# ==========================================
# 6. DISPLAY PRODUCTS & ALERTS (Features 9, 10)
# ==========================================

def display_products_table(products):
    """
    Prints a formatted inventory table displaying all products.
    """
    if not products:
        print("\nNo products found in inventory.")
        return

    print("\n" + "=" * 90)
    print(f"{'ID':<5} | {'Product Name':<22} | {'Qty':<6} | {'Cost ($)':<10} | {'Price ($)':<10} | {'Total Cost':<12} | {'Status'}")
    print("-" * 90)

    for p in products:
        p_id = p.get("id", "-")
        name = p.get("name", "Unknown")[:22]
        qty = p.get("quantity", 0)
        cost = p.get("cost_price", 0.0)
        price = p.get("selling_price", 0.0)
        threshold = p.get("low_stock_threshold", 5)
        total_cost_val = qty * cost

        if qty == 0:
            status = "OUT OF STOCK"
        elif qty <= threshold:
            status = f"LOW STOCK (<= {threshold})"
        else:
            status = "IN STOCK"

        print(f"{p_id:<5} | {name:<22} | {qty:<6} | ${cost:>8,.2f} | ${price:>8,.2f} | ${total_cost_val:>10,.2f} | {status}")

    print("=" * 90)


def get_low_stock_products(products):
    """
    Returns a list of products whose quantity is less than or equal to their low-stock threshold.
    """
    return [p for p in products if p.get("quantity", 0) <= p.get("low_stock_threshold", 5)]


def display_low_stock_alerts(products):
    """
    Identifies and displays products needing reorder.
    """
    low_stock_items = get_low_stock_products(products)
    if not low_stock_items:
        print("\n✓ Great news! All inventory levels are healthy (no low-stock alerts).")
        return

    print("\n" + "!" * 75)
    print("                     LOW-STOCK REORDER ALERTS")
    print("!" * 75)
    print(f"{'ID':<5} | {'Product Name':<25} | {'Current Qty':<12} | {'Reorder Threshold'}")
    print("-" * 75)
    for p in low_stock_items:
        qty = p.get("quantity", 0)
        threshold = p.get("low_stock_threshold", 5)
        tag = "[OUT OF STOCK]" if qty == 0 else "[LOW STOCK]"
        print(f"{p['id']:<5} | {p['name']:<25} | {qty:<12} | {threshold} {tag}")
    print("!" * 75)


# ==========================================
# 7. INVENTORY VALUATION (Feature 11)
# ==========================================

def calculate_inventory_value(products):
    """
    Calculates total inventory valuation metrics:
    - Total cost value (capital tied up in stock)
    - Total retail value (potential gross sales)
    - Potential profit and margin
    """
    total_items = len(products)
    total_units = sum(p.get("quantity", 0) for p in products)
    total_cost_value = sum(p.get("quantity", 0) * p.get("cost_price", 0.0) for p in products)
    total_retail_value = sum(p.get("quantity", 0) * p.get("selling_price", 0.0) for p in products)
    potential_profit = total_retail_value - total_cost_value
    potential_margin = (potential_profit / total_retail_value * 100) if total_retail_value > 0 else 0.0

    return {
        "total_items": total_items,
        "total_units": total_units,
        "total_cost_value": round(total_cost_value, 2),
        "total_retail_value": round(total_retail_value, 2),
        "potential_profit": round(potential_profit, 2),
        "potential_margin": round(potential_margin, 2)
    }


def display_inventory_valuation(products):
    """
    Displays a formatted report of total inventory values.
    """
    metrics = calculate_inventory_value(products)

    print("\n" + "=" * 50)
    print("           TOTAL INVENTORY VALUATION")
    print("=" * 50)
    print(f" Catalog Product Types:      {metrics['total_items']:>15}")
    print(f" Total Units in Stock:       {metrics['total_units']:>15,}")
    print("-" * 50)
    print(f" Total Inventory Cost Value: ${metrics['total_cost_value']:>15,.2f}")
    print(f" Total Potential Retail:     ${metrics['total_retail_value']:>15,.2f}")
    print(f" Potential Gross Profit:     ${metrics['potential_profit']:>15,.2f}")
    print(f" Potential Profit Margin:    {metrics['potential_margin']:>15.1f}%")
    print("=" * 50)


# ==========================================
# 8. SALES SUMMARY & ANALYTICS (Feature 12)
# ==========================================

def calculate_sales_metrics(sales_list):
    """
    Computes aggregated sales metrics from sales records.
    """
    total_transactions = len(sales_list)
    total_units_sold = sum(s.get("quantity", 0) for s in sales_list)
    total_revenue = sum(s.get("total_revenue", 0.0) for s in sales_list)
    total_cogs = sum(s.get("cogs", 0.0) for s in sales_list)
    total_profit = sum(s.get("profit", 0.0) for s in sales_list)
    profit_margin = (total_profit / total_revenue * 100) if total_revenue > 0 else 0.0

    return {
        "transactions": total_transactions,
        "units_sold": total_units_sold,
        "total_revenue": round(total_revenue, 2),
        "total_cogs": round(total_cogs, 2),
        "total_profit": round(total_profit, 2),
        "profit_margin": round(profit_margin, 2)
    }


def display_sales_summary(sales_list):
    """
    Displays formatted sales summary and recent transactions log.
    """
    if not sales_list:
        print("\nNo sales transactions recorded yet.")
        return

    metrics = calculate_sales_metrics(sales_list)

    print("\n" + "=" * 55)
    print("                SALES & REVENUE SUMMARY")
    print("=" * 55)
    print(f" Total Sales Transactions:   {metrics['transactions']:>18}")
    print(f" Total Product Units Sold:   {metrics['units_sold']:>18,}")
    print(f" Gross Revenue:             ${metrics['total_revenue']:>18,.2f}")
    print(f" Cost of Goods Sold (COGS): ${metrics['total_cogs']:>18,.2f}")
    print("-" * 55)
    print(f" Net Realized Profit:       ${metrics['total_profit']:>18,.2f}")
    print(f" Overall Profit Margin:      {metrics['profit_margin']:>17.1f}%")
    print("=" * 55)

    print("\n--- Recent Sales Log ---")
    print(f"{'Sale ID':<8} | {'Date':<19} | {'Product':<20} | {'Qty':<5} | {'Revenue ($)':<12} | {'Profit ($)'}")
    print("-" * 80)
    for s in sales_list[-10:]:  # Show up to 10 most recent sales
        s_id = s.get("sale_id", "-")
        date_str = s.get("date", "-")
        p_name = s.get("product_name", "-")[:20]
        qty = s.get("quantity", 0)
        rev = s.get("total_revenue", 0.0)
        prof = s.get("profit", 0.0)
        print(f"{s_id:<8} | {date_str:<19} | {p_name:<20} | {qty:<5} | ${rev:>10,.2f} | ${prof:>9,.2f}")
    print("=" * 80)
