# MediGuide-AI: Healthcare Document Intelligence & Clinical Safety Platform

**AMD Developer Hackathon — ACT III: Health & Wellbeing**

[![Python Version](https://img.shields.io/badge/python-3.11+-blue.svg)](https://www.python.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.110+-009688.svg)](https://fastapi.tiangolo.com/)
[![React](https://img.shields.io/badge/React-19.0-61DAFB.svg)](https://react.dev/)
[![SQLite](https://img.shields.io/badge/SQLite-WAL--Mode-003B57.svg)](https://www.sqlite.org/)
[![Tests](https://img.shields.io/badge/Tests-64%2F64%20Passed-brightgreen.svg)]()
[![License](https://img.shields.io/badge/License-MIT-green.svg)]()

MediGuide-AI is a healthcare document intelligence and human-in-the-loop safety platform engineered to bridge the clinical comprehension gap between complex diagnostic lab reports and patient understanding.

Combining local biomedical Natural Language Processing (NLP) with deterministic clinical safety guardrails, SQLite ACID persistence, server-side Role-Based Access Control (RBAC), and physician escalation workflows, MediGuide-AI ensures that healthcare information is both accessible to patients and rigorously validated by licensed healthcare professionals.

---

> ### **CRITICAL CLINICAL SAFETY DISCLAIMER**
> MediGuide-AI is an educational and informational aid and is **NOT** a medical diagnostic device, clinical decision system, or substitute for professional medical judgment. It does not formulate clinical diagnoses, prescribe medications, or recommend treatment dosages. In the event of a medical emergency, immediately contact emergency services (such as 911) or seek urgent medical attention.

---

## Key Features & Capabilities

### 1. Document Extraction & OCR
- **Digital PDFs**: Native text and vector layer extraction using PyMuPDF (`fitz`).
- **Scanned Reports & Images**: Automated optical character recognition via PaddleOCR with angle classification supporting `.png`, `.jpg`, `.jpeg`, `.bmp`, and `.tiff`.

### 2. Biomedical Entity Extraction & Summarization (Frozen Pipeline)
- **Biomedical NER**: Token classification powered by `d4data/biomedical-ner-all` identifying symptoms, diagnostic tests, medications, and clinical observations.
- **Patient-Friendly Summarization**: Fine-tuned `sshleifer/distilbart-cnn-6-6` abstractive summarization.
- **Deterministic Metric Guardrails**: Post-summarization numeric metric comparator validating that all blood pressure, glucose, and lab values in the summary match extracted facts exactly. If verification detects a discrepancy, a deterministic template fallback is activated automatically.

### 3. Human-in-the-Loop Clinical Escalation & Safety Review
- **Automatic Risk Stratification**: Rule-based categorization (`LOW`, `MEDIUM`, `HIGH`, `UNCERTAIN`).
- **Clinician Triage**: High-risk cases are automatically escalated to a clinical review queue for licensed physician inspection.
- **Permanent Review Audit Trail**: Physicians submit validated decisions, review notes, and professional signatures saved with ACID guarantees in SQLite.

### 4. Server-Side Authentication & RBAC
- **Password Security**: PBKDF2-HMAC-SHA256 (100,000 hashing iterations) with unique 16-byte random salts.
- **Cryptographic Access Tokens**: HMAC-SHA256 signed Bearer JWT tokens.
- **Patient Data Isolation**: Patients can strictly only view their own uploaded records; accessing another patient's report returns HTTP 403 Forbidden.

### 5. End-to-End Multilingual Healthcare Intelligence
- **Supported Languages**: English (`en`), Tamil (`ta` — தமிழ்), Hindi (`hi` — हिन्दी), Telugu (`te` — తెలుగు), Malayalam (`ml` — മലയാളം), and Kannada (`kn` — ಕನ್ನಡ).
- **Zero Paid APIs / Privacy First**: 100% self-contained local translation and Unicode Indic script detection running locally without third-party translation keys or paid cloud APIs.
- **Strict Clinical Measurement Preservation**: Critical medical facts—including numeric blood pressure (`130/85`), laboratory numbers (`12.5`), scientific units (`mmHg`, `g/dL`, `mg/dL`), medications (`Aspirin`, `Metformin`), and dates—remain unaltered and preserved verbatim during translation to prevent medical hallucinations or unit corruption.
- **Dynamic Report Translation**: Patients can view simplified report summaries, clinical observations, and next-step guidance in their preferred language (`GET /api/reports/{id}?lang=...` and `POST /api/reports/{id}/translate`) without modifying or corrupting the stored medical record.
- **Conversational Multilingual AI Agent**: Patient Assistant (`ai/patient_agent.py`) communicates in any of the 6 languages, detects Indic scripts automatically, and triggers localized high-risk emergency escalation for critical symptoms (e.g., chest pain, `நெஞ்சு வலி`, `सीने में दर्द`, `ఛాతీ నొప్పి`, `നെഞ്ചുവേദന`, `ಎದೆ ನೋವು`).
- **Persistent User Language Preference**: The patient's chosen language is saved in SQLite (`users.preferred_language`), synced across login sessions, and immediately reflected across the entire user interface.

### 6. Patient Engagement & Appointment Preparation
- **Appointment Prep**: Organize tailored discussion questions based on extracted lab values, check off required medical documents, and print customized appointment sheets in any preferred language.
- **Patient Assistant**: Conversational health query assistant explaining laboratory terminology and medical abbreviations with non-diagnostic boundaries.

---

## Seeded Default Accounts

For quick hackathon evaluation and demonstration:

| Role | Email Address | Password | Clinical Specialty / Permissions |
| :--- | :--- | :--- | :--- |
| **Patient** | `alex@example.com` | `patient123` | Patient Portal, Upload, Personal Report History, Appointment Prep |
| **Doctor** | `sarah@example.com` | `doctor123` | Doctor Clinical Portal, Pending Review Queue, Decision Sign-off |
| **Admin** | `admin@example.com` | `admin123` | Administrative Governance, Account Management, System Telemetry |

---

## Quick Start Guide (Windows Development)

### Prerequisites
- Python 3.11+
- Node.js 18+ and npm
- Windows PowerShell

### 1. Backend Setup & Startup

```powershell
# Navigate to repository root
cd C:\MediGuide-AI

# Create and activate virtual environment (optional if Python installed globally)
python -m venv venv
.\venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt

# Start the FastAPI backend server with hot reload
uvicorn backend.app:app --host 127.0.0.1 --port 8000 --reload
```

The backend API documentation is available at `http://127.0.0.1:8000/docs`.

### 2. Frontend Setup & Startup

```powershell
# In a separate terminal window:
cd C:\MediGuide-AI\frontend

# Install frontend dependencies
npm install

# Start Vite development server
npm run dev
```

The web application will open at `http://localhost:5173`.

---

## Automated Test Suites

MediGuide-AI includes comprehensive automated tests covering the frozen AI pipeline, API endpoints, authentication, RBAC, persistence, and production build:

```powershell
# 1. Run all multilingual support tests (Indic detection, preservation, translation APIs)
pytest test_multilingual.py -v

# 2. Run all API gateway and downstream security tests
pytest test_api.py test_downstream.py -v

# 3. Run the frozen AI pipeline baseline tests
pytest test_mediguide.py -v

# 4. Verify frontend production build
cd frontend
npm run build
```

---

## Architecture & Codebase Structure

```
C:\MediGuide-AI
├── ai/
│   ├── document_processor.py   # [FROZEN] PyMuPDF & PaddleOCR extraction
│   ├── medical_extractor.py    # [FROZEN] d4data/biomedical-ner-all token classification
│   ├── summarizer.py           # [FROZEN] sshleifer/distilbart-cnn-6-6 & metric verification
│   ├── translator.py           # Zero-cloud Indic detection, translation & value preservation
│   └── patient_agent.py        # Conversational multilingual patient agent
├── backend/
│   ├── app.py                  # FastAPI gateway, routers, schemas, and middleware
│   ├── database.py             # SQLite schema, WAL mode, PBKDF2 hashing, migrations
│   └── auth.py                 # JWT issuance, HMAC-SHA256 verification, RBAC guards
├── human_review/
│   └── review_manager.py       # Clinical review queue delegating to SQLite
├── risk/
│   └── risk_engine.py          # Clinical threshold and risk rule evaluation
├── frontend/
│   ├── src/
│   │   ├── context/AuthContext.jsx   # Client auth state, Bearer token injection
│   │   ├── pages/patient/            # Upload, Analysis, MyReports, AppointmentPrep
│   │   ├── pages/doctor/             # ReviewRequests, ReviewCase, CompletedReviews
│   │   └── pages/admin/              # Users, Doctors, SystemMonitoring
│   └── vite.config.js
├── mediguide.db                # SQLite ACID database file
├── test_api.py                 # API endpoint & error handling tests (12 tests)
├── test_downstream.py          # Auth, RBAC, persistence & admin tests (19 tests)
├── test_mediguide.py           # Frozen AI pipeline tests (33 tests)
├── ARCHITECTURE.md             # Detailed engineering and schema specification
├── DEMO_SCRIPT.md              # 8-step evaluator walkthrough script
├── TEST_REPORT.md              # Comprehensive test report & pass counts
├── HACKATHON_SUBMISSION_CHECKLIST.md  # ACT III Health & Wellbeing checklist
└── PROJECT_DESCRIPTION.md      # Executive summary & clinical problem statement
```

---

## Hardware & Deployment Disclosures

- **Current Verified Baseline**: Runs 100% locally on standard x86-64 CPUs with PyTorch and PaddleOCR CPU runtimes.
- **No Paid Cloud Infrastructure**: MediGuide-AI does not require paid external APIs, proprietary cloud services, or internet access during inference.
- **AMD Readiness**: Engineered with PyTorch and Hugging Face Transformers abstractions designed for zero-code portability to AMD Instinct GPU accelerators and AMD ROCm runtime environments.