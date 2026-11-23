"""
FastAPI application with API Key authentication, Sliding Window rate limiting, and request monitoring.
"""
import time
import re
from typing import Optional
from fastapi import FastAPI, Request, Response, Header, HTTPException, Depends, status
from pydantic import BaseModel
from database import init_db
from rate_limiter import SlidingWindowRateLimiter
from api_service import APIService

app = FastAPI(
    title="API Rate Limiting & Request Monitoring System",
    description="High-performance API with per-key sliding window rate limits, real-time throttling, and analytics logging.",
    version="1.0.0"
)

# Shared service and limiter instances
service = APIService()
limiter = SlidingWindowRateLimiter(window_seconds=60)


class RegisterRequest(BaseModel):
    username: str
    email: str
    tier: Optional[str] = "free"


# Dependency for API key authentication & rate limiting
async def authenticate_and_rate_limit(
    request: Request,
    x_api_key: Optional[str] = Header(None, alias="X-API-Key")
):
    start_time = time.time()
    endpoint = request.url.path
    method = request.method
    client_ip = request.client.host if request.client else "127.0.0.1"

    if not x_api_key:
        duration_ms = (time.time() - start_time) * 1000
        service.log_request(None, endpoint, method, 401, client_ip, duration_ms)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Missing required 'X-API-Key' header."
        )

    key_details = service.get_api_key_details(x_api_key)
    if not key_details or not key_details["is_active"]:
        duration_ms = (time.time() - start_time) * 1000
        service.log_request(None, endpoint, method, 403, client_ip, duration_ms)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid or revoked API key."
        )

    # Check Rate Limit
    max_reqs = key_details["rate_limit_per_minute"]
    allowed, remaining, retry_after = limiter.check_and_record(x_api_key, max_reqs)

    if not allowed:
        duration_ms = (time.time() - start_time) * 1000
        service.log_request(key_details["key_id"], endpoint, method, 429, client_ip, duration_ms)
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Tier '{key_details['tier']}' permits {max_reqs} requests/min.",
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(max_reqs),
                "X-RateLimit-Remaining": "0",
            }
        )

    # Store for endpoint use and logging
    request.state.key_details = key_details
    request.state.start_time = start_time
    request.state.remaining = remaining
    request.state.limit = max_reqs
    return key_details


@app.middleware("http")
async def monitor_requests(request: Request, call_next):
    start_time = time.time()
    response = await call_next(request)
    duration_ms = (time.time() - start_time) * 1000

    # Inject rate limit headers if available on request state
    if hasattr(request.state, "limit"):
        response.headers["X-RateLimit-Limit"] = str(request.state.limit)
        response.headers["X-RateLimit-Remaining"] = str(request.state.remaining)

    # If the request was authenticated, log successful execution
    if hasattr(request.state, "key_details"):
        key_id = request.state.key_details["key_id"]
        client_ip = request.client.host if request.client else "127.0.0.1"
        service.log_request(
            key_id, request.url.path, request.method, response.status_code, client_ip, duration_ms
        )

    return response


# ==================== Public Endpoints ====================

@app.get("/")
def health_check():
    return {
        "status": "online",
        "service": "API Rate Limiting & Request Monitoring Engine",
        "docs_url": "/docs"
    }


@app.post("/api/v1/auth/register", status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest):
    try:
        data = service.register_user(req.username, req.email, req.tier or "free")
        return {
            "message": "User registered successfully. Keep your API key secure.",
            "data": data
        }
    except Exception as e:
        if "UNIQUE constraint" in str(e):
            raise HTTPException(status_code=400, detail="Username or email already exists.")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/v1/admin/dashboard")
def admin_dashboard():
    """Administrative analytics and traffic dashboard."""
    return service.get_admin_dashboard()


# ==================== Protected Endpoints ====================

@app.get("/api/v1/data/ping")
def ping(auth=Depends(authenticate_and_rate_limit)):
    return {
        "message": "pong",
        "user": auth["username"],
        "tier": auth["tier"]
    }


@app.get("/api/v1/data/resources")
def get_resources(auth=Depends(authenticate_and_rate_limit)):
    return {
        "user": auth["username"],
        "resources": [
            {"id": 1, "name": "Payment Gateway API", "status": "active"},
            {"id": 2, "name": "SMS Delivery Engine", "status": "active"},
            {"id": 3, "name": "KYC Verification Service", "status": "active"},
        ]
    }


@app.get("/api/v1/metrics/usage")
def get_usage(auth=Depends(authenticate_and_rate_limit)):
    return service.get_usage_metrics(auth["key_value"])
