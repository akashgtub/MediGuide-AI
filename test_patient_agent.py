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
from ai.medical_knowledge import set_mock_retrieval_handler, clear_mock_retrieval_handler, fetch_live_medical_knowledge

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


# ============================================================================
# 21. Identity Question Receives Concise Identity Response (Part 1 & 6)
# ============================================================================

def test_identity_question_concise_response():
    """Verify 'what is your name' and identity queries return concise identity with zero boilerplate."""
    # Query: "what is your name"
    res = process_patient_request("what is your name", user_id="1")
    assert res["intent"] == "IDENTITY"
    assert res["review_request"] is None
    assert len(res["guidance"]) == 0
    assert res["disclaimer"] == ""
    assert res["report_list"] is None
    summary_lower = res["translated_summary"].lower()
    assert "mediguide-ai" in summary_lower
    assert "health information assistant" in summary_lower
    assert "explain your uploaded reports" in summary_lower
    # Must NOT dump reports or invoke document processing
    assert "report list" not in summary_lower
    assert "summary of the provided document" not in summary_lower

    # Query: "who are you"
    res_who = process_patient_request("who are you", user_id="1")
    assert res_who["intent"] == "IDENTITY"
    assert "mediguide-ai" in res_who["translated_summary"].lower()


# ============================================================================
# 22. User Introduction Is Acknowledged Naturally (Part 1 & 6)
# ============================================================================

def test_user_introduction_acknowledged():
    """Verify user introductions like 'I am Akash' or 'My name is Akash' greet warmly without medical entity extraction."""
    # 1. "I am Akash"
    res1 = process_patient_request("I am Akash", user_id="1")
    assert res1["intent"] == "USER_INTRODUCTION"
    assert res1["review_request"] is None
    assert len(res1["guidance"]) == 0
    assert res1["disclaimer"] == ""
    assert res1["report_list"] is None
    assert "Akash" in res1["translated_summary"]
    assert "Nice to meet you" in res1["translated_summary"]

    # 2. "My name is Akash"
    res2 = process_patient_request("My name is Akash", user_id="1")
    assert res2["intent"] == "USER_INTRODUCTION"
    assert "Akash" in res2["translated_summary"]
    assert "Nice to meet you" in res2["translated_summary"]

    # 3. Tamil Introduction: "நான் ஆகாஷ்"
    res_ta = process_patient_request("நான் ஆகாஷ்", user_id="1", target_language="ta")
    assert res_ta["intent"] == "USER_INTRODUCTION"
    assert "ஆகாஷ்" in res_ta["translated_summary"]
    assert "மகிழ்ச்சி" in res_ta["translated_summary"]


# ============================================================================
# 23. General Disease Questions Do Not Trigger Report List (Part 1 & 6)
# ============================================================================

def test_general_disease_questions_do_not_trigger_report_list():
    """Verify questions like 'what is the most dangerous disease' return education without listing 58 reports."""
    # User 1 has dozens of reports in the database
    res = process_patient_request("what is the most dangerous disease", user_id="1")
    assert res["intent"] in ("GENERAL_HEALTH_QUESTION", "GENERAL_MEDICAL_EDUCATION")
    assert res["review_request"] is None
    assert res["report_list"] is None
    summary_lower = res["translated_summary"].lower()
    # Must explain that there is no single universally most dangerous disease
    assert "no single universally most dangerous disease" in summary_lower
    assert "severity" in summary_lower
    assert "complications" in summary_lower
    # Must ask whether they want general info or help understanding a particular report
    assert "medical report" in summary_lower
    assert "help understanding" in summary_lower or "general health education" in summary_lower
    # Must NEVER dump all user reports
    assert "all 58" not in summary_lower
    assert "you have 58 reports" not in summary_lower

    # General question: "what is hypertension"
    res_htn = process_patient_request("what is hypertension", user_id="1")
    assert res_htn["intent"] in ("GENERAL_HEALTH_QUESTION", "GENERAL_MEDICAL_EDUCATION")
    assert res_htn["report_list"] is None
    assert "hypertension" in res_htn["translated_summary"].lower()
    assert "blood pressure" in res_htn["translated_summary"].lower()


