# Real Estate Property Listing and Search System

A comprehensive, relational property management and search application built in Python and SQLite for real estate agencies, brokerage firms, and property managers.

## Problem Statement

Real estate agencies and independent property brokers often struggle with:
- Disorganized property records scattered across spreadsheets or paper logs.
- Difficulty matching prospective buyers to available inventory based on specific criteria (budget, location, bedrooms, property type).
- Tracking property availability and preventing viewings or offers on already contracted or sold properties.
- Accurately recording price negotiations, offers, and counter-offers.
- Calculating agent commissions and analyzing sales performance across an agency's portfolio.

This application provides a centralized, relational system that organizes owners, agents, listings, inquiries, property viewings, and offers while computing financial commissions and market metrics.

---

## Features

1. **Owner & Agent Registration**: Manage property owners and licensed agents with customizable commission rates.
2. **Comprehensive Property Listings**: Support for multiple property categories (`apartment`, `house`, `commercial`, `land`, `villa`) and transaction types (`sale`, `rent`).
3. **Multi-Parameter Search Engine**: Filter inventory dynamically by city, listing type, property type, price ranges, bedrooms, and square footage, with custom sort orders (`price_asc`, `price_desc`, `newest`, `area_desc`).
4. **Prospective Client Profiles**: Track buyer/renter contact info, maximum budgets, and property preferences.
5. **Customer Inquiry Management**: Log and track client interest and messages per listing.
6. **Showing & Viewing Schedule**: Book, complete, and record client feedback for scheduled property tours.
7. **Offers & Negotiation Workflow**: Submit formal purchase/lease offers with status tracking (`pending`, `accepted`, `rejected`, `countered`).
8. **Automated Deal Closing & Commissions**: When an offer is accepted, the property status automatically transitions to `sold` or `rented`, competing pending offers are rejected, and the agent's commission is calculated.
9. **Agency Market Analytics**: Overview of total inventory, active/sold/rented counts, closed sales/rental volumes, and average price per square foot.
10. **Agent Performance Leaderboard**: Track deals closed, sales volume, and total commissions earned per agent.

---

## Database Architecture

The system uses an SQLite relational database (`real_estate.db`) with strict constraints and foreign keys:

- `owners`: Unique owner codes, contact information, and audit timestamps.
- `agents`: Unique agent codes, contact details, and commission percentage rates.
- `clients`: Prospective buyer/tenant profiles with budget constraints.
- `properties`: Property details, location, specifications (beds, baths, sqft), pricing, and lifecycle status (`available`, `under_contract`, `sold`, `rented`, `off_market`).
- `inquiries`: Direct inquiries linked between clients and properties.
- `viewings`: Scheduled property tours with feedback logs.
- `offers`: Formal financial bids with closing dates and calculated commission amounts.

---

## How to Run

### Interactive Application
```bash
python3 main.py
```

### Automated Unit Tests
```bash
python3 -m unittest test_property.py
```
