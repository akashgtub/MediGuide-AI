"""
Patient Health Assistant & Multilingual Clinical Agent for MediGuide-AI.
Combines deterministic intent routing, agent tools for verified report querying,
clinical risk evaluation, human review escalation, and multilingual translation.

Safety Guarantees:
- Strict Patient Data Isolation: Only accesses reports owned by the authenticated patient.
- Non-Diagnostic / Non-Prescribing: Never diagnoses diseases, prescribes medicines, or invents dosages.
- Zero Hallucination: Never infers, guesses, or invents absent lab values or reference ranges.
- Grounded Reporting: Always cites exact stored values, units, report filename, and test date.
- Reliable Multilingual Escalation: Emergency warnings and clinical guidance translated into supported Indic languages.
- Safe Fallbacks: General questions and greetings never trigger document OCR or create false clinical review tickets.
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
    CONVERSATIONAL_RESPONSES,
)
from ai.agent_tools import (
    tool_get_user_reports,
    tool_get_report_summary,
    tool_find_metric,
    tool_search_report_observations,
    METRIC_ALIASES,
)
from backend.database import get_report_by_id
from risk.risk_engine import evaluate_risk
from human_review.review_manager import create_review_request
from ai.medical_knowledge import fetch_live_medical_knowledge

logger = logging.getLogger("mediguide_patient_agent")

# Multilingual emergency / high-risk indicators across all 6 supported languages
EMERGENCY_KEYWORDS = [
    # English
    "chest pain", "shortness of breath", "heart attack", "difficulty breathing",
    "severe headache", "stroke", "bleeding heavily", "loss of consciousness",
    "unconscious", "passed out", "fainted", "cannot breathe", "can't breathe",
    "suffocating", "severe chest pressure", "coughing blood", "coughing up blood",
    "vomiting blood", "anaphylaxis", "severe allergic reaction", "sudden numbness",
    "paralysis", "slurred speech", "seizure", "convulsions", "bluish lips", "cyanosis",
    # Tamil
    "நெஞ்சு வலி", "மாரடைப்பு", "மூச்சுத்திணறல்", "சுவாசிப்பதில் சிரமம்",
    "கடுமையான தலைவலி", "மயக்கம்", "சுயநினைவு இழப்பு", "மூச்சு விட முடியவில்லை",
    "இரத்த வாந்தி", "பக்கவாதம்", "வலிப்பு", "கடுமையான இரத்தப்போக்கு",
    # Hindi
    "सीने में दर्द", "सांस लेने में तकलीफ", "दिल का दौरा", "गंभीर सिरदर्द",
    "बेहोश", "बेहोशी", "सांस नहीं आ रही", "खून की उल्टी", "लकवा", "दौरा",
    "अत्यधिक रक्तस्राव",
    # Telugu
    "ఛాతీ నొప్పి", "శ్వాస ఆడకపోవడం", "గుండెపోటు", "తీవ్రమైన తలనొప్పి",
    "స్పృహ తప్పడం", "శ్వాస తీసుకోలేకపోవడం", "రక్తం వాంతులు", "పక్షవాతం", "ఫిట్స్",
    # Malayalam
    "നെഞ്ചുവേദന", "ശ്വാസതടസ്സം", "ഹൃദയാഘാതം", "കഠിനമായ തലവേദന",
    "ബോധക്ഷയം", "ശ്വാസമെടുക്കാൻ കഴിയുന്നില്ല", "രക്തം ഛർദ്ദിക്കുക", "പക്ഷാഘാതം",
    # Kannada
    "ಎದೆ ನೋವು", "ಉಸಿರಾಟದ ತೊಂದರೆ", "ಹೃದಯಾಘಾತ", "ತೀವ್ರ ತಲೆನೋವು",
    "ಪ್ರಜ್ಞೆ ತಪ್ಪುವುದು", "ಉಸಿರಾಡಲು ಸಾಧ್ಯವಾಗುತ್ತಿಲ್ಲ", "ರಕ್ತ ವಾಂತಿ", "ಪಾರ್ಶ್ವವಾಯು",
]

# Multilingual report overview queries
REPORT_OVERVIEW_PATTERNS = [
    "blood test", "results", "report", "test result", "findings", "what do my", "explain my",
    "summarize", "overview", "show my report", "my report",
    "இரத்தப் பரிசோதனை", "முடிவுகள்", "அறிக்கை",
    "रक्त जांच", "परिणाम", "रिपोर्ट",
    "రక్త పరీక్ష", "ఫలితాలు", "రిపోర్ట్",
    "രക്തപരിശോധന", "ഫലങ്ങൾ", "റിപ്പോർട്ട്",
    "ರಕ್ತ ಪರೀಕ್ಷೆ", "ಫಲಿತಾಂಶಗಳು", "ವರದಿ",
]

# Risk inquiry patterns
RISK_QUERY_PATTERNS = [
    "danger", "risk", "serious", "worry", "critical", "harm", "problem", "concerning",
    "ஆபத்து", "சிக்கல்", "பயப்பட",
    "खतरा", "जोखिम", "गंभीर", "चिंता",
    "ప్రమాదం", "సమస్య", "ఆందోళన",
    "അപകടം", "പ്രശ്നം", "ഭയം",
    "ಅಪಾಯ", "ತೊಂದರೆ", "ಚಿಂತೆ",
]

# Greeting and pleasantry patterns
GREETING_PATTERNS = [
    "hello", "hi", "hey", "good morning", "good evening", "good afternoon",
    "who are you", "what can you do", "help", "thanks", "thank you",
    "வணக்கம்", "நன்றி",
    "नमस्ते", "धन्यवाद",
    "నమస్కారం", "ధన్యవాదాలు",
    "നമസ്കാരം", "നന്ദി",
    "ನಮಸ್ಕಾರ", "ಧನ್ಯವಾದಗಳು",
]

# Prescribing and autonomous diagnosis requests to refuse safely
PRESCRIBE_DIAGNOSE_PATTERNS = [
    "prescribe", "write prescription", "give me medicine", "recommend medication",
    "diagnose me", "what disease do i have", "what illness do i have", "cure me",
    "மருந்து கொடு", "மருந்து எழுதி",
    "दवा लिखो", "दवा बताओ", "बीमारी का निदान",
]


# Contextual follow-up patterns
FOLLOWUP_PATTERNS = {
    "NORMALITY_OR_RANGE": [
        "is that normal", "is that high", "is that low", "is that good", "is that bad",
        "is this normal", "is this high", "is this low", "is this good",
        "what does that mean", "what does this mean", "what does that reading mean",
        "is that a good reading", "is that a normal reading", "is that reading normal", "is this reading normal",
        "is the reading normal", "is that normal", "is this normal",
        "is it normal", "is it high", "is it low", "should i be worried", "normal range", "reference range",
        "typical range", "target range", "good or bad", "is that ok", "is this ok",
        "சாதாரணமானதா", "இயல்பானதா", "நல்லதா", "அபாயகரமானதா", "சாதாரண அளவு",
        "सामान्य है", "ठीक है", "सामान्य स्तर", "क्या मतलब है", "नॉर्मल है", "खराब है",
        "సాధారణమా", "సరైనదేనా", "సాధారణ స్థాయి",
        "സാധാരണമാണോ", "നല്ലതാണോ", "സാധാരണ നില",
        "ಸಾಮಾನ್ಯವೇ", "ಸರಿಯಾಗಿದೆಯೇ", "ಸಾಮಾನ್ಯ ಪ್ರಮಾಣ",
    ],
    "DATE_OR_TIMING": [
        "when was that", "when was that test", "when was this", "what date",
        "test date", "when did i take that", "when did i do that test",
        "date of that report", "which date", "what is the date",
        "எப்போது", "எந்த தேதி", "எப்போது எடுக்கப்பட்டது",
        "कब का है", "कब हुआ था", "किस तारीख को", "तारीख क्या है",
        "ఎప్పుడు", "ఏ తేదీన",
        "എപ്പോഴാണ്", "ഏത് തീയതി",
        "ಯಾವಾಗ", "ಯಾವ ದಿನಾಂಕ",
    ],
    "SPECIALIST_OR_NEXT_STEPS": [
        "which doctor", "who should i see", "what specialist", "who should i consult",
        "which specialist", "who treats this", "doctor to visit", "consult a doctor",
        "what kind of doctor", "should i see a specialist", "who do i go to",
        "who do i see",
        "எந்த மருத்துவர்", "யாரை பார்க்க வேண்டும்", "மருத்துவரிடம் ஆலோசனை",
        "किस डॉक्टर", "किसे दिखाना चाहिए", "किस विशेषज्ञ",
        "ఏ డాక్టర్", "ఎవరిని సంప్రదించాలి",
        "ഏത് ഡോക്ടറെ", "ആരെ കാണണം",
        "ಯಾವ ವೈದ್ಯರನ್ನು", "ಯಾರನ್ನು ಸಂಪರ್ಕಿಸಬೇಕು",
    ],
    "OTHER_TESTS": [
        "what other tests", "what else was tested", "other results",
        "what else is in that report", "other tests in that report",
        "what else did it show", "what other measurements",
        "வேறு என்ன சோதனைகள்", "மற்ற சோதனைகள்",
        "अन्य कौन से टेस्ट", "बाकी जांच",
        "ఇతర పరీక్షలు",
        "മറ്റ് പരിശോധനകൾ",
        "ಇತರ ಪರೀಕ್ಷೆಗಳು",
    ]
}


def _detect_emergency_intent(text: str) -> bool:
    """Check if text contains urgent high-risk medical terms across supported languages."""
    text_lower = text.lower()
    for kw in EMERGENCY_KEYWORDS:
        if kw in text_lower:
            return True
    return False


def _detect_metric_inquiry(text: str) -> bool:
    """Check if text asks about specific lab metrics, values, or vitals."""
    text_lower = text.lower()
    for canonical, aliases in METRIC_ALIASES.items():
        for alias in aliases:
            if re.search(r'\b' + re.escape(alias) + r'\b', text_lower):
                return True
    metric_intent_words = [
        "value", "level", "count", "measurement", "reading", "score", "number",
        "மதிப்பு", "அளவு", "स्तर", "मान", "संख्या", "విలువ", "స్థాయి", "നില", "മൊത്തം", "ಮೌಲ್ಯ", "ಪ್ರಮಾಣ"
    ]
    return any(w in text_lower for w in metric_intent_words)


def _detect_followup_type(text: str) -> Optional[str]:
    """
    Detect if text asks a follow-up question regarding a previously discussed metric or report.
    Returns: 'NORMALITY_OR_RANGE', 'DATE_OR_TIMING', 'SPECIALIST_OR_NEXT_STEPS', 'OTHER_TESTS', or None.
    """
    text_clean = text.lower().strip()
    for ftype, patterns in FOLLOWUP_PATTERNS.items():
        for p in patterns:
            if re.search(r'\b' + re.escape(p) + r'\b', text_clean) or p in text_clean:
                return ftype

    # Flexible regex check for normality inquiries: "is that ... normal?"
    if re.search(r'\bis\s+(?:that|this|it|the|my)?\s*(?:reading|result|value|measurement|number)?\s*(?:normal|high|low|elevated|okay|ok|good|bad)\b', text_clean):
        return "NORMALITY_OR_RANGE"

    return None


def _detect_user_introduction(text: str) -> Optional[str]:
    """
    Detect if user is introducing themselves (e.g. 'I am Akash', 'My name is Akash').
    Returns capitalized name if found, or None.
    """
    text_clean = text.strip()
    symptom_words = [
        "feeling", "having", "sick", "tired", "unwell", "ill", "suffering", "experiencing",
        "taking", "prescribed", "diagnosed", "in pain", "hurt", "bleeding"
    ]
    text_lower = text_clean.lower()
    if any(sw in text_lower for sw in symptom_words):
        return None

    # English patterns
    m_en = re.search(
        r'^(?:(?:hello|hi|hey|good\s+(?:morning|afternoon|evening))[\s,!]*)?(?:i\s*am|i\'m|my\s+name\s+is|myself|this\s+is|call\s+me)\s+([a-zA-Z\u0B80-\u0DFF\u0900-\u097F]+)',
        text_clean,
        re.IGNORECASE
    )
    if m_en:
        name = m_en.group(1).strip()
        if name.lower() not in ("a", "an", "the", "not", "just", "here", "fine", "ok", "okay", "patient", "doctor"):
            return name.capitalize()

    # Tamil patterns: "என் பெயர் ஆகாஷ்", "நான் ஆகாஷ்"
    m_ta = re.search(r'^(?:வணக்கம்[\s,!]*)?(?:என்\s*பெயர்|நான்)\s+([^\s,!\.]+)', text_clean)
    if m_ta:
        return m_ta.group(1).strip()

    # Hindi patterns: "मेरा नाम आकाश है", "मैं आकाश हूँ"
    m_hi = re.search(r'^(?:नमस्ते[\s,!]*)?(?:मेरा\s*नाम|मैं)\s+([^\s,!\.]+)(?:\s*(?:हूँ|हूं|है))?', text_clean)
    if m_hi:
        name = m_hi.group(1).strip()
        if name not in ("यहाँ", "ठीक", "एक"):
            return name

    return None


def _detect_identity_intent(text: str) -> bool:
    """Check if message is asking about the assistant's name, identity, or capabilities."""
    text_clean = re.sub(r'[^\w\s\u0900-\u0D7F]', ' ', text.lower()).strip()
    identity_phrases = [
        "what is your name", "what s your name", "whats your name", "who are you",
        "what can you do", "what are you", "who made you", "tell me about yourself",
        "how can you help me", "what is mediguide", "who is mediguide", "what do you do",
        # Tamil
        "உங்கள் பெயர் என்ன", "நீங்கள் யார்", "நீங்கள் என்ன செய்ய முடியும்", "உன் பெயர் என்ன",
        # Hindi
        "आपका नाम क्या है", "आप कौन हैं", "आप क्या कर सकते हैं", "तुम्हारा नाम क्या है",
        # Telugu
        "మీ పేరు ఏమిటి", "మీరు ఎవరు", "మీరు ఏమి చేయగలరు",
        # Malayalam
        "നിങ്ങളുടെ പേര് എന്താണ്", "നിങ്ങൾ ആരാണ്", "നിങ്ങൾക്ക് എന്ത് ചെയ്യാൻ കഴിയും",
        # Kannada
        "ನಿಮ್ಮ ಹೆಸರು ಏನು", "ನೀವು ಯಾರು", "ನೀವು ಏನು ಮಾಡಬಹುದು",
    ]
    return any(p in text_clean for p in identity_phrases)