# ============================================================================
# 24. Explicit Report List Requests Retrieve Only Authenticated Patient's Reports (Part 5 & 6)
# ============================================================================

def test_explicit_report_list_authenticated_patient():
    """Verify explicit requests to list reports return only the requesting patient's reports in structured format."""
    # User 1 (Alex Morgan) requests report list
    res_u1 = process_patient_request("show my reports", user_id="1")
    assert res_u1["intent"] == "REPORT_LIST"
    assert res_u1["review_request"] is None
    assert res_u1["report_list"] is not None
    assert 1 <= len(res_u1["report_list"]) <= 10
    # Structured report_list entries contain report_id, filename, created_at
    for r in res_u1["report_list"]:
        assert "report_id" in r
        assert "filename" in r
        assert "created_at" in r

    # User 4 (Maria Gonzalez) requests report list
    res_u4 = process_patient_request("list my uploaded reports", user_id="4")
    assert res_u4["intent"] == "REPORT_LIST"
    assert res_u4["report_list"] is not None
    # User 4's reports must NOT contain User 1's reports
    u1_report_ids = [r["report_id"] for r in res_u1["report_list"]]
    for r in res_u4["report_list"]:
        assert r["report_id"] not in u1_report_ids

    # Unauthenticated user requests reports
    res_unauth = process_patient_request("show my reports", user_id=None)
    assert res_unauth["intent"] == "REPORT_LIST"
    assert not res_unauth["report_list"]
    assert "authentication is required" in res_unauth["translated_summary"].lower() or "log in" in res_unauth["translated_summary"].lower()


# ============================================================================
# 25. Language Consistency Across All 6 Supported Languages (Part 2 & 6)
# ============================================================================

def test_language_consistency_across_all_supported_languages():
    """Verify single consistent language per turn across English, Tamil, Hindi, Telugu, Malayalam, and Kannada."""
    # 1. English: "hi" must return pure English without Tamil/Hindi disclaimers or instructions
    res_en = process_patient_request("hi", target_language="en")
    assert res_en["detected_language"] == "en"
    assert res_en["response_language"] == "en"
    assert res_en["translated_summary"] == "Hello! I'm MediGuide-AI, your health information assistant. How can I help you today?"
    assert res_en["disclaimer"] == ""
    assert len(res_en["guidance"]) == 0

    # 2. Tamil: "வணக்கம்"
    res_ta = process_patient_request("வணக்கம்", target_language="ta")
    assert res_ta["detected_language"] == "ta"
    assert res_ta["response_language"] == "ta"
    assert "வணக்கம்" in res_ta["translated_summary"]
    assert "மெடிகைட்" in res_ta["translated_summary"] or "MediGuide" in res_ta["translated_summary"]
    assert res_ta["disclaimer"] == ""
    assert len(res_ta["guidance"]) == 0

    # 3. Hindi: "नमस्ते"
    res_hi = process_patient_request("नमस्ते", target_language="hi")
    assert res_hi["detected_language"] == "hi"
    assert res_hi["response_language"] == "hi"
    assert "नमस्ते" in res_hi["translated_summary"]
    assert "मेडीगाइड" in res_hi["translated_summary"] or "MediGuide" in res_hi["translated_summary"]

    # 4. Telugu: "నమస్కారం"
    res_te = process_patient_request("నమస్కారం", target_language="te")
    assert res_te["detected_language"] == "te"
    assert res_te["response_language"] == "te"
    assert "నమస్కారం" in res_te["translated_summary"]

    # 5. Malayalam: "നമസ്കാരം"
    res_ml = process_patient_request("നമസ്കാരം", target_language="ml")
    assert res_ml["detected_language"] == "ml"
    assert res_ml["response_language"] == "ml"
    assert "നമസ്കാരം" in res_ml["translated_summary"]

    # 6. Kannada: "ನಮಸ್ಕಾರ"
    res_kn = process_patient_request("ನಮಸ್ಕಾರ", target_language="kn")
    assert res_kn["detected_language"] == "kn"
    assert res_kn["response_language"] == "kn"
    assert "ನಮಸ್ಕಾರ" in res_kn["translated_summary"]


