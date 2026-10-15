# MediGuide-AI: Hackathon Demonstration Script

**AMD Developer Hackathon — ACT III: Health & Wellbeing**

This demonstration script walks evaluators through the complete end-to-end clinical workflow using synthetic, anonymized medical test data.

---

## Demonstration Overview

| Stage | Action / Workflow | User Role & Credentials | Primary Verification Point |
| :---: | :--- | :--- | :--- |
| **1** | System Login | Patient: `alex@example.com` / `patient123` | PBKDF2 authentication & JWT issuance |
| **2** | Upload Synthetic Report | Patient (`Alex Morgan`) | Multi-format upload & PaddleOCR extraction |
| **3** | AI Summary & Metric Display | Patient | Frozen DistilBART summary & empty states |
| **4** | Dynamic Risk Status | Patient | High-risk escalation badge & disclaimer |
| **5** | Switch to Clinician Role | Doctor: `sarah@example.com` / `doctor123` | Server-side RBAC validation |
| **6** | Clinical Review Queue | Doctor (`Dr. Sarah Wilson, MD`) | Escalated case triage (`MG-1024`) |
| **7** | Record Review Decision | Doctor | Persistent clinician sign-off & notes |
| **8** | Review Archive & Patient Prep | Doctor & Patient | Permanent SQLite archive & appointment checklist |

---

## Step-by-Step Demonstration Walkthrough

### Stage 1: Patient Authentication
1. Open the web application at `http://localhost:5173`.
2. On the **Sign In** screen, use one-click Quick Login by selecting **"Continue as Patient"** (or input `alex@example.com` / `patient123`).
3. **Observed Result**: The application verifies credentials against the SQLite database, stores a cryptographically signed Bearer token, and navigates to the Patient Dashboard (`/patient`).

---

### Stage 2: Upload Synthetic Diagnostic Report
1. In the sidebar, navigate to **Upload Report** (`/patient/upload`).
2. Drag and drop the provided synthetic test image: `C:\MediGuide-AI\synthetic_report.png` (or any `.png`, `.jpg`, or `.pdf` file).
3. Click **"Analyze Report Now"**.
4. **Observed Result**: A live multi-stage progress tracker displays:
   - *Step 1/3: Reading document and extracting clinical text (PaddleOCR)*
   - *Step 2/3: Recognizing biomedical entities, symptoms & measurements (`d4data/biomedical-ner-all`)*
   - *Step 3/3: Generating patient summary & verifying clinical metrics (`sshleifer/distilbart-cnn-6-6`)*

---

### Stage 3: View Generated AI Summary & Extracted Findings
1. The application automatically transitions to **Report Analysis** (`/patient/reports/:id`).
2. Observe the **Patient-Friendly Summary**:
   - The frozen summarization pipeline presents a clear, plain-language translation of the lab results.
3. Observe the **Extracted Findings Grid**:
   - Symptoms, medications, and measurements (e.g., Blood Pressure, Heart Rate) are displayed faithfully.
   - Missing fields display explicit **"None detected"** or **"None listed"** empty states—no fabricated data.
   - Non-diagnostic clinical safety disclaimer is permanently visible at the bottom of the card.

---

### Stage 4: High-Risk Alert & Automatic Escalation
1. Observe the prominent risk banner in the header:
   - **`[High Risk — Clinical Review Escalated]`** (or Standard Normal Routing for baseline vitals).
2. The risk assessment engine identified an elevated vital sign or high-risk symptom and inserted an escalation record into the clinical review queue.
3. The report and risk assessment are permanently stored in SQLite under the patient's authenticated user ID.

---

### Stage 5: Role Switch to Licensed Clinician
1. Log out via the sidebar or top navigation.
2. On the Sign In screen, select **"Continue as Doctor"** (or input `sarah@example.com` / `doctor123`).
3. **Observed Result**: Clinician credentials are authenticated; the navigation bar updates with Doctor Clinical Portal features (`/doctor`).

---

### Stage 6: Inspect Pending Clinical Review Queue
1. In the doctor sidebar, navigate to **Review Queue** (`/doctor/reviews`).
2. Observe the list of pending cases (`PENDING_REVIEW`).
3. Locate case **`MG-1024`** (or the newly escalated report):
   - Notice the anonymized patient ID (`PT-8821`), flagged risk level (`HIGH`), and exact trigger reasons.
4. Click **"Review Case"** to inspect the full clinical dossier.

---

### Stage 7: Submit Authorized Clinician Decision
1. On the **Case Review** dossier (`/doctor/reviews/MG-1024`):
   - Inspect the extracted vitals, patient symptoms, and original document text.
2. In the **Clinical Decision & Action** panel:
   - Select Decision: **"Recommend immediate physician follow-up"**
   - Enter Reviewer Notes: *"Reviewed blood pressure findings. Advise patient to discontinue unprescribed analgesics and arrange same-day outpatient evaluation."*
   - Verify Reviewer Name: `Dr. Sarah Wilson, MD`
3. Click **"Submit Clinical Sign-Off"**.
4. **Observed Result**: The decision, clinician identity, and timestamp are committed via an ACID transaction to SQLite. The case status transitions to **`COMPLETED`**.

---

### Stage 8: Completed Reviews Archive & Appointment Preparation
1. **Clinician Archive**: Navigate to **Completed Reviews** (`/doctor/completed`).
   - Case `MG-1024` is now permanently archived with its full audit trail, timestamp, and signed clinician notes.
2. **Patient History**: Log back in as `alex@example.com` and open **My Reports** (`/patient/reports`).
   - The uploaded report is permanently listed with its risk status and reference ID.
3. **Appointment Preparation**: Navigate to **Appointment Prep** (`/patient/prep`).
   - The patient can review personalized questions formulated from the diagnostic findings, check off required medical documents, add personal symptom notes, and print the prep sheet for their physician appointment.
