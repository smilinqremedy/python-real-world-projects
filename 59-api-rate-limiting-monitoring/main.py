"""
Server launcher and CLI management utility for API Rate Limiting & Monitoring System.
"""
import sys
import uvicorn
from api_service import APIService


def print_banner(title: str):
    print("\n" + "=" * 65)
    print(f" {title.upper()} ")
    print("=" * 65)


def cli():
    service = APIService()

    while True:
        print_banner("API Rate Limiting & Request Monitoring")
        print("1. Start FastAPI Server (uvicorn on port 8000)")
        print("2. Register New User & Generate API Key")
        print("3. View Admin Traffic & Rate Limit Dashboard")
        print("4. Inspect API Key Usage Metrics")
        print("0. Exit")

        choice = input("\nSelect an option [0-4]: ").strip()

        if choice == "1":
            print("\nStarting Uvicorn Server at http://127.0.0.1:8000 ...")
            print("Access Swagger API Docs at: http://127.0.0.1:8000/docs")
            uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)

        elif choice == "2":
            print_banner("Register API User")
            username = input("Username: ").strip()
            email = input("Email: ").strip()
            print("Select Tier:")
            print("  - free       (5 requests / min)")
            print("  - starter    (30 requests / min)")
            print("  - pro        (120 requests / min)")
            print("  - unlimited  (10,000 requests / min)")
            tier = input("Tier [free]: ").strip() or "free"
            try:
                res = service.register_user(username, email, tier)
                print("\n[SUCCESS] API Key Generated Successfully!")
                print(f"User:       {res['username']}")
                print(f"Email:      {res['email']}")
                print(f"Tier:       {res['tier']}")
                print(f"Limit:      {res['rate_limit_per_minute']} req/min")
                print(f"API Key:    {res['api_key']}")
                print("\nPass this header in requests: X-API-Key: " + res['api_key'])
            except Exception as e:
                print(f"Error: {e}")

        elif choice == "3":
            print_banner("System Dashboard")
            stats = service.get_admin_dashboard()
            print(f"Registered Users:     {stats['total_users']}")
            print(f"Active API Keys:      {stats['total_keys']}")
            print(f"Total Requests:       {stats['total_requests']}")
            print(f"Throttled Requests:   {stats['throttled_requests']}")

            print("\nTraffic by Endpoint:")
            for ep in stats["endpoint_breakdown"]:
                print(f"  {ep['endpoint']}: {ep['count']} requests (avg: {ep['avg_duration_ms']} ms)")

            print("\nTop API Consumers:")
            for c in stats["top_consumers"]:
                print(f"  Key {c['key']} ({c['username']} - {c['tier']}): {c['requests']} calls")

        elif choice == "4":
            print_banner("Inspect Key Metrics")
            key = input("Enter API Key: ").strip()
            metrics = service.get_usage_metrics(key)
            if "error" in metrics:
                print(f"Error: {metrics['error']}")
            else:
                print(f"Tier:           {metrics['tier']}")
                print(f"Limit:          {metrics['rate_limit_per_minute']} req/min")
                print(f"Total Requests: {metrics['total_requests']}")
                print(f"Successful:     {metrics['successful_requests']}")
                print(f"Throttled:      {metrics['throttled_requests']}")

        elif choice == "0":
            print("Goodbye!")
            sys.exit(0)
        else:
            print("Invalid selection.")


if __name__ == "__main__":
    if len(sys.argv) > 1 and sys.argv[1] == "--serve":
        uvicorn.run("app:app", host="127.0.0.1", port=8000, reload=False)
    else:
        cli()