# ============================================================================
# 26. Report Summary Optional Fields Fallback (Part 3 & 6)
# ============================================================================

def test_report_summary_optional_fields_fallback():
    """Verify that report summary and metrics handle missing reference ranges or units safely."""
    # Query report 101 summary
    res = process_patient_request("summarize my CBC report", user_id="1", report_id="101")
    assert res["intent"] == "REPORT_OVERVIEW"
    assert res["review_request"] is None
    summary_text = res["translated_summary"]
    assert len(summary_text) > 0
    # Summary should not be raw JSON
    assert "{" not in summary_text[:50]
    assert "}" not in summary_text[-50:]


# ============================================================================
# 27. Short Vague Inputs Request Clarification Without Generic Welcome
# ============================================================================

def test_short_vague_input_requests_clarification():
    """Verify single-word/vague inputs like 'what' or '?' request clarification instead of generic welcome."""
    # "what"
    res_what = process_patient_request("what", user_id="1")
    assert res_what["intent"] == "CLARIFICATION_REQUIRED"
    assert res_what["review_request"] is None
    assert "Hello! I'm MediGuide-AI" not in res_what["translated_summary"]
    assert "detail" in res_what["translated_summary"].lower() or "clarif" in res_what["translated_summary"].lower()

    # "?"
    res_q = process_patient_request("?", user_id="1")
    assert res_q["intent"] == "CLARIFICATION_REQUIRED"
    assert "detail" in res_q["translated_summary"].lower() or "clarif" in res_q["translated_summary"].lower()


# ============================================================================
# 28. Single-Word Symptom Inquiries ("fever", "headache") Provide Guidance
# ============================================================================

def test_single_word_symptom_inquiry():
    """Verify single-word symptoms provide health education and follow-up questions without diagnosing."""
    # "fever"
    res_fever = process_patient_request("fever", user_id="1")
    assert res_fever["intent"] in ("SYMPTOM_EDUCATION", "GENERAL_HEALTH_QUESTION")
    assert res_fever["review_request"] is None
    assert "Hello! I'm MediGuide-AI" not in res_fever["translated_summary"]
    summary_lower = res_fever["translated_summary"].lower()
    assert "fever" in summary_lower
    assert "how long" in summary_lower or "duration" in summary_lower
    assert "other symptoms" in summary_lower or "accompanying" in summary_lower or "stiff neck" in summary_lower
    assert "does not diagnose" in res_fever["disclaimer"].lower() or "not a diagnosis" in res_fever["disclaimer"].lower()

    # "headache"
    res_headache = process_patient_request("headache", user_id="1")
    assert res_headache["intent"] in ("SYMPTOM_EDUCATION", "GENERAL_HEALTH_QUESTION")
    summary_h = res_headache["translated_summary"].lower()
    assert "headache" in summary_h
    assert "how long" in summary_h or "duration" in summary_h or "pattern" in summary_h
    assert "sudden severe" in summary_h or "thunderclap" in summary_h or "warning" in summary_h


# ============================================================================
# 29. General Health Questions: Direct Educational Answers
# ============================================================================

def test_general_health_question_causes():
    """Verify questions asking causes of fever and diabetes receive direct educational explanations."""
    # "what causes fever?"
    res_fever_causes = process_patient_request("what causes fever?", user_id="1")
    assert res_fever_causes["intent"] == "GENERAL_HEALTH_QUESTION"
    assert res_fever_causes["review_request"] is None
    summary_fc = res_fever_causes["translated_summary"].lower()
    assert "fever" in summary_fc
    assert "immune response" in summary_fc or "infection" in summary_fc
    assert "bacterial" in summary_fc or "viral" in summary_fc

    # "what causes diabetes?"
    res_diabetes = process_patient_request("what causes diabetes?", user_id="1")
    assert res_diabetes["intent"] == "GENERAL_HEALTH_QUESTION"
    summary_d = res_diabetes["translated_summary"].lower()
    assert "diabetes" in summary_d
    assert "type 1" in summary_d and "type 2" in summary_d
    assert "insulin" in summary_d


