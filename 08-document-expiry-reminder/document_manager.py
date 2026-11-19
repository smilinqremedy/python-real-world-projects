"""
Personal Document Expiry Reminder System - Core Logic
Manages document registration, date calculations, status tagging, filtering,
expiry reports, and JSON persistence.
"""

import json
import os
from datetime import datetime, date

DATA_FILE = "documents.json"

DEFAULT_CATEGORIES = [
    "Identification",
    "Travel",
    "Vehicle",
    "Financial & Legal",
    "Health & Insurance",
    "Professional & Certifications",
    "Housing & Utilities",
    "Other"
]


# ==========================================
# 1. STORAGE & PERSISTENCE
# ==========================================

def load_data(file_path=DATA_FILE):
    """
    Loads document records from a JSON file.
    Recovers with default empty structure if file is missing, empty, or corrupted.
    """
    if not os.path.exists(file_path):
        return {"documents": []}

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
            if not content:
                return {"documents": []}
            data = json.loads(content)
            if not isinstance(data, dict) or "documents" not in data or not isinstance(data["documents"], list):
                return {"documents": []}
            return data
    except (json.JSONDecodeError, IOError) as error:
        print(f"\n[Warning] Could not read '{file_path}' ({error}). Starting with fresh data.")
        return {"documents": []}


def save_data(data, file_path=DATA_FILE):
    """
    Saves document records to a JSON file formatted with indentation.
    """
    try:
        with open(file_path, "w", encoding="utf-8") as file:
            json.dump(data, file, indent=4)
        return True
    except IOError as error:
        print(f"\n[Error] Failed to save data to '{file_path}': {error}")
        return False


# ==========================================
# 2. VALIDATION & DATE CALCULATIONS
# ==========================================

def parse_date(date_str):
    """
    Validates and parses a date string in YYYY-MM-DD format.
    Returns datetime.date object or raises ValueError.
    """
    if not date_str or not isinstance(date_str, str):
        raise ValueError("Date string cannot be empty.")
    try:
        return datetime.strptime(date_str.strip(), "%Y-%m-%d").date()
    except ValueError:
        raise ValueError(f"Invalid date format '{date_str}'. Expected YYYY-MM-DD (e.g. 2026-11-19).")


def calculate_days_remaining(expiry_date_str, reference_date=None):
    """
    Calculates number of days remaining until expiry.
    Returns negative integer if already expired.
    """
    today = reference_date if reference_date is not None else date.today()
    exp_date = parse_date(expiry_date_str)
    return (exp_date - today).days


def evaluate_document_status(expiry_date_str, reference_date=None):
    """
    Evaluates status badge and urgency description based on days remaining.
    Statuses:
    - 'EXPIRED': days < 0
    - 'CRITICAL': 0 <= days <= 7 (Expiring within 7 days)
    - 'EXPIRING_SOON': 8 <= days <= 30 (Expiring within 30 days)
    - 'VALID': days > 30 (Healthy)
    """
    days = calculate_days_remaining(expiry_date_str, reference_date)

    if days < 0:
        return {
            "status": "EXPIRED",
            "days_remaining": days,
            "badge": "[EXPIRED]",
            "message": f"Expired {abs(days)} day(s) ago"
        }
    elif days <= 7:
        return {
            "status": "CRITICAL",
            "days_remaining": days,
            "badge": "[CRITICAL (<=7d)]",
            "message": f"Expiring in {days} day(s)" if days > 0 else "Expires TODAY!"
        }
    elif days <= 30:
        return {
            "status": "EXPIRING_SOON",
            "days_remaining": days,
            "badge": "[EXPIRING (<=30d)]",
            "message": f"Expiring in {days} day(s)"
        }
    else:
        return {
            "status": "VALID",
            "days_remaining": days,
            "badge": "[VALID]",
            "message": f"{days} days remaining"
        }


def generate_next_id(documents):
    """Generates next incremental integer ID."""
    if not documents:
        return 1
    return max(doc.get("id", 0) for doc in documents) + 1


def find_document_by_id(documents, doc_id):
    """Finds document dictionary by ID, or None if not found."""
    for d in documents:
        if d.get("id") == doc_id:
            return d
    return None


# ==========================================
# 3. REGISTRATION & UPDATING
# ==========================================

def register_document(data, name, category, issue_date_str, expiry_date_str,
                      document_number="", issuing_authority="", notes="", file_path=DATA_FILE):
    """
    Registers a new personal document with issue and expiry dates.
    Validates that expiry date is strictly after issue date.
    """
    clean_name = name.strip()
    clean_cat = category.strip()

    if not clean_name:
        raise ValueError("Document name cannot be blank.")
    if not clean_cat:
        raise ValueError("Document category cannot be blank.")

    issue_dt = parse_date(issue_date_str)
    expiry_dt = parse_date(expiry_date_str)

    if expiry_dt <= issue_dt:
        raise ValueError(f"Expiry date ({expiry_date_str}) must be after issue date ({issue_date_str}).")

    new_id = generate_next_id(data["documents"])
    now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    document = {
        "id": new_id,
        "name": clean_name,
        "category": clean_cat,
        "document_number": document_number.strip(),
        "issue_date": issue_dt.strftime("%Y-%m-%d"),
        "expiry_date": expiry_dt.strftime("%Y-%m-%d"),
        "issuing_authority": issuing_authority.strip(),
        "notes": notes.strip(),
        "created_at": now_str,
        "updated_at": now_str
    }

    data["documents"].append(document)
    save_data(data, file_path)
    return document


