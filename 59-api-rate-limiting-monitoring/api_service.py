"""
Service layer for API user registration, key issuance, request logging, and analytics.
"""
import secrets
from typing import Optional, Dict, List, Any
from database import get_connection, init_db


class APIService:
    TIER_LIMITS = {
        "free": 5,          # 5 requests per minute
        "starter": 30,      # 30 requests per minute
        "pro": 120,         # 120 requests per minute
        "unlimited": 10000, # effectively unmetered
    }

    def __init__(self, db_path=None):
        self.db_path = db_path
        init_db(self.db_path)

    def _get_connection(self):
        return get_connection(self.db_path)

    def register_user(self, username: str, email: str, tier: str = "free") -> Dict[str, Any]:
        username = username.strip().lower()
        email = email.strip().lower()
        tier = tier.strip().lower()
        if tier not in self.TIER_LIMITS:
            tier = "free"

        limit = self.TIER_LIMITS[tier]
        api_key = f"ak_{tier}_{secrets.token_urlsafe(24)}"

        conn = self._get_connection()
        try:
            with conn:
                cursor = conn.execute(
                    "INSERT INTO api_users (username, email) VALUES (?, ?)",
                    (username, email)
                )
                user_id = cursor.lastrowid

                conn.execute(
                    """
                    INSERT INTO api_keys (user_id, key_value, tier, rate_limit_per_minute)
                    VALUES (?, ?, ?, ?)
                    """,
                    (user_id, api_key, tier, limit)
                )

                return {
                    "user_id": user_id,
                    "username": username,
                    "email": email,
                    "api_key": api_key,
                    "tier": tier,
                    "rate_limit_per_minute": limit,
                }
        finally:
            conn.close()

    def get_api_key_details(self, key_value: str) -> Optional[Dict[str, Any]]:
        conn = self._get_connection()
        try:
            row = conn.execute(
                """
                SELECT k.id as key_id, k.key_value, k.tier, k.rate_limit_per_minute, k.is_active,
                       u.id as user_id, u.username, u.email
                FROM api_keys k
                JOIN api_users u ON k.user_id = u.id
                WHERE k.key_value = ?
                """,
                (key_value,)
            ).fetchone()
            return dict(row) if row else None
        finally:
            conn.close()

    def log_request(self, api_key_id: Optional[int], endpoint: str, method: str,
                    status_code: int, ip_address: Optional[str], duration_ms: float):
        conn = self._get_connection()
        try:
            with conn:
                conn.execute(
                    """
                    INSERT INTO request_logs (api_key_id, endpoint, method, status_code, ip_address, duration_ms)
                    VALUES (?, ?, ?, ?, ?, ?)
                    """,
                    (api_key_id, endpoint, method, status_code, ip_address, round(duration_ms, 2))
                )
        finally:
            conn.close()

    def get_usage_metrics(self, key_value: str) -> Dict[str, Any]:
        key_details = self.get_api_key_details(key_value)
        if not key_details:
            return {"error": "Key not found"}

        conn = self._get_connection()
        try:
            key_id = key_details["key_id"]
            total_requests = conn.execute(
                "SELECT count(*) FROM request_logs WHERE api_key_id = ?", (key_id,)
            ).fetchone()[0]

            successful = conn.execute(
                "SELECT count(*) FROM request_logs WHERE api_key_id = ? AND status_code >= 200 AND status_code < 300",
                (key_id,)
            ).fetchone()[0]

            throttled = conn.execute(
                "SELECT count(*) FROM request_logs WHERE api_key_id = ? AND status_code = 429",
                (key_id,)
            ).fetchone()[0]

            recent_logs = conn.execute(
                """
                SELECT endpoint, method, status_code, duration_ms, timestamp
                FROM request_logs
                WHERE api_key_id = ?
                ORDER BY timestamp DESC LIMIT 10
                """,
                (key_id,)
            ).fetchall()

            return {
                "key_value": key_value[:10] + "...",
                "tier": key_details["tier"],
                "rate_limit_per_minute": key_details["rate_limit_per_minute"],
                "total_requests": total_requests,
                "successful_requests": successful,
                "throttled_requests": throttled,
                "recent_requests": [dict(r) for r in recent_logs]
            }
        finally:
            conn.close()

    def get_admin_dashboard(self) -> Dict[str, Any]:
        conn = self._get_connection()
        try:
            total_users = conn.execute("SELECT count(*) FROM api_users").fetchone()[0]
            total_keys = conn.execute("SELECT count(*) FROM api_keys").fetchone()[0]
            total_requests = conn.execute("SELECT count(*) FROM request_logs").fetchone()[0]
            throttled_requests = conn.execute("SELECT count(*) FROM request_logs WHERE status_code = 429").fetchone()[0]

            endpoint_stats = conn.execute(
                """
                SELECT endpoint, count(*) as count, round(avg(duration_ms), 2) as avg_duration_ms
                FROM request_logs
                GROUP BY endpoint
                ORDER BY count DESC
                """
            ).fetchall()

            top_keys = conn.execute(
                """
                SELECT k.key_value, u.username, k.tier, count(r.id) as request_count
                FROM request_logs r
                JOIN api_keys k ON r.api_key_id = k.id
                JOIN api_users u ON k.user_id = u.id
                GROUP BY k.id
                ORDER BY request_count DESC LIMIT 5
                """
            ).fetchall()

            return {
                "total_users": total_users,
                "total_keys": total_keys,
                "total_requests": total_requests,
                "throttled_requests": throttled_requests,
                "endpoint_breakdown": [dict(r) for r in endpoint_stats],
                "top_consumers": [
                    {
                        "key": r["key_value"][:12] + "...",
                        "username": r["username"],
                        "tier": r["tier"],
                        "requests": r["request_count"]
                    } for r in top_keys
                ]
            }
        finally:
            conn.close()
