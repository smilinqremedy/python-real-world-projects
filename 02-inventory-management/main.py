"""
Inventory Management System - CLI Interface
Entry point for managing small business retail inventory.
"""

import sys
from inventory_manager import (
    load_data,
    add_product,
    update_product_details,
    record_purchase,
    record_sale,
    display_products_table,
    display_low_stock_alerts,
    display_inventory_valuation,
    display_sales_summary,
    find_product_by_id,
    get_valid_int,
    get_valid_float,
    get_non_empty_string,
    DATA_FILE
)


def display_menu():
    """
    Displays the interactive CLI menu for the inventory system.
    """
    print("\n" + "=" * 54)
    print("   RETAIL INVENTORY MANAGEMENT SYSTEM (CLI)   ")
    print("=" * 54)
    print(" 1. Add New Product")
    print(" 2. Display All Available Products")
    print(" 3. Update Product Information")
    print(" 4. Record Product Purchase (Restock)")
    print(" 5. Record Product Sale")
    print(" 6. View Low-Stock Alerts")
    print(" 7. Calculate Total Inventory Value")
    print(" 8. Generate Sales & Profit Summary")
    print(" 9. Exit System")
    print("=" * 54)


def handle_add_product(data):
    """
    Handles prompt flow for adding a new product.
    """
    print("\n--- [Add New Product] ---")
    name = get_non_empty_string("Enter product name: ")
    quantity = get_valid_int("Enter initial stock quantity", min_val=0, default=0)
    cost_price = get_valid_float("Enter unit cost price ($)", min_val=0.01)
    selling_price = get_valid_float("Enter unit selling price ($)", min_val=0.01)
    threshold = get_valid_int("Enter low-stock reorder threshold", min_val=0, default=5)

    product = add_product(data, name, quantity, cost_price, selling_price, threshold, DATA_FILE)
    if product:
        print(f"\n✓ Product '{product['name']}' created successfully with Unique ID: {product['id']}.")


def handle_update_product(data):
    """
    Handles prompt flow for updating an existing product.
    """
    print("\n--- [Update Product Information] ---")
    if not data["products"]:
        print("No products in inventory to update.")
        return

    product_id = get_valid_int("Enter Product ID to update", min_val=1)
    product = find_product_by_id(data["products"], product_id)
    if not product:
        print(f"[Error] Product ID {product_id} not found.")
        return

    print(f"\nCurrent details for '{product['name']}':")
    print(f"  Name: {product['name']}")
    print(f"  Cost Price: ${product['cost_price']:.2f}")
    print(f"  Selling Price: ${product['selling_price']:.2f}")
    print(f"  Low-Stock Threshold: {product['low_stock_threshold']}")
    print("(Press Enter to keep current value)")

    new_name = input(f"New name [{product['name']}]: ").strip()
    new_cost_str = input(f"New cost price [${product['cost_price']:.2f}]: ").strip()
    new_selling_str = input(f"New selling price [${product['selling_price']:.2f}]: ").strip()
    new_threshold_str = input(f"New low-stock threshold [{product['low_stock_threshold']}]: ").strip()

    new_cost = float(new_cost_str.lstrip("$£€")) if new_cost_str else None
    new_selling = float(new_selling_str.lstrip("$£€")) if new_selling_str else None
    new_threshold = int(new_threshold_str) if new_threshold_str else None

    success, msg = update_product_details(
        data,
        product_id,
        new_name=new_name if new_name else None,
        new_cost=new_cost,
        new_selling=new_selling,
        new_threshold=new_threshold,
        file_path=DATA_FILE
    )
    if success:
        print(f"\n✓ {msg}")
    else:
        print(f"\n[Error] {msg}")


