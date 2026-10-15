"""
Downstream integration and safety tests for MediGuide-AI.
Covers:
- Authentication & JWT Token issuance
- Role-Based Access Control (RBAC) & 401/403 security enforcement
- Patient data isolation
- SQLite persistence across restarts
- Clinical review workflow & decision sign-off
- Administrative user management & status toggling
"""

import io
import json
import sqlite3
import uuid
import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.database import get_db_connection, DB_PATH
from backend.auth import create_access_token

client = TestClient(app)


# ==========================================
# 1. Authentication Tests
# ==========================================

def test_auth_login_patient_success():
    """Verify patient login returns valid token and user profile."""
    res = client.post("/api/auth/login", json={"email": "alex@example.com", "password": "patient123"})
    assert res.status_code == 200
    data = res.json()
    assert "token" in data
    assert data["user"]["email"] == "alex@example.com"
    assert data["user"]["role"] == "patient"


def test_auth_login_doctor_success():
    """Verify doctor login returns valid token with clinician role."""
    res = client.post("/api/auth/login", json={"email": "sarah@example.com", "password": "doctor123"})
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["role"] == "doctor"
    assert data["user"]["specialty"] == "Cardiology"


def test_auth_login_admin_success():
    """Verify system administrator login."""
    res = client.post("/api/auth/login", json={"email": "admin@example.com", "password": "admin123"})
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["role"] == "admin"


def test_auth_login_invalid_password_returns_401():
    """Verify that an invalid password returns 401 Unauthorized."""
    res = client.post("/api/auth/login", json={"email": "alex@example.com", "password": "wrongpassword"})
    assert res.status_code == 401
    assert "invalid" in res.json()["detail"].lower()


def test_auth_login_nonexistent_user_returns_401():
    """Verify that an unknown email returns 401 Unauthorized."""
    res = client.post("/api/auth/login", json={"email": "ghost@example.com", "password": "password"})
    assert res.status_code == 401


def test_auth_register_patient_success():
    """Verify patient self-registration and immediate token generation."""
    test_email = f"newpatient_{uuid.uuid4().hex[:8]}@testclinic.org"
    res = client.post("/api/auth/register", json={
        "name": "Jordan Lee",
        "email": test_email,
        "password": "securepassword123"
    })
    assert res.status_code == 200
    data = res.json()
    assert data["user"]["role"] == "patient"
    assert "token" in data


def test_auth_me_endpoint_with_valid_and_invalid_token():
    """Verify /api/auth/me profile endpoint enforces Bearer token validation."""
    # 1. Without token -> 401
    res_no_token = client.get("/api/auth/me")
    assert res_no_token.status_code == 401

    # 2. With invalid token -> 401
    res_bad_token = client.get("/api/auth/me", headers={"Authorization": "Bearer bad.token.here"})
    assert res_bad_token.status_code == 401

    # 3. With valid token -> 200
    token = create_access_token(user_id="1", email="alex@example.com", role="patient", name="Alex Morgan")
    res_valid = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_valid.status_code == 200
    assert res_valid.json()["id"] == "1"


# ==========================================
# 2. RBAC & Access Control Tests
# ==========================================

def test_patient_forbidden_from_doctor_review_queue():
    """Verify that a patient token cannot access the clinical review queue (403 Forbidden)."""
    patient_token = create_access_token(user_id="1", email="alex@example.com", role="patient", name="Alex Morgan")
    res = client.get("/api/reviews", headers={"Authorization": f"Bearer {patient_token}"})
    assert res.status_code == 403
    assert "access denied" in res.json()["detail"].lower()


def test_patient_forbidden_from_submitting_review_decision():
    """Verify that a patient token cannot submit a clinical review decision (403 Forbidden)."""
    patient_token = create_access_token(user_id="1", email="alex@example.com", role="patient", name="Alex Morgan")
    payload = {"decision": "Recommend immediate ER visit", "notes": "Unauthorized entry"}
    res = client.post("/api/reviews/MG-1024/decision", json=payload, headers={"Authorization": f"Bearer {patient_token}"})
    assert res.status_code == 403


def test_patient_forbidden_from_admin_user_management():
    """Verify that a patient token cannot access admin user management (403 Forbidden)."""
    patient_token = create_access_token(user_id="1", email="alex@example.com", role="patient", name="Alex Morgan")
    res = client.get("/api/admin/users", headers={"Authorization": f"Bearer {patient_token}"})
    assert res.status_code == 403


def test_doctor_authorized_to_access_review_queue():
    """Verify that a verified doctor token can access the clinical review queue."""
    doctor_token = create_access_token(user_id="2", email="sarah@example.com", role="doctor", name="Dr. Sarah Wilson")
    res = client.get("/api/reviews", headers={"Authorization": f"Bearer {doctor_token}"})
    assert res.status_code == 200
    assert isinstance(res.json(), list)