def update_document(data, doc_id, name=None, category=None, issue_date_str=None,
                    expiry_date_str=None, document_number=None, issuing_authority=None,
                    notes=None, file_path=DATA_FILE):
    """
    Updates editable fields of an existing document.
    """
    doc = find_document_by_id(data["documents"], doc_id)
    if not doc:
        raise ValueError(f"Document ID {doc_id} not found.")

    if name is not None and name.strip():
        doc["name"] = name.strip()
    if category is not None and category.strip():
        doc["category"] = category.strip()
    if document_number is not None:
        doc["document_number"] = document_number.strip()
    if issuing_authority is not None:
        doc["issuing_authority"] = issuing_authority.strip()
    if notes is not None:
        doc["notes"] = notes.strip()

    # Handle dates validation if updating either or both
    new_issue_str = issue_date_str if issue_date_str else doc["issue_date"]
    new_expiry_str = expiry_date_str if expiry_date_str else doc["expiry_date"]

    issue_dt = parse_date(new_issue_str)
    expiry_dt = parse_date(new_expiry_str)

    if expiry_dt <= issue_dt:
        raise ValueError(f"Expiry date ({new_expiry_str}) must be after issue date ({new_issue_str}).")

    doc["issue_date"] = issue_dt.strftime("%Y-%m-%d")
    doc["expiry_date"] = expiry_dt.strftime("%Y-%m-%d")
    doc["updated_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    save_data(data, file_path)
    return doc


def delete_document(data, doc_id, file_path=DATA_FILE):
    """Deletes a document by ID."""
    doc = find_document_by_id(data["documents"], doc_id)
    if not doc:
        raise ValueError(f"Document ID {doc_id} not found.")
    data["documents"].remove(doc)
    save_data(data, file_path)
    return doc


# ==========================================
# 4. FILTERING & SEARCH
# ==========================================

def get_expired_documents(documents, reference_date=None):
    """
    Returns all documents whose expiry date is in the past (days < 0).
    Sorted most overdue first.
    """
    today = reference_date if reference_date is not None else date.today()
    expired = []

    for d in documents:
        days = calculate_days_remaining(d["expiry_date"], today)
        if days < 0:
            d_copy = d.copy()
            d_copy["days_remaining"] = days
            expired.append(d_copy)

    expired.sort(key=lambda x: x["days_remaining"])
    return expired


def get_documents_expiring_within(documents, max_days, reference_date=None):
    """
    Returns active (non-expired) documents expiring within max_days (0 <= days <= max_days).
    Sorted by days remaining ascending (most urgent first).
    """
    today = reference_date if reference_date is not None else date.today()
    expiring = []

    for d in documents:
        days = calculate_days_remaining(d["expiry_date"], today)
        if 0 <= days <= max_days:
            d_copy = d.copy()
            d_copy["days_remaining"] = days
            expiring.append(d_copy)

    expiring.sort(key=lambda x: x["days_remaining"])
    return expiring


def search_documents(documents, query_str):
    """
    Searches documents by name, category, or document number.
    """
    q = query_str.strip().lower()
    if not q:
        return []
    return [
        d for d in documents
        if q in d.get("name", "").lower()
        or q in d.get("category", "").lower()
        or q in d.get("document_number", "").lower()
    ]


# ==========================================
# 5. EXPIRY REPORTS & ANALYTICS
# ==========================================

def generate_expiry_report_data(documents, reference_date=None):
    """
    Generates comprehensive summary metrics and categorized breakdown of documents.
    """
    today = reference_date if reference_date is not None else date.today()
    total = len(documents)

    expired_list = []
    critical_7d_list = []
    expiring_30d_list = []
    valid_list = []
    category_counts = {}

    for d in documents:
        cat = d.get("category", "Other")
        category_counts[cat] = category_counts.get(cat, 0) + 1

        eval_res = evaluate_document_status(d["expiry_date"], today)
        status = eval_res["status"]

        d_entry = d.copy()
        d_entry["days_remaining"] = eval_res["days_remaining"]
        d_entry["badge"] = eval_res["badge"]
        d_entry["message"] = eval_res["message"]

        if status == "EXPIRED":
            expired_list.append(d_entry)
        elif status == "CRITICAL":
            critical_7d_list.append(d_entry)
        elif status == "EXPIRING_SOON":
            expiring_30d_list.append(d_entry)
        else:
            valid_list.append(d_entry)

    # Sort each group by urgency
    expired_list.sort(key=lambda x: x["days_remaining"])
    critical_7d_list.sort(key=lambda x: x["days_remaining"])
    expiring_30d_list.sort(key=lambda x: x["days_remaining"])
    valid_list.sort(key=lambda x: x["days_remaining"])

    return {
        "report_date": today.strftime("%Y-%m-%d"),
        "total_documents": total,
        "counts": {
            "expired": len(expired_list),
            "critical_7d": len(critical_7d_list),
            "expiring_30d": len(expiring_30d_list),
            "valid": len(valid_list)
        },
        "expired_documents": expired_list,
        "critical_7d_documents": critical_7d_list,
        "expiring_30d_documents": expiring_30d_list,
        "valid_documents": valid_list,
        "category_counts": category_counts
    }
