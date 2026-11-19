# Small Business Retail Inventory Management System

A reliable, feature-rich command-line inventory management and point-of-sale tracking system developed in Python for small retail businesses.

---

## 📌 Problem the Project Solves

Small retail businesses frequently depend on manual record-keeping, handwritten logs, or basic spreadsheets to track stock levels, incoming shipments, and customer sales. This manual approach introduces critical business problems:
- **Discrepant Stock Records**: Differences between recorded counts and actual physical inventory.
- **Stockouts and Lost Sales**: Running out of fast-moving products without advance notice, leading to dissatisfied customers and forfeited revenue.
- **Overselling**: Accepting orders or selling items that are actually out of stock.
- **Unclear Profit Margins**: Lack of real-time visibility into the true cost of goods sold (COGS), gross margins, and overall capital tied up in inventory.

The **Small Business Retail Inventory Management System** eliminates these inefficiencies with an automated, data-driven CLI application backed by persistent JSON storage, strict transaction validation, automated stock deductions, and real-time alerts.

---

## 🎯 Project Objectives

- **Automate Stock Control**: Accurately update inventory quantities upon purchases (restocking) and sales transactions.
- **Prevent Inaccurate Transactions**: Enforce defensive validation preventing sales when on-hand stock is insufficient or exhausted.
- **Proactive Stock Monitoring**: Automatically generate low-stock reorder warnings when product quantities fall below configurable safety thresholds.
- **Financial Clarity**: Provide instant valuation of total inventory capital (cost value vs. potential retail value) and comprehensive sales summaries detailing revenue, COGS, and gross profit margins.
- **Zero-Dependency Simplicity**: Deliver an extensible, offline application built purely with Python's standard library.

---

## ✨ Features

1. **Add New Products**: Create products with auto-generated unique IDs, product names, initial stock quantities, cost prices, selling prices, and customizable low-stock reorder thresholds.
2. **Unique ID Assignment**: Auto-increments integer identifiers across the catalog, guaranteeing unambiguous item indexing.
3. **Product Information Updates**: Modify existing product names, cost prices, selling prices, and reorder thresholds at any time.
4. **Record Product Purchases (Restock)**: Log incoming shipments, record purchase costs, and automatically increase on-hand quantities.
5. **Record Product Sales**: Process customer orders by Product ID and quantity sold.
6. **Automatic Stock Reduction**: Deduct sold quantities immediately upon transaction confirmation.
7. **Insufficient Stock Prevention**: Strictly blocks any sale that exceeds current available inventory.
8. **Display Available Products**: Formats the entire product catalog in an easy-to-read table showing IDs, names, quantities, unit economics, total cost values, and stock status indicators (`IN STOCK`, `LOW STOCK`, `OUT OF STOCK`).
9. **Low-Stock Alerts**: Flags products at or below their reorder threshold to prevent stockouts.
10. **Total Inventory Valuation**: Calculates total units in stock, total cost value (capital invested), total potential retail revenue, potential gross profit, and projected margin.
11. **Sales & Profit Summary**: Aggregates total sales transactions, units sold, gross revenue, Cost of Goods Sold (COGS), net realized profit, and overall profit margin.
12. **Persistent JSON Storage**: Automatically persists catalog state, sales logs, and purchase receipts to `inventory.json` with recovery logic for corrupted or missing files.

---

## 🛠 Technologies Used

- **Language**: Python 3.12+ (Compatible with Python 3.8+)
- **Standard Library Modules**:
  - `json`: Structured serialization and disk persistence.
  - `datetime`: Accurate timestamping of sales and purchase logs.
  - `os`: File existence checks and path management.
  - `unittest`: Comprehensive automated test suite.
- **Version Control**: Git & GitHub

---

## 📂 Project Organization

```text
Small-Business-Inventory-Management-System/
├── inventory_manager.py   # Core domain logic, validation, calculations & storage
├── main.py                # Interactive command-line user interface
├── test_inventory.py      # Automated unit test suite
├── inventory.json         # Persistent JSON database (auto-created on startup)
├── .gitignore             # Ignored temporary and environment files
└── README.md              # Project documentation and user manual
```

---

## 🚀 Installation Instructions

### Prerequisites
- Python 3.8 or higher installed on your machine. Check with:
  ```bash
  python3 --version
  ```

