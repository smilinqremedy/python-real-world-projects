"""
Database schema and initialization for Real Estate Property Listing and Search System.
"""
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "real_estate.db")


def get_connection(db_path=None):
    """Establish database connection with foreign key enforcement."""
    conn = sqlite3.connect(db_path or DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn


def init_db(db_path=None):
    """Create normalized relational tables and search indexes."""
    conn = get_connection(db_path)
    with conn:
        conn.executescript("""
        CREATE TABLE IF NOT EXISTS owners (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            owner_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS agents (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            agent_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            commission_rate REAL NOT NULL DEFAULT 3.0 CHECK(commission_rate >= 0.0 AND commission_rate <= 100.0),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS clients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            client_code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            phone TEXT NOT NULL,
            budget_max REAL CHECK(budget_max >= 0),
            preferred_type TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS properties (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            listing_code TEXT UNIQUE NOT NULL,
            owner_id INTEGER REFERENCES owners(id) ON DELETE RESTRICT NOT NULL,
            agent_id INTEGER REFERENCES agents(id) ON DELETE SET NULL,
            title TEXT NOT NULL,
            description TEXT,
            property_type TEXT NOT NULL CHECK(property_type IN ('apartment', 'house', 'commercial', 'land', 'villa')),
            listing_type TEXT NOT NULL CHECK(listing_type IN ('sale', 'rent')),
            price REAL NOT NULL CHECK(price > 0),
            address TEXT NOT NULL,
            city TEXT NOT NULL,
            bedrooms INTEGER DEFAULT 0 CHECK(bedrooms >= 0),
            bathrooms REAL DEFAULT 0.0 CHECK(bathrooms >= 0.0),
            area_sqft REAL NOT NULL CHECK(area_sqft > 0),
            status TEXT NOT NULL DEFAULT 'available' CHECK(status IN ('available', 'under_contract', 'sold', 'rented', 'off_market')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS inquiries (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER REFERENCES properties(id) ON DELETE CASCADE NOT NULL,
            client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE NOT NULL,
            message TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'new' CHECK(status IN ('new', 'contacted', 'closed')),
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS viewings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER REFERENCES properties(id) ON DELETE CASCADE NOT NULL,
            client_id INTEGER REFERENCES clients(id) ON DELETE CASCADE NOT NULL,
            agent_id INTEGER REFERENCES agents(id) ON DELETE SET NULL,
            viewing_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'scheduled' CHECK(status IN ('scheduled', 'completed', 'cancelled')),
            feedback TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS offers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            property_id INTEGER REFERENCES properties(id) ON DELETE RESTRICT NOT NULL,
            client_id INTEGER REFERENCES clients(id) ON DELETE RESTRICT NOT NULL,
            offer_amount REAL NOT NULL CHECK(offer_amount > 0),
            offer_date TEXT NOT NULL,
            status TEXT NOT NULL DEFAULT 'pending' CHECK(status IN ('pending', 'accepted', 'rejected', 'countered')),
            commission_earned REAL DEFAULT 0.0,
            closing_date TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );

        CREATE INDEX IF NOT EXISTS idx_properties_search ON properties(city, property_type, listing_type, price, status);
        CREATE INDEX IF NOT EXISTS idx_properties_owner ON properties(owner_id);
        CREATE INDEX IF NOT EXISTS idx_properties_agent ON properties(agent_id);
        CREATE INDEX IF NOT EXISTS idx_viewings_date ON viewings(viewing_date);
        CREATE INDEX IF NOT EXISTS idx_offers_status ON offers(status);
        """)
    conn.close()
