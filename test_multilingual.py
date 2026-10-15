"""
Automated Unit and Integration Tests for Multilingual Support in MediGuide-AI.
Covers:
- All 6 supported language codes and native labels (en, ta, hi, te, ml, kn)
- Unicode script detection for Tamil, Hindi, Telugu, Malayalam, and Kannada
- Saving, retrieving, and persisting language preferences in SQLite
- Switching languages during patient assistant conversations
- Medical values, dosages, units, dates, and test results remaining unchanged
- Report translation without modifying stored raw reports
- Non-diagnostic clinical safety disclaimers in all supported languages
- Emergency / high-risk escalation detection in native Indian languages
- Patient data isolation and authentication protection
- Backward compatibility with existing API endpoints
"""

import io
import json
import sqlite3
import pytest
from fastapi.testclient import TestClient

from backend.app import app
from backend.database import get_db_connection, DB_PATH, get_user_by_id, update_user_language
from backend.auth import create_access_token
from ai.translator import (
    translate_text,
    detect_language,
    is_language_supported,
    get_supported_languages,
    SUPPORTED_LANGUAGES,
)
from ai.patient_agent import process_patient_request

client = TestClient(app)


# ============================================================================
# 1. Supported Languages Metadata & Validation Tests
# ============================================================================

def test_supported_languages_list():
    """Verify all 6 required languages and native script names are present."""
    languages = get_supported_languages()
    assert len(languages) >= 6
    codes = {l["code"] for l in languages}
    expected_codes = {"en", "ta", "hi", "te", "ml", "kn"}
    assert expected_codes.issubset(codes)

    # Verify native script labels
    lang_map = {l["code"]: l["native_name"] for l in languages}
    assert lang_map["en"] == "English"
    assert lang_map["ta"] == "தமிழ்"
    assert lang_map["hi"] == "हिन्दी"
    assert lang_map["te"] == "తెలుగు"
    assert lang_map["ml"] == "മലയാളം"
    assert lang_map["kn"] == "ಕನ್ನಡ"

    # Verify validation helper
    for c in expected_codes:
        assert is_language_supported(c) is True
    assert is_language_supported("unknown_xyz") is False
    assert is_language_supported("") is False
    assert is_language_supported(None) is False


def test_api_languages_endpoint():
    """Verify GET /api/languages returns supported languages."""
    res = client.get("/api/languages")
    assert res.status_code == 200
    data = res.json()
    assert len(data) >= 6
    codes = [item["code"] for item in data]
    assert "en" in codes
    assert "ta" in codes
    assert "hi" in codes
    assert "te" in codes
    assert "ml" in codes
    assert "kn" in codes


# ============================================================================
# 2. Unicode Script Detection Tests
# ============================================================================

def test_unicode_script_detection():
    """Verify accurate detection of Tamil, Hindi, Telugu, Malayalam, and Kannada scripts."""
    # Tamil
    assert detect_language("வணக்கம் எனக்கு தலைவலி உள்ளது") == "ta"
    assert detect_language("எனது இரத்தப் பரிசோதனை முடிவுகள் என்ன சொல்கின்றன?") == "ta"

    # Hindi / Devanagari
    assert detect_language("नमस्ते मुझे सिरदर्द और बुखार है") == "hi"
    assert detect_language("मेरी रक्त जांच के परिणाम क्या कहते हैं?") == "hi"

    # Telugu
    assert detect_language("నమస్కారం నాకు తలనొప్పిగా ఉంది") == "te"
    assert detect_language("నా రక్త పరీక్ష ఫలితాలు ఏమి చెబుతున్నాయి?") == "te"

    # Malayalam
    assert detect_language("നമസ്കാരം എനിക്ക് തലവേദനയുണ്ട്") == "ml"
    assert detect_language("എന്റെ രക്തപരിശോധനാ ഫലങ്ങൾ എന്താണ് പറയുന്നത്?") == "ml"

    # Kannada
    assert detect_language("ನಮಸ್ಕಾರ ನನಗೆ ತಲೆನೋವು ಇದೆ") == "kn"
    assert detect_language("ನನ್ನ ರಕ್ತ ಪರೀಕ್ಷೆಯ ಫಲಿತಾಂಶಗಳು ಏನು ಹೇಳುತ್ತವೆ?") == "kn"

    # English / Latin default
    assert detect_language("Hello I have a headache") == "en"
    assert detect_language("") == "en"
    assert detect_language(None) == "en"


