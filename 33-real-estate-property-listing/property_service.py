"""
Core business logic and management service for Real Estate Property Listing and Search System.
"""
from datetime import datetime
import re
from database import get_connection, init_db


class PropertyService:
    def __init__(self, db_path=None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    @staticmethod
    def _validate_email(email):
        pattern = r"^[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+$"
        if not re.match(pattern, email.strip()):
            raise ValueError(f"Invalid email address: {email}")

    # ==================== Stakeholder Registration ====================

    def register_owner(self, owner_code, name, email, phone):
        owner_code = owner_code.strip().upper()
        name = name.strip()
        email = email.strip().lower()
        phone = phone.strip()

        if not owner_code or not name or not email or not phone:
            raise ValueError("Owner code, name, email, and phone are all required.")
        self._validate_email(email)

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO owners (owner_code, name, email, phone) VALUES (?, ?, ?, ?)",
                    (owner_code, name, email, phone)
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Owner code '{owner_code}' or email '{email}' already registered.")
            raise
        finally:
            conn.close()

    def get_owner(self, owner_code):
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM owners WHERE owner_code = ?", (owner_code.strip().upper(),)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_owners(self):
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM owners ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def register_agent(self, agent_code, name, email, phone, commission_rate=3.0):
        agent_code = agent_code.strip().upper()
        name = name.strip()
        email = email.strip().lower()
        phone = phone.strip()

        if not agent_code or not name or not email or not phone:
            raise ValueError("Agent code, name, email, and phone are required.")
        if not (0.0 <= commission_rate <= 100.0):
            raise ValueError("Commission rate must be between 0% and 100%.")
        self._validate_email(email)

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO agents (agent_code, name, email, phone, commission_rate) VALUES (?, ?, ?, ?, ?)",
                    (agent_code, name, email, phone, commission_rate)
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Agent code '{agent_code}' or email '{email}' already exists.")
            raise
        finally:
            conn.close()

    def get_agent(self, agent_code):
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM agents WHERE agent_code = ?", (agent_code.strip().upper(),)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_agents(self):
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM agents ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def register_client(self, client_code, name, email, phone, budget_max=None, preferred_type=None):
        client_code = client_code.strip().upper()
        name = name.strip()
        email = email.strip().lower()
        phone = phone.strip()

        if not client_code or not name or not email or not phone:
            raise ValueError("Client code, name, email, and phone are required.")
        if budget_max is not None and budget_max < 0:
            raise ValueError("Maximum budget cannot be negative.")
        self._validate_email(email)

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO clients (client_code, name, email, phone, budget_max, preferred_type) VALUES (?, ?, ?, ?, ?, ?)",
                    (client_code, name, email, phone, budget_max, preferred_type.strip().lower() if preferred_type else None)
                )
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Client code '{client_code}' or email '{email}' already exists.")
            raise
        finally:
            conn.close()

    def get_client(self, client_code):
        conn = self._get_connection()
        try:
            row = conn.execute("SELECT * FROM clients WHERE client_code = ?", (client_code.strip().upper(),)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def list_clients(self):
        conn = self._get_connection()
        try:
            rows = conn.execute("SELECT * FROM clients ORDER BY name ASC").fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Property Listing Operations ====================

    def add_property(self, listing_code, owner_code, title, property_type,
                     listing_type, price, address, city, area_sqft,
                     bedrooms=0, bathrooms=0.0, description="", agent_code=None):
        listing_code = listing_code.strip().upper()
        title = title.strip()
        prop_type = property_type.strip().lower()
        list_type = listing_type.strip().lower()
        address = address.strip()
        city = city.strip().title()

        if not listing_code or not title or not address or not city:
            raise ValueError("Listing code, title, address, and city are mandatory.")
        if prop_type not in ("apartment", "house", "commercial", "land", "villa"):
            raise ValueError("Property type must be apartment, house, commercial, land, or villa.")
        if list_type not in ("sale", "rent"):
            raise ValueError("Listing type must be 'sale' or 'rent'.")
        if price <= 0:
            raise ValueError("Price must be greater than zero.")
        if area_sqft <= 0:
            raise ValueError("Area square footage must be greater than zero.")
        if bedrooms < 0 or bathrooms < 0:
            raise ValueError("Bedrooms and bathrooms cannot be negative.")

        conn = self._get_connection()
        try:
            owner = conn.execute("SELECT id FROM owners WHERE owner_code = ?", (owner_code.strip().upper(),)).fetchone()
            if not owner:
                raise ValueError(f"Owner with code '{owner_code}' does not exist.")
            owner_id = owner["id"]

            agent_id = None
            if agent_code:
                agent = conn.execute("SELECT id FROM agents WHERE agent_code = ?", (agent_code.strip().upper(),)).fetchone()
                if not agent:
                    raise ValueError(f"Agent with code '{agent_code}' does not exist.")
                agent_id = agent["id"]

            with conn:
                cursor = conn.execute("""
                    INSERT INTO properties (
                        listing_code, owner_id, agent_id, title, description,
                        property_type, listing_type, price, address, city,
                        bedrooms, bathrooms, area_sqft, status
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'available')
                """, (
                    listing_code, owner_id, agent_id, title, description.strip(),
                    prop_type, list_type, price, address, city,
                    bedrooms, bathrooms, area_sqft
                ))
                return cursor.lastrowid
        except Exception as e:
            if "UNIQUE constraint failed" in str(e):
                raise ValueError(f"Property with listing code '{listing_code}' already exists.")
            raise
        finally:
            conn.close()

    def update_property_status(self, listing_code, new_status):
        listing_code = listing_code.strip().upper()
        new_status = new_status.strip().lower()
        if new_status not in ("available", "under_contract", "sold", "rented", "off_market"):
            raise ValueError(f"Invalid property status: {new_status}")

        conn = self._get_connection()
        try:
            with conn:
                updated = conn.execute(
                    "UPDATE properties SET status = ? WHERE listing_code = ?",
                    (new_status, listing_code)
                ).rowcount
                if updated == 0:
                    raise ValueError(f"Property '{listing_code}' not found.")
                return True
        finally:
            conn.close()

    def update_property_price(self, listing_code, new_price):
        if new_price <= 0:
            raise ValueError("New price must be greater than zero.")

        conn = self._get_connection()
        try:
            with conn:
                updated = conn.execute(
                    "UPDATE properties SET price = ? WHERE listing_code = ?",
                    (new_price, listing_code.strip().upper())
                ).rowcount
                if updated == 0:
                    raise ValueError(f"Property '{listing_code}' not found.")
                return True
        finally:
            conn.close()

    def get_property(self, listing_code):
        conn = self._get_connection()
        try:
            row = conn.execute("""
                SELECT p.*, o.owner_code, o.name as owner_name, o.phone as owner_phone,
                       a.agent_code, a.name as agent_name, a.commission_rate
                FROM properties p
                JOIN owners o ON p.owner_id = o.id
                LEFT JOIN agents a ON p.agent_id = a.id
                WHERE p.listing_code = ?
            """, (listing_code.strip().upper(),)).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    # ==================== Multi-Parameter Search Engine ====================

    def search_properties(self, city=None, property_type=None, listing_type=None,
                          min_price=None, max_price=None, min_bedrooms=None,
                          min_area_sqft=None, status="available", sort_by="price_asc"):
        conn = self._get_connection()
        try:
            query = """
                SELECT p.*, o.name as owner_name, a.name as agent_name
                FROM properties p
                JOIN owners o ON p.owner_id = o.id
                LEFT JOIN agents a ON p.agent_id = a.id
                WHERE 1=1
            """
            params = []

            if status:
                query += " AND p.status = ?"
                params.append(status.strip().lower())

            if city:
                query += " AND LOWER(p.city) LIKE ?"
                params.append(f"%{city.strip().lower()}%")

            if property_type:
                query += " AND p.property_type = ?"
                params.append(property_type.strip().lower())

            if listing_type:
                query += " AND p.listing_type = ?"
                params.append(listing_type.strip().lower())

            if min_price is not None:
                query += " AND p.price >= ?"
                params.append(float(min_price))

            if max_price is not None:
                query += " AND p.price <= ?"
                params.append(float(max_price))

            if min_bedrooms is not None:
                query += " AND p.bedrooms >= ?"
                params.append(int(min_bedrooms))

            if min_area_sqft is not None:
                query += " AND p.area_sqft >= ?"
                params.append(float(min_area_sqft))

            # Sorting
            sort_map = {
                "price_asc": " ORDER BY p.price ASC",
                "price_desc": " ORDER BY p.price DESC",
                "area_desc": " ORDER BY p.area_sqft DESC",
                "newest": " ORDER BY p.created_at DESC"
            }
            query += sort_map.get(sort_by, " ORDER BY p.price ASC")

            rows = conn.execute(query, params).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Customer Inquiries & Viewings ====================

    def create_inquiry(self, listing_code, client_code, message):
        conn = self._get_connection()
        try:
            prop = conn.execute("SELECT id FROM properties WHERE listing_code = ?", (listing_code.strip().upper(),)).fetchone()
            if not prop:
                raise ValueError(f"Property '{listing_code}' not found.")

            client = conn.execute("SELECT id FROM clients WHERE client_code = ?", (client_code.strip().upper(),)).fetchone()
            if not client:
                raise ValueError(f"Client '{client_code}' not found.")

            with conn:
                cursor = conn.execute(
                    "INSERT INTO inquiries (property_id, client_id, message) VALUES (?, ?, ?)",
                    (prop["id"], client["id"], message.strip())
                )
                return cursor.lastrowid
        finally:
            conn.close()

    def list_inquiries(self, listing_code=None):
        conn = self._get_connection()
        try:
            if listing_code:
                rows = conn.execute("""
                    SELECT i.*, p.listing_code, p.title as property_title, c.client_code, c.name as client_name, c.phone as client_phone
                    FROM inquiries i
                    JOIN properties p ON i.property_id = p.id
                    JOIN clients c ON i.client_id = c.id
                    WHERE p.listing_code = ?
                    ORDER BY i.created_at DESC
                """, (listing_code.strip().upper(),)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT i.*, p.listing_code, p.title as property_title, c.client_code, c.name as client_name, c.phone as client_phone
                    FROM inquiries i
                    JOIN properties p ON i.property_id = p.id
                    JOIN clients c ON i.client_id = c.id
                    ORDER BY i.created_at DESC
                """).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    def schedule_viewing(self, listing_code, client_code, viewing_date_str, agent_code=None):
        conn = self._get_connection()
        try:
            prop = conn.execute("SELECT id, status, agent_id FROM properties WHERE listing_code = ?", (listing_code.strip().upper(),)).fetchone()
            if not prop:
                raise ValueError(f"Property '{listing_code}' not found.")
            if prop["status"] in ("sold", "rented", "off_market"):
                raise ValueError(f"Cannot schedule viewing for property with status '{prop['status']}'.")

            client = conn.execute("SELECT id FROM clients WHERE client_code = ?", (client_code.strip().upper(),)).fetchone()
            if not client:
                raise ValueError(f"Client '{client_code}' not found.")

            agent_id = prop["agent_id"]
            if agent_code:
                ag = conn.execute("SELECT id FROM agents WHERE agent_code = ?", (agent_code.strip().upper(),)).fetchone()
                if ag:
                    agent_id = ag["id"]

            with conn:
                cursor = conn.execute("""
                    INSERT INTO viewings (property_id, client_id, agent_id, viewing_date, status)
                    VALUES (?, ?, ?, ?, 'scheduled')
                """, (prop["id"], client["id"], agent_id, viewing_date_str))
                return cursor.lastrowid
        finally:
            conn.close()

    def complete_viewing(self, viewing_id, feedback=""):
        conn = self._get_connection()
        try:
            with conn:
                updated = conn.execute("""
                    UPDATE viewings
                    SET status = 'completed', feedback = ?
                    WHERE id = ?
                """, (feedback.strip(), viewing_id)).rowcount
                if updated == 0:
                    raise ValueError(f"Viewing #{viewing_id} not found.")
                return True
        finally:
            conn.close()

    def list_viewings(self, listing_code=None):
        conn = self._get_connection()
        try:
            if listing_code:
                rows = conn.execute("""
                    SELECT v.*, p.listing_code, p.title as property_title,
                           c.client_code, c.name as client_name, a.name as agent_name
                    FROM viewings v
                    JOIN properties p ON v.property_id = p.id
                    JOIN clients c ON v.client_id = c.id
                    LEFT JOIN agents a ON v.agent_id = a.id
                    WHERE p.listing_code = ?
                    ORDER BY v.viewing_date ASC
                """, (listing_code.strip().upper(),)).fetchall()
            else:
                rows = conn.execute("""
                    SELECT v.*, p.listing_code, p.title as property_title,
                           c.client_code, c.name as client_name, a.name as agent_name
                    FROM viewings v
                    JOIN properties p ON v.property_id = p.id
                    JOIN clients c ON v.client_id = c.id
                    LEFT JOIN agents a ON v.agent_id = a.id
                    ORDER BY v.viewing_date ASC
                """).fetchall()
            return [dict(r) for r in rows]
        finally:
            conn.close()

    # ==================== Offers & Deals Management ====================

    def make_offer(self, listing_code, client_code, offer_amount, offer_date_str=None):
        if offer_amount <= 0:
            raise ValueError("Offer amount must be positive.")
        offer_date = offer_date_str or datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        conn = self._get_connection()
        try:
            prop = conn.execute("SELECT id, status FROM properties WHERE listing_code = ?", (listing_code.strip().upper(),)).fetchone()
            if not prop:
                raise ValueError(f"Property '{listing_code}' not found.")
            if prop["status"] not in ("available", "under_contract"):
                raise ValueError(f"Cannot submit offer on property with status '{prop['status']}'.")

            client = conn.execute("SELECT id FROM clients WHERE client_code = ?", (client_code.strip().upper(),)).fetchone()
            if not client:
                raise ValueError(f"Client '{client_code}' not found.")

            with conn:
                cursor = conn.execute("""
                    INSERT INTO offers (property_id, client_id, offer_amount, offer_date, status)
                    VALUES (?, ?, ?, ?, 'pending')
                """, (prop["id"], client["id"], offer_amount, offer_date))
                return cursor.lastrowid
        finally:
            conn.close()

    def respond_to_offer(self, offer_id, decision, closing_date_str=None):
        decision = decision.strip().lower()
        if decision not in ("accepted", "rejected", "countered"):
            raise ValueError("Decision must be 'accepted', 'rejected', or 'countered'.")

        close_date = closing_date_str or datetime.now().strftime("%Y-%m-%d")

        conn = self._get_connection()
        try:
            offer = conn.execute("""
                SELECT o.*, p.id as prop_id, p.listing_type, p.agent_id, a.commission_rate
                FROM offers o
                JOIN properties p ON o.property_id = p.id
                LEFT JOIN agents a ON p.agent_id = a.id
                WHERE o.id = ?
            """, (offer_id,)).fetchone()
            if not offer:
                raise ValueError(f"Offer #{offer_id} not found.")

            if offer["status"] != "pending":
                raise ValueError(f"Offer #{offer_id} is already '{offer['status']}'.")

            with conn:
                if decision == "accepted":
                    rate = offer["commission_rate"] if offer["commission_rate"] is not None else 0.0
                    commission = round(offer["offer_amount"] * (rate / 100.0), 2)

                    # Update accepted offer
                    conn.execute("""
                        UPDATE offers
                        SET status = 'accepted', commission_earned = ?, closing_date = ?
                        WHERE id = ?
                    """, (commission, close_date, offer_id))

                    # Update property status
                    new_prop_status = "sold" if offer["listing_type"] == "sale" else "rented"
                    conn.execute("""
                        UPDATE properties
                        SET status = ?
                        WHERE id = ?
                    """, (new_prop_status, offer["prop_id"]))

                    # Reject any other pending offers on this property
                    conn.execute("""
                        UPDATE offers
                        SET status = 'rejected'
                        WHERE property_id = ? AND id != ? AND status = 'pending'
                    """, (offer["prop_id"], offer_id))

                    return {
                        "offer_id": offer_id,
                        "status": "accepted",
                        "property_status": new_prop_status,
                        "commission_earned": commission
                    }
                else:
                    conn.execute("UPDATE offers SET status = ? WHERE id = ?", (decision, offer_id))
                    return {"offer_id": offer_id, "status": decision}
        finally:
            conn.close()

    # ==================== Reporting & Analytics ====================

    def generate_market_report(self):
        conn = self._get_connection()
        try:
            total_properties = conn.execute("SELECT COUNT(*) as cnt FROM properties").fetchone()["cnt"]

            status_rows = conn.execute("""
                SELECT status, COUNT(*) as cnt
                FROM properties
                GROUP BY status
            """).fetchall()
            status_breakdown = {r["status"]: r["cnt"] for r in status_rows}

            type_rows = conn.execute("""
                SELECT property_type, COUNT(*) as cnt
                FROM properties
                GROUP BY property_type
            """).fetchall()
            type_breakdown = {r["property_type"]: r["cnt"] for r in type_rows}

            # Completed sales and rentals
            sales = conn.execute("""
                SELECT COALESCE(SUM(offer_amount), 0.0) as total_vol,
                       COALESCE(SUM(commission_earned), 0.0) as total_comm,
                       COUNT(*) as deals_count
                FROM offers o
                JOIN properties p ON o.property_id = p.id
                WHERE o.status = 'accepted' AND p.listing_type = 'sale'
            """).fetchone()

            rentals = conn.execute("""
                SELECT COALESCE(SUM(offer_amount), 0.0) as total_vol,
                       COALESCE(SUM(commission_earned), 0.0) as total_comm,
                       COUNT(*) as deals_count
                FROM offers o
                JOIN properties p ON o.property_id = p.id
                WHERE o.status = 'accepted' AND p.listing_type = 'rent'
            """).fetchone()

            # Average price per square foot across active properties
            avg_sqft_row = conn.execute("""
                SELECT AVG(price / area_sqft) as avg_price_per_sqft
                FROM properties
                WHERE status = 'available'
            """).fetchone()
            avg_sqft = round(avg_sqft_row["avg_price_per_sqft"], 2) if avg_sqft_row and avg_sqft_row["avg_price_per_sqft"] else 0.0

            return {
                "total_properties": total_properties,
                "status_breakdown": status_breakdown,
                "type_breakdown": type_breakdown,
                "available_count": status_breakdown.get("available", 0),
                "sold_count": status_breakdown.get("sold", 0),
                "rented_count": status_breakdown.get("rented", 0),
                "total_sales_volume": round(sales["total_vol"], 2),
                "sales_deals_closed": sales["deals_count"],
                "total_rental_volume": round(rentals["total_vol"], 2),
                "rental_deals_closed": rentals["deals_count"],
                "total_commissions_earned": round(sales["total_comm"] + rentals["total_comm"], 2),
                "avg_price_per_sqft_available": avg_sqft
            }
        finally:
            conn.close()

    def generate_agent_performance_report(self):
        conn = self._get_connection()
        try:
            agents = conn.execute("SELECT * FROM agents ORDER BY name ASC").fetchall()
            performance = []
            for ag in agents:
                agent_id = ag["id"]

                listings = conn.execute("""
                    SELECT COUNT(*) as total_listed,
                           SUM(CASE WHEN status = 'available' THEN 1 ELSE 0 END) as active_listed
                    FROM properties
                    WHERE agent_id = ?
                """, (agent_id,)).fetchone()

                closed = conn.execute("""
                    SELECT COUNT(*) as deals_closed,
                           COALESCE(SUM(o.offer_amount), 0.0) as volume_closed,
                           COALESCE(SUM(o.commission_earned), 0.0) as total_comm
                    FROM offers o
                    JOIN properties p ON o.property_id = p.id
                    WHERE p.agent_id = ? AND o.status = 'accepted'
                """, (agent_id,)).fetchone()

                performance.append({
                    "agent_code": ag["agent_code"],
                    "name": ag["name"],
                    "commission_rate_pct": ag["commission_rate"],
                    "total_listings": listings["total_listed"] or 0,
                    "active_listings": listings["active_listed"] or 0,
                    "deals_closed": closed["deals_closed"] or 0,
                    "total_volume_closed": round(closed["volume_closed"], 2),
                    "commissions_earned": round(closed["total_comm"], 2)
                })
            return performance
        finally:
            conn.close()
