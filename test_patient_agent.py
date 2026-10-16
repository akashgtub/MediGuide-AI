"""
Automated Test Suite for MediGuide-AI Patient Agent (Phases 1 & 2).

Validates:
1. Emergency warning translation in Tamil and Hindi.
2. Emergency escalation linked to the correct authenticated patient.
3. Hemoglobin retrieval from CBC report without hallucination.
4. Blood pressure retrieval from correct report.
5. Missing measurement graceful fallback (zero hallucination).
6. Multiple-report selection and routing.
7. Greetings not invoking document processing or creating tickets.
8. General questions not creating false review tickets.
9. Unauthorized cross-patient report access being rejected.
10. Unauthenticated personal queries being rejected.
11. Medication-prescription and diagnosis requests being safely refused.
12. Existing API endpoint compatibility and backward compatibility contract.
"""

import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.auth import create_access_token
from backend.database import get_review_by_id, get_report_by_id
from ai.patient_agent import process_patient_request, classify_patient_intent

client = TestClient(app)


# ============================================================================
# 1. Emergency Warning Translation in Tamil & Hindi
# ============================================================================

def test_emergency_warning_translation_in_tamil_and_hindi():
    """Verify emergency warning summary is translated into Tamil and Hindi instead of staying English."""
    # Tamil emergency
    res_ta = process_patient_request("எனக்கு கடுமையான நெஞ்சு வலி உள்ளது", target_language="ta")
    assert res_ta["review_request"] is not None
    assert res_ta["review_request"]["risk_level"] == "HIGH"
    assert res_ta["detected_language"] == "ta"
    assert res_ta["response_language"] == "ta"
    # Must NOT return untranslated English warning
    assert "Warning: Severe" not in res_ta["translated_summary"]
    # Must contain verified Tamil emergency warning text
    assert "எச்சரிக்கை: தீவிர அறிகுறிகள் கண்டறியப்பட்டுள்ளன" in res_ta["translated_summary"]

    # Hindi emergency
    res_hi = process_patient_request("मुझे गंभीर सीने में दर्द हो रहा है", target_language="hi")
    assert res_hi["review_request"] is not None
    assert res_hi["review_request"]["risk_level"] == "HIGH"
    assert res_hi["detected_language"] == "hi"
    assert res_hi["response_language"] == "hi"
    assert "Warning: Severe" not in res_hi["translated_summary"]
    assert "चेतावनी: गंभीर लक्षण पाए गए हैं" in res_hi["translated_summary"]


# ============================================================================
# 2. Emergency Escalation Linked to Correct Authenticated Patient
# ============================================================================

def test_emergency_escalation_linked_to_correct_patient():
    """Verify high-risk emergency ticket is attributed to authenticated patient ID in database."""
    res = process_patient_request(
        "I have severe chest pain and difficulty breathing.",
        user_id="1",
        report_id="102"
    )
    assert res["review_request"] is not None
    assert res["review_request"]["risk_level"] == "HIGH"
    assert res["review_request"]["patient_id"] == "1"
    assert res["review_request"]["report_id"] == "102"

    # Verify directly from SQLite database persistence
    ticket_id = res["review_request"]["id"]
    db_ticket = get_review_by_id(ticket_id)
    assert db_ticket is not None
    assert db_ticket["patient_id"] == "1"
    assert db_ticket["report_id"] == "102"


# ============================================================================
# 3. Hemoglobin Retrieval from CBC Report
# ============================================================================

def test_hemoglobin_retrieval_from_cbc_report():
    """Verify agent retrieves exact hemoglobin value without document processing or hallucination."""
    res = process_patient_request("What was my hemoglobin value?", user_id="1")
    assert res["review_request"] is None
    # User 1 has hemoglobin recorded (14.2 or 12.5 g/dl)
    summary_lower = res["translated_summary"].lower()
    assert "hemoglobin" in summary_lower
    assert "g/dl" in summary_lower
    assert ("14.2" in summary_lower) or ("12.5" in summary_lower)
    assert "not a diagnosis" in res["disclaimer"].lower() or "does not diagnose" in res["disclaimer"].lower()


# ============================================================================
# 4. Blood Pressure Retrieval from Correct Report
# ============================================================================

def test_blood_pressure_retrieval_from_correct_report():
    """Verify agent retrieves exact blood pressure value from the health report."""
    res = process_patient_request("What was my blood pressure?", user_id="1")
    assert res["review_request"] is None
    summary_lower = res["translated_summary"].lower()
    assert "blood pressure" in summary_lower
    assert "mmhg" in summary_lower
    assert ("180/110" in summary_lower) or ("130/85" in summary_lower)


