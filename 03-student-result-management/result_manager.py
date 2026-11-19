"""
Student Result Management System - Core Logic
Handles student registration, score recording, calculations, grading rules,
statistical summaries, ranking, search, and JSON persistence.
"""

import json
import os
from datetime import datetime

DATA_FILE = "results_data.json"

DEFAULT_GRADING_SCALE = [
    {"min_score": 70.0, "grade": "A", "remark": "Distinction"},
    {"min_score": 60.0, "grade": "B", "remark": "Very Good"},
    {"min_score": 50.0, "grade": "C", "remark": "Credit"},
    {"min_score": 45.0, "grade": "D", "remark": "Pass"},
    {"min_score": 40.0, "grade": "E", "remark": "Fair"},
    {"min_score": 0.0,  "grade": "F", "remark": "Fail"}
]

DEFAULT_SUBJECTS = [
    "Mathematics",
    "English Language",
    "Biology",
    "Chemistry",
    "Physics",
    "Economics",
    "Civic Education",
    "Geography",
    "Literature in English"
]


# ==========================================
# 1. STORAGE & PERSISTENCE
# ==========================================

def load_data(file_path=DATA_FILE):
    """
    Loads student result data from a JSON file.
    Recovers with default empty structure if file is missing, empty, or corrupted.
    """
    if not os.path.exists(file_path):
        return {
            "grading_scale": DEFAULT_GRADING_SCALE.copy(),
            "students": []
        }

    try:
        with open(file_path, "r", encoding="utf-8") as file:
            content = file.read().strip()
            if not content:
                return {"grading_scale": DEFAULT_GRADING_SCALE.copy(), "students": []}
            data = json.loads(content)
            if not isinstance(data, dict):
                return {"grading_scale": DEFAULT_GRADING_SCALE.copy(), "students": []}
            if "grading_scale" not in data or not isinstance(data["grading_scale"], list):
                data["grading_scale"] = DEFAULT_GRADING_SCALE.copy()
            if "students" not in data or not isinstance(data["students"], list):
                data["students"] = []
            return data
    except (json.JSONDecodeError, IOError) as error:
        print(f"\n[Warning] Could not read '{file_path}' ({error}). Starting with fresh data.")
        return {"grading_scale": DEFAULT_GRADING_SCALE.copy(), "students": []}


