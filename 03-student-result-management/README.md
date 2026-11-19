# Secondary School Student Result Management System

A robust, modular, command-line academic grading and report generation system built in Python for secondary schools.

---

## 📌 Problem the Project Solves

Secondary schools often face immense operational challenges when managing student examination results manually:
- **Error-Prone Calculations**: Manual arithmetic often leads to mistakes in total and average score computations.
- **Slow Report Generation**: Compiling individual student term reports, calculating overall class rankings, and determining grade boundaries manually is time-consuming and tedious.
- **Data Inconsistency**: Unvalidated scores (e.g., negative marks or scores above 100) and lost paper records undermine academic integrity.
- **Limited Analytical Insights**: School administrators struggle to identify top and struggling students or evaluate subject-by-subject academic performance.

The **Student Result Management System** solves these challenges by providing a fast, reliable, and completely offline CLI tool backed by persistent JSON storage, strict score validation, automatic grade mapping, and class analytics.

---

## 🎯 Project Objectives

- **Automate Grade Computations**: Instantly calculate total marks, average percentages, and letter grades across all enrolled subjects.
- **Eliminate Data Entry Errors**: Strictly enforce score validation ensuring marks fall within $0.0$ and $100.0$.
- **Ensure Traceability**: Automatically assign unique, formatted registration numbers (e.g., `REG-2026-001`) to prevent identity collisions.
- **Provide Actionable Reporting**: Generate standardized individual student result reports and macro-level class performance analytics.
- **Configurable Standards**: Enable flexible, custom grading rules adaptable to varying secondary school benchmarks.

---

## ✨ Features

1. **Student Registration**: Register students with full names and class levels (e.g., SS 1, SS 2, SS 3).
2. **Unique Registration Number Generation**: Auto-generates unique, chronological registration codes formatted as `REG-YYYY-XXX`.
3. **Multi-Subject Score Recording**: Log scores for standard secondary school subjects (Mathematics, English Language, Physics, Biology, Chemistry, etc.) or add custom subjects.
4. **Defensive Score Validation**: Enforces input constraints between $0.0$ and $100.0$, rejecting invalid scores or non-numeric inputs.
5. **Total Score Calculation**: Sums marks across all recorded subjects.
6. **Average Score Calculation**: Dynamically computes arithmetic mean percentages.
7. **Configurable Grading Rules**: Maps numerical scores to letter grades (`A`, `B`, `C`, `D`, `E`, `F`) and remarks using customizable boundaries.
8. **Highest-Performing Student Identification**: Detects the top academic achiever by class average.
9. **Lowest-Performing Student Identification**: Identifies students needing academic intervention and tutoring.
10. **Individual Result Reports (Report Cards)**: Formats detailed term transcripts showing subject scores, letter grades, remarks, class position, and final GPA.
11. **Class Performance Summaries**: Compiles school-wide analytics including class averages, overall grade distribution histograms, and subject-by-subject performance benchmarks.
12. **Student Search**: Search by exact registration number or partial name matching.
13. **JSON Persistence**: Persists student records and grading rules with automated recovery from missing or corrupted data.

---

## 🛠 Technologies Used

- **Language**: Python 3.12+ (Compatible with Python 3.8+)
- **Standard Library Modules**:
  - `json`: Data serialization and disk persistence.
  - `datetime`: Year-based registration numbering.
  - `os`: File existence checks and path management.
  - `unittest`: Automated unit test coverage.
- **Version Control**: Git & GitHub

---

## 📂 Project Organization

```text
Student-Result-Management-System/
├── result_manager.py     # Core business logic: calculations, grading, ranking, persistence
├── main.py               # Interactive CLI interface and navigation menu
├── test_results.py       # Automated unit test suite
├── results_data.json     # Persistent JSON database (auto-generated)
├── .gitignore            # Git exclusion rules
└── README.md             # Project documentation and user manual
```

---

## 🚀 Installation Instructions

### Prerequisites
- Python 3.8 or higher installed on your system. Verify with:
  ```bash
  python3 --version
  ```

### Clone the Repository
```bash
git clone https://github.com/smilinqremedy/Student-Result-Management-System.git
cd Student-Result-Management-System
```

*(No third-party packages are required; the application runs out of the box using Python's standard library).*

---

## 💻 How to Run the Application

Launch the command-line application:

```bash
python3 main.py
```

Run the automated test suite:

```bash
python3 -m unittest test_results.py
```

---

## 📖 Example Usage

### 1. Main Navigation Menu
```text
======================================================
   STUDENT RESULT MANAGEMENT SYSTEM (CLI)   
======================================================
 1. Register New Student
 2. Record / Update Subject Scores
 3. Search Student by Registration Number
 4. Generate Individual Student Report Card
 5. View Class Performance Summary
 6. View Top & Lowest Performing Students
 7. Display All Students Roster
 8. View / Configure Grading Scale
 9. Exit System
======================================================
Enter your choice (1-9):
```

### 2. Registering a Student
```text
--- [Register New Student] ---
Enter student full name: Emeka Okafor
Enter class (e.g. SS 1, SS 2, SS 3) [default: SS 1]: SS 3

✓ Student 'Emeka Okafor' successfully registered!
  Assigned Registration Number: REG-2026-001
```

### 3. Individual Student Report Card
```text
=================================================================
           SECONDARY SCHOOL ACADEMIC RESULT REPORT
=================================================================
 Student Name:    Emeka Okafor              Reg No: REG-2026-001
 Class:           SS 3                      Position: 1/35
-----------------------------------------------------------------
Subject                   | Score (%)  | Grade    | Remark
-----------------------------------------------------------------
Mathematics               |     92.0%  | A        | Distinction
English Language          |     84.0%  | A        | Distinction
Physics                   |     88.0%  | A        | Distinction
Chemistry                 |     79.0%  | A        | Distinction
Biology                   |     74.0%  | A        | Distinction
-----------------------------------------------------------------
 Total Score:        417.0 / 500
 Average Score:       83.4%
 Overall Grade:   A (Distinction)
=================================================================
```

### 4. Class Performance Summary
```text
=================================================================
            CLASS PERFORMANCE SUMMARY REPORT
=================================================================
 Total Students Registered:       35
 Students with Results:           35
 Class Average Score:          68.45%
-----------------------------------------------------------------
 Highest Performing Student:  Emeka Okafor (REG-2026-001)
   Score: 83.40% | Grade: A
 Lowest Performing Student:   Bob Smith (REG-2026-014)
   Score: 48.20% | Grade: D
=================================================================

--- Overall Grade Distribution ---
 Grade A (70%+ | Distinction):   8 students ( 22.9%) ####
 Grade B (60%+ | Very Good  ):  14 students ( 40.0%) ########
 Grade C (50%+ | Credit     ):   9 students ( 25.7%) #####
 Grade D (45%+ | Pass       ):   3 students (  8.6%) #
 Grade E (40%+ | Fair       ):   1 students (  2.9%) 
 Grade F ( 0%+ | Fail       ):   0 students (  0.0%) 
```

---

## 🧪 Testing

The repository includes comprehensive unit test coverage in `test_results.py`:
- Unique registration ID numbering format
- Strict score validation (rejecting negative, over-100, and non-numeric inputs)
- Score recording and subject dictionary updates
- Configurable grade assignment
- Total and average score calculations
- Top and lowest performer determination
- Full and partial search functionality
- JSON data persistence and corruption handling

Run tests:
```bash
python3 -m unittest test_results.py
```
Output:
```text
..........
----------------------------------------------------------------------
Ran 10 tests in 0.030s

OK
```
