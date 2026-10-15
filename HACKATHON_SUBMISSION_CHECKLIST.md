# MediGuide-AI: AMD Developer Hackathon Submission Checklist

**Track**: ACT III — Health & Wellbeing  
**Evaluation Date**: October 2026  
**Status**: COMPLETE & VERIFIED

---

## 1. Frozen AI Pipeline Compliance

| Requirement | Status | Verification Detail |
| :--- | :---: | :--- |
| **PyMuPDF Document Extraction** | **FROZEN** | `ai/document_processor.py` untouched; native PDF extraction preserved. |
| **PaddleOCR Engine** | **FROZEN** | Angle classifier, language parameters, and image pre-processing untouched. |
| **Biomedical NER (`d4data`)** | **FROZEN** | Model version, tokenizer, entity mapping, and aggregation strategy untouched. |
| **DistilBART Summarizer (`6-6`)** | **FROZEN** | `sshleifer/distilbart-cnn-6-6` generation parameters and lengths untouched. |
| **Deterministic Metric Verification** | **FROZEN** | Numeric metric validation comparator and deterministic template fallback intact. |
| **Pipeline Performance & Budgets** | **FROZEN** | 15-second CPU execution budget, worker thread timeouts, and model caching untouched. |
| **Frozen Pipeline Baseline Tests** | **VERIFIED** | `test_mediguide.py`: 33/33 tests passing with 0 modifications. |

---

## 2. Downstream Architecture & Persistence

| Requirement | Status | Verification Detail |
| :--- | :---: | :--- |
| **SQLite ACID Storage** | **VERIFIED** | Relational schema in `backend/database.py` with Write-Ahead Logging (WAL) and foreign keys. |
| **Data Retention Across Restarts** | **VERIFIED** | Verified by `test_reports_persisted_to_sqlite_across_reconnect` across independent SQLite connections. |
| **No In-Memory Data Loss** | **VERIFIED** | Human review requests and report findings persist permanently in `mediguide.db`. |
| **Duplicate Submission Prevention** | **VERIFIED** | Idempotent upsert logic prevents duplicate review tickets on network retries. |

---

## 3. Security, Authentication & Role-Based Access Control

| Requirement | Status | Verification Detail |
| :--- | :---: | :--- |
| **Password Hashing** | **VERIFIED** | PBKDF2-HMAC-SHA256 (100,000 rounds) with cryptographically secure random salts. Zero plaintext storage. |
| **Cryptographic Access Tokens** | **VERIFIED** | HMAC-SHA256 signed Bearer JWT tokens with server-side validation (`backend/auth.py`). |
| **Server-Side RBAC Enforcement** | **VERIFIED** | `require_role(["patient" \| "doctor" \| "admin"])` protects endpoints; client-side claims rejected. |
| **Patient Data Isolation** | **VERIFIED** | Patients cannot view other patients' reports (HTTP 403 Forbidden verified by automated tests). |
| **Clinician Queue Authorization** | **VERIFIED** | Only verified clinicians and administrators can access the review queue or submit clinical decisions. |
| **CORS & Environment Hygiene** | **VERIFIED** | CORS restricted to configured localhost origins; `.env.example` provided; secrets excluded from Git. |

---

## 4. Clinical Safety & Medical Ethics

| Requirement | Status | Verification Detail |
| :--- | :---: | :--- |
| **Non-Diagnostic Disclaimers** | **VERIFIED** | Prominently displayed across Patient Dashboard, Report Analysis, and Patient Assistant. |
| **No Autonomous Prescribing** | **VERIFIED** | System never prescribes medications, alters dosages, or offers definitive clinical diagnoses. |
| **Synthetic Test Data Only** | **VERIFIED** | 100% of benchmark documents and test cases utilize synthetic, anonymized data. Zero PHI collected. |
| **Human Escalation Safety Net** | **VERIFIED** | Configured high-risk vital signs automatically trigger physician review routing before patient guidance. |
| **Permanent Review Audit Trail** | **VERIFIED** | Clinician reviews record reviewer identity, decision, clinical notes, and timestamp in SQLite. |

---

## 5. Technology & Platform Disclosures

| Requirement | Status | Statement / Verification |
| :--- | :---: | :--- |
| **Honest Hardware Profile** | **VERIFIED** | Local CPU inference baseline fully verified; designed for AMD ROCm & AMD Instinct GPU compatibility. |
| **No Paid Cloud Services** | **VERIFIED** | 0 external paid APIs; runs 100% locally on standard workstation environments. |
| **Frontend Production Readiness** | **VERIFIED** | `npm run build` succeeds in 8.61s with 0 errors. |
| **No Git Commits / Pushes** | **VERIFIED** | Working tree retained in uncommitted status for developer review as strictly mandated. |
