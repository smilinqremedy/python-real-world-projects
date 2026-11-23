# Project 59: API Rate Limiting & Request Monitoring System

A production-grade Python web service built with **FastAPI** and **SQLite** implementing a thread-safe **Sliding Window Counter** rate limiter, API key authentication, real-time HTTP 429 throttling with `Retry-After` calculation, request latency telemetry, and administrative usage analytics.

## Features

- **API Key Authentication**: Ingests and authenticates keys via `X-API-Key` request header.
- **Sliding Window Rate Limiter**:
  - Evicts timestamps older than 60 seconds from key-specific queues.
  - Dynamically calculates exact `Retry-After` seconds until the oldest request leaves the current window.
  - Returns standard RFC rate limit headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `Retry-After`.
- **Tier-Based Limits**:
  - `free`: 5 requests/min
  - `starter`: 30 requests/min
  - `pro`: 120 requests/min
  - `unlimited`: 10,000 requests/min
- **Request Telemetry & Logging**:
  - Logs IP address, HTTP method, path, response status code, and millisecond processing time into SQLite.
- **Interactive OpenAPI & Swagger Documentation**: Auto-generated interactive API documentation at `/docs`.
- **Administrative Dashboard & Metrics**:
  - Key-level usage: total requests, successful counts, and throttled events.
  - Global overview: top API consumers and endpoint traffic breakdown.

## Database Schema

- `api_users`: User identity details (`username`, `email`).
- `api_keys`: Secure random tokens (`key_value`), subscription tier, and custom `rate_limit_per_minute`.
- `request_logs`: Timestamped audit trail of endpoint calls, client IPs, response statuses, and execution durations.

## Installation & Dependencies

Requires Python 3.10+, `fastapi`, `uvicorn`, `pydantic`, and `httpx` (for test suite).

```bash
pip install fastapi uvicorn pydantic httpx
```

## Running the Server

Start the interactive CLI:

```bash
cd 59-api-rate-limiting-monitoring
python3 main.py
```

Or run the FastAPI server directly:

```bash
uvicorn app:app --host 127.0.0.1 --port 8000 --reload
```

## Running Automated Tests

Run the integration and rate limit unit tests:

```bash
python3 -m unittest test_api.py -v
```