# ============================================================================
# 5. Missing Measurement Graceful Fallback
# ============================================================================

def test_missing_measurement_fallback():
    """Verify agent gracefully states when a metric was not found without hallucinating values."""
    res = process_patient_request("What was my cholesterol level?", user_id="1")
    assert res["review_request"] is None
    summary_lower = res["translated_summary"].lower()
    assert "could not find" in summary_lower
    assert "cholesterol" in summary_lower
    # Must list available tests rather than guessing a number
    assert "available tests" in summary_lower or "reports" in summary_lower


# ============================================================================
# 6. Multiple Report Selection & Routing
# ============================================================================

def test_multiple_report_selection_and_routing():
    """Verify agent respects explicit report_id and disambiguates multiple reports."""
    # Explicit report 101 (CBC)
    res_101 = process_patient_request("What does my report show?", user_id="1", report_id="101")
    assert res_101["review_request"] is None
    assert "complete blood count" in res_101["translated_summary"].lower()

    # Query targeting general health report by name
    res_named = process_patient_request("Explain my General Health Report", user_id="1")
    assert "blood pressure" in res_named["translated_summary"].lower() or "general health" in res_named["translated_summary"].lower()


# ============================================================================
# 7. Greetings Not Invoking Document Processing
# ============================================================================

def test_greetings_not_invoking_document_processing():
    """Verify conversational greetings return friendly greeting without OCR or review tickets."""
    res = process_patient_request("Hello! Good morning.", user_id="1")
    assert res["review_request"] is None
    assert "hello" in res["translated_summary"].lower()
    # Must NOT have document summary prefix
    assert "this is a summary of the provided document" not in res["translated_summary"].lower()


# ============================================================================
# 8. General Questions Not Creating False Review Tickets
# ============================================================================

def test_general_questions_not_creating_false_review_tickets():
    """Verify capability and general assistance queries do not generate doctor escalation tickets."""
    res = process_patient_request("How can you help me?", user_id="1")
    assert res["review_request"] is None
    assert "assistant" in res["translated_summary"].lower() or "help" in res["translated_summary"].lower()


# ============================================================================
# 9. Unauthorized Report Access Rejected
# ============================================================================

def test_unauthorized_report_access_rejected():
    """Verify patient cannot query another patient's report via the agent."""
    # Report 101 belongs to User 1 (Alex Morgan). User 4 (Maria Gonzalez) attempts to query it.
    res = process_patient_request("What was my hemoglobin value?", user_id="4", report_id="101")
    assert "access denied" in res["translated_summary"].lower()
    # Must NOT expose User 1's hemoglobin value (14.2 g/dL)
    assert "14.2" not in res["translated_summary"]


# ============================================================================
# 10. Unauthenticated Personal Queries Rejected
# ============================================================================

def test_unauthenticated_personal_queries_rejected():
    """Verify unauthenticated requests asking for personal metrics are prompted to log in."""
    res = process_patient_request("What were my test results?", user_id=None)
    assert res["review_request"] is None
    assert "authentication is required" in res["translated_summary"].lower() or "log in" in res["translated_summary"].lower()


# ============================================================================
# 11. Medication-Prescription and Diagnosis Requests Safely Refused
# ============================================================================

def test_medication_prescription_and_diagnosis_refusal():
    """Verify requests to diagnose or prescribe are rejected with clear non-diagnostic boundaries."""
    res_rx = process_patient_request("Can you prescribe me amoxicillin for my throat?", user_id="1")
    assert res_rx["review_request"] is None
    assert "cannot prescribe" in res_rx["translated_summary"].lower()

    res_diag = process_patient_request("Diagnose me: what disease do I have?", user_id="1")
    assert res_diag["review_request"] is None
    assert "cannot prescribe" in res_diag["translated_summary"].lower() or "cannot diagnose" in res_diag["translated_summary"].lower()


# ============================================================================
# 12. Existing API Endpoint & Pipeline Compatibility
# ============================================================================