def save_data(data, file_path=DATA_FILE):
    """
    Saves student result data to a JSON file formatted with indentation.
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

def validate_score(score):
    """
    Validates that a score is a numeric value between 0.0 and 100.0 inclusive.
    Returns (True, score_float) if valid, or (False, error_message).
    """
    try:
        val = float(score)
        if 0.0 <= val <= 100.0:
            return True, round(val, 2)
        return False, f"Score must be between 0 and 100. Received: {val}"
    except (ValueError, TypeError):
        return False, "Score must be a valid numeric value."


def get_valid_score(prompt_text):
    """
    Prompts user until a valid score between 0 and 100 is provided.
    """
    while True:
        user_input = input(prompt_text).strip()
        is_valid, result = validate_score(user_input)
        if is_valid:
            return result
        print(f"  [Error] {result}")


def get_non_empty_string(prompt_text, default=None):
    """
    Prompts user for text, ensuring it is not empty.
    """
    while True:
        display_prompt = f"{prompt_text} [default: {default}]: " if default is not None else f"{prompt_text}: "
        user_input = input(display_prompt).strip()

        if not user_input and default is not None:
            return default
        if user_input:
            return user_input
        print("  [Error] Input cannot be blank.")


def generate_unique_reg_number(students, prefix="REG"):
    """
    Generates a unique registration number formatted like REG-2026-001.
    """
    year = datetime.now().year
    existing_nums = []

    for s in students:
        reg = s.get("reg_number", "")
        if reg.startswith(f"{prefix}-{year}-"):
            try:
                num_part = int(reg.split("-")[-1])
                existing_nums.append(num_part)
            except ValueError:
                pass

    next_num = max(existing_nums, default=0) + 1
    return f"{prefix}-{year}-{next_num:03d}"


# ==========================================
# 3. STUDENT REGISTRATION & SEARCH
# ==========================================

def register_student(data, name, class_level="SS 1", file_path=DATA_FILE):
    """
    Registers a new student, assigns a unique registration number, and saves to JSON.
    """
    clean_name = name.strip().title()
    reg_number = generate_unique_reg_number(data["students"])

    student = {
        "reg_number": reg_number,
        "name": clean_name,
        "class_level": class_level.strip(),
        "scores": {}  # Format: {"Subject": score_float}
    }

    data["students"].append(student)
    save_data(data, file_path)
    return student


def search_student_by_reg_number(students, reg_number):
    """
    Finds a student by exact registration number (case-insensitive).
    """
    query = reg_number.strip().upper()
    for student in students:
        if student.get("reg_number", "").upper() == query:
            return student
    return None


def search_students_by_query(students, query_str):
    """
    Searches students matching registration number or name (partial, case-insensitive).
    """
    q = query_str.strip().lower()
    matches = []
    for s in students:
        if q in s.get("reg_number", "").lower() or q in s.get("name", "").lower():
            matches.append(s)
    return matches


# ==========================================
# 4. SUBJECT SCORES & GRADING LOGIC
# ==========================================

def record_subject_score(data, reg_number, subject, score, file_path=DATA_FILE):
    """
    Records or updates a validated score for a student's subject.
    """
    student = search_student_by_reg_number(data["students"], reg_number)
    if not student:
        return False, f"Student with registration number '{reg_number}' not found."

    is_valid, validated_score = validate_score(score)
    if not is_valid:
        return False, validated_score

    clean_subject = subject.strip().title()
    student["scores"][clean_subject] = validated_score
    save_data(data, file_path)
    return True, f"Recorded score of {validated_score:.1f}% in '{clean_subject}' for {student['name']}."


def assign_grade(score, grading_scale=None):
    """
    Assigns a letter grade and remark based on configurable grading rules.
    Grading rules are sorted by min_score descending.
    """
    scale = grading_scale if grading_scale is not None else DEFAULT_GRADING_SCALE
    # Ensure scale is evaluated from highest threshold to lowest
    sorted_scale = sorted(scale, key=lambda rule: rule["min_score"], reverse=True)

    for rule in sorted_scale:
        if score >= rule["min_score"]:
            return rule["grade"], rule["remark"]

    return "F", "Fail"


# ==========================================
# 5. CALCULATIONS & PERFORMANCE METRICS
# ==========================================

def calculate_student_metrics(student, grading_scale=None):
    """
    Calculates total score, average score, and overall grade for a single student.
    Returns a dictionary of metrics.
    """
    scores = student.get("scores", {})
    if not scores:
        return {
            "total_score": 0.0,
            "subject_count": 0,
            "average_score": 0.0,
            "overall_grade": "N/A",
            "overall_remark": "No scores recorded",
            "subject_details": []
        }

    total_score = sum(scores.values())
    subject_count = len(scores)
    average_score = round(total_score / subject_count, 2)
    overall_grade, overall_remark = assign_grade(average_score, grading_scale)

    subject_details = []
    for subject, score in scores.items():
        grade, remark = assign_grade(score, grading_scale)
        subject_details.append({
            "subject": subject,
            "score": score,
            "grade": grade,
            "remark": remark
        })

    return {
        "total_score": round(total_score, 2),
        "subject_count": subject_count,
        "average_score": average_score,
        "overall_grade": overall_grade,
        "overall_remark": overall_remark,
        "subject_details": subject_details
    }


def rank_students(students, grading_scale=None):
    """
    Ranks students based on their average score (descending).
    Returns a list of tuples: (student, rank, metrics)
    """
    scored_students = []
    unscored_students = []

    for s in students:
        metrics = calculate_student_metrics(s, grading_scale)
        if metrics["subject_count"] > 0:
            scored_students.append((s, metrics))
        else:
            unscored_students.append((s, metrics))

    # Sort scored students descending by average score
    scored_students.sort(key=lambda item: item[1]["average_score"], reverse=True)

    ranked_list = []
    for rank_idx, (s, metrics) in enumerate(scored_students, start=1):
        ranked_list.append((s, rank_idx, metrics))

    for s, metrics in unscored_students:
        ranked_list.append((s, "-", metrics))

    return ranked_list


def get_highest_performing_student(students, grading_scale=None):
    """
    Determines the student with the highest average score.
    Returns (student, metrics) or None.
    """
    ranked = rank_students(students, grading_scale)
    scored = [item for item in ranked if item[1] != "-"]
    if not scored:
        return None
    return scored[0][0], scored[0][2]


def get_lowest_performing_student(students, grading_scale=None):
    """
    Determines the student with the lowest average score (among those with recorded scores).
    Returns (student, metrics) or None.
    """
    ranked = rank_students(students, grading_scale)
    scored = [item for item in ranked if item[1] != "-"]
    if not scored:
        return None
    return scored[-1][0], scored[-1][2]


# ==========================================
# 6. REPORT GENERATION & SUMMARIES
# ==========================================

def generate_individual_report_card(student, class_rank="-", total_students=0, grading_scale=None):
    """
    Generates and displays a formal student academic result report.
    """
    metrics = calculate_student_metrics(student, grading_scale)

    print("\n" + "=" * 65)
    print("           SECONDARY SCHOOL ACADEMIC RESULT REPORT")
    print("=" * 65)
    print(f" Student Name:    {student['name']:<25} Reg No: {student['reg_number']}")
    print(f" Class:           {student.get('class_level', 'N/A'):<25} Position: {class_rank}/{total_students}")
    print("-" * 65)
    print(f"{'Subject':<25} | {'Score (%)':<10} | {'Grade':<8} | {'Remark'}")
    print("-" * 65)

    if not metrics["subject_details"]:
        print("  [No subject scores recorded yet for this student]")
    else:
        for sub in metrics["subject_details"]:
            print(f"{sub['subject']:<25} | {sub['score']:>8.1f}%  | {sub['grade']:<8} | {sub['remark']}")

    print("-" * 65)
    print(f" Total Score:     {metrics['total_score']:>8.1f} / {metrics['subject_count'] * 100}")
    print(f" Average Score:   {metrics['average_score']:>8.1f}%")
    print(f" Overall Grade:   {metrics['overall_grade']} ({metrics['overall_remark']})")
    print("=" * 65)


def generate_class_performance_summary(students, grading_scale=None):
    """
    Generates and displays an aggregate class performance report including:
    - Total students and recorded count
    - Class average, highest and lowest scores
    - Subject-by-subject average scores
    - Overall grade distribution
    """
    if not students:
        print("\nNo students registered in the system.")
        return

    ranked = rank_students(students, grading_scale)
    scored_students = [item for item in ranked if item[1] != "-"]

    print("\n" + "=" * 65)
    print("            CLASS PERFORMANCE SUMMARY REPORT")
    print("=" * 65)
    print(f" Total Students Registered:   {len(students):>6}")
    print(f" Students with Results:       {len(scored_students):>6}")

    if not scored_students:
        print("\nNo subject scores recorded for any student yet.")
        print("=" * 65)
        return

    # Calculate overall class average
    all_averages = [item[2]["average_score"] for item in scored_students]
    class_average = sum(all_averages) / len(all_averages)
    highest_student, highest_metrics = scored_students[0][0], scored_students[0][2]
    lowest_student, lowest_metrics = scored_students[-1][0], scored_students[-1][2]

    print(f" Class Average Score:         {class_average:>6.2f}%")
    print("-" * 65)
    print(f" Highest Performing Student:  {highest_student['name']} ({highest_student['reg_number']})")
    print(f"   Score: {highest_metrics['average_score']:.2f}% | Grade: {highest_metrics['overall_grade']}")
    print(f" Lowest Performing Student:   {lowest_student['name']} ({lowest_student['reg_number']})")
    print(f"   Score: {lowest_metrics['average_score']:.2f}% | Grade: {lowest_metrics['overall_grade']}")
    print("=" * 65)

    # Grade Distribution
    grade_counts = {}
    for item in scored_students:
        g = item[2]["overall_grade"]
        grade_counts[g] = grade_counts.get(g, 0) + 1

    print("\n--- Overall Grade Distribution ---")
    scale = grading_scale if grading_scale is not None else DEFAULT_GRADING_SCALE
    for rule in sorted(scale, key=lambda r: r["min_score"], reverse=True):
        count = grade_counts.get(rule["grade"], 0)
        pct = (count / len(scored_students) * 100) if scored_students else 0.0
        bar = "#" * int(pct // 5)
        print(f" Grade {rule['grade']} ({rule['min_score']:>2.0f}%+ | {rule['remark']:<11}): {count:>3} students ({pct:>5.1f}%) {bar}")

    # Subject-by-Subject Averages
    subject_scores = {}
    for s in students:
        for subj, sc in s.get("scores", {}).items():
            if subj not in subject_scores:
                subject_scores[subj] = []
            subject_scores[subj].append(sc)

    print("\n--- Subject-by-Subject Performance ---")
    print(f"{'Subject':<25} | {'Enrolled':<9} | {'Average Score':<14} | {'Grade'}")
    print("-" * 65)
    for subj, sc_list in sorted(subject_scores.items()):
        sub_avg = sum(sc_list) / len(sc_list)
        sub_grade, _ = assign_grade(sub_avg, grading_scale)
        print(f"{subj:<25} | {len(sc_list):<9} | {sub_avg:>10.2f}%   | {sub_grade}")

    print("=" * 65)


def display_all_students_table(students, grading_scale=None):
    """
    Displays all registered students in a formatted roster with their rank, total, and average.
    """
    if not students:
        print("\nNo students registered yet.")
        return

    ranked = rank_students(students, grading_scale)
    total_students = len(students)

    print("\n" + "=" * 80)
    print(f"{'Rank':<5} | {'Reg No':<14} | {'Student Name':<22} | {'Class':<8} | {'Total':<7} | {'Average':<8} | {'Grade'}")
    print("-" * 80)

    for s, rank, metrics in ranked:
        reg = s.get("reg_number", "-")
        name = s.get("name", "Unknown")[:22]
        cls = s.get("class_level", "-")[:8]
        tot = f"{metrics['total_score']:.1f}" if metrics["subject_count"] > 0 else "-"
        avg = f"{metrics['average_score']:.1f}%" if metrics["subject_count"] > 0 else "-"
        grd = metrics["overall_grade"]

        print(f"{str(rank):<5} | {reg:<14} | {name:<22} | {cls:<8} | {tot:<7} | {avg:<8} | {grd}")

    print("=" * 80)
