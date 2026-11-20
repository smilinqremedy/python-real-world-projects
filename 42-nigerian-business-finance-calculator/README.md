# Nigerian Tax and Business Revenue Calculator

A modular financial calculation and tax obligation estimation engine built in Python and SQLite for small and medium-sized businesses operating in Nigeria.

---

## The Problem

Small business owners and entrepreneurs in Nigeria frequently struggle with tracking daily revenue, classifying direct vs operational overhead, calculating gross and net margins, and understanding estimated tax exposure under the Nigerian tax framework (Finance Act, Companies Income Tax Act - CITA, Tertiary Education Trust Fund Act, and Value Added Tax - VAT).

This system provides a structured platform to record sales, track business expenses, separate revenue from profit, calculate margins, dynamically configure tax rules, and export formal financial summaries to CSV and PDF format with explicit calculation assumptions.

---

## Nigerian Tax Framework & Rules

The system implements the Nigerian tax architecture as established by the **Finance Act**:

1. **Companies Income Tax (CIT)** (Configurable):
   - **Small Companies** (Gross Turnover $\le$ ₦25,000,000): **0% CIT** (Full exemption incentive).
   - **Medium Companies** (Gross Turnover > ₦25,000,000 and $\le$ ₦100,000,000): **20% CIT**.
   - **Large Companies** (Gross Turnover > ₦100,000,000): **30% CIT**.

2. **Tertiary Education Tax (EDT / TETFund)**:
   - **3.0%** of assessable profit for all registered corporate entities.

3. **Value Added Tax (VAT)**:
   - **7.5%** standard rate on qualifying taxable sales and services.

4. **Minimum Tax**:
   - Evaluated at **0.5%** of gross turnover where turnover exceeds ₦25,000,000 and standard CIT is lower or zero.

5. **Configurable Tax Engine**:
   - All rates and turnover thresholds are stored in the database and can be customized via CLI or service layer to accommodate future Finance Act amendments.

6. **Statutory Non-Assessment Disclaimer**:
   - All reports, CLI screens, and exports prominently display the mandatory legal disclaimer:
     > *DISCLAIMER: This calculation is an indicative estimate for planning purposes only and does NOT constitute an official tax assessment or legal advice. Final tax liabilities must be assessed and filed with the Federal Inland Revenue Service (FIRS) or State Internal Revenue Service (SIRS) in accordance with applicable tax laws.*

---

## Architectural Separation of Concerns

1. **Separation of Revenue and Profit**:
   - **Gross Revenue**: Total monetary inflow from sales and services.
   - **Cost of Goods Sold (COGS)**: Direct inventory, procurement, and production costs.
   - **Gross Profit**: $\text{Gross Revenue} - \text{COGS}$.
   - **Operating Expenses (OpEx)**: Indirect operational overhead (rent, salaries, utilities, marketing).
   - **Net Profit**: $\text{Gross Profit} - \text{OpEx}$.

2. **Input Validation**:
   - Rejects negative amounts, zero amounts, invalid dates (`YYYY-MM-DD`), and invalid business classifications.

3. **Multi-Format Reporting**:
   - **CSV Export**: Standard tabular export compatible with spreadsheet software.
   - **PDF Export**: Pure Python zero-dependency PDF 1.4 generator creating professional financial and tax estimate sheets.

---

## How to Run the Application

Navigate to the project directory and launch the interactive CLI:

```bash
cd 42-nigerian-business-finance-calculator
python3 main.py
```

### Main CLI Features
- Record daily sales with VAT toggle and payment method selection.
- Record business expenses categorized into COGS, OpEx, or Capital Expenditure.
- View real-time P&L Dashboard with gross/net profit and margin percentages.
- View monthly financial breakdowns.
- Generate Nigerian Tax Estimation reports with detailed statutory assumptions.
- Customize tax rates and turnover thresholds.
- Export to CSV (`exports/financial_statement_*.csv`) and PDF (`exports/financial_tax_report_*.pdf`).

---

## Running Automated Tests

Run the comprehensive unit test suite:

```bash
python3 -m unittest test_finance.py -v
```