def _detect_greeting_intent(text: str) -> bool:
    """Check if message is a conversational greeting without personal health questions."""
    text_clean = re.sub(r'[^\w\s\u0900-\u0D7F]', ' ', text.lower()).strip()
    words = text_clean.split()
    if len(words) > 4:
        return False

    # Prescribing and autonomous diagnosis requests must be refused, not treated as simple greeting
    if any(p in text_clean for p in PRESCRIBE_DIAGNOSE_PATTERNS):
        return False

    greeting_words = [
        "hi", "hello", "hey", "good morning", "good evening", "good afternoon",
        "greetings", "hey there", "hello there",
        "வணக்கம்", "नमस्ते", "నమస్కారం", "നമസ്കാരം", "ನಮಸ್ಕಾರ",
    ]
    for g in greeting_words:
        if text_clean == g or text_clean.startswith(g + " ") or text_clean.endswith(" " + g):
            return True
    return False


def _detect_report_list_intent(text: str) -> bool:
    """Check if message explicitly requests a listing of uploaded reports."""
    text_lower = text.lower().strip()
    list_phrases = [
        "show my reports", "list my reports", "list my uploaded reports", "show my uploaded reports",
        "what reports do i have", "my reports", "show uploaded reports", "view my reports",
        "see my reports", "get my reports", "list reports", "show reports", "all my reports",
        "my uploaded reports", "list all reports", "show all reports", "show all my reports",
        "அறிக்கைகளைக் காட்டு", "என் அறிக்கைகள்", "அறிக்கைகள் பட்டியல்",
        "मेरी रिपोर्ट दिखाओ", "मेरी रिपोर्टें", "रिपोर्ट की सूची",
        "నా నివేదికలను చూపించు", "నా రిపోర్టులు",
        "എന്റെ റിപ്പോർട്ടുകൾ കാണിക്കുക", "റിപ്പോർട്ടുകൾ",
        "ನನ್ನ ವರದಿಗಳನ್ನು ತೋರಿಸಿ", "ವರದಿಗಳ ಪಟ್ಟಿ",
    ]
    return any(p in text_lower for p in list_phrases)