### Clone the Repository
```bash
git clone https://github.com/smilinqremedy/Small-Business-Inventory-Management-System.git
cd Small-Business-Inventory-Management-System
```

*(No external pip libraries are required. Everything runs using standard Python).*

---

## 💻 How to Run the Application

Launch the inventory management CLI:

```bash
python3 main.py
```

Run the automated test suite:

```bash
python3 -m unittest test_inventory.py
```

---

## 📖 Example Usage

### 1. Main Navigation Menu
```text
======================================================
   RETAIL INVENTORY MANAGEMENT SYSTEM (CLI)   
======================================================
 1. Add New Product
 2. Display All Available Products
 3. Update Product Information
 4. Record Product Purchase (Restock)
 5. Record Product Sale
 6. View Low-Stock Alerts
 7. Calculate Total Inventory Value
 8. Generate Sales & Profit Summary
 9. Exit System
======================================================
Enter your choice (1-9):
```

### 2. Adding a Product
```text
--- [Add New Product] ---
Enter product name: Wireless Ergonomic Mouse
Enter initial stock quantity [default: 0]: 15
Enter unit cost price ($): 12.50
Enter unit selling price ($): 29.99
Enter low-stock reorder threshold [default: 5]: 4

✓ Product 'Wireless Ergonomic Mouse' created successfully with Unique ID: 1.
```

### 3. Displaying Available Products Table
```text
==========================================================================================
ID    | Product Name           | Qty    | Cost ($)   | Price ($)  | Total Cost   | Status
------------------------------------------------------------------------------------------
1     | Wireless Mouse         | 15     | $   12.50  | $   29.99  | $    187.50  | IN STOCK
2     | USB-C Hub              | 3      | $    8.00  | $   19.99  | $     24.00  | LOW STOCK (<= 5)
==========================================================================================
```

### 4. Processing a Sale & Receipt Generation
```text
--- [Record Product Sale] ---
Enter Product ID being sold: 1
Selected: 'Wireless Ergonomic Mouse' | Unit Price: $29.99 | In Stock: 15
Enter quantity to sell: 3

==================================================
                 SALE RECEIPT
==================================================
 Sale Transaction ID: 1
 Product:             Wireless Ergonomic Mouse (ID: 1)
 Units Sold:          3
 Unit Selling Price:  $29.99
 Total Charged:       $89.97
 Gross Profit:        $52.47
 Remaining Stock:     12
==================================================
```

### 5. Prevent Sale When Stock is Insufficient
```text
--- [Record Product Sale] ---
Enter Product ID being sold: 2
Selected: 'USB-C Hub' | Unit Price: $19.99 | In Stock: 3
Enter quantity to sell: 10

[Sale Rejected] Insufficient stock! Requested: 10, Available in stock: 3.
```

### 6. Inventory Valuation Report
```text
==================================================
           TOTAL INVENTORY VALUATION
==================================================
 Catalog Product Types:                    2
 Total Units in Stock:                    15
--------------------------------------------------
 Total Inventory Cost Value:      $       174.00
 Total Potential Retail:          $       419.85
 Potential Gross Profit:          $       245.85
 Potential Profit Margin:                   58.6%
==================================================
```

### 7. Sales Summary
```text
=======================================================
                SALES & REVENUE SUMMARY
=======================================================
 Total Sales Transactions:                    1
 Total Product Units Sold:                    3
 Gross Revenue:                      $            89.97
 Cost of Goods Sold (COGS):          $            37.50
-------------------------------------------------------
 Net Realized Profit:                $            52.47
 Overall Profit Margin:                            58.3%
=======================================================
```

---

## 🧪 Testing

The repository contains automated unit tests in `test_inventory.py` covering all business logic:
- Unique ID auto-generation
- File persistence and corrupted JSON auto-recovery
- Product detail editing
- Restocking and cost price adjustments
- Automatic stock reduction upon sale
- Preventing sales when stock is insufficient
- Low-stock threshold detection
- Inventory valuation calculations
- Sales and margin metrics

Run the tests:
```bash
python3 -m unittest test_inventory.py
```
Output:
```text
..........
----------------------------------------------------------------------
Ran 10 tests in 0.025s

OK
```
