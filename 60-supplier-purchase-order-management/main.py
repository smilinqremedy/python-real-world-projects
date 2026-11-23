"""
Command-Line Interface for Supplier Purchase Order Management System.
"""
import sys
from po_service import POService, POWorkflowError


def print_banner(title: str):
    print("\n" + "=" * 65)
    print(f" {title.upper()} ")
    print("=" * 65)


def seed_demo(service: POService):
    try:
        service.register_supplier("SUP-101", "Prime Industrial Supplies Ltd", "Amina Yusuf", "amina@primesupplies.ng", "+2348021113344", "Ikeja, Lagos")
        service.register_supplier("SUP-102", "National Timber & Steel Mills", "Emeka Okoro", "emeka@nationaltimber.ng", "+2348035557788", "Enugu")

        service.add_product("STEEL-BAR-16", "High-Tensile Steel Bar 16mm", 18500.0, initial_stock=8, reorder_level=25, category="Metals")
        service.add_product("PLYWOOD-3/4", "Marine Plywood 3/4 inch sheet", 9200.0, initial_stock=35, reorder_level=20, category="Timber")
        service.add_product("SAFETY-BOOTS", "Steel-Toe Safety Work Boots", 14000.0, initial_stock=5, reorder_level=15, category="PPE")

        po1 = service.create_purchase_order("SUP-101", notes="Urgent restocking for Q4 construction project")
        service.add_po_item(po1, "STEEL-BAR-16", quantity=50)
        service.add_po_item(po1, "SAFETY-BOOTS", quantity=20)
        service.approve_purchase_order(po1)

        # Receive partial delivery
        service.receive_delivery(po1, "SAFETY-BOOTS", quantity_delivered=20, received_by="Audu Warehouse Mgr")

        print(f"Demo data seeded successfully! Sample PO Created & Partially Delivered: {po1}")
    except Exception as e:
        print(f"Note: Seed data or error: {e}")


