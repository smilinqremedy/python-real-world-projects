# Python Real-World Projects Portfolio

[![Python](https://img.shields.io/badge/Python-3.10%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Projects](https://img.shields.io/badge/Projects-60%20Complete-brightgreen.svg)](#portfolio-projects)

A curated collection of **25 production-grade, modular real-world applications** built in Python. Each project addresses a distinct operational, financial, logistics, or data management challenge using standard library tools (`sqlite3`, `json`, `datetime`, `unittest`) with clean architectural separation between presentation (CLI), business logic (service layer), and persistent data access.

---

## Architecture Principles

Every project in this repository adheres to consistent software engineering standards:
1. **Separation of Concerns**: Presentation (CLI interactive menus), business logic / analytics service layer, and data storage are strictly isolated.
2. **Defensive Programming**: Comprehensive input validation, boundary checking, and custom error handling across all user operations.
3. **Data Integrity & Immutability**: Relational integrity enforced via SQLite foreign key constraints, check constraints, and historical snapshotting for financial calculations.
4. **Standard Library Only**: High portability with zero third-party pip dependencies required.
5. **Independent Testability**: Each project contains a dedicated `unittest` test suite covering business rules, edge cases, and data persistence.

---

## Portfolio Projects

| # | Project Name | Directory | Storage | Domain | Status |
|---|--------------|-----------|---------|--------|--------|
| **01** | [Expense & Budget Tracker](01-expense-budget-tracker/) | `01-expense-budget-tracker/` | JSON | Personal Finance | :white_check_mark: Complete |
| **02** | [Inventory Management System](02-inventory-management/) | `02-inventory-management/` | JSON | Retail & Inventory | :white_check_mark: Complete |
| **03** | [Student Result Management System](03-student-result-management/) | `03-student-result-management/` | JSON | Academic Records | :white_check_mark: Complete |
| **04** | [Hospital Appointment Management System](04-hospital-appointment/) | `04-hospital-appointment/` | SQLite | Healthcare Scheduling | :white_check_mark: Complete |
| **05** | [Electricity & Household Power Tracker](05-electricity-tracker/) | `05-electricity-tracker/` | SQLite | Utility Management | :white_check_mark: Complete |
| **06** | [Job Application Tracking System](06-job-application-tracker/) | `06-job-application-tracker/` | JSON | Career & Recruitment | :white_check_mark: Complete |
| **07** | [Queue Management System](07-queue-management/) | `07-queue-management/` | SQLite | Operations & Queuing | :white_check_mark: Complete |
| **08** | [Personal Document Expiry Reminder](08-document-expiry-reminder/) | `08-document-expiry-reminder/` | JSON | Document Compliance | :white_check_mark: Complete |
| **09** | [Customer Support Ticket System](09-customer-support-tickets/) | `09-customer-support-tickets/` | SQLite | Customer Service CRM | :white_check_mark: Complete |
| **10** | [Sales & Profit Analysis System](10-sales-profit-analysis/) | `10-sales-profit-analysis/` | SQLite | Financial Analytics | :white_check_mark: Complete |
| **11** | [Property Rental Management System](11-property-rental/) | `11-property-rental/` | SQLite | Real Estate & Leasing | :white_check_mark: Complete |
| **12** | [Restaurant Order Management System](12-restaurant-order-management/) | `12-restaurant-order-management/` | SQLite | Food & Hospitality | :white_check_mark: Complete |
| **13** | [Employee Attendance Management System](13-employee-attendance/) | `13-employee-attendance/` | SQLite | Human Resources & Workforce | :white_check_mark: Complete |
| **14** | [Laundry Service Management System](14-laundry-management/) | `14-laundry-management/` | SQLite | Service & Operations | :white_check_mark: Complete |
| **15** | [Vehicle Maintenance Tracking System](15-vehicle-maintenance/) | `15-vehicle-maintenance/` | SQLite | Fleet & Automotive | :white_check_mark: Complete |
| **16** | [Water Delivery Management System](16-water-delivery/) | `16-water-delivery/` | SQLite | Logistics & Route Distribution | :white_check_mark: Complete |
| **17** | [Event Registration & Ticketing System](17-event-ticketing/) | `17-event-ticketing/` | SQLite | Events & Ticketing | :white_check_mark: Complete |
| **18** | [Agricultural Produce Trading System](18-agricultural-trading/) | `18-agricultural-trading/` | SQLite | Agribusiness & Supply Chain | :white_check_mark: Complete |
| **19** | [Technical Repair Service Management](19-technical-repair/) | `19-technical-repair/` | SQLite | Repair & Warranty Services | :white_check_mark: Complete |
| **20** | [Donation & Charity Management System](20-charity-management/) | `20-charity-management/` | SQLite | Non-Profit & Fundraising | :white_check_mark: Complete |
| **21** | [Microfinance Loan Management System](21-microfinance-loan-management/) | `21-microfinance-loan-management/` | SQLite | Financial Credit & Lending | :white_check_mark: Complete |
| **22** | [Pharmacy Inventory & Sales System](22-pharmacy-inventory-management/) | `22-pharmacy-inventory-management/` | SQLite | Healthcare & Pharmaceuticals | :white_check_mark: Complete |
| **23** | [School Fee Payment Management System](23-school-fee-management/) | `23-school-fee-management/` | SQLite | Education & Tuition Billing | :white_check_mark: Complete |
| **24** | [Internet Cafe Management System](24-internet-cafe-management/) | `24-internet-cafe-management/` | SQLite | Hospitality & IT Terminals | :white_check_mark: Complete |
| **25** | [Logistics & Shipment Tracking System](25-logistics-shipment-tracking/) | `25-logistics-shipment-tracking/` | SQLite | Freight, Courier & Logistics | :white_check_mark: Complete |
| **31** | [Online Examination Management System](31-online-examination-system/) | `31-online-examination-system/` | SQLite | Education & Assessments | :white_check_mark: Complete |
| **32** | [Automated Email Notification System](32-automated-email-notification/) | `32-automated-email-notification/` | SQLite & smtplib | Communication & Automation | :white_check_mark: Complete |
| **33** | [Real Estate Property Listing & Search System](33-real-estate-property-listing/) | `33-real-estate-property-listing/` | SQLite | Real Estate & Brokerage | :white_check_mark: Complete |
| **41** | [Hospital Patient Records Management System](41-hospital-patient-records/) | `41-hospital-patient-records/` | SQLite | Healthcare & Clinical Records | :white_check_mark: Complete |
| **42** | [Nigerian Tax & Business Revenue Calculator](42-nigerian-business-finance-calculator/) | `42-nigerian-business-finance-calculator/` | SQLite & CSV/PDF | Financial Calculations & Tax | :white_check_mark: Complete |
| **43** | [Job Recruitment & Applicant Tracking System](43-job-recruitment-tracker/) | `43-job-recruitment-tracker/` | SQLite & Local File Storage | Career, HR & Recruitment | :white_check_mark: Complete |
| **51** | [Hospital Pharmacy Prescription Management](51-hospital-pharmacy-prescription-management/) | `51-hospital-pharmacy-prescription-management/` | SQLite | Healthcare & Pharmaceuticals | :white_check_mark: Complete |
| **52** | [Automated Job Application Email Assistant](52-job-application-email-assistant/) | `52-job-application-email-assistant/` | SQLite & smtplib | Communication & Automation | :white_check_mark: Complete |
| **53** | [Digital Asset & Equipment Assignment Tracker](53-digital-asset-assignment-tracker/) | `53-digital-asset-assignment-tracker/` | SQLite | IT Operations & Asset Tracking | :white_check_mark: Complete |
| **54** | [Website Contact Form Spam Detection](54-contact-form-spam-detection/) | `54-contact-form-spam-detection/` | SQLite | Web Security & Form Moderation | :white_check_mark: Complete |
| **55** | [Fuel Station Sales & Tank Monitoring](55-fuel-station-sales-monitoring/) | `55-fuel-station-sales-monitoring/` | SQLite & Decimal | Petroleum Retail & Inventory | :white_check_mark: Complete |
| **56** | [Personal Password Security Audit Tool](56-password-security-audit-tool/) | `56-password-security-audit-tool/` | Local In-Memory | Cybersecurity & Audit | :white_check_mark: Complete |
| **57** | [Customer Subscription & Renewal Management](57-customer-subscription-renewal-management/) | `57-customer-subscription-renewal-management/` | SQLite | SaaS & Recurring Subscriptions | :white_check_mark: Complete |
| **58** | [CSV Data Cleaning & Validation Tool](58-csv-data-cleaning-validation-tool/) | `58-csv-data-cleaning-validation-tool/` | Pandas & CSV | Data Engineering & Cleansing | :white_check_mark: Complete |
| **59** | [API Rate Limiting & Monitoring System](59-api-rate-limiting-monitoring/) | `59-api-rate-limiting-monitoring/` | FastAPI & SQLite | Web Security & API Traffic Control | :white_check_mark: Complete |
| **60** | [Supplier Purchase Order Management](60-supplier-purchase-order-management/) | `60-supplier-purchase-order-management/` | SQLite | Procurement, Inventory & Supply Chain | :white_check_mark: Complete |
| **61** | [Network Intrusion Detection System](61-network-intrusion-detection-system/) | `61-network-intrusion-detection-system/` | Scapy & SQLite | Cybersecurity & Network Defense | :white_check_mark: Complete |
| **62** | [Digital Forensics File Metadata Analyzer](62-digital-forensics-metadata-analyzer/) | `62-digital-forensics-metadata-analyzer/` | Python Hashlib & SQLite | Digital Forensics & Integrity | :white_check_mark: Complete |
| **63** | [Security Incident Response Management](63-security-incident-response-management/) | `63-security-incident-response-management/` | Python OOP & SQLite | SOC & Incident Handling | :white_check_mark: Complete |
| **64** | [Web Security Header Scanner](64-web-security-header-scanner/) | `64-web-security-header-scanner/` | Requests & JSON/HTML | Web Application Security | :white_check_mark: Complete |
| **65** | [Fileless Malware Behavior Detection](65-fileless-malware-behavior-detection/) | `65-fileless-malware-behavior-detection/` | Python EDR & SQLite | Endpoint Security & Threat Detection | :white_check_mark: Complete |
| **66** | [Cloud Storage Security Configuration Auditor](66-cloud-storage-security-auditor/) | `66-cloud-storage-security-auditor/` | PyYAML, JSON & AWS S3 | Cloud Security & Compliance | :white_check_mark: Complete |
| **67** | [Phishing Email Detection & Analysis](67-phishing-email-detection-analysis/) | `67-phishing-email-detection-analysis/` | Python EML & SQLite | Email Security & Threat Analysis | :white_check_mark: Complete |
| **68** | [USB Device Activity Monitor & Audit](68-usb-device-activity-monitor/) | `68-usb-device-activity-monitor/` | Python & SQLite | Endpoint Hardware & Removable Media | :white_check_mark: Complete |
| **69** | [Vulnerability Risk Prioritization](69-vulnerability-risk-prioritization/) | `69-vulnerability-risk-prioritization/` | FastAPI, Pandas & SQLite | Vulnerability Management & DevSecOps | :white_check_mark: Complete |
| **70** | [Security Log Correlation & Threat Hunting](70-security-log-correlation-threat-hunting/) | `70-security-log-correlation-threat-hunting/` | Python SIEM & SQLite | SOC & Multi-Stage Threat Hunting | :white_check_mark: Complete |
| **71** | [Bank Loan Default Prediction System](71-bank-loan-default-prediction/) | `71-bank-loan-default-prediction/` | Scikit-learn, Pandas & SQLite | Financial Credit Risk & Machine Learning | :white_check_mark: Complete |
| **72** | [House Price Prediction System](72-house-price-prediction/) | `72-house-price-prediction/` | Scikit-learn, Pandas & Streamlit | Real Estate Valuation & Regression | :white_check_mark: Complete |
| **73** | [Customer Churn Prediction System](73-customer-churn-prediction/) | `73-customer-churn-prediction/` | Scikit-learn, Pandas & SQLite | Customer Retention & Classification | :white_check_mark: Complete |
| **74** | [Email Spam Classification System](74-email-spam-classification/) | `74-email-spam-classification/` | Scikit-learn, TF-IDF & SQLite | Natural Language Processing & Cyber Defense | :white_check_mark: Complete |
| **81** | [Road Accident Severity Prediction](81-road-accident-severity-prediction/) | `81-road-accident-severity-prediction/` | Scikit-learn, Pandas & SQLite | Transportation Safety & Classification | :white_check_mark: Complete |
| **82** | [Facial Expression Recognition System](82-facial-expression-recognition/) | `82-facial-expression-recognition/` | PyTorch, OpenCV & CNN | Computer Vision & Affective Analysis | :white_check_mark: Complete |
| **83** | [Electricity Consumption Forecasting](83-electricity-consumption-forecasting/) | `83-electricity-consumption-forecasting/` | Statsmodels, Scikit-learn & ARIMA | Time-Series Forecasting & Energy | :white_check_mark: Complete |
| **84** | [Plant Disease Image Classification System](84-plant-disease-image-classification/) | `84-plant-disease-image-classification/` | PyTorch, OpenCV & CNN | Agricultural Vision & Plant Pathology | :white_check_mark: Complete |
| **85** | [Employee Resignation Prediction System](85-employee-attrition-prediction/) | `85-employee-attrition-prediction/` | Scikit-learn, Pandas & SQLite | People Analytics & Workforce Retention | :white_check_mark: Complete |
| **91** | [AI-Based Medical Image Classification System](91-medical-image-classification/) | `91-medical-image-classification/` | CNN, NumPy, Pillow & Streamlit | Deep Learning & Medical Imaging | :white_check_mark: Complete |
| **92** | [Real-Time Object Detection System](92-real-time-object-detection/) | `92-real-time-object-detection/` | YOLO, OpenCV & NMS | Computer Vision & Object Detection | :white_check_mark: Complete |
| **93** | [AI-Powered Facial Recognition Attendance System](93-facial-recognition-attendance/) | `93-facial-recognition-attendance/` | SQLite, PBKDF2 & Ethical Biometrics | Biometrics & Enterprise Access | :white_check_mark: Complete |
| **94** | [AI-Powered Voice-to-Text Transcription System](94-voice-to-text-transcription/) | `94-voice-to-text-transcription/` | Speech Recognition, Wave & Levenshtein | Speech Processing & NLP | :white_check_mark: Complete |
| **95** | [AI-Powered Sign Language Recognition System](95-sign-language-recognition/) | `95-sign-language-recognition/` | MediaPipe, NumPy & Hand Landmarks | Computer Vision & Assistive Tech | :white_check_mark: Complete |
| **96** | [Intelligent Document Question-Answering System](96-document-question-answering/) | `96-document-question-answering/` | RAG, Vector Embeddings & Cosine Search | NLP & Information Retrieval | :white_check_mark: Complete |
| **97** | [AI-Powered Human Activity Recognition System](97-human-activity-recognition/) | `97-human-activity-recognition/` | 1D-CNN, IMU Sensors & Time-Series | Deep Learning & Wearable AI | :white_check_mark: Complete |
| **98** | [AI-Powered News Article Summarization System](98-news-article-summarization/) | `98-news-article-summarization/` | TextRank, NER & ROUGE Evaluation | NLP & Automated Summarization | :white_check_mark: Complete |
| **99** | [AI-Based Financial Fraud Detection System](99-ai-financial-fraud-detection/) | `99-ai-financial-fraud-detection/` | Isolation Forest, Weighted Classifier & PR-AUC | Financial Cybersecurity & Anomaly Detection | :white_check_mark: Complete |
| **100** | [AI-Powered Personal Learning Assistant](100-ai-personal-learning-assistant/) | `100-ai-personal-learning-assistant/` | SQLite, NLP & Grounded Quiz Generation | EdTech & Personalized Learning | :white_check_mark: Complete |

---

## How to Run Any Project

Navigate into any project directory and launch its entrypoint:

```bash
cd 01-expense-budget-tracker
python3 main.py
```

To run the automated test suite for any project:

```bash
python3 -m unittest discover -s . -p "test_*.py"
```