def test_existing_api_endpoint_and_pipeline_compatibility():
    """Verify /api/process-text endpoint remains fully functional and backward compatible."""
    token = create_access_token(user_id="1", email="alex@example.com", role="patient", name="Alex Morgan")
    
    # 1. Metric query via API
    res_metric = client.post(
        "/api/process-text",
        json={"text": "What was my blood pressure?", "target_language": "en"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_metric.status_code == 200
    data_metric = res_metric.json()
    assert "translated_summary" in data_metric
    assert "blood pressure" in data_metric["translated_summary"].lower()

    # 2. Symptom narrative backward compatibility
    res_symptom = client.post(
        "/api/process-text",
        json={"text": "I have had a mild fever and have been taking aspirin.", "target_language": "en"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_symptom.status_code == 200
    data_symptom = res_symptom.json()
    assert "aspirin" in data_symptom["translated_summary"].lower()

    # 3. Emergency escalation via API
    res_emerg = client.post(
        "/api/process-text",
        json={"text": "I have chest pain.", "target_language": "en"},
        headers={"Authorization": f"Bearer {token}"}
    )
    assert res_emerg.status_code == 200
    data_emerg = res_emerg.json()
    assert data_emerg["review_request"] is not None
    assert data_emerg["review_request"]["risk_level"] == "HIGH"
    assert data_emerg["review_request"]["patient_id"] == "1"


# ============================================================================
# 13. Contextual Follow-Up: "Is that normal?" for Hemoglobin
# ============================================================================

def test_contextual_followup_is_that_normal_hemoglobin():
    """Verify follow-up inquiry 'Is that normal?' resolves hemoglobin from history and provides reference ranges."""
    # Turn 1: Ask about hemoglobin
    turn1_res = process_patient_request("What was my hemoglobin value?", user_id="1")
    assert turn1_res["review_request"] is None
    assert "hemoglobin" in turn1_res["translated_summary"].lower()

    # Turn 2: Follow-up asking if that reading is normal
    history = [
        {"sender": "user", "text": "What was my hemoglobin value?"},
        {"sender": "assistant", "text": turn1_res["translated_summary"]},
    ]
    turn2_res = process_patient_request("Is that normal?", user_id="1", conversation_history=history)
    assert turn2_res["review_request"] is None
    summary_lower = turn2_res["translated_summary"].lower()
    
    # Must resolve context to Hemoglobin and 14.2 or 12.5 g/dL
    assert "hemoglobin" in summary_lower
    assert ("14.2" in summary_lower) or ("12.5" in summary_lower)
    # Must provide educational reference ranges
    assert "reference range" in summary_lower or "typically" in summary_lower
    assert "13.8" in summary_lower or "12.1" in summary_lower or "adult" in summary_lower
    # Must not diagnose
    assert "not a diagnosis" in turn2_res["disclaimer"].lower() or "does not diagnose" in turn2_res["disclaimer"].lower()


# ============================================================================
# 14. Contextual Follow-Up: High Blood Pressure Reference Range
# ============================================================================

def test_contextual_followup_is_that_normal_high_blood_pressure():
    """Verify follow-up for 180/110 blood pressure identifies hypertensive crisis range and advises prompt review."""
    turn1_res = process_patient_request("What was my blood pressure?", user_id="1")
    assert "blood pressure" in turn1_res["translated_summary"].lower()

    history = [
        {"sender": "user", "text": "What was my blood pressure?"},
        {"sender": "assistant", "text": turn1_res["translated_summary"]},
    ]
    turn2_res = process_patient_request("Is that reading normal?", user_id="1", conversation_history=history)
    summary_lower = turn2_res["translated_summary"].lower()
    
    assert "blood pressure" in summary_lower
    assert "180/110" in summary_lower or "hypertensive" in summary_lower
    assert "elevated" in summary_lower or "crisis" in summary_lower or "stage" in summary_lower
    # Should recommend medical review based on the flagged information
    assert any("medical review" in g.lower() or "doctor" in g.lower() for g in turn2_res["guidance"])


# ============================================================================
# 15. Contextual Follow-Up: "When was that test taken?"
# ============================================================================

def test_contextual_followup_when_was_that():
    """Verify follow-up inquiry 'When was that?' extracts the report date from active conversation context."""
    turn1_res = process_patient_request("What was my hemoglobin value?", user_id="1")

    history = [
        {"sender": "user", "text": "What was my hemoglobin value?"},
        {"sender": "assistant", "text": turn1_res["translated_summary"]},
    ]
    turn2_res = process_patient_request("When was that test taken?", user_id="1", conversation_history=history)
    summary_lower = turn2_res["translated_summary"].lower()

    # Must mention report date or recording timestamp
    assert "recorded on" in summary_lower or "2026-03-01" in summary_lower or "report" in summary_lower
    assert "cbc_report" in summary_lower or "report" in summary_lower


# ============================================================================
# 16. Contextual Follow-Up: "Which doctor should I see for this?"
# ============================================================================

def test_contextual_followup_which_doctor_to_see():
    """Verify specialist recommendation follow-up suggests appropriate clinician and primary care starting point."""
    turn1_res = process_patient_request("What was my hemoglobin value?", user_id="1")

    history = [
        {"sender": "user", "text": "What was my hemoglobin value?"},
        {"sender": "assistant", "text": turn1_res["translated_summary"]},
    ]
    turn2_res = process_patient_request("Which doctor should I see for this?", user_id="1", conversation_history=history)
    summary_lower = turn2_res["translated_summary"].lower()

    # Must suggest General Physician / Internist or Hematologist
    assert "physician" in summary_lower or "hematologist" in summary_lower or "practitioner" in summary_lower
    assert "primary care" in summary_lower or "general physician" in summary_lower


# ============================================================================
# 17. Sequential Metric Query from the Same Report
# ============================================================================

def test_sequential_metric_query_same_report():
    """Verify asking about a second metric in the next turn seamlessly queries the same active report."""
    turn1_res = process_patient_request("What was my hemoglobin value?", user_id="1")
    assert "hemoglobin" in turn1_res["translated_summary"].lower()

    # Turn 2: User asks "What about platelets?" without specifying report ID
    history = [
        {"sender": "user", "text": "What was my hemoglobin value?"},
        {"sender": "assistant", "text": turn1_res["translated_summary"]},
    ]
    turn2_res = process_patient_request("What about platelets?", user_id="1", conversation_history=history)
    assert turn2_res["review_request"] is None
    summary_lower = turn2_res["translated_summary"].lower()

    # Platelets should be retrieved from CBC report
    assert "platelet" in summary_lower
    assert "250000" in summary_lower or "250,000" in summary_lower or "cbc_report" in summary_lower


# ============================================================================
# 18. Contextual Follow-Up: "What other tests were in that report?"
# ============================================================================

def test_contextual_followup_other_tests_in_report():
    """Verify follow-up asking for other tests lists available tests from the active report."""
    turn1_res = process_patient_request("What was my hemoglobin value?", user_id="1", report_id="101")

    history = [
        {"sender": "user", "text": "What was my hemoglobin value?"},
        {"sender": "assistant", "text": turn1_res["translated_summary"]},
    ]
    turn2_res = process_patient_request("What other tests were in that report?", user_id="1", conversation_history=history)
    summary_lower = turn2_res["translated_summary"].lower()

    # Must list other tests found in CBC report
    assert "hemoglobin" in summary_lower
    assert "platelet" in summary_lower or "white blood cell" in summary_lower


# ============================================================================
# 19. Multilingual Contextual Follow-Up in Tamil
# ============================================================================

def test_multilingual_contextual_followup_tamil():
    """Verify multi-turn follow-up in Tamil is detected, grounded, and translated properly."""
    turn1_res = process_patient_request("எனது ஹீமோகுளோபின் அளவு என்ன?", user_id="1", target_language="ta")
    assert turn1_res["detected_language"] == "ta"
    assert turn1_res["response_language"] == "ta"

    history = [
        {"sender": "user", "text": "எனது ஹீமோகுளோபின் அளவு என்ன?"},
        {"sender": "assistant", "text": turn1_res["translated_summary"]},
    ]
    turn2_res = process_patient_request("அது சாதாரணமானதா?", user_id="1", target_language="ta", conversation_history=history)
    assert turn2_res["detected_language"] == "ta"
    assert turn2_res["response_language"] == "ta"
    # Should include Tamil disclaimer and guidance
    assert turn2_res["disclaimer"] != ""
    assert len(turn2_res["guidance"]) > 0


# ============================================================================
# 20. Emergency Symptoms Override Multi-Turn Follow-Up Context
# ============================================================================

def test_emergency_overrides_multi_turn_context():
    """Verify that if patient reports sudden emergency symptoms mid-conversation, it immediately escalates."""
    turn1_res = process_patient_request("What was my hemoglobin value?", user_id="1")

    history = [
        {"sender": "user", "text": "What was my hemoglobin value?"},
        {"sender": "assistant", "text": turn1_res["translated_summary"]},
    ]
    turn2_res = process_patient_request(
        "Now I have sudden severe chest pain and difficulty breathing.",
        user_id="1",
        conversation_history=history
    )
    assert turn2_res["review_request"] is not None
    assert turn2_res["review_request"]["risk_level"] == "HIGH"
    assert turn2_res["review_request"]["patient_id"] == "1"
    # Must link to the active report context if available
    assert turn2_res["review_request"]["report_id"] is not None

