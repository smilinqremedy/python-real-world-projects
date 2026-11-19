"""
Job Application Tracker - Core Business Logic
Handles JSON storage, data validation, status progression, interview scheduling,
company searches, and conversion funnel analytics.
"""

import json
import os
from datetime import datetime

DATA_FILE = "applications.json"

VALID_STATUSES = [
    "Applied",
    "Assessment",
    "Interview",
    "Offered",
    "Rejected"
]


# ==========================================
# 1. STORAGE & PERSISTENCE
# ==========================================

def load_data(file_path=DATA_FILE):
    """
    Loads job applications from a JSON file.
    Recovers with default empty structure if file is missing, empty, or corrupted.
    """
    if not os.path.exists(file_path):
        return {"applications": []}

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
            if not content:
                return {"applications": []}
            data = json.loads(content)
            if not isinstance(data, dict) or "applications" not in data or not isinstance(data["applications"], list):
                return {"applications": []}
            return data
    except (json.JSONDecodeError, IOError) as error:
        print(f"\n[Warning] Could not read '{file_path}' ({error}). Starting with fresh data.")
        return {"applications": []}


def save_data(data, file_path=DATA_FILE):
    """
    Saves job applications to a JSON file formatted with indentation.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        return True
    except IOError as error:
        print(f"\n[Error] Failed to save data to '{file_path}': {error}")
        return False


# ==========================================
# 2. VALIDATION & HELPERS
# ==========================================

def validate_date_string(date_str, allow_datetime=False):
    """
    Validates date string in YYYY-MM-DD or optionally YYYY-MM-DD HH:MM format.
    Returns normalized string if valid, otherwise raises ValueError.
    """
    cleaned = date_str.strip()
    if allow_datetime and len(cleaned) > 10:
        for fmt in ("%Y-%m-%d %H:%M", "%Y-%m-%d %I:%M %p"):
            try:
                dt = datetime.strptime(cleaned, fmt)
                return dt.strftime("%Y-%m-%d %H:%M")
            except ValueError:
                pass
    try:
        dt = datetime.strptime(cleaned, "%Y-%m-%d")
        return dt.strftime("%Y-%m-%d")
    except ValueError:
        expected = "YYYY-MM-DD (or YYYY-MM-DD HH:MM)" if allow_datetime else "YYYY-MM-DD"
        raise ValueError(f"Invalid date format '{date_str}'. Expected {expected}.")


def generate_next_id(applications):
    """
    Generates a unique incremental integer ID for a new job application.
    """
    if not applications:
        return 1
    return max(app.get("id", 0) for app in applications) + 1


def find_application_by_id(applications, app_id):
    """
    Finds and returns an application dictionary by ID, or None if not found.
    """
    for app in applications:
        if app.get("id") == app_id:
            return app
    return None


# ==========================================
# 3. APPLICATION CRUD & STATUS TRACKING
# ==========================================

def add_application(data, company, job_title, application_date=None, job_description="",
                    application_link="", status="Applied", interview_date=None, notes="", file_path=DATA_FILE):
    """
    Adds a new job application to the tracking list and saves to JSON.
    """
    company_clean = company.strip()
    title_clean = job_title.strip()

    if not company_clean:
        raise ValueError("Company name cannot be blank.")
    if not title_clean:
        raise ValueError("Job title cannot be blank.")

    app_date = validate_date_string(application_date) if application_date else datetime.today().strftime("%Y-%m-%d")

    if status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{status}'. Allowed statuses: {', '.join(VALID_STATUSES)}")

    inv_date = validate_date_string(interview_date, allow_datetime=True) if interview_date else None
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    new_id = generate_next_id(data["applications"])
    application = {
        "id": new_id,
        "company": company_clean,
        "job_title": title_clean,
        "application_date": app_date,
        "job_description": job_description.strip(),
        "application_link": application_link.strip(),
        "status": status,
        "interview_date": inv_date,
        "notes": notes.strip(),
        "created_at": now_str,
        "updated_at": now_str
    }

    data["applications"].append(application)
    save_data(data, file_path)
    return application


def update_application_status(data, app_id, new_status, interview_date=None, notes=None, file_path=DATA_FILE):
    """
    Updates the stage/status of an existing job application.
    """
    app = find_application_by_id(data["applications"], app_id)
    if not app:
        raise ValueError(f"Application ID {app_id} not found.")

    if new_status not in VALID_STATUSES:
        raise ValueError(f"Invalid status '{new_status}'. Allowed: {', '.join(VALID_STATUSES)}")

    app["status"] = new_status
    if interview_date:
        app["interview_date"] = validate_date_string(interview_date, allow_datetime=True)
    if notes is not None:
        app["notes"] = notes.strip()

    app["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data, file_path)
    return app


def update_application_details(data, app_id, company=None, job_title=None, job_description=None,
                               application_link=None, interview_date=None, notes=None, file_path=DATA_FILE):
    """
    Updates editable fields of an existing application.
    """
    app = find_application_by_id(data["applications"], app_id)
    if not app:
        raise ValueError(f"Application ID {app_id} not found.")

    if company is not None and company.strip():
        app["company"] = company.strip()
    if job_title is not None and job_title.strip():
        app["job_title"] = job_title.strip()
    if job_description is not None:
        app["job_description"] = job_description.strip()
    if application_link is not None:
        app["application_link"] = application_link.strip()
    if interview_date is not None:
        app["interview_date"] = validate_date_string(interview_date, allow_datetime=True) if interview_date.strip() else None
    if notes is not None:
        app["notes"] = notes.strip()

    app["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    save_data(data, file_path)
    return app


# ==========================================
# 4. SEARCH & FILTERING
# ==========================================

def search_applications_by_company(applications, company_query):
    """
    Searches applications by company name (case-insensitive substring match).
    """
    query = company_query.strip().lower()
    if not query:
        return []
    return [app for app in applications if query in app.get("company", "").lower()]


def get_upcoming_interviews(applications):
    """
    Returns upcoming interviews sorted chronologically ascending.
    Filters applications with interview_date >= today's date.
    """
    today_str = datetime.today().strftime("%Y-%m-%d")
    upcoming = []

    for app in applications:
        inv_date = app.get("interview_date")
        if inv_date:
            date_prefix = inv_date[:10]
            if date_prefix >= today_str:
                upcoming.append(app)

    # Sort chronologically by interview_date ascending
    upcoming.sort(key=lambda x: x["interview_date"])
    return upcoming


# ==========================================
# 5. METRICS & SUCCESS STATISTICS
# ==========================================

def calculate_application_statistics(applications):
    """
    Computes total applications, count per status, and conversion funnel rates.
    """
    total = len(applications)
    status_counts = {status: 0 for status in VALID_STATUSES}

    for app in applications:
        st = app.get("status", "Applied")
        if st in status_counts:
            status_counts[st] += 1
        else:
            status_counts[st] = 1

    applied = status_counts.get("Applied", 0)
    assessment = status_counts.get("Assessment", 0)
    interview = status_counts.get("Interview", 0)
    offered = status_counts.get("Offered", 0)
    rejected = status_counts.get("Rejected", 0)

    # Funnel Rates
    interview_rate = round(((interview + offered) / total * 100), 1) if total > 0 else 0.0
    offer_rate = round((offered / total * 100), 1) if total > 0 else 0.0
    rejection_rate = round((rejected / total * 100), 1) if total > 0 else 0.0
    active_pipeline = applied + assessment + interview

    return {
        "total_applications": total,
        "active_pipeline": active_pipeline,
        "status_counts": status_counts,
        "interview_rate_pct": interview_rate,
        "offer_rate_pct": offer_rate,
        "rejection_rate_pct": rejection_rate
    }
