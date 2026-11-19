# Online Examination Management System

A robust, relational examination management and automated assessment engine built in Python and SQLite for educational institutions, academies, and certification providers.

## Problem Statement

Educational and training organizations often struggle with traditional examination workflows:
- Unreliable manual scheduling leading to unauthorized retakes.
- Difficulty managing examination duration and enforcing strict submission deadlines.
- Inaccurate manual grading of multiple-choice tests.
- Lack of immediate feedback for candidates and delayed reporting for instructors.

This system provides a structured, automated assessment platform enforcing candidate verification, time-window constraints, automated grading, instant candidate score cards, and instructor analytics.

---

## Features

1. **User Role Management**: Register and manage candidates (students), instructors (teachers), and administrators with email validation.
2. **Curriculum & Subject Organization**: Create academic subjects linked to designated teachers.
3. **Multiple-Choice Question Bank**: Build exams with question options (A, B, C, D), designated correct answers, and customizable point weights.
4. **Duration & Availability Windows**: Enforce strict exam duration limits (in minutes) and optional start/end availability windows.
5. **Candidate Enrollment**: Controlled exam assignments preventing unauthorized students from accessing test materials.
6. **Live Examination Workflow**: Track in-progress exam sessions with automatic session resumption.
7. **Automated Expiry & Submission**: Automatic submission when the exam timer expires, preventing late submissions.
8. **Objective Grading Engine**: Immediate automated evaluation of student submissions against correct answer keys with percentage and pass/fail calculations.
9. **Review & Results Breakdown**: Candidate access to detailed question-by-question performance reviews.
10. **Institutional Performance Analytics**: Exam-wide metrics including pass rate, average/highest/lowest scores, and question difficulty analysis.

---

## Database Architecture

The system uses an SQLite relational database (`examination.db`) with strict constraints and foreign keys:

- `users`: Registered users with unique `user_id`, `email`, and role constraint (`'student'`, `'teacher'`, `'admin'`).
- `subjects`: Academic subjects with unique subject codes.
- `exams`: Exam configurations including duration, passing score thresholds, availability windows, and publication status.
- `questions`: Multiple-choice questions with 4 options, valid option check (`'A'`, `'B'`, `'C'`, `'D'`), and point weights.
- `exam_assignments`: Links candidates to exams with completion status and retake permissions (`retake_authorized`).
- `exam_sessions`: Tracks student test instances, started time, calculated expiration time, submission time, and final scores.
- `student_answers`: Stores candidate selected options, correctness evaluation, and awarded points.

---

## How to Run

### Interactive Application
```bash
python3 main.py
```

### Automated Unit Tests
```bash
python3 -m unittest test_exam.py
```