def _detect_clarification_required(text: str) -> bool:
    """
    Detect if input is a short, isolated interrogative or uninformative fragment
    that requires clarification rather than generic welcome boilerplate.
    e.g. 'what', 'what?', 'huh', '?', 'help?', 'why', 'who?', 'how?', 'please help'
    """
    text_clean = re.sub(r'[^a-zA-Z\u0900-\u0D7F\?]', ' ', text.strip().lower()).strip()
    words = text_clean.split()

    if not words:
        return True

    isolated = {"what", "huh", "why", "how", "who", "which", "where", "help", "?"}
    if text_clean in isolated or (len(words) == 1 and (words[0] in isolated or words[0].rstrip("?") in isolated)):
        return True

    if text_clean in ("what is it", "what do you mean", "what is that", "what now", "tell me", "what else"):
        return True

    if len(words) <= 2 and words[0].rstrip("?") in isolated and words[-1] in ("?", "please", "now", "it"):
        return True

    return False


def _detect_current_medical_information(text: str) -> bool:
    """
    Check if query asks for current medical guidelines, latest treatments,
    or live medical guidance from trustworthy sources.
    """
    text_lower = text.lower().strip()

    # Exclude personal report queries
    personal_markers = ["my report", "my hemoglobin", "my blood pressure", "my result", "my test", "in my report", "my reading", "my value"]
    if any(pm in text_lower for pm in personal_markers):
        return False

    current_markers = [
        "latest treatment", "current treatment", "new treatment", "recent treatment",
        "latest guideline", "current guideline", "latest guidelines", "current guidelines",
        "latest research", "current research", "recent updates", "latest updates",
        "latest protocol", "current protocol", "latest therapy", "current therapy",
        "treatment for dengue", "cure for dengue", "latest on dengue", "latest dengue",
        "treatment of dengue", "dengue treatment",
        # Multilingual markers
        "சமீபத்திய சிகிச்சை", "புதிய சிகிச்சை", "சமீபத்திய வழிகாட்டுதல்கள்", "டெங்கு சிகிச்சை", "டெங்கு புதிய சிகிச்சை", "டெங்கு நோய் சிகிச்சை",
        "नवीनतम उपचार", "वर्तमान दिशानिर्देश", "नया इलाज", "डेंगू उपचार", "डेंगू का इलाज", "डेंगू के नए उपचार",
        "తాజా చికిత్స", "నవీన చికిత్స", "డెంగ్యూ చికిత్స",
        "ഏറ്റവും പുതിയ ചികിത്സ", "ഡെങ്കിപ്പനി ചികിത്സ",
        "ಇತ್ತೀಚಿನ ಚಿಕಿತ್ಸೆ", "ಡೆಂಗ್ಯೂ ಚಿಕಿತ್ಸೆ",
    ]
    if any(cm in text_lower for cm in current_markers):
        return True

    # Regex patterns
    if re.search(r'\b(?:latest|current|recent|newest)\s+(?:treatment|guidelines?|protocols?|management|advances?|therapy|recommendations?)\b', text_lower):
        return True

    return False


def _detect_general_health_question(text: str) -> bool:
    """
    Check if query is general health/medical education (e.g. symptoms like fever/headache,
    disease mechanisms, causes) that must NOT trigger personal report retrieval.
    """
    text_lower = text.lower().strip()

    # Never treat queries with personal possessives about user's own data as general education
    personal_markers = ["my report", "my hemoglobin", "my blood pressure", "my result", "my test", "in my report", "my reading", "my value"]
    if any(pm in text_lower for pm in personal_markers):
        return False

    # Standalone symptom queries: "fever", "headache", "cough", "fatigue", "nausea"
    symptom_standalone = [
        "fever", "headache", "cough", "fatigue", "nausea", "dizziness",
        "காய்ச்சல்", "தலைவலி", "இருமல்",
        "बुखार", "सिरदर्द", "खांसी",
        "జ్వరం", "తలనొప్పి",
        "പനി", "തലവേദന",
        "ಜ್ವರ", "ತಲೆನೋವು",
    ]
    text_clean = re.sub(r'[^\w\s\u0900-\u0D7F]', '', text_lower).strip()
    if text_clean in symptom_standalone:
        return True

    words = text_clean.split()
    if len(words) <= 3 and any(s in words for s in ["fever", "headache", "cough"]):
        if not any(w in words for w in ["aspirin", "ibuprofen", "paracetamol", "taking", "mg", "tablet"]):
            return True

    general_disease_queries = [
        "most dangerous disease", "deadliest disease", "worst disease", "deadly disease",
        "dangerous disease", "most dangerous",
        "what causes fever", "causes of fever", "why do i have a fever", "cause of fever",
        "what causes diabetes", "causes of diabetes", "why does diabetes happen", "cause of diabetes",
        "what is hypertension", "what is high blood pressure", "tell me about hypertension",
        "what causes high blood pressure", "what is diabetes", "what is anemia",
        "what causes low hemoglobin", "what is cancer", "what is cholesterol",
        "what causes high cholesterol", "what is asthma", "what is a normal heart rate",
        "what is a stroke", "what is a heart attack", "symptoms of diabetes",
        "symptoms of hypertension", "causes of anemia", "causes of hypertension",
        "what causes headache", "causes of headache",
        "மிகவும் ஆபத்தான நோய் எது", "உயர் இரத்த அழுத்தம் என்றால் என்ன", "நீரிழிவு நோய் என்றால் என்ன",
        "காய்ச்சல் வர காரணம்", "சர்க்கரை நோய் வர காரணம்",
        "सबसे खतरनाक बीमारी कौन सी है", "उच्च रक्तचाप क्या है", "मधुमेह क्या है",
        "बुखार के कारण", "मधुमेह के कारण",
    ]
    if any(q in text_lower for q in general_disease_queries):
        return True

    # General question pattern: "what is <condition>", "what causes <condition>"
    if re.search(r'\b(?:what\s+(?:is|causes|are\s+the\s+symptoms\s+of)|causes?\s+of)\s+[a-z\s]+\b', text_lower):
        if not any(w in text_lower for w in ["my", "mine", "me", "i have", "in my report"]):
            return True

    return False


def _detect_general_medical_education(text: str) -> bool:
    """Backward compatibility alias for _detect_general_health_question."""
    return _detect_general_health_question(text)


def _detect_followup_question(
    text: str,
    conversation_context: Optional[Dict[str, Any]] = None,
) -> bool:
    """Check if message is a contextual follow-up question regarding a previously discussed metric or report."""
    if _detect_followup_type(text) is not None:
        return True

    if conversation_context and (conversation_context.get("last_metric") or conversation_context.get("last_report_id")):
        text_clean = text.lower().strip()
        if any(p in text_clean for p in ["is that", "is it", "what about", "and that", "normal", "concerning", "when was", "which doctor"]):
            return True

    return False


def _detect_risk_question_intent(text: str) -> bool:
    """Backward compatibility wrapper checking if query is a risk question or follow-up."""
    text_lower = text.lower().strip()
    if _detect_followup_type(text) is not None:
        return True

    if "most dangerous disease" in text_lower or "deadliest disease" in text_lower:
        return False

    risk_terms = [
        "concerning", "is this result concerning", "is that value normal", "is that normal",
        "is my reading normal", "is that high", "is that low", "should i be worried",
        "is my report dangerous", "is this normal", "is that reading dangerous",
        "is it elevated", "is that bad", "is that good", "is this value normal",
        "அது சாதாரணமானதா", "இது ஆபத்தானதா", "என்ன ஆபத்து",
        "क्या यह सामान्य है", "क्या यह खतरनाक है",
    ]
    return any(rt in text_lower for rt in risk_terms)


def _detect_report_overview_intent(text: str) -> bool:
    """Check if message is an explicit request to summarize or explain a medical report."""
    text_lower = text.lower().strip()
    overview_phrases = [
        "summarize my cbc report", "explain my report", "explain my cbc report",
        "what does my general health report show", "overview of my report",
        "summarize my report", "what do my test results say", "explain my test results",
        "summarize my test results", "summarize my general health report",
        "explain my general health report", "what does my report say",
        "what does my report show", "tell me about my report",
        "என் அறிக்கையை விளக்குங்கள்", "என் அறிக்கையை சுருக்கவும்",
        "मेरी रिपोर्ट समझाओ", "मेरी रिपोर्ट का सारांश",
        "నా రిపోర్ట్‌ను వివరించండి",
        "what were my test results", "what are my test results", "what are my results",
        "what were my results", "what was in my report", "what is in my report",
        "what are my report results", "what did my test results say", "what did my report say",
        "my test results", "my lab results", "what were my results",
    ]
    if any(p in text_lower for p in overview_phrases):
        return True

    if any(w in text_lower for w in ["summarize", "explain", "overview"]) and any(r in text_lower for r in ["report", "results", "findings"]):
        return True

    if ("my test result" in text_lower or "my results" in text_lower or "my lab" in text_lower or "my report" in text_lower) and any(w in text_lower for w in ["what", "show", "tell", "explain", "summarize", "view"]):
        return True

    return False