# ============================================================================
# 3. Clinical Medical Terminology & Value Preservation Tests
# ============================================================================

def test_medical_measurements_and_units_preserved_during_translation():
    """
    CRITICAL SAFETY REQUIREMENT:
    Measurements, scientific units, drug names, and dates must never be
    altered, lost, or mistranslated.
    """
    sample_summary = (
        "This is a summary of the provided document. "
        "Please note this is not a diagnosis or clinical recommendation. "
        "Reported symptoms: fatigue. "
        "Tests mentioned: blood pressure, hemoglobin. "
        "Dates found: 07 October 2026. "
        "Recorded measurements: 130/85, 12.5 (mmhg, g/dl)."
    )

    for target_lang in ["ta", "hi", "te", "ml", "kn"]:
        translated = translate_text(sample_summary, target_language=target_lang)
        # Numbers and vital metrics must remain verbatim
        assert "130/85" in translated, f"Failed for {target_lang}"
        assert "12.5" in translated, f"Failed for {target_lang}"
        # Units must remain verbatim
        assert "mmhg" in translated.lower(), f"Failed for {target_lang}"
        assert "g/dl" in translated.lower(), f"Failed for {target_lang}"
        # Date must remain verbatim
        assert "07 October 2026" in translated, f"Failed for {target_lang}"
        # English term preserved alongside translated concept
        assert "fatigue" in translated.lower(), f"Failed for {target_lang}"


def test_disclaimers_present_in_all_languages():
    """Verify safety disclaimers exist in all supported Indian languages."""
    standard_disclaimer = (
        "This is a summary of the provided document. "
        "Please note this is not a diagnosis or clinical recommendation."
    )

    for lang in ["ta", "hi", "te", "ml", "kn"]:
        trans = translate_text(standard_disclaimer, target_language=lang)
        assert len(trans) > 10
        assert trans != standard_disclaimer  # Must actually be translated


def test_backward_compatibility_with_es_fallback():
    """Verify backward compatibility with test_mediguide.py for unsupported language codes."""
    res_es = translate_text("Hello", target_language="es")
    assert res_es == "[Translated to es]: Hello"

    res_en = translate_text("Hello", target_language="en")
    assert res_en == "Hello"


# ============================================================================
# 4. User Language Preference Persistence Tests
# ============================================================================