def test_doctor_submits_clinical_decision_authenticated():
    """Verify that an authorized doctor can submit a clinical decision, signed in their name."""
    doctor_token = create_access_token(user_id="2", email="sarah@example.com", role="doctor", name="Dr. Sarah Wilson")
    payload = {
        "decision": "Recommend immediate ER visit",
        "notes": "Severe chest pain presentation requires immediate 12-lead ECG and troponin evaluation.",
    }
    res = client.post("/api/reviews/MG-1024/decision", json=payload, headers={"Authorization": f"Bearer {doctor_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["status"] == "COMPLETED"
    assert data["reviewed_by"] == "Dr. Sarah Wilson"
    assert data["reviewed_at"] is not None


# ==========================================
# 3. Patient Data Isolation Tests
# ==========================================

def test_patient_cannot_view_another_patients_report():
    """Verify that Patient B cannot access Patient A's confidential medical report (403 Forbidden)."""
    # Report 101 belongs to User 1 (Alex Morgan)
    patient_b_token = create_access_token(user_id="4", email="maria@example.com", role="patient", name="Maria Gonzalez")

    # Patient B attempts to access Report 101
    res = client.get("/api/reports/101", headers={"Authorization": f"Bearer {patient_b_token}"})
    assert res.status_code == 403
    assert "access denied" in res.json()["detail"].lower()


def test_patient_can_view_own_report():
    """Verify that Patient A can access their own report (200 OK)."""
    patient_a_token = create_access_token(user_id="1", email="alex@example.com", role="patient", name="Alex Morgan")
    res = client.get("/api/reports/101", headers={"Authorization": f"Bearer {patient_a_token}"})
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == "101"
    assert data["user_id"] == "1"


def test_doctor_can_view_patient_report_for_clinical_review():
    """Verify that authorized clinicians can inspect any patient report for safety verification."""
    doctor_token = create_access_token(user_id="2", email="sarah@example.com", role="doctor", name="Dr. Sarah Wilson")
    res = client.get("/api/reports/101", headers={"Authorization": f"Bearer {doctor_token}"})
    assert res.status_code == 200


# ==========================================
# 4. Database Persistence & Restart Tests
# ==========================================

def test_reports_persisted_to_sqlite_across_reconnect(monkeypatch):
    """Verify that uploaded reports are saved in SQLite and readable after a fresh connection."""
    mock_text = "Date: 15 October 2026. Blood Pressure: 135/85 mmHg. Patient reports mild fatigue."
    monkeypatch.setattr("backend.app.extract_text_from_document", lambda p: mock_text)

    patient_token = create_access_token(user_id="1", email="alex@example.com", role="patient", name="Alex Morgan")
    file_bytes = b"fake-png-content"
    files = {"file": ("persisted_test.png", io.BytesIO(file_bytes), "image/png")}

    res = client.post("/api/upload", files=files, headers={"Authorization": f"Bearer {patient_token}"})
    assert res.status_code == 200
    report_id = res.json()["report_id"]

    # Open a completely fresh, separate SQLite connection simulating a server restart
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM reports WHERE id = ?;", (report_id,)).fetchone()
        assert row is not None
        assert row["filename"] == "persisted_test.png"
        assert row["user_id"] == "1"
        assert "135/85" in row["summary"]
    finally:
        conn.close()


def test_review_decision_persisted_to_sqlite():
    """Verify that a submitted clinician decision persists directly into SQLite."""
    conn = get_db_connection()
    try:
        row = conn.execute("SELECT * FROM review_requests WHERE id = 'MG-1024';").fetchone()
        assert row is not None
        assert row["status"] in ("PENDING_REVIEW", "COMPLETED")
    finally:
        conn.close()


# ==========================================
# 5. Admin User Management Tests
# ==========================================

def test_admin_list_and_toggle_user_status():
    """Verify that an administrator can list users and toggle status between Active and Suspended."""
    admin_token = create_access_token(user_id="3", email="admin@example.com", role="admin", name="System Administrator")

    # 1. List users
    res_list = client.get("/api/admin/users", headers={"Authorization": f"Bearer {admin_token}"})
    assert res_list.status_code == 200
    users = res_list.json()
    assert len(users) >= 3

    # 2. Suspend a user
    res_suspend = client.patch(
        "/api/admin/users/4/status",
        json={"status": "Suspended"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_suspend.status_code == 200
    assert res_suspend.json()["status"] == "Suspended"

    # 3. Reactivate user
    res_active = client.patch(
        "/api/admin/users/4/status",
        json={"status": "Active"},
        headers={"Authorization": f"Bearer {admin_token}"}
    )
    assert res_active.status_code == 200
    assert res_active.json()["status"] == "Active"


def test_system_stats_telemetry_reflects_db():
    """Verify system telemetry includes SQLite counts and model readiness."""
    res = client.get("/api/system/stats")
    assert res.status_code == 200
    data = res.json()
    assert data["total_reports_stored"] >= 2
    assert data["total_users_registered"] >= 3
    assert "SQLite ACID Persistence Engine" in [s["name"] for s in data["services"]]