def handle_record_purchase(data):
    """
    Handles prompt flow for restocking inventory.
    """
    print("\n--- [Record Product Purchase / Restock] ---")
    if not data["products"]:
        print("Inventory is empty. Please add a product first.")
        return

    product_id = get_valid_int("Enter Product ID being purchased/restocked", min_val=1)
    product = find_product_by_id(data["products"], product_id)
    if not product:
        print(f"[Error] Product ID {product_id} not found.")
        return

    print(f"Restocking: '{product['name']}' (Current stock: {product['quantity']})")
    qty = get_valid_int("Enter quantity purchased", min_val=1)
    
    use_current_cost = input(f"Use existing cost price (${product['cost_price']:.2f})? (y/n, default: y): ").strip().lower()
    unit_cost = None
    if use_current_cost == "n":
        unit_cost = get_valid_float("Enter new purchase cost per unit ($)", min_val=0.01)

    success, result = record_purchase(data, product_id, qty, unit_cost=unit_cost, file_path=DATA_FILE)
    if success:
        print(f"\n✓ Purchase recorded! Added {qty} units to '{product['name']}'. New stock: {product['quantity']}.")
    else:
        print(f"\n[Error] {result}")


def handle_record_sale(data):
    """
    Handles prompt flow for recording a product sale with automatic stock check.
    """
    print("\n--- [Record Product Sale] ---")
    if not data["products"]:
        print("Inventory is empty. No products available to sell.")
        return

    product_id = get_valid_int("Enter Product ID being sold", min_val=1)
    product = find_product_by_id(data["products"], product_id)
    if not product:
        print(f"[Error] Product ID {product_id} not found.")
        return

    print(f"Selected: '{product['name']}' | Unit Price: ${product['selling_price']:.2f} | In Stock: {product['quantity']}")
    if product["quantity"] == 0:
        print("  [Error] This product is currently OUT OF STOCK. Sale cannot proceed.")
        return

    qty = get_valid_int("Enter quantity to sell", min_val=1)

    success, result = record_sale(data, product_id, qty, file_path=DATA_FILE)
    if success:
        print("\n" + "=" * 50)
        print("                 SALE RECEIPT")
        print("=" * 50)
        print(f" Sale Transaction ID: {result['sale_id']}")
        print(f" Product:             {result['product_name']} (ID: {result['product_id']})")
        print(f" Units Sold:          {result['quantity']}")
        print(f" Unit Selling Price:  ${result['unit_price']:.2f}")
        print(f" Total Charged:       ${result['total_revenue']:.2f}")
        print(f" Gross Profit:        ${result['profit']:.2f}")
        print(f" Remaining Stock:     {product['quantity']}")
        print("=" * 50)

        # Trigger low-stock warning if applicable
        if product["quantity"] <= product.get("low_stock_threshold", 5):
            print(f" [ALERT] Product '{product['name']}' is now at or below low-stock threshold ({product['quantity']} left)!")
    else:
        print(f"\n[Sale Rejected] {result}")


def main():
    """
    Main application loop.
    """
    print("\nStarting Retail Inventory Management System...")
    data = load_data(DATA_FILE)

    while True:
        try:
            display_menu()
            choice = input("Enter your choice (1-9): ").strip()

            if choice == "1":
                handle_add_product(data)
            elif choice == "2":
                display_products_table(data["products"])
            elif choice == "3":
                handle_update_product(data)
            elif choice == "4":
                handle_record_purchase(data)
            elif choice == "5":
                handle_record_sale(data)
            elif choice == "6":
                display_low_stock_alerts(data["products"])
            elif choice == "7":
                display_inventory_valuation(data["products"])
            elif choice == "8":
                display_sales_summary(data["sales"])
            elif choice == "9":
                print("\nExiting Inventory Management System. Thank you for your business!\n")
                sys.exit(0)
            else:
                print("\n[Error] Invalid selection. Please enter a number between 1 and 9.")

        except KeyboardInterrupt:
            print("\n\nOperation interrupted by user. Returning to main menu...")
        except EOFError:
            print("\nExiting. Goodbye.")
            sys.exit(0)


if __name__ == "__main__":
    main()