def test_update_and_persist_language_preference():
    """Verify updating and persisting user preferred language via API and SQLite."""
    # 1. Update user 1 (Alex Morgan) language preference to Tamil
    token = create_access_token(user_id="1", email="alex@example.com", role="patient", name="Alex Morgan")
    res = client.patch(
        "/api/auth/language",
        json={"preferred_language": "ta"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code == 200
    assert res.json()["preferred_language"] == "ta"

    # 2. Verify /api/auth/me reflects the updated preference
    res_me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert res_me.status_code == 200
    assert res_me.json()["preferred_language"] == "ta"

    # 3. Direct SQLite verification
    user_db = get_user_by_id("1")
    assert user_db["preferred_language"] == "ta"

    # 4. Switch to Hindi and verify
    res_hi = client.patch(
        "/api/auth/language",
        json={"preferred_language": "hi"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res_hi.status_code == 200
    assert res_hi.json()["preferred_language"] == "hi"

    # Restore default for test isolation
    update_user_language("1", "en")


def test_update_language_invalid_code_rejected():
    """Verify invalid language code is rejected with 422/400."""
    token = create_access_token(user_id="1", email="alex@example.com", role="patient", name="Alex Morgan")
    res = client.patch(
        "/api/auth/language",
        json={"preferred_language": "invalid_lang"},
        headers={"Authorization": f"Bearer {token}"},
    )
    assert res.status_code in (400, 422)


def test_login_returns_preferred_language():
    """Verify /api/auth/login response includes preferred_language."""
    res = client.post("/api/auth/login", json={"email": "alex@example.com", "password": "patient123"})
    assert res.status_code == 200
    data = res.json()
    assert "preferred_language" in data["user"]


# ============================================================================
# 5. Multilingual Patient Agent & Conversation Tests
# ============================================================================

def test_process_text_in_tamil_direct():
    """Verify patient assistant processes direct question in Tamil and responds in Tamil."""
    res = client.post(
        "/api/process-text",
        json={
            "text": "எனது இரத்தப் பரிசோதனை முடிவுகள் என்ன சொல்கின்றன?",
            "target_language": "ta",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["detected_language"] == "ta"
    assert data["response_language"] == "ta"
    assert "translated_summary" in data
    assert len(data["translated_summary"]) > 0
    assert "disclaimer" in data


def test_process_text_in_hindi_direct():
    """Verify patient assistant processes question in Hindi."""
    res = client.post(
        "/api/process-text",
        json={
            "text": "मेरी रक्त जांच के परिणाम क्या कहते हैं?",
            "target_language": "hi",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["detected_language"] == "hi"
    assert data["response_language"] == "hi"


def test_multilingual_emergency_escalation():
    """Verify emergency symptoms in Indian languages trigger high risk escalation."""
    # Tamil severe chest pain
    res_ta = client.post(
        "/api/process-text",
        json={"text": "எனக்கு கடுமையான நெஞ்சு வலி உள்ளது", "target_language": "ta"},
    )
    assert res_ta.status_code == 200
    data_ta = res_ta.json()
    assert data_ta["review_request"] is not None
    assert data_ta["review_request"]["risk_level"] == "HIGH"

    # Hindi severe chest pain
    res_hi = client.post(
        "/api/process-text",
        json={"text": "मुझे गंभीर सीने में दर्द हो रहा है", "target_language": "hi"},
    )
    assert res_hi.status_code == 200
    data_hi = res_hi.json()
    assert data_hi["review_request"] is not None
    assert data_hi["review_request"]["risk_level"] == "HIGH"


# ============================================================================
# 6. Report Translation Endpoints & Ownership Tests
# ============================================================================

def test_report_translation_endpoint():
    """Verify POST /api/reports/{id}/translate translates summary to target language."""
    patient_token = create_access_token(user_id="1", email="alex@example.com", role="patient", name="Alex Morgan")
    res = client.post(
        "/api/reports/101/translate",
        json={"target_language": "ta"},
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["language"] == "ta"
    assert "summary" in data
    assert "guidance" in data
    # Measurements from report 101 must be preserved
    assert "14.2" in data["summary"]
    assert "g/dl" in data["summary"].lower()


def test_report_get_with_lang_query():
    """Verify GET /api/reports/101?lang=hi returns report with translated presentation layer."""
    patient_token = create_access_token(user_id="1", email="alex@example.com", role="patient", name="Alex Morgan")
    res = client.get(
        "/api/reports/101?lang=hi",
        headers={"Authorization": f"Bearer {patient_token}"},
    )
    assert res.status_code == 200
    data = res.json()
    assert data["language"] == "hi"
    assert "summary_original" in data
    assert data["summary_original"] != data["summary"]
    # Original text must NOT be overwritten
    assert "Complete Blood Count" in data["extracted_text"]


def test_report_translation_patient_isolation():
    """Verify patient cannot translate or access another patient's report."""
    maria_token = create_access_token(user_id="4", email="maria@example.com", role="patient", name="Maria Gonzalez")
    res = client.post(
        "/api/reports/101/translate",
        json={"target_language": "ta"},
        headers={"Authorization": f"Bearer {maria_token}"},
    )
    assert res.status_code == 403
