"""
Patient Health Assistant & Multilingual Clinical Agent for MediGuide-AI.
Combines document processing, entity extraction, summarization, clinical risk
evaluation, human review escalation, and multilingual translation.

Safety Guarantees:
- Always includes mandatory non-diagnostic disclaimers.
- Detects emergency high-risk indicators across all supported languages.
- Preserves patient data isolation: only accesses reports owned by the authenticated patient.
- Preserves exact numbers, units, medications, and dates without hallucination.
"""

import re
import logging
from typing import Optional, Dict, Any, List

from ai.document_processor import process_document
from ai.medical_extractor import extract_medical_info
from ai.summarizer import summarize_medical_info
from ai.translator import (
    translate_text,
    detect_language,
    is_language_supported,
    SUPPORTED_LANGUAGES,
    DEFAULT_LANGUAGE,
    CLINICAL_DISCLAIMERS,
)
from risk.risk_engine import evaluate_risk
from human_review.review_manager import create_review_request

logger = logging.getLogger("mediguide_patient_agent")

# Multilingual emergency / high-risk indicators
EMERGENCY_KEYWORDS = [
    # English
    "chest pain", "shortness of breath", "heart attack", "difficulty breathing",
    "severe headache", "stroke", "bleeding heavily",
    # Tamil
    "நெஞ்சு வலி", "மாரடைப்பு", "மூச்சுத்திணறல்", "சுவாசிப்பதில் சிரமம்", "கடுமையான தலைவலி",
    # Hindi
    "सीने में दर्द", "सांस लेने में तकलीफ", "दिल का दौरा", "गंभीर सिरदर्द",
    # Telugu
    "ఛాతీ నొప్పి", "శ్వాస ఆడకపోవడం", "గుండెపోటు", "తీవ్రమైన తలనొప్పి",
    # Malayalam
    "നെഞ്ചുവേദന", "ശ്വാസതടസ്സം", "ഹൃദയാഘാതം", "കഠിനമായ തലവേദന",
    # Kannada
    "ಎದೆ ನೋವು", "ಉಸಿರಾಟದ ತೊಂದರೆ", "ಹೃದಯಾಘಾತ", "ತೀವ್ರ ತಲೆನೋವು",
]

# Multilingual question intent patterns
REPORT_QUERY_PATTERNS = [
    "blood test", "results", "report", "test result", "findings", "what do my",
    "இரத்தப் பரிசோதனை", "முடிவுகள்", "அறிக்கை",
    "रक्त जांच", "परिणाम", "रिपोर्ट",
    "రక్త పరీక్ష", "ఫలితాలు", "రిపోర్ట్",
    "രക്തപരിശോധന", "ഫലങ്ങൾ", "റിപ്പോർട്ട്",
    "ರಕ್ತ ಪರೀಕ್ಷೆ", "ಫಲಿತಾಂಶಗಳು", "ವರದಿ",
]

RISK_QUERY_PATTERNS = [
    "danger", "risk", "serious", "worry", "critical", "harm", "problem",
    "ஆபத்து", "சிக்கல்", "பயப்பட",
    "खतरा", "जोखिम", "गंभीर", "चिंता",
    "ప్రమాదం", "సమస్య", "ఆందోళన",
    "അപകടം", "പ്രശ്നം", "ഭയം",
    "ಅಪಾಯ", "ತೊಂದರೆ", "ಚಿಂತೆ",
]


def _detect_emergency_intent(text: str) -> bool:
    """Check if text contains urgent high-risk medical terms across supported languages."""
    text_lower = text.lower()
    for kw in EMERGENCY_KEYWORDS:
        if kw in text_lower:
            return True
    return False


def _is_report_inquiry(text: str) -> bool:
    """Check if message is asking about existing test results or report."""
    text_lower = text.lower()
    return any(p in text_lower for p in REPORT_QUERY_PATTERNS)


def _is_risk_inquiry(text: str) -> bool:
    """Check if message is asking about risk or danger."""
    text_lower = text.lower()
    return any(p in text_lower for p in RISK_QUERY_PATTERNS)


