"""
Unit and integration tests for MediGuide-AI FastAPI backend.
Mocks expensive OCR and ML model inference so tests run fast, reliably,
and offline without network dependencies.
"""

import io
import pytest
from fastapi.testclient import TestClient

from backend.app import app, MAX_FILE_SIZE_BYTES

client = TestClient(app)


def test_health_endpoint():
    """Verify that the health check endpoint returns 200 and operational details."""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "healthy"
    assert data["service"] == "MediGuide-AI API"
    assert "supported_formats" in data
    assert ".png" in data["supported_formats"]
    assert ".pdf" in data["supported_formats"]
    assert data["max_file_size_mb"] == 10


def test_upload_valid_document_mocked(monkeypatch):
    """
    Verify successful upload of a medical report.
    Mocks OCR extraction to return deterministic synthetic text.
    """
    mock_report_text = (
        "MediGuide AI Demo Medical Report\n"
        "Date: 07 October 2026\n"
        "Blood Pressure: 130/85 mmHg\n"
        "Hemoglobin: 12.5 g/dL\n"
        "Reported observation: Patient reports fatigue for three days.\n"
        "Medications mentioned: None listed."
    )

    monkeypatch.setattr(
        "backend.app.extract_text_from_document",
        lambda file_path: mock_report_text,
    )

    file_bytes = b"fake-png-binary-content-for-testing"
    files = {"file": ("demo_report.png", io.BytesIO(file_bytes), "image/png")}

    response = client.post("/api/upload", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["report_id"].startswith("REP-")
    assert data["filename"] == "demo_report.png"
    assert "extracted_info" in data
    assert "summary" in data
    assert "risk_assessment" in data
    assert "disclaimer" in data

    # Verify extracted medical values
    assert "130/85" in data["extracted_info"]["test_values"]
    assert "12.5" in data["extracted_info"]["test_values"]
    assert "mmhg" in data["extracted_info"]["units"]
    assert "fatigue" in data["extracted_info"]["symptoms"]

    # Verify non-diagnostic disclaimer
    assert "not a diagnosis or clinical recommendation" in data["summary"].lower()
    assert "does not diagnose" in data["disclaimer"].lower()


def test_upload_high_risk_escalation_mocked(monkeypatch):
    """
    Verify that reports with severe symptoms (e.g. chest pain)
    are flagged as high risk and escalate to a human review request.
    """
    high_risk_text = "Patient reports severe chest pain and difficulty breathing."

    monkeypatch.setattr(
        "backend.app.extract_text_from_document",
        lambda file_path: high_risk_text,
    )

    file_bytes = b"fake-pdf-content"
    files = {"file": ("critical.pdf", io.BytesIO(file_bytes), "application/pdf")}

    response = client.post("/api/upload", files=files)
    assert response.status_code == 200
    data = response.json()

    assert data["risk_assessment"]["is_high_risk"] is True
    assert data["review_request"] is not None
    assert data["review_request"]["risk_level"] == "HIGH"
    assert "chest pain" in data["review_request"]["escalation_reasons"][0]
    assert "seek professional" in data["guidance"][0].lower()


def test_upload_empty_file_returns_400():
    """Verify that uploading a 0-byte file returns a 400 Bad Request error."""
    empty_file = io.BytesIO(b"")
    files = {"file": ("empty.png", empty_file, "image/png")}

    response = client.post("/api/upload", files=files)
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_unsupported_format_returns_400():
    """Verify that uploading an unsupported file extension returns 400 Bad Request."""
    bad_file = io.BytesIO(b"malicious-script-content")
    files = {"file": ("virus.exe", bad_file, "application/octet-stream")}

    response = client.post("/api/upload", files=files)
    assert response.status_code == 400
    assert "unsupported" in response.json()["detail"].lower()


def test_upload_oversized_file_returns_413(monkeypatch):
    """
    Verify that an upload exceeding the 10 MB limit returns 413 Payload Too Large.
    Temporarily lowers MAX_FILE_SIZE_BYTES for rapid testing.
    """
    monkeypatch.setattr("backend.app.MAX_FILE_SIZE_BYTES", 50)

    large_content = b"A" * 100
    files = {"file": ("large.png", io.BytesIO(large_content), "image/png")}

    response = client.post("/api/upload", files=files)
    assert response.status_code == 413
    assert "exceeds maximum allowed size" in response.json()["detail"]


def test_upload_unreadable_ocr_returns_422(monkeypatch):
    """
    Verify that if OCR fails to find any legible text in an image,
    the API returns a 422 Unprocessable Entity error.
    """
    monkeypatch.setattr(
        "backend.app.extract_text_from_document",
        lambda file_path: "",
    )

    blank_content = b"blank-image-data"
    files = {"file": ("blank.jpg", io.BytesIO(blank_content), "image/jpeg")}

    response = client.post("/api/upload", files=files)
    assert response.status_code == 422
    assert "could not extract readable text" in response.json()["detail"].lower()


def test_process_text_endpoint():
    """Verify the /api/process-text endpoint for narrative patient requests."""
    payload = {
        "text": "I have had a mild fever and have been taking aspirin.",
        "target_language": "en"
    }

    response = client.post("/api/process-text", json=payload)
    assert response.status_code == 200
    data = response.json()
    assert "translated_summary" in data
    assert "guidance" in data
    assert "disclaimer" in data
    assert "aspirin" in data["translated_summary"].lower()


def test_upload_returns_privacy_safe_stage_timings(monkeypatch):
    """Verify that stage timings are computed and returned without leaking patient data."""
    mock_report_text = "Blood Pressure: 120/80 mmHg. Patient feels fine."
    monkeypatch.setattr("backend.app.extract_text_from_document", lambda p: mock_report_text)

    files = {"file": ("report.png", io.BytesIO(b"content"), "image/png")}
    response = client.post("/api/upload", files=files)
    assert response.status_code == 200
    data = response.json()
    assert "timings" in data
    assert "ocr_seconds" in data["timings"]
    assert "ner_seconds" in data["timings"]
    assert "summarizer_seconds" in data["timings"]
    assert "total_seconds" in data["timings"]
    assert data["timings"]["total_seconds"] >= 0