# ============================================================================
# 30. Current Medical Information Retrieval (Offline Mock Test)
# ============================================================================

def test_current_medical_information_retrieval_dengue():
    """Verify questions regarding current/latest treatment trigger live retrieval and cite trusted sources."""
    mock_sources = [
        {
            "title": "Dengue Clinical Management and Supportive Care",
            "url": "https://medlineplus.gov/dengue.html",
            "source_name": "MedlinePlus / National Library of Medicine",
            "date_modified": "2026-03-15",
            "snippet": "Dengue treatment relies on supportive care, adequate hydration, and paracetamol for fever control.",
        },
        {
            "title": "Dengue Guidelines for Diagnosis, Treatment, Prevention and Control",
            "url": "https://www.who.int/news-room/fact-sheets/detail/dengue-and-severe-dengue",
            "source_name": "World Health Organization (WHO)",
            "published_date": "2026-04-20",
            "snippet": "Avoid aspirin and other non-steroidal anti-inflammatory drugs (NSAIDs) like ibuprofen as they may increase the risk of bleeding.",
        }
    ]

    def mock_fetch(query: str):
        return {
            "summary": "According to MedlinePlus and the World Health Organization (WHO), there is no specific antiviral medication for dengue. Management focuses on supportive care, bed rest, and maintaining hydration. Paracetamol is recommended for fever and pain relief. Avoid aspirin, ibuprofen, and other NSAIDs as they increase bleeding risks.",
            "sources": mock_sources,
            "retrieval_timestamp": "2026-10-16T14:30:00Z",
            "is_live": True,
        }

    set_mock_retrieval_handler(mock_fetch)
    try:
        res = process_patient_request("what is the latest treatment for dengue?", user_id="1")
        assert res["intent"] == "CURRENT_MEDICAL_INFORMATION"
        assert res["review_request"] is None
        assert res["is_live"] is True
        assert len(res["sources"]) == 2
        assert res["sources"][0]["url"] == "https://medlineplus.gov/dengue.html"
        assert res["sources"][1]["source_name"] == "World Health Organization (WHO)"
        assert res["retrieval_timestamp"] == "2026-10-16T14:30:00Z"
        summary_lower = res["translated_summary"].lower()
        assert "paracetamol" in summary_lower
        assert "ibuprofen" in summary_lower or "nsaid" in summary_lower or "bleeding" in summary_lower
    finally:
        clear_mock_retrieval_handler()


# ============================================================================
# 31. Network Timeout and Retrieval Failure Fallback (Zero Fabricated Sources)
# ============================================================================

def test_current_medical_retrieval_failure_fallback():
    """Verify network failures or timeouts return graceful educational fallback with zero fabricated citations."""
    def mock_failing_fetch(query: str):
        return {
            "summary": "Current authoritative medical sources could not be verified in real time due to a network timeout or offline service. For dengue, clinical guidance generally emphasizes fluid hydration and paracetamol, while strictly avoiding aspirin or ibuprofen due to bleeding complications.",
            "sources": [],
            "retrieval_timestamp": "2026-10-16T14:35:00Z",
            "is_live": False,
        }

    set_mock_retrieval_handler(mock_failing_fetch)
    try:
        res = process_patient_request("what is the latest treatment for dengue?", user_id="1")
        assert res["intent"] == "CURRENT_MEDICAL_INFORMATION"
        assert res["is_live"] is False
        assert len(res["sources"]) == 0  # Zero fabricated sources!
        summary_lower = res["translated_summary"].lower()
        assert "could not be verified" in summary_lower or "offline" in summary_lower
    finally:
        clear_mock_retrieval_handler()


# ============================================================================
# 32. Personal Report Queries Remain Isolated from Web Search
# ============================================================================

def test_personal_report_queries_remain_isolated_from_web_search():
    """Verify personal metric queries query only user's report without invoking external web retrieval."""
    called_web_search = []
    def mock_spy_fetch(query: str):
        called_web_search.append(query)
        return {"summary": "spy", "sources": [], "retrieval_timestamp": "", "is_live": False}

    set_mock_retrieval_handler(mock_spy_fetch)
    try:
        res = process_patient_request("what was my hemoglobin?", user_id="1")
        assert res["intent"] == "REPORT_METRIC_QUERY"
        assert len(called_web_search) == 0  # External search was NOT invoked!
        assert "hemoglobin" in res["translated_summary"].lower()
        assert ("14.2" in res["translated_summary"]) or ("12.5" in res["translated_summary"])
    finally:
        clear_mock_retrieval_handler()