def main():
    service = POService()

    while True:
        print_banner("Supplier Purchase Order & Inventory Management")
        print("1. Register Supplier")
        print("2. List Suppliers")
        print("3. Add Product to Catalog")
        print("4. View Product Catalog & Inventory Levels")
        print("5. Check Low Stock Items (Reorder Alerts)")
        print("6. Create Purchase Order (Draft)")
        print("7. Add Line Item to Draft PO")
        print("8. Approve Purchase Order")
        print("9. Receive Physical Delivery (Atomic Stock Increment)")
        print("10. Cancel Purchase Order")
        print("11. View Purchase Order Details & Delivery History")
        print("12. Record Supplier Payment")
        print("13. View Supplier Statement & Account Balance")
        print("14. Purchasing & Operational Dashboard")
        print("15. Seed Demo Data")
        print("0. Exit")

        choice = input("\nSelect an option [0-15]: ").strip()

        if choice == "1":
            print_banner("Register Supplier")
            code = input("Supplier Code (e.g. SUP-201): ").strip()
            cname = input("Company Name: ").strip()
            pname = input("Contact Person Name: ").strip()
            email = input("Email: ").strip()
            phone = input("Phone Number: ").strip()
            addr = input("Address: ").strip() or None
            try:
                sid = service.register_supplier(code, cname, pname, email, phone, addr)
                print(f"Supplier '{cname}' registered successfully! (ID: {sid})")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "2":
            print_banner("Supplier Directory")
            suppliers = service.list_suppliers()
            if not suppliers:
                print("No suppliers registered yet.")
            else:
                for s in suppliers:
                    print(f"[{s['supplier_code']}] {s['company_name']} | Contact: {s['contact_name']} | Email: {s['email']} | Phone: {s['phone']}")

        elif choice == "3":
            print_banner("Add Product to Catalog")
            sku = input("SKU: ").strip()
            name = input("Product Name: ").strip()
            category = input("Category [General]: ").strip() or "General"
            try:
                cost = float(input("Unit Cost Price (NGN): ").strip())
                stock = int(input("Initial Stock Quantity: ").strip())
                reorder = int(input("Reorder Level: ").strip())
                pid = service.add_product(sku, name, cost, stock, reorder, category)
                print(f"Product '{name}' (SKU: {sku}) added successfully! (ID: {pid})")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "4":
            print_banner("Product Catalog & Stock")
            products = service.list_products()
            for p in products:
                status_flag = " [LOW STOCK ALERT]" if p['stock_quantity'] <= p['reorder_level'] else ""
                print(f"[{p['sku']}] {p['name']} | Cost: ₦{p['unit_cost']:,.2f} | In Stock: {p['stock_quantity']} (Reorder @ {p['reorder_level']}){status_flag}")

        elif choice == "5":
            print_banner("Low Stock Alert (At or Below Reorder Level)")
            low = service.get_low_stock_products()
            if not low:
                print("All products have healthy inventory levels above reorder thresholds.")
            else:
                for p in low:
                    print(f"ALERT: [{p['sku']}] {p['name']} - Current Stock: {p['stock_quantity']} | Threshold: {p['reorder_level']}")

        elif choice == "6":
            print_banner("Create Purchase Order")
            sup_code = input("Supplier Code: ").strip()
            notes = input("Order Notes (optional): ").strip() or None
            try:
                po_num = service.create_purchase_order(sup_code, notes=notes)
                print(f"Purchase Order created in Draft state! PO Number: {po_num}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "7":
            print_banner("Add Line Item to Draft PO")
            po_num = input("PO Number: ").strip()
            sku = input("Product SKU: ").strip()
            try:
                qty = int(input("Quantity to Order: ").strip())
                cost_str = input("Unit Cost override (leave empty to use catalog cost): ").strip()
                cost = float(cost_str) if cost_str else None
                service.add_po_item(po_num, sku, qty, cost)
                print(f"Item {sku} (Qty: {qty}) added to PO {po_num} successfully!")
            except POWorkflowError as we:
                print(f"WORKFLOW ERROR: {we}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "8":
            print_banner("Approve Purchase Order")
            po_num = input("PO Number: ").strip()
            try:
                service.approve_purchase_order(po_num)
                print(f"Purchase Order '{po_num}' is now Approved and authorized for delivery!")
            except POWorkflowError as we:
                print(f"WORKFLOW ERROR: {we}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "9":
            print_banner("Receive Physical Delivery (Atomic Inventory Update)")
            po_num = input("PO Number: ").strip()
            sku = input("Product SKU: ").strip()
            try:
                qty = int(input("Quantity Delivered: ").strip())
                recv_by = input("Received By (Staff Name): ").strip()
                notes = input("Delivery Notes (optional): ").strip() or None

                res = service.receive_delivery(po_num, sku, qty, recv_by, notes=notes)
                print("\n[SUCCESS] Delivery verified and stock updated!")
                print(f"PO Number:              {res['po_number']}")
                print(f"Product:                {res['product_name']} ({res['sku']})")
                print(f"Quantity Delivered:     {res['quantity_delivered']}")
                print(f"Total Received on Item: {res['total_received_for_item']} / {res['ordered_quantity']}")
                print(f"Updated Stock on Hand:  {res['updated_warehouse_stock']}")
                print(f"PO Status:              {res['po_status']}")
            except POWorkflowError as we:
                print(f"DELIVERY WORKFLOW ERROR: {we}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "10":
            print_banner("Cancel Purchase Order")
            po_num = input("PO Number: ").strip()
            reason = input("Cancellation Reason: ").strip()
            try:
                service.cancel_purchase_order(po_num, reason)
                print(f"Purchase Order '{po_num}' has been cancelled.")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "11":
            print_banner("PO Details & Delivery History")
            po_num = input("PO Number: ").strip()
            try:
                po = service.get_po_details(po_num)
                print(f"\nPO Number:    {po['po_number']}")
                print(f"Supplier:     {po['supplier_name']} ({po['supplier_code']})")
                print(f"Order Date:   {po['order_date']}")
                print(f"Status:       {po['status']}")
                print(f"Total Amount: ₦{po['total_amount']:,.2f}")
                print(f"Notes:        {po['notes'] or 'None'}")

                print("\nLine Items:")
                for item in po["items"]:
                    print(f"  - [{item['sku']}] {item['product_name']}: Ordered {item['quantity_ordered']} | Received {item['quantity_received']} | Rate: ₦{item['unit_cost']:,.2f} | Subtotal: ₦{item['subtotal']:,.2f}")

                print("\nDelivery Receipts:")
                if not po["deliveries"]:
                    print("  No deliveries recorded yet.")
                else:
                    for d in po["deliveries"]:
                        print(f"  - [{d['delivery_date']}] Delivered {d['quantity_delivered']} units of {d['product_name']} | Received by: {d['received_by']}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "12":
            print_banner("Record Supplier Payment")
            sup = input("Supplier Code: ").strip()
            po_ref = input("Related PO Number (optional): ").strip() or None
            try:
                amt = float(input("Payment Amount (NGN): ").strip())
                method = input("Payment Method [Bank Transfer]: ").strip() or "Bank Transfer"
                notes = input("Payment Notes: ").strip() or None
                res = service.record_payment(sup, amt, method, po_ref, notes)
                print(f"Payment recorded! Ref: {res['payment_ref']} | Amount: ₦{res['amount']:,.2f} to {res['supplier']}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "13":
            print_banner("Supplier Account Statement")
            sup = input("Supplier Code: ").strip()
            try:
                stmt = service.get_supplier_statement(sup)
                print(f"\nSupplier:             {stmt['company_name']} ({stmt['supplier_code']})")
                print(f"Total Purchases:      ₦{stmt['total_orders_value']:,.2f}")
                print(f"Total Payments Made:  ₦{stmt['total_paid']:,.2f}")
                print(f"Outstanding Balance:  ₦{stmt['outstanding_balance']:,.2f}")

                print("\nPurchase Orders:")
                for o in stmt["orders"]:
                    print(f"  - [{o['order_date']}] {o['po_number']}: ₦{o['total_amount']:,.2f} ({o['status']})")

                print("\nPayment History:")
                for p in stmt["payments"]:
                    print(f"  - [{p['payment_date']}] {p['payment_ref']}: ₦{p['amount']:,.2f} via {p['payment_method']}")
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "14":
            print_banner("Purchasing & Operational Dashboard")
            summary = service.get_purchasing_summary()
            print(f"Total Purchase Orders:       {summary['total_purchase_orders']}")
            print(f"Total Committed PO Spend:    ₦{summary['total_committed_spend']:,.2f}")
            print(f"Low Stock Products Count:    {summary['low_stock_items_count']}")
            print("\nOrder Status Breakdown:")
            for st, cnt in summary["status_breakdown"].items():
                print(f"  - {st}: {cnt}")

        elif choice == "15":
            seed_demo(service)

        elif choice == "0":
            print("Exiting Supplier Purchase Order Management. Goodbye!")
            sys.exit(0)
        else:
            print("Invalid choice. Please select 0 to 15.")


if __name__ == "__main__":
    main()