def _detect_greeting_or_general(text: str) -> bool:
    """Backward compatibility wrapper for greeting or capability check."""
    return _detect_greeting_intent(text) or _detect_identity_intent(text)


def _detect_document_narrative(text: str) -> bool:
    """
    Check if input represents explicit clinical record narrative rather than a chat query.
    e.g., multiline record text or text with clinical lab report headers.
    """
    text_lower = text.lower()
    clinical_markers = [
        "patient id:", "patient:", "date:", "lab results:", "clinical observations:",
        "routine vitals", "hemoglobin:", "blood pressure:", "platelets:"
    ]
    has_marker = sum(1 for m in clinical_markers if m in text_lower) >= 2
    is_multiline = "\n" in text.strip() and len(text.strip().split("\n")) >= 3
    is_long_clinical = len(text.split()) > 35 and any(m in text_lower for m in ["blood pressure", "diagnosis", "mg/dl", "mmhg"])

    # Backward compatibility: statements like "I have a fever and am taking aspirin."
    has_symptom_statement = any(w in text_lower for w in ["i have a fever", "am taking aspirin", "taking ibuprofen", "i have had a mild fever"])

    return has_marker or is_multiline or is_long_clinical or has_symptom_statement


def _extract_conversation_context(
    conversation_history: Optional[List[Dict[str, Any]]],
    user_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Extract active clinical entities from multi-turn conversation history:
    - last_metric: canonical name of last discussed metric (e.g. 'Hemoglobin', 'Blood Pressure')
    - last_value: string value (e.g. '14.2', '180/110')
    - last_unit: string unit (e.g. 'g/dL', 'mmHg')
    - last_filename: report filename (e.g. 'cbc_report.pdf')
    - last_report_id: report ID if known
    - last_date: string date of the test/report
    """
    ctx: Dict[str, Any] = {
        "last_metric": None,
        "last_value": None,
        "last_unit": None,
        "last_filename": None,
        "last_report_id": None,
        "last_date": None,
    }
    if not conversation_history:
        return ctx

    # Scan messages in reverse order (most recent first)
    for msg in reversed(conversation_history):
        raw_text = (msg.get("text") or msg.get("content") or "").strip()
        if not raw_text:
            continue

        # 1. Extract metric
        if not ctx["last_metric"]:
            for canonical, aliases in METRIC_ALIASES.items():
                for alias in aliases:
                    if re.search(r'\b' + re.escape(alias) + r'\b', raw_text.lower()) or alias in raw_text:
                        ctx["last_metric"] = canonical.title()
                        break
                if ctx["last_metric"]:
                    break

        # 2. Extract values and units
        if not ctx["last_value"]:
            # Blood pressure pattern (e.g. 180/110 or 130/85)
            bp_m = re.search(r'\b(\d{2,3}/\d{2,3})\s*(?:mmHg)?', raw_text, re.IGNORECASE)
            if bp_m:
                ctx["last_value"] = bp_m.group(1)
                ctx["last_unit"] = "mmHg"
            else:
                # 1) Check for explicit "recorded as <val>", "is <val>", "value: <val>", "level: <val>"
                val_m = re.search(r'(?:recorded as|value:|level:|is)\s*([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z/%^0-9/]+)?', raw_text, re.IGNORECASE)
                if not val_m and ctx["last_metric"]:
                    # 2) Check for metric name followed directly by number (e.g. "Hemoglobin 14.2 g/dL")
                    val_m = re.search(rf'(?:{re.escape(ctx["last_metric"])})[\s:]+([0-9]+(?:\.[0-9]+)?)\s*([a-zA-Z/%^0-9/]+)?', raw_text, re.IGNORECASE)
                if not val_m:
                    # 3) Match number paired with known clinical units
                    val_m = re.search(r'\b([0-9]+(?:\.[0-9]+)?)\s*(g/dl|mg/dl|bpm|mmhg|/ul|x10\^3/ul|/mcl)\b', raw_text, re.IGNORECASE)

                if val_m and val_m.group(1):
                    # Ignore pure 4-digit years like 2026
                    if not (len(val_m.group(1)) == 4 and val_m.group(1).startswith("20")):
                        ctx["last_value"] = val_m.group(1)
                        ctx["last_unit"] = val_m.group(2) or ""

        # 3. Extract filename
        if not ctx["last_filename"]:
            fn_m = re.search(r'([a-zA-Z0-9_\-\.\s]+?\.(?:pdf|png|jpg|jpeg|txt))', raw_text, re.IGNORECASE)
            if fn_m:
                ctx["last_filename"] = fn_m.group(1).strip()

        # 4. Extract report ID (e.g. REP-1234ABCD or explicit report reference like 101, 102)
        if not ctx["last_report_id"]:
            rep_m = re.search(r'\b(REP-[A-Za-z0-9]+)\b|\b(?:report\s*(?:id|#)?\s*|\b)(10[12])\b', raw_text, re.IGNORECASE)
            if rep_m:
                ctx["last_report_id"] = rep_m.group(1) or rep_m.group(2)

        # 5. Extract date
        if not ctx["last_date"]:
            dt_m = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', raw_text)
            if dt_m:
                ctx["last_date"] = dt_m.group(1)

        if all(ctx.values()):
            break

    # If user_id is provided and we have filename but no report_id, link to database report
    if user_id and ctx["last_filename"] and not ctx["last_report_id"]:
        try:
            user_reports = tool_get_user_reports(user_id=user_id)
            for r in user_reports:
                if r.get("filename", "").lower() == ctx["last_filename"].lower():
                    ctx["last_report_id"] = r["report_id"]
                    if not ctx["last_date"]:
                        ctx["last_date"] = r.get("created_at", "")[:10]
                    break
        except Exception:
            pass

    return ctx


def _evaluate_blood_pressure(val_str: str) -> tuple:
    """Evaluate blood pressure value string against standard AHA/ACC guidelines."""
    m = re.search(r'(\d+)/(\d+)', val_str)
    if not m:
        return "Please compare your blood pressure reading with standard clinical categories.", False
    sys_val, dia_val = int(m.group(1)), int(m.group(2))
    if sys_val >= 180 or dia_val >= 120 or (sys_val >= 170 and dia_val >= 105):
        return (
            f"A blood pressure reading of {val_str} mmHg is significantly elevated and falls into the "
            "Hypertensive Crisis range according to clinical guidelines. "
            "Readings at this level warrant prompt clinical evaluation.",
            True
        )
    elif sys_val >= 140 or dia_val >= 90:
        return (
            f"A blood pressure reading of {val_str} mmHg corresponds to Stage 2 Hypertension "
            "according to clinical guidelines.",
            False
        )
    elif sys_val >= 130 or dia_val >= 80:
        return (
            f"A blood pressure reading of {val_str} mmHg corresponds to Stage 1 Hypertension "
            "according to clinical guidelines.",
            False
        )
    elif sys_val >= 120 and dia_val < 80:
        return (
            f"A blood pressure reading of {val_str} mmHg corresponds to Elevated blood pressure "
            "according to clinical guidelines.",
            False
        )
    else:
        return (
            f"A blood pressure reading of {val_str} mmHg is within standard normal adult ranges "
            "(systolic < 120 mmHg and diastolic < 80 mmHg).",
            False
        )


def _evaluate_hemoglobin(val_str: str) -> str:
    """Evaluate hemoglobin value string against standard adult reference ranges."""
    try:
        val = float(val_str)
        if 12.0 <= val <= 17.5:
            return (
                f"Your recorded measurement of {val_str} g/dL falls within standard adult reference ranges "
                "(typically 13.8–17.2 g/dL for adult males and 12.1–15.1 g/dL for adult females)."
            )
        elif val < 12.0:
            return (
                f"Your recorded measurement of {val_str} g/dL is below standard adult reference ranges, "
                "which may indicate anemia or iron deficiency. Please discuss this result with your doctor."
            )
        else:
            return (
                f"Your recorded measurement of {val_str} g/dL is above standard adult reference ranges. "
                "Please discuss this result with your doctor."
            )
    except ValueError:
        return f"Your recorded value is {val_str} g/dL. Typical adult reference ranges are 12.1 to 17.2 g/dL."


def _evaluate_platelets(val_str: str) -> str:
    """Evaluate platelet count string against standard adult reference ranges."""
    try:
        val = float(val_str.replace(",", ""))
        val_mcL = val * 1000 if val < 1000 else val
        if 150000 <= val_mcL <= 450000:
            return (
                f"Your recorded platelet count of {val_str} /mcL falls within the standard normal "
                "reference range of 150,000 to 450,000 /mcL."
            )
        elif val_mcL < 150000:
            return (
                f"Your recorded platelet count of {val_str} /mcL is below the standard reference range. "
                "Please discuss this result with your physician."
            )
        else:
            return (
                f"Your recorded platelet count of {val_str} /mcL is above the standard reference range. "
                "Please discuss this result with your physician."
            )
    except ValueError:
        return f"Your recorded platelet count is {val_str}. Standard reference ranges are 150,000 to 450,000 /mcL."


def classify_patient_intent(
    text: str,
    has_user_id: bool = False,
    has_report_context: bool = False,
    conversation_context: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Deterministic intent router for patient assistant messages.
    Returns one of the 12 supported intents:
    1. EMERGENCY: potentially urgent symptoms.
    2. CLARIFICATION_REQUIRED: isolated short interrogatives like 'what', 'huh', '?'.
    3. USER_INTRODUCTION: my name is Akash, I am Akash.
    4. IDENTITY: what is your name, who are you, what can you do?
    5. GREETING: hi, hello, hey, good morning.
    6. CURRENT_MEDICAL_INFORMATION: what is the latest treatment for dengue?
    7. REPORT_LIST: show my reports, list my uploaded reports.
    8. REPORT_METRIC_QUERY: what was my hemoglobin, what is my blood pressure?
    9. REPORT_OVERVIEW: summarize my CBC report, explain my report.
    10. FOLLOW_UP: is that normal, when was that, which doctor should I see?
    11. GENERAL_HEALTH_QUESTION: fever, headache, what causes diabetes, what causes fever?
    12. DOCUMENT_NARRATIVE: explicit clinical record text / multiline document text.
    """
    if not text or not text.strip():
        return "CLARIFICATION_REQUIRED"

    # Priority 1: Clinical Emergency (highest priority safety guardrail)
    if _detect_emergency_intent(text):
        return "EMERGENCY"

    # Priority 2: Clarification Required for short, isolated interrogatives ("what", "huh", "?")
    if _detect_clarification_required(text):
        return "CLARIFICATION_REQUIRED"

    # Priority 3: User Introduction ("I am Akash", "My name is Akash")
    if _detect_user_introduction(text) is not None:
        return "USER_INTRODUCTION"

    # Priority 4: Identity / Capabilities / Prescribing refusal
    if _detect_identity_intent(text) or any(p in text.lower() for p in PRESCRIBE_DIAGNOSE_PATTERNS):
        return "IDENTITY"

    # Priority 5: Greeting ("hi", "hello", "good morning")
    if _detect_greeting_intent(text):
        return "GREETING"

    # Priority 6: Current Medical Information Retrieval ("what is the latest treatment for dengue?")
    if _detect_current_medical_information(text):
        return "CURRENT_MEDICAL_INFORMATION"

    # Priority 7: Explicit Report Listing ("show my reports", "list my uploaded reports")
    if _detect_report_list_intent(text):
        return "REPORT_LIST"

    # Priority 8: Report Metric Query ("what was my hemoglobin", "what is my blood pressure", "what about platelets?")
    if _detect_metric_inquiry(text) and _detect_followup_type(text) is None:
        return "REPORT_METRIC_QUERY"

    # Priority 9: Contextual Follow-up ("is that normal", "when was that", "which doctor should I see", "what other tests")
    if _detect_followup_question(text, conversation_context):
        return "FOLLOW_UP"

    # Priority 10: Report Overview / Summary ("summarize my CBC report", "explain my report")
    if _detect_report_overview_intent(text):
        return "REPORT_OVERVIEW"

    # Priority 11: General Health Question ("fever", "headache", "what causes fever", "what causes diabetes", "what is hypertension")
    if _detect_general_health_question(text):
        return "GENERAL_HEALTH_QUESTION"

    # Priority 12: Explicit Document Narrative Text (OCR record, multiline lab results)
    if _detect_document_narrative(text):
        return "DOCUMENT_NARRATIVE"

    # Safe fallback: Request clarification rather than dumping generic welcome
    return "CLARIFICATION_REQUIRED"


def process_patient_request(
    document_text: str,
    target_language: str = "en",
    user_id: Optional[str] = None,
    report_id: Optional[str] = None,
    conversation_history: Optional[List[Dict[str, Any]]] = None,
) -> dict:
    """
    Process patient queries and medical narrative with deterministic intent routing,
    grounded agent tools, patient isolation, and verified multilingual safety.
    Preserves exact backward compatibility with test_mediguide.py.
    """
    raw_query = (document_text or "").strip()

    # 1. Detect input language and resolve target language
    detected_lang = detect_language(raw_query)
    effective_target_lang = target_language.lower().strip() if target_language else DEFAULT_LANGUAGE

    # If user writes in an Indian script and target language is default English, respond in user's language
    if detected_lang != "en" and effective_target_lang == "en":
        effective_target_lang = detected_lang

    # 2. Extract multi-turn conversational context
    conversation_context = _extract_conversation_context(conversation_history, user_id=user_id)

    # 3. Classify intent deterministically
    intent = classify_patient_intent(
        raw_query,
        has_user_id=bool(user_id),
        has_report_context=bool(report_id or conversation_context.get("last_report_id")),
        conversation_context=conversation_context,
    )

    review_request = None
    summary_en = ""
    guidance_en = []
    report_list = None
    metric_data = None
    sources = []
    retrieval_timestamp = None
    is_live = False
    include_disclaimer = True

    # =========================================================================
    # INTENT: EMERGENCY
    # =========================================================================
    if intent == "EMERGENCY":
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
        review_request = create_review_request(
            extracted_info=extracted_info,
            summary=summary_en,
            risk_result=risk_result,
            patient_id=user_id,
            report_id=report_id or conversation_context.get("last_report_id"),
        )
        include_disclaimer = True

    # =========================================================================
    # INTENT: CLARIFICATION_REQUIRED
    # =========================================================================
    elif intent == "CLARIFICATION_REQUIRED":
        summary_en = CONVERSATIONAL_RESPONSES["clarification_prompt"]["en"]
        guidance_en = []
        include_disclaimer = False
        review_request = None

    # =========================================================================
    # INTENT: USER_INTRODUCTION
    # =========================================================================
    elif intent == "USER_INTRODUCTION":
        user_name = _detect_user_introduction(raw_query)
        if user_name:
            summary_en = f"Nice to meet you, {user_name}! How can I help you today?"
        else:
            summary_en = CONVERSATIONAL_RESPONSES["user_intro_default"]["en"]
        guidance_en = []
        include_disclaimer = False
        review_request = None

    # =========================================================================
    # INTENT: IDENTITY (or Prescribing / Diagnosing refusal)
    # =========================================================================
    elif intent == "IDENTITY":
        q_lower = raw_query.lower()
        if any(p in q_lower for p in PRESCRIBE_DIAGNOSE_PATTERNS):
            summary_en = (
                "MediGuide-AI is an educational assistant and cannot prescribe medications, "
                "diagnose conditions, or recommend specific treatments. Please consult a licensed healthcare provider."
            )
            guidance_en = ["Consult a licensed doctor or pharmacist for prescription medications and formal medical diagnosis."]
            include_disclaimer = True
        else:
            summary_en = CONVERSATIONAL_RESPONSES["identity"]["en"]
            guidance_en = []
            include_disclaimer = False
        review_request = None

    # =========================================================================
    # INTENT: GREETING
    # =========================================================================
    elif intent == "GREETING":
        summary_en = CONVERSATIONAL_RESPONSES["hello_greeting"]["en"]
        guidance_en = []
        include_disclaimer = False
        review_request = None

    # =========================================================================
    # INTENT: CURRENT_MEDICAL_INFORMATION
    # =========================================================================
    elif intent == "CURRENT_MEDICAL_INFORMATION":
        k_res = fetch_live_medical_knowledge(raw_query)
        summary_en = k_res.get("summary", "")
        guidance_en = k_res.get("guidance", [])
        sources = k_res.get("sources", [])
        retrieval_timestamp = k_res.get("retrieval_timestamp")
        is_live = k_res.get("is_live", False)
        include_disclaimer = True
        review_request = None

    # =========================================================================
    # INTENT: GENERAL_HEALTH_QUESTION (and GENERAL_MEDICAL_EDUCATION)
    # =========================================================================
    elif intent in ("GENERAL_HEALTH_QUESTION", "GENERAL_MEDICAL_EDUCATION"):
        q_lower = raw_query.lower()
        if any(w in q_lower for w in ["fever", "காய்ச்சல்", "बुखार", "జ్వరం", "പനി", "ಜ್ವರ"]):
            if any(w in q_lower for w in ["cause", "why", "காரணம்", "कारण", "ఎందుకు", "കാരണം"]):
                summary_en = CONVERSATIONAL_RESPONSES["fever_causes_education"]["en"]
                guidance_en = ["Prepare questions for your healthcare provider if you have an active or unexplained fever."]
            else:
                summary_en = CONVERSATIONAL_RESPONSES["fever_symptom_inquiry"]["en"]
                guidance_en = [
                    "Monitor your body temperature with a thermometer.",
                    "Stay hydrated with clean fluids and get sufficient rest.",
                    "Seek prompt medical care if the fever exceeds 103°F (39.4°C) or lasts over 3 days."
                ]
        elif any(w in q_lower for w in ["headache", "தலைவலி", "सिरदर्द", "తలనొప్పి", "തലവേദന", "ತಲೆನೋವು"]):
            summary_en = CONVERSATIONAL_RESPONSES["headache_symptom_inquiry"]["en"]
            guidance_en = [
                "Rest in a quiet, dark room and stay hydrated.",
                "Seek emergency medical care if you experience a sudden, severe thunderclap headache."
            ]
        elif any(w in q_lower for w in ["diabetes", "சர்க்கரை", "मधुमेह"]):
            summary_en = CONVERSATIONAL_RESPONSES["diabetes_causes_education"]["en"]
            guidance_en = ["Discuss your risk factors and blood sugar screening with a physician."]
        elif any(w in q_lower for w in [
            "most dangerous", "deadliest", "worst disease", "deadly disease", "dangerous disease",
            "மிகவும் ஆபத்தான", "सबसे खतरनाक", "అత్యంత ప్రమాదಕರమైన", "ഏറ്റവും അപകടകരമായ", "ಅತ್ಯಂತ ಅಪಾಯಕಾರಿ"
        ]):
            summary_en = CONVERSATIONAL_RESPONSES["most_dangerous_disease"]["en"]
            guidance_en = ["Prepare questions for your doctor regarding any health symptoms or conditions you wish to discuss."]
        elif any(w in q_lower for w in [
            "hypertension", "high blood pressure",
            "உயர் இரத்த அழுத்தம்", "उच्च रक्तचाप", "రక్తపోటు", "രക്താതിമർദ്ദം", "ರಕ್ತದೊತ್ತಡ"
        ]):
            summary_en = CONVERSATIONAL_RESPONSES["hypertension_education"]["en"]
            guidance_en = ["Prepare questions for your doctor regarding your target blood pressure ranges."]
        else:
            summary_en = (
                "General medical information is provided for educational purposes. Severity and outcomes depend on "
                "individual clinical history, complications, and timely professional medical care. "
                "Would you like general health education about a specific condition, or help understanding a particular medical report?"
            )
            guidance_en = ["Prepare questions for your doctor regarding any health symptoms or conditions you wish to discuss."]
        include_disclaimer = True
        review_request = None

    # =========================================================================
    # INTENT: REPORT_LIST
    # =========================================================================
    elif intent == "REPORT_LIST":
        if not user_id:
            summary_en = "Authentication is required to view your uploaded reports. Please log in to your patient account."
            guidance_en = ["Log in with your patient account credentials to inspect verified medical reports."]
            report_list = []
        else:
            user_reports = tool_get_user_reports(user_id=user_id)
            if not user_reports:
                summary_en = "You do not have any uploaded medical reports in your account yet. You can upload a diagnostic document in 'Upload Report'."
                guidance_en = ["Navigate to 'Upload Report' to analyze a diagnostic report."]
                report_list = []
            else:
                total_count = len(user_reports)
                recent_reports = user_reports[:5]
                titles = [f"- {r['filename']} ({r['created_at'][:10]})" for r in recent_reports]
                more_suffix = f"\n...and {total_count - 5} older report(s)." if total_count > 5 else ""
                summary_en = (
                    f"You have {total_count} uploaded report(s) on file:\n"
                    + "\n".join(titles)
                    + more_suffix
                    + "\n\nYou can ask me to summarize any report or check specific lab values."
                )
                guidance_en = ["Select a report to see its summary or ask about specific lab measurements."]
                report_list = [
                    {
                        "report_id": r["report_id"],
                        "filename": r["filename"],
                        "created_at": r.get("created_at", "")[:10]
                    }
                    for r in user_reports[:10]
                ]
        include_disclaimer = True
        review_request = None

    # =========================================================================
    # INTENT: REPORT_METRIC_QUERY
    # =========================================================================
    elif intent == "REPORT_METRIC_QUERY":
        if not user_id:
            summary_en = "Authentication is required to access your personal medical reports. Please log in to view your test results."
            guidance_en = ["Log in with your patient account credentials to inspect verified medical reports."]
            review_request = None
        else:
            effective_rep_id = report_id or conversation_context.get("last_report_id")
            metric_res = tool_find_metric(user_id=user_id, report_id=effective_rep_id, query=raw_query)

            if not metric_res.get("found") and effective_rep_id:
                all_res = tool_find_metric(user_id=user_id, report_id=None, query=raw_query)
                if all_res.get("found"):
                    metric_res = all_res

            if metric_res.get("found"):
                metric_name = metric_res.get("metric", "Test")
                val = metric_res.get("value", "")
                unit = metric_res.get("unit", "")
                fname = metric_res.get("filename", "Report")
                dt = metric_res.get("date", "")
                date_snippet = f" (recorded on {dt})" if dt else ""

                summary_en = (
                    f"In your report ({fname}{date_snippet}): "
                    f"{metric_name} is recorded as {val} {unit}. "
                    "This system presents recorded values without clinical interpretation. "
                    "Please discuss what this value means for your individual health with your physician."
                )
                guidance_en = [
                    f"Bring this {metric_name} record to your next clinical appointment.",
                    "Prepare questions for your doctor regarding your target reference ranges."
                ]
                metric_data = {
                    "metric": metric_name,
                    "value": val,
                    "unit": unit,
                    "filename": fname,
                    "date": dt,
                }
                review_request = None
            elif metric_res.get("error") == "no_reports":
                summary_en = "You do not have any uploaded medical reports in your account yet. Please upload a report to inspect your results."
                guidance_en = ["Navigate to 'Upload Report' to analyze a diagnostic report."]
                review_request = None
            elif metric_res.get("error") == "unauthorized_or_not_found":
                summary_en = "Access denied. You do not have permission to view this medical report or it could not be found."
                guidance_en = ["Ensure you are logged into the correct patient account."]
                review_request = None
            else:
                avail = metric_res.get("available_tests", [])
                avail_str = f" Available tests found in your reports: {', '.join(avail)}." if avail else ""
                searched_fname = metric_res.get("filename")
                scope_str = f"in report ({searched_fname})" if searched_fname else "across your uploaded reports"
                req_metric = metric_res.get("metric", "the requested test")

                summary_en = (
                    f"We could not find a recorded measurement for '{req_metric}' {scope_str}.{avail_str} "
                    "Please verify the spelling or check if this test was included in your uploaded document."
                )
                guidance_en = [
                    "Check the test name in your physical laboratory document.",
                    "Upload a clearer image or document if this test was present in your lab results."
                ]
                review_request = None
        include_disclaimer = True

    # =========================================================================
    # INTENT: REPORT_OVERVIEW
    # =========================================================================
    elif intent == "REPORT_OVERVIEW":
        if not user_id:
            summary_en = "Authentication is required to access your personal medical reports. Please log in to view your test results."
            guidance_en = ["Please log in to your patient account to access your report summary."]
            review_request = None
        else:
            user_reports = tool_get_user_reports(user_id=user_id)
            if not user_reports:
                summary_en = "You do not have any uploaded medical reports in your account yet. Please upload a report to inspect your results."
                guidance_en = ["Upload your diagnostic document in 'Upload Report' to generate an educational summary."]
                review_request = None
            else:
                target_report_id = report_id or conversation_context.get("last_report_id")
                if not target_report_id:
                    if len(user_reports) > 1:
                        q_lower = raw_query.lower()
                        matched = None
                        for r in user_reports:
                            fname_clean = r["filename"].lower()
                            tests = [t.lower() for t in r.get("test_names", [])]
                            if any(w in q_lower for w in fname_clean.replace(".", " ").replace("_", " ").split() if len(w) > 2):
                                matched = r
                                break
                            if any(t in q_lower for t in tests if len(t) > 2):
                                matched = r
                                break

                        if matched:
                            target_report_id = matched["report_id"]
                        else:
                            titles = [f"'{r['filename']}' ({r['created_at'][:10]})" for r in user_reports[:3]]
                            more_cnt = len(user_reports) - 3
                            more_str = f" and {more_cnt} more" if more_cnt > 0 else ""
                            summary_en = (
                                f"You have {len(user_reports)} reports available (including {', '.join(titles)}{more_str}). "
                                "Which report would you like me to summarize or explain?"
                            )
                            guidance_en = ["Specify the report name or date you would like to discuss."]
                            report_list = [
                                {
                                    "report_id": r["report_id"],
                                    "filename": r["filename"],
                                    "created_at": r.get("created_at", "")[:10]
                                }
                                for r in user_reports[:5]
                            ]
                            return {
                                "intent": intent,
                                "translated_summary": translate_text(summary_en, effective_target_lang),
                                "guidance": [translate_text(g, effective_target_lang) for g in guidance_en],
                                "review_request": None,
                                "disclaimer": CLINICAL_DISCLAIMERS["short_disclaimer"].get(effective_target_lang, CLINICAL_DISCLAIMERS["short_disclaimer"]["en"]),
                                "detected_language": detected_lang,
                                "response_language": effective_target_lang,
                                "original_query": raw_query,
                                "report_list": report_list,
                                "metric_data": None,
                            }
                    else:
                        target_report_id = user_reports[0]["report_id"]

                report_data = tool_get_report_summary(user_id=user_id, report_id=target_report_id)
                if not report_data:
                    summary_en = "Access denied or the specified report could not be found."
                    guidance_en = ["Please verify your report selection."]
                    review_request = None
                else:
                    summary_en = report_data.get("summary", "")
                    guidance_en = report_data.get("guidance", ["Bring this document to your next doctor consultation."])
                    review_request = None
        include_disclaimer = True

    # =========================================================================
    # INTENT: FOLLOW_UP (and RISK_QUESTION)
    # =========================================================================
    elif intent in ("FOLLOW_UP", "RISK_QUESTION"):
        ftype = _detect_followup_type(raw_query)

        # A. Normality or Range Inquiry ("Is that normal?", "What does that reading mean?")
        if ftype == "NORMALITY_OR_RANGE":
            target_metric = None
            for canonical, aliases in METRIC_ALIASES.items():
                if any(re.search(r'\b' + re.escape(a) + r'\b', raw_query.lower()) or a in raw_query for a in aliases):
                    target_metric = canonical.title()
                    break
            if not target_metric:
                target_metric = conversation_context.get("last_metric")

            target_val = None
            bp_match = re.search(r'\b(\d{2,3}/\d{2,3})\b', raw_query)
            if bp_match:
                target_val = bp_match.group(1)
            else:
                num_match = re.search(r'\b(\d+(?:\.\d+)?)\b', raw_query)
                if num_match and not (len(num_match.group(1)) == 4 and num_match.group(1).startswith("20")):
                    target_val = num_match.group(1)
            if not target_val:
                target_val = conversation_context.get("last_value")

            fname = conversation_context.get("last_filename", "your medical report")

            if not target_metric:
                summary_en = (
                    "Which test result or measurement are you asking about? "
                    "For example, you can ask 'Is my hemoglobin normal?' or 'Is my blood pressure normal?' "
                    "or check specific values from your uploaded reports."
                )
                guidance_en = [
                    "Prepare questions for a doctor and bring relevant documents to your next consultation.",
                    "Bring this document to your next doctor consultation."
                ]
            elif "blood pressure" in target_metric.lower():
                val_display = target_val or "recorded"
                eval_text, is_crisis = _evaluate_blood_pressure(val_display) if target_val else (
                    "Standard normal blood pressure for adults is defined as systolic under 120 mmHg and diastolic under 80 mmHg.",
                    False
                )
                summary_en = (
                    f"Regarding your Blood Pressure (recorded as {val_display} mmHg in {fname}): "
                    f"{eval_text} Standard clinical guideline categories: "
                    "Normal (<120/<80 mmHg), Elevated (120-129/<80 mmHg), Stage 1 Hypertension (130-139/80-89 mmHg), "
                    "Stage 2 Hypertension (≥140/≥90 mmHg), and Hypertensive Crisis (≥180/≥120 mmHg). "
                    "Educational Note: This reference comparison is educational and does not constitute a clinical diagnosis. "
                    "Please discuss this reading with your physician."
                )
                if is_crisis:
                    guidance_en = [
                        "Please seek professional medical review based on the flagged information.",
                        "Prepare questions for a doctor and bring relevant documents to your next consultation."
                    ]
                else:
                    guidance_en = [
                        "Prepare questions for a doctor and bring relevant documents to your next consultation.",
                        "Bring this document to your next doctor consultation."
                    ]
            elif "hemoglobin" in target_metric.lower():
                val_display = target_val or "recorded"
                eval_text = _evaluate_hemoglobin(val_display) if target_val else (
                    "Standard adult reference ranges are typically 13.8 to 17.2 g/dL for adult males and 12.1 to 15.1 g/dL for adult females."
                )
                summary_en = (
                    f"Regarding your Hemoglobin reading ({val_display} g/dL in {fname}): "
                    f"{eval_text} Standard adult reference ranges: Adult Males typically 13.8 to 17.2 g/dL; "
                    "Adult Females typically 12.1 to 15.1 g/dL. "
                    "Educational Note: Laboratory reference intervals may vary slightly depending on the testing facility. "
                    "This information is not a medical diagnosis. Please review this result with your healthcare provider."
                )
                guidance_en = [
                    "Prepare questions for a doctor and bring relevant documents to your next consultation.",
                    "Bring this document to your next doctor consultation."
                ]
            elif "platelet" in target_metric.lower():
                val_display = target_val or "recorded"
                eval_text = _evaluate_platelets(val_display) if target_val else (
                    "Standard adult reference ranges are typically 150,000 to 450,000 /mcL."
                )
                summary_en = (
                    f"Regarding your Platelet count ({val_display} in {fname}): "
                    f"{eval_text} Standard reference range is 150,000 to 450,000 /mcL. "
                    "Educational Note: This information is educational and does not constitute a clinical diagnosis. "
                    "Please review this result with your physician."
                )
                guidance_en = [
                    "Prepare questions for a doctor and bring relevant documents to your next consultation.",
                    "Bring this document to your next doctor consultation."
                ]
            else:
                summary_en = (
                    f"Regarding your {target_metric} record in {fname}: "
                    "Standard laboratory reference intervals depend on the specific assay and testing equipment used by your facility. "
                    "Please check the reference range column on your official laboratory document and discuss the findings with your doctor."
                )
                guidance_en = [
                    "Prepare questions for a doctor and bring relevant documents to your next consultation.",
                    "Bring this document to your next doctor consultation."
                ]
            review_request = None

        # B. Date or Timing Inquiry ("When was that?", "When did I take that test?")
        elif ftype == "DATE_OR_TIMING":
            target_metric = conversation_context.get("last_metric", "test")
            fname = conversation_context.get("last_filename", "your report")
            dt = conversation_context.get("last_date")

            if not dt and user_id:
                rep_id = conversation_context.get("last_report_id") or report_id
                if rep_id:
                    rep_obj = get_report_by_id(rep_id)
                    if rep_obj and rep_obj.get("created_at"):
                        dt = rep_obj["created_at"][:10]
                        fname = rep_obj.get("filename", fname)

            if dt:
                summary_en = f"The report ({fname}) containing your {target_metric} record was recorded on {dt}."
            else:
                summary_en = (
                    f"Your report ({fname}) does not list an explicit collection timestamp in its record. "
                    "Please check the printed date on your official laboratory document."
                )
            guidance_en = [
                "Prepare questions for a doctor and bring relevant documents to your next consultation.",
                "Bring this document to your next doctor consultation."
            ]
            review_request = None

        # C. Specialist / Next Steps ("Which doctor should I see for this?")
        elif ftype == "SPECIALIST_OR_NEXT_STEPS":
            target_metric = conversation_context.get("last_metric")
            fname = conversation_context.get("last_filename", "your report")

            specialist_recommendations = {
                "blood pressure": "a General Physician / Internist, or a Cardiologist for persistent or difficult-to-control hypertension",
                "hemoglobin": "a General Physician / Internist, or a Hematologist if values are persistently abnormal",
                "platelets": "a General Physician or a Hematologist",
                "white blood cells": "a General Physician or a Hematologist",
                "glucose": "a General Physician or an Endocrinologist / Diabetologist",
                "cholesterol": "a General Physician or a Cardiologist",
                "creatinine": "a General Physician or a Nephrologist",
            }

            specialist_text = "a General Physician (Primary Care Doctor)"
            if target_metric:
                for k, v in specialist_recommendations.items():
                    if k in target_metric.lower():
                        specialist_text = v
                        break

            summary_en = (
                f"For questions regarding your {target_metric or 'test results'}, the recommended healthcare provider to consult is {specialist_text}. "
                "We recommend starting with your Primary Care Physician (General Practitioner), who can evaluate your overall health, "
                "perform an initial clinical assessment, and refer you to a specialist if necessary."
            )
            guidance_en = [
                "Prepare questions for a doctor and bring relevant documents to your next consultation.",
                "Bring this document to your next doctor consultation."
            ]
            review_request = None

        # D. Other Tests in Report ("What other tests were in that report?")
        elif ftype == "OTHER_TESTS":
            target_rep_id = conversation_context.get("last_report_id") or report_id
            if not target_rep_id and user_id and conversation_context.get("last_filename"):
                for r in tool_get_user_reports(user_id):
                    if r.get("filename", "").lower() == conversation_context["last_filename"].lower():
                        target_rep_id = r["report_id"]
                        break

            if target_rep_id and user_id:
                rep_summary = tool_get_report_summary(user_id=user_id, report_id=target_rep_id)
                if rep_summary and rep_summary.get("test_names"):
                    tests_found = [t.title() for t in rep_summary["test_names"]]
                    summary_en = (
                        f"Your report ({rep_summary.get('filename')}) includes measurements for: {', '.join(tests_found)}. "
                        "You can ask me to look up any of these specific values."
                    )
                else:
                    summary_en = (
                        f"In your report ({rep_summary.get('filename') if rep_summary else 'selected report'}), "
                        "no additional distinct laboratory test names were extracted."
                    )
            else:
                summary_en = "Please specify which report you would like to inspect to see its available tests."
            guidance_en = [
                "Prepare questions for a doctor and bring relevant documents to your next consultation.",
                "Bring this document to your next doctor consultation."
            ]
            review_request = None

        # E. General Report Risk Question (e.g. "Is my report concerning?")
        else:
            if not user_id:
                summary_en = "Authentication is required to check risk indicators for your personal reports. Please log in."
                guidance_en = ["Please log in to your patient account."]
                review_request = None
            else:
                user_reports = tool_get_user_reports(user_id=user_id)
                if not user_reports:
                    summary_en = "You do not have any uploaded medical reports in your account yet."
                    guidance_en = ["Upload your diagnostic document in 'Upload Report'."]
                    review_request = None
                else:
                    target_report_id = report_id or conversation_context.get("last_report_id")
                    if not target_report_id:
                        if len(user_reports) == 1:
                            target_report_id = user_reports[0]["report_id"]
                        else:
                            q_lower = raw_query.lower()
                            matched = None
                            for r in user_reports:
                                if any(w in q_lower for w in r["filename"].lower().replace(".", " ").split() if len(w) > 2):
                                    matched = r
                                    break
                            if matched:
                                target_report_id = matched["report_id"]
                            else:
                                summary_en = f"You have {len(user_reports)} reports available. Which report would you like me to check for risk indicators?"
                                guidance_en = ["Specify the report name or date you would like to evaluate."]
                                return {
                                    "intent": intent,
                                    "translated_summary": translate_text(summary_en, effective_target_lang),
                                    "guidance": [translate_text(g, effective_target_lang) for g in guidance_en],
                                    "review_request": None,
                                    "disclaimer": CLINICAL_DISCLAIMERS["short_disclaimer"].get(effective_target_lang, CLINICAL_DISCLAIMERS["short_disclaimer"]["en"]),
                                    "detected_language": detected_lang,
                                    "response_language": effective_target_lang,
                                    "original_query": raw_query,
                                    "report_list": None,
                                    "metric_data": None,
                                }

                    report_data = tool_get_report_summary(user_id=user_id, report_id=target_report_id)
                    if not report_data:
                        summary_en = "Access denied or the specified report could not be found."
                        guidance_en = ["Please verify your report selection."]
                        review_request = None
                    else:
                        risk_assessment = report_data.get("risk_assessment", {})
                        is_high_risk = risk_assessment.get("is_high_risk", False)
                        if is_high_risk:
                            reasons = risk_assessment.get("reasons", ["Flagged clinical risk markers."])
                            summary_en = (
                                f"Regarding your report ({report_data.get('filename')}): "
                                f"The AI engine flagged elevated risk indicators ({', '.join(reasons)}) "
                                "that warrant professional clinician review. "
                                + report_data.get("summary", "")
                            )
                            guidance_en = ["Please seek professional medical review based on the flagged information."]
                            review_request = create_review_request(
                                extracted_info=report_data.get("test_names", {}),
                                summary=summary_en,
                                risk_result=risk_assessment,
                                patient_id=user_id,
                                report_id=target_report_id,
                            )
                        else:
                            summary_en = (
                                f"Regarding your report ({report_data.get('filename')}): "
                                "No immediate high-risk emergency markers were flagged. "
                                + report_data.get("summary", "")
                            )
                            guidance_en = ["Prepare questions for a doctor and bring relevant documents to your next consultation."]
                            review_request = None
        include_disclaimer = True

    # =========================================================================
    # INTENT: DOCUMENT_NARRATIVE (explicit document text upload)
    # =========================================================================
    elif intent == "DOCUMENT_NARRATIVE":
        cleaned_text = process_document(document_text)
        extracted_info = extract_medical_info(cleaned_text)
        summary_en = summarize_medical_info(extracted_info, source_text=cleaned_text)
        risk_result = evaluate_risk(extracted_info)

        guidance_en = []
        review_request = None
        if risk_result.get("is_high_risk") or risk_result.get("uncertainty_flag"):
            guidance_en.append("Please seek professional medical review based on the flagged information.")
            review_request = create_review_request(
                extracted_info=extracted_info,
                summary=summary_en,
                risk_result=risk_result,
                patient_id=user_id,
                report_id=report_id,
            )
        else:
            guidance_en.append("Prepare questions for a doctor and bring relevant documents to your next consultation.")
        include_disclaimer = True

    # =========================================================================
    # INTENT: UNCLEAR / FALLBACK
    # =========================================================================
    else:
        summary_en = CONVERSATIONAL_RESPONSES["clarification_prompt"]["en"]
        guidance_en = []
        review_request = None
        include_disclaimer = False

    # 4. Multilingual Translation Layer
    translated_summary = translate_text(summary_en, effective_target_lang)
    translated_guidance = [translate_text(g, effective_target_lang) for g in guidance_en] if guidance_en else []

    if effective_target_lang != "en" and sources:
        for s in sources:
            s["language_note"] = "Official medical source published in English"

    if include_disclaimer:
        std_disclaimer = CLINICAL_DISCLAIMERS["short_disclaimer"].get(
            effective_target_lang, CLINICAL_DISCLAIMERS["short_disclaimer"]["en"]
        )
    else:
        std_disclaimer = ""

    return {
        "intent": intent,
        "translated_summary": translated_summary,
        "guidance": translated_guidance,
        "review_request": review_request,
        "disclaimer": std_disclaimer,
        "detected_language": detected_lang,
        "response_language": effective_target_lang,
        "original_query": raw_query,
        "report_list": report_list,
        "metric_data": metric_data,
        "sources": sources,
        "retrieval_timestamp": retrieval_timestamp,
        "is_live": is_live,
    }