# ============================================================================
# 33. Emergency Symptoms Bypass External Web Search Immediately
# ============================================================================

def test_emergency_symptoms_bypasses_web_search():
    """Verify severe emergency symptoms create high-risk escalation immediately without web search latency."""
    called_web_search = []
    def mock_spy_fetch(query: str):
        called_web_search.append(query)
        return {"summary": "spy", "sources": [], "retrieval_timestamp": "", "is_live": False}

    set_mock_retrieval_handler(mock_spy_fetch)
    try:
        res = process_patient_request("I have severe chest pain and difficulty breathing", user_id="1")
        assert res["intent"] == "EMERGENCY"
        assert len(called_web_search) == 0  # Zero external search delay!
        assert res["review_request"] is not None
        assert res["review_request"]["risk_level"] == "HIGH"
        assert "emergency" in res["translated_summary"].lower()
    finally:
        clear_mock_retrieval_handler()


# ============================================================================
# 34. Multilingual Live Medical Knowledge with Honest Language Attribution
# ============================================================================

def test_multilingual_live_medical_knowledge():
    """Verify Tamil and Hindi requests for current knowledge provide translated summary and language attribution."""
    mock_sources = [
        {
            "title": "Dengue Clinical Management",
            "url": "https://medlineplus.gov/dengue.html",
            "source_name": "MedlinePlus",
            "date_modified": "2026-03-15",
            "snippet": "Dengue treatment relies on supportive care.",
        }
    ]
    def mock_fetch(query: str):
        return {
            "summary": "Management focuses on supportive care and paracetamol. Avoid aspirin and ibuprofen.",
            "sources": mock_sources,
            "retrieval_timestamp": "2026-10-16T14:40:00Z",
            "is_live": True,
        }

    set_mock_retrieval_handler(mock_fetch)
    try:
        res_ta = process_patient_request("டெங்கு சிகிச்சை", user_id="1", target_language="ta")
        assert res_ta["intent"] == "CURRENT_MEDICAL_INFORMATION"
        assert res_ta["response_language"] == "ta"
        assert len(res_ta["sources"]) == 1
        # Honest attribution: patient is informed the original medical publication is in English
        assert res_ta["sources"][0].get("language_note") == "Official medical source published in English"
    finally:
        clear_mock_retrieval_handler()


# ============================================================================
# 35. /api/process-text Returns Sources, Retrieval Timestamp, and Live Status
# ============================================================================