def process_patient_request(
    document_text: str,
    target_language: str = "en",
    user_id: Optional[str] = None,
    report_id: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> dict:
    """
    Combine summary, translation, risk information, and safe guidance.
    Supports English, Tamil, Hindi, Telugu, Malayalam, and Kannada.
    Preserves exact backward compatibility with test_mediguide.py.
    """
    raw_query = document_text or ""
    
    # 1. Detect input language and resolve target language
    detected_lang = detect_language(raw_query)
    effective_target_lang = target_language.lower().strip() if target_language else DEFAULT_LANGUAGE

    # If user writes in an Indian script and target language is default English, respond in user's language
    if detected_lang != "en" and effective_target_lang == "en":
        effective_target_lang = detected_lang

    # 2. Check for emergency keywords across languages
    is_emergency = _detect_emergency_intent(raw_query)

    # 3. Handle contextual report Q&A and follow-ups if authorized user report exists
    context_report = None
    if user_id:
        try:
            from backend.database import get_reports_by_user, get_report_by_id
            if report_id:
                rep = get_report_by_id(report_id)
                if rep and rep.get("user_id") == user_id:
                    context_report = rep
            if not context_report:
                user_reports = get_reports_by_user(user_id=user_id)
                if user_reports:
                    context_report = user_reports[0]
        except Exception as e:
            logger.debug("Database report lookup for patient assistant: %s", e)

    # 4. Formulate response based on intent and authorized report context
    if is_emergency:
        # High-risk emergency escalation
        risk_result = {
            "is_high_risk": True,
            "reasons": ["Reported severe emergency symptoms."],
            "uncertainty_flag": False,
        }
        extracted_info = {
            "symptoms": ["severe symptoms / chest pain"],
            "medications": [],
            "test_names": [],
            "test_values": [],
            "units": [],
            "dates": [],
            "observations": [raw_query],
            "entities": [],
            "inferred_info": [],
        }
        summary_en = "Warning: Severe medical symptoms detected. Emergency clinical intervention is advised."
        guidance_en = [
            "Please seek professional medical review based on the flagged information.",
            "Seek immediate emergency medical attention.",
        ]
        review_request = create_review_request(extracted_info, summary_en, risk_result)

    elif context_report and (_is_risk_inquiry(raw_query) or _is_report_inquiry(raw_query)):
        # Patient is asking a follow-up about their report or risk status
        extracted_info = context_report.get("extracted_info", {})
        risk_result = context_report.get("risk_assessment", {"is_high_risk": False, "uncertainty_flag": False})
        
        if _is_risk_inquiry(raw_query):
            if risk_result.get("is_high_risk"):
                summary_en = (
                    f"Regarding your report ({context_report.get('filename', 'Report')}): "
                    "The AI engine flagged high-risk indicators that require professional clinician review. "
                    + context_report.get("summary", "")
                )
                guidance_en = ["Please seek professional medical review based on the flagged information."]
                review_request = create_review_request(extracted_info, summary_en, risk_result)
            else:
                summary_en = (
                    f"Regarding your report ({context_report.get('filename', 'Report')}): "
                    "No immediate high-risk emergency markers were flagged. "
                    + context_report.get("summary", "")
                )
                guidance_en = ["Prepare questions for a doctor and bring relevant documents to your next consultation."]
                review_request = None
        else:
            # Report summary inquiry
            summary_en = context_report.get("summary", "")
            guidance_en = context_report.get("guidance", ["Bring this document to your next doctor consultation."])
            review_request = None
    else:
        # Standard clinical processing pipeline
        cleaned_text = process_document(document_text)
        extracted_info = extract_medical_info(cleaned_text)
        summary_en = summarize_medical_info(extracted_info)
        risk_result = evaluate_risk(extracted_info)

        guidance_en = []
        review_request = None
        if risk_result.get("is_high_risk") or risk_result.get("uncertainty_flag"):
            guidance_en.append("Please seek professional medical review based on the flagged information.")
            review_request = create_review_request(extracted_info, summary_en, risk_result)
        else:
            guidance_en.append("Prepare questions for a doctor and bring relevant documents to your next consultation.")

    # 5. Multilingual Translation Layer
    translated_summary = translate_text(summary_en, effective_target_lang)
    translated_guidance = [translate_text(g, effective_target_lang) for g in guidance_en]
    
    std_disclaimer = CLINICAL_DISCLAIMERS["short_disclaimer"].get(
        effective_target_lang, CLINICAL_DISCLAIMERS["short_disclaimer"]["en"]
    )

    return {
        "translated_summary": translated_summary,
        "guidance": translated_guidance,
        "review_request": review_request,
        "disclaimer": std_disclaimer,
        "detected_language": detected_lang,
        "response_language": effective_target_lang,
        "original_query": raw_query,
    }