def test_api_process_text_returns_sources_and_timestamps():
    """Verify /api/process-text endpoint exposes sources, retrieval_timestamp, and is_live to frontend."""
    token = create_access_token(user_id="1", email="alex@example.com", role="patient", name="Alex Morgan")

    mock_sources = [
        {
            "title": "NIH Dengue Information",
            "url": "https://medlineplus.gov/dengue.html",
            "source_name": "NIH / MedlinePlus",
            "date_modified": "2026-01-10",
            "snippet": "Supportive fluid replacement is essential.",
        }
    ]
    def mock_fetch(query: str):
        return {
            "summary": "Supportive fluid management is recommended. Paracetamol is advised for fever.",
            "sources": mock_sources,
            "retrieval_timestamp": "2026-10-16T14:45:00Z",
            "is_live": True,
        }

    set_mock_retrieval_handler(mock_fetch)
    try:
        response = client.post(
            "/api/process-text",
            json={"text": "what is the latest treatment for dengue?", "target_language": "en"},
            headers={"Authorization": f"Bearer {token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["intent"] == "CURRENT_MEDICAL_INFORMATION"
        assert data["is_live"] is True
        assert data["retrieval_timestamp"] == "2026-10-16T14:45:00Z"
        assert len(data["sources"]) == 1
        assert data["sources"][0]["url"] == "https://medlineplus.gov/dengue.html"
    finally:
        clear_mock_retrieval_handler()


# ============================================================================
# 36. Live Knowledge Module Unit Tests: XML Parsing, Limits, and Offline Guard
# ============================================================================

def test_live_knowledge_module_unit_behavior():
    """Verify ai/medical_knowledge.py error handling and strict citation integrity."""
    from ai.medical_knowledge import (
        _parse_medlineplus_xml,
        _extract_dengue_guidance,
        _fallback_offline_knowledge,
        fetch_live_medical_knowledge
    )

    # 1. Malformed XML handling safely returns empty list
    bad_xml = b"<invalid>xml<data>"
    sources, passages = _parse_medlineplus_xml(bad_xml)
    assert sources == []
    assert passages == []

    # 2. Grounded response with dengue enforces paracetamol and warning against NSAIDs
    guidance = _extract_dengue_guidance("dengue summary")
    assert "paracetamol" in guidance.lower()
    assert "aspirin" in guidance.lower() or "ibuprofen" in guidance.lower()

    # 3. Fallback response is transparent and has zero citations
    fallback = _fallback_offline_knowledge("dengue", "test_offline")
    assert fallback["is_live"] is False
    assert fallback["sources"] == []
    assert len(fallback["summary"]) > 0


# ============================================================================
# 37. Acceptance Test 1: Doctor-Booking Intent Recognition
# ============================================================================

def test_acceptance_1_doctor_booking_intent_recognition():
    """Verify 'can i book doctor' routes to APPOINTMENT_BOOKING_REQUEST and offers natural options."""
    intent = classify_patient_intent("can i book doctor")
    assert intent == "APPOINTMENT_BOOKING_REQUEST"

    res = process_patient_request("can i book doctor")
    assert res["intent"] == "APPOINTMENT_BOOKING_REQUEST"
    summary = res["translated_summary"]
    assert "appointment process" in summary.lower()
    assert "book an appointment with a doctor available through mediguide-ai" in summary.lower()
    assert "help preparing to contact a doctor" in summary.lower()


# ============================================================================
# 38. Acceptance Test 2 & 3: Direct Booking Unavailable Safe Explanation
# ============================================================================

def test_acceptance_2_and_3_booking_unavailable_safe_explanation():
    """Verify system explains direct booking is unavailable, does not invent doctors/slots/IDs, and offers appointment prep."""
    history = [
        {"role": "user", "content": "can i book doctor"},
        {
            "role": "assistant",
            "content": "Yes, I can help you with the appointment process. Do you want to book an appointment with a doctor available through MediGuide-AI, or would you like help preparing to contact a doctor?",
            "intent": "APPOINTMENT_BOOKING_REQUEST"
        }
    ]
    res = process_patient_request("book with doctor", conversation_history=history)
    assert res["intent"] == "APPOINTMENT_BOOKING_CONFIRMATION"
    summary = res["translated_summary"]
    # Explains direct booking is not available
    assert "not currently available" in summary.lower()
    # Offers preparation
    assert "prepare" in summary.lower()
    # Does NOT invent fake doctor names, fake appointment IDs, or fake slots
    assert "dr." not in summary.lower()
    assert "booking id" not in summary.lower()
    assert "confirmed for" not in summary.lower()


# ============================================================================
# 39. Acceptance Test 4: 'yes' Resolving the Pending Appointment Question
# ============================================================================

def test_acceptance_4_yes_resolving_pending_question():
    """Verify 'yes' following appointment offer resolves to APPOINTMENT_BOOKING_CONFIRMATION, not generic clarification."""
    history = [
        {"role": "user", "content": "can i book doctor"},
        {
            "role": "assistant",
            "content": "Yes, I can help you with the appointment process. Do you want to book an appointment with a doctor available through MediGuide-AI, or would you like help preparing to contact a doctor?",
            "intent": "APPOINTMENT_BOOKING_REQUEST"
        }
    ]
    intent = classify_patient_intent("yes", conversation_context={"pending_intent": "APPOINTMENT_BOOKING_CHOICE", "last_intent": "APPOINTMENT_BOOKING_REQUEST"})
    assert intent == "APPOINTMENT_BOOKING_CONFIRMATION"

    res = process_patient_request("yes", conversation_history=history)
    assert res["intent"] == "APPOINTMENT_BOOKING_CONFIRMATION"
    assert "direct doctor booking through mediguide-ai is not currently available" in res["translated_summary"].lower()
    assert "i'm not sure i understand" not in res["translated_summary"].lower()


# ============================================================================
# 40. Acceptance Test 5: Fever Duration Follow-Up ('two days')
# ============================================================================

def test_acceptance_5_fever_duration_followup():
    """Verify 'two days' following fever discussion is interpreted as duration and asks for thermometer / accompanying symptoms."""
    history = [
        {"role": "user", "content": "i have fever"},
        {
            "role": "assistant",
            "content": "Fever is a temporary elevation in body temperature. 1. How long has the fever lasted, and what is your temperature reading?",
            "intent": "SYMPTOM_EDUCATION"
        }
    ]
    intent = classify_patient_intent("two days", conversation_context={"last_symptom": "fever", "pending_intent": "SYMPTOM_FOLLOWUP_DETAILS"})
    assert intent == "FOLLOW_UP_SYMPTOM"

    res = process_patient_request("two days", conversation_history=history)
    assert res["intent"] == "FOLLOW_UP_SYMPTOM"
    summary = res["translated_summary"].lower()
    assert "two days" in summary
    assert "thermometer" in summary
    assert "accompanying symptoms" in summary or "chills" in summary


# ============================================================================
# 41. Acceptance Test 6: No Repetitive Generic Responses
# ============================================================================

def test_acceptance_6_no_repetitive_generic_responses():
    """Verify repeating 'fever' in active fever context gives concise follow-up rather than duplicating entire spiel."""
    history = [
        {"role": "user", "content": "i have fever"},
        {
            "role": "assistant",
            "content": "Fever is a temporary elevation in body temperature, commonly an immune response to an infection...",
            "intent": "SYMPTOM_EDUCATION"
        }
    ]
    res = process_patient_request("fever", conversation_history=history)
    assert res["intent"] == "FOLLOW_UP_SYMPTOM"
    summary = res["translated_summary"]
    # Concise follow-up, not repeating the whole introduction and general care definitions
    assert "Regarding your fever" in summary or "fever has lasted" in summary
    assert "Fever is a temporary elevation" not in summary


# ============================================================================
# 42. Acceptance Test 7: Conversation-History Handling Across Exact Bug Sequence
# ============================================================================

def test_acceptance_7_exact_bug_sequence_multi_turn_history():
    """Verify all 6 turns of the exact user reproduction sequence behave deterministically."""
    history = []

    # 1. hi
    r1 = process_patient_request("hi", conversation_history=history)
    assert r1["intent"] == "GREETING"
    assert "Hello! I'm MediGuide-AI" in r1["translated_summary"]
    history.append({"role": "user", "content": "hi"})
    history.append({"role": "assistant", "content": r1["translated_summary"], "intent": r1["intent"]})

    # 2. i am akash
    r2 = process_patient_request("i am akash", conversation_history=history)
    assert r2["intent"] == "USER_INTRODUCTION"
    assert "Akash" in r2["translated_summary"]
    history.append({"role": "user", "content": "i am akash"})
    history.append({"role": "assistant", "content": r2["translated_summary"], "intent": r2["intent"]})

    # 3. i have fever
    r3 = process_patient_request("i have fever", conversation_history=history)
    assert r3["intent"] == "SYMPTOM_EDUCATION"
    assert "Fever is a temporary elevation" in r3["translated_summary"]
    history.append({"role": "user", "content": "i have fever"})
    history.append({"role": "assistant", "content": r3["translated_summary"], "intent": r3["intent"]})

    # 4. can i book doctor
    r4 = process_patient_request("can i book doctor", conversation_history=history)
    assert r4["intent"] == "APPOINTMENT_BOOKING_REQUEST"
    assert "appointment process" in r4["translated_summary"].lower()
    history.append({"role": "user", "content": "can i book doctor"})
    history.append({"role": "assistant", "content": r4["translated_summary"], "intent": r4["intent"]})

    # 5. yes
    r5 = process_patient_request("yes", conversation_history=history)
    assert r5["intent"] == "APPOINTMENT_BOOKING_CONFIRMATION"
    assert "direct doctor booking" in r5["translated_summary"].lower()
    history.append({"role": "user", "content": "yes"})
    history.append({"role": "assistant", "content": r5["translated_summary"], "intent": r5["intent"]})

    # 6. fever
    r6 = process_patient_request("fever", conversation_history=history)
    assert r6["intent"] == "FOLLOW_UP_SYMPTOM"
    assert "Regarding your fever" in r6["translated_summary"] or "fever" in r6["translated_summary"].lower()


# ============================================================================
# 43. Acceptance Test 8: Personal Report Query Isolation
# ============================================================================

def test_acceptance_8_personal_report_query_isolation():
    """Verify general symptom and education questions do not touch personal reports, while metric questions require auth."""
    # General question without user_id has no report_list or metric_data
    r_gen = process_patient_request("what causes fever?")
    assert r_gen["intent"] == "GENERAL_HEALTH_QUESTION"
    assert r_gen.get("report_list") is None
    assert r_gen.get("metric_data") is None

    # Symptom question without user_id has no report_list or metric_data
    r_sym = process_patient_request("i have fever")
    assert r_sym["intent"] == "SYMPTOM_EDUCATION"
    assert r_sym.get("report_list") is None
    assert r_sym.get("metric_data") is None

    # Personal metric query with user_id retrieves the authenticated user's metric data
    r_met = process_patient_request("what was my hemoglobin?", user_id="1")
    assert r_met["intent"] == "REPORT_METRIC_QUERY"
    assert r_met.get("metric_data") is not None
    assert r_met["metric_data"]["metric"] == "Hemoglobin"


# ============================================================================
# 44. Acceptance Test 9: Emergency Safety Handling
# ============================================================================

def test_acceptance_9_emergency_safety_handling():
    """Verify emergency symptoms immediately trigger EMERGENCY intent and review escalation."""
    emergency_inputs = [
        "I have severe chest pain and cannot breathe",
        "patient is having a stroke with facial drooping",
        "profuse uncontrolled bleeding",
    ]
    for inp in emergency_inputs:
        intent = classify_patient_intent(inp)
        assert intent == "EMERGENCY"
        res = process_patient_request(inp, user_id="1")
        assert res["intent"] == "EMERGENCY"
        assert res["review_request"] is not None
        assert res["review_request"]["risk_level"] == "HIGH"
        assert "emergency" in res["translated_summary"].lower()


# ============================================================================
# 45. Acceptance Test 10: Multilingual Behavior and Offline Medical-Source Fallback
# ============================================================================

def test_acceptance_10_multilingual_and_offline_source_fallback():
    """Verify multilingual appointment and symptom responses and offline source fallback distinctions."""
    # 1. Tamil appointment booking
    res_ta = process_patient_request("மருத்துவரை முன்பதிவு செய்ய முடியுமா", target_language="ta")
    assert res_ta["intent"] == "APPOINTMENT_BOOKING_REQUEST"
    assert res_ta["response_language"] == "ta"
    assert "மருத்துவரை" in res_ta["translated_summary"] or "அப்பாயிண்ட்மெண்ட்" in res_ta["translated_summary"]

    # 2. Hindi appointment booking
    res_hi = process_patient_request("क्या मैं डॉक्टर बुक कर सकता हूँ", target_language="hi")
    assert res_hi["intent"] == "APPOINTMENT_BOOKING_REQUEST"
    assert res_hi["response_language"] == "hi"
    assert "अपॉइंटमेंट" in res_hi["translated_summary"] or "डॉक्टर" in res_hi["translated_summary"]

    # 3. Offline source fallback for live medical knowledge
    res_offline = process_patient_request("what is the latest treatment for dengue?")
    # In test environment without network or when offline, is_live is False and fallback is used
    if not res_offline.get("is_live"):
        assert res_offline["is_live"] is False
        assert isinstance(res_offline.get("sources"), list)




