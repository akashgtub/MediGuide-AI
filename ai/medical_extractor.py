import os
import re
import logging
from typing import Dict, List, Any

# Silence OneDNN precision/round-off informational messages
os.environ["TF_ENABLE_ONEDNN_OPTS"] = "0"
# Prevent OpenMP runtime conflict when both Paddle and PyTorch are loaded on Windows
os.environ["KMP_DUPLICATE_LIB_OK"] = "TRUE"

# Model metadata
NER_MODEL_NAME = "d4data/biomedical-ner-all"
NER_MODEL_LINK = "https://huggingface.co/d4data/biomedical-ner-all"
NER_MODEL_LICENSE = "Apache-2.0"

# Verified supported categories from d4data/biomedical-ner-all
SUPPORTED_NER_CATEGORIES = {
    "Sign_symptom",
    "Disease_disorder",
    "Diagnostic_procedure",
    "Medication",
    "Dosage",
    "Biological_structure",
    "Clinical_event",
    "Duration",
    "Date",
    "Lab_value",
}

# Exclusion terms for medication headers and non-medication text
MEDICATION_EXCLUSION_TERMS = {
    "medication", "medications", "med", "meds", "medicine", "medicines",
    "drug", "drugs", "prescription", "prescriptions", "rx", "treatment",
    "treatments", "therapy", "none", "none listed", "none noted", "nil", "n/a",
    "denies", "no", "no medications", "unspecified", "not listed", "none reported"
}

# Stopwords and noise terms that should not be extracted as test names
TEST_NAME_STOPWORDS = {
    "med", "demo", "mediguide", "mediguide ai", "ai", "report", "medical report",
    "patient", "patient id", "id", "date", "observation", "reported observation",
    "clinical", "procedure", "test", "tests", "examination", "exam", "result", "results"
}

# General non-entity noise terms to filter from raw NER output
RAW_NER_FILTER_TERMS = {
    "med", "demo", "none", "medications", "medication", "mediguide", "mediguide ai", "ai"
}

# Module-level singleton for the NER pipeline
_ner_pipeline = None

def get_ner_pipeline():
    """
    Lazily load and return the Hugging Face token-classification pipeline
    for the pretrained biomedical NER model 'd4data/biomedical-ner-all'.
    Handles missing dependencies or loading errors safely.
    """
    global _ner_pipeline
    if _ner_pipeline is not None:
        return _ner_pipeline

    try:
        from transformers import pipeline
        _ner_pipeline = pipeline(
            "ner",
            model=NER_MODEL_NAME,
            aggregation_strategy="simple"
        )
    except Exception as e:
        logging.warning(f"Could not initialize biomedical NER model '{NER_MODEL_NAME}': {e}")
        _ner_pipeline = None

    return _ner_pipeline


def _merge_adjacent_entities(raw_entities: List[Dict[str, Any]], text: str) -> List[Dict[str, Any]]:
    """
    Merge adjacent subword tokens belonging to the same entity category,
    preserving exact spans and slice from original source text.
    Filters out noise tokens and document headers.
    """
    if not raw_entities:
        return []

    merged: List[Dict[str, Any]] = []
    for ent in raw_entities:
        group = ent.get("entity_group") or ent.get("entity")
        start = ent.get("start")
        end = ent.get("end")
        score = float(ent.get("score", 0.0))

        if not group or start is None or end is None:
            continue

        # Check if adjacent to the previous entity of the same category
        if merged and merged[-1]["label"] == group and (start <= merged[-1]["end"] + 1):
            prev = merged[-1]
            prev["end"] = max(prev["end"], end)
            prev["text"] = text[prev["start"]:prev["end"]]
            prev["confidence"] = min(prev["confidence"], round(score, 4))
        else:
            merged.append({
                "text": text[start:end],
                "label": group,
                "start": start,
                "end": end,
                "confidence": round(score, 4),
                "source": "ner_model"
            })

    # Filter out obvious non-entity noise terms (e.g., 'Med' from 'MediGuide', 'None' as Lab_value, 'Medications' as Medication)
    clean_entities: List[Dict[str, Any]] = []
    for ent in merged:
        t_clean = ent["text"].strip().lower()
        if t_clean in RAW_NER_FILTER_TERMS:
            continue
        if ent["label"] == "Medication" and t_clean in MEDICATION_EXCLUSION_TERMS:
            continue
        if ent["label"] == "Diagnostic_procedure" and t_clean in TEST_NAME_STOPWORDS:
            continue
        if ent["label"] == "Lab_value" and t_clean in {"demo", "none", "n/a", "nil"}:
            continue
        clean_entities.append(ent)

    return clean_entities


def _chunk_and_predict(pipeline_obj: Any, text: str, max_chunk_chars: int = 1500) -> List[Dict[str, Any]]:
    """
    Safely process long documents by chunking at sentence boundaries,
    re-aligning character offsets to the original source text.
    """
    if len(text) <= max_chunk_chars:
        try:
            raw = pipeline_obj(text)
            return _merge_adjacent_entities(raw, text)
        except Exception as e:
            logging.error(f"NER inference failed on text: {e}")
            return []

    # Chunk long documents by sentence or paragraph breaks
    chunks: List[tuple] = []
    pattern = re.compile(r'(?<=[.!?\n])\s+')
    splits = pattern.split(text)

    current_chunk: List[str] = []
    current_len = 0
    current_start = 0

    for segment in splits:
        if not segment:
            continue
        seg_start = text.find(segment, current_start)
        if seg_start == -1:
            seg_start = current_start

        if current_len + len(segment) > max_chunk_chars and current_chunk:
            chunk_str = text[current_start:seg_start].strip()
            if chunk_str:
                chunks.append((chunk_str, current_start))
            current_chunk = [segment]
            current_len = len(segment)
            current_start = seg_start
        else:
            current_chunk.append(segment)
            current_len += len(segment) + 1

    if current_chunk:
        chunk_str = text[current_start:].strip()
        if chunk_str:
            chunks.append((chunk_str, current_start))

    all_entities: List[Dict[str, Any]] = []
    for chunk_str, offset in chunks:
        try:
            raw = pipeline_obj(chunk_str)
            merged = _merge_adjacent_entities(raw, chunk_str)
            for m in merged:
                m["start"] += offset
                m["end"] += offset
                all_entities.append(m)
        except Exception as e:
            logging.error(f"NER inference failed on chunk: {e}")

    return all_entities


def extract_biomedical_entities(text: str) -> List[Dict[str, Any]]:
    """
    Extract recognized biomedical named entities from text using the pretrained
    model 'd4data/biomedical-ner-all'.

    Returns structured entities preserving original source text and spans:
    [
        {
            "text": "fatigue",
            "label": "Sign_symptom",
            "start": 163,
            "end": 170,
            "confidence": 0.9999,
            "source": "ner_model"
        },
        ...
    ]

    Safety Guarantee:
    This function ONLY identifies recognized mentions.
    It does NOT make clinical decisions, diagnoses, or prescriptions.
    """
    if not text or not isinstance(text, str) or not text.strip():
        return []

    pipeline_obj = get_ner_pipeline()
    if pipeline_obj is None:
        logging.warning("Biomedical NER pipeline unavailable; returning empty entity list.")
        return []

    return _chunk_and_predict(pipeline_obj, text)


def _extract_observations(text: str) -> List[str]:
    """
    Extract observation text separately while preserving exact source wording.
    Prevents inclusion of preceding lab test values/units (e.g., '12.5 g/dL').
    Handles both inline headers ("Reported observation: text") and multiline
    headers ("Reported observation:\ntext").
    Splits sentences safely without breaking decimal numbers (e.g. 12.5).
    """
    observations: List[str] = []

    # Normalize multiline observation headers (e.g. "Reported observation:\nPatient...")
    normalized_text = re.sub(
        r'\b(reported\s+observation|clinical\s+observation|observation|notes?)\s*:\s*\n+',
        r'\1: ',
        text,
        flags=re.IGNORECASE
    )

    # Decimal-safe sentence split: matches sentence-ending punctuation or newlines,
    # but does NOT match a period that is between two digits (e.g. 12.5).
    sentences = [s.strip() for s in re.split(r'(?<!\d)\.|\.(?!\d)|[!?]|\n+', normalized_text) if s.strip()]

    for sentence in sentences:
        sentence_lower = sentence.lower()

        # Ignore standalone heading lines that contain no body content
        if re.match(r'^(?:reported\s+observation|clinical\s+observation|observation|notes?)\s*:\s*$', sentence_lower):
            continue

        # Check for explicit observation headers (e.g., "Reported observation:", "Observation:")
        header_match = re.search(
            r'(?:reported\s+observation|clinical\s+observation|observation|notes?)\s*:\s*(.+)',
            sentence,
            flags=re.IGNORECASE
        )
        if header_match:
            obs_content = header_match.group(1).strip()
            # Truncate at subsequent section headers if multiple fields were concatenated
            obs_content = re.split(r'\b(?:Medications?|Tests?|Vitals?|Date|Patient\s+ID)\b\s*:', obs_content, flags=re.IGNORECASE)[0].strip()
            obs_clean = obs_content.rstrip('.') + '.' if obs_content and not obs_content.endswith('.') else obs_content
            if obs_clean and obs_clean not in observations:
                observations.append(obs_clean)
            continue

        # Check for narrative observation keywords (e.g. "It was noted that patient was tired.")
        if any(keyword in sentence_lower for keyword in ('observed', 'noted', 'reports', 'reported', 'appears')):
            # Strip any leading test measurements or units if glued (e.g. "12.5 g/dL Patient reports...")
            cleaned = re.sub(
                r'^(?:.*?\b(?:\d+(?:\.\d+)?(?:/\d+)?\s*(?:mg/dl|mmhg|bpm|%|g/dl))\b[.,:]?\s*)',
                '',
                sentence,
                flags=re.IGNORECASE
            ).strip()
            # Strip trailing section headers if any
            cleaned = re.split(r'\b(?:Medications?|Tests?|Vitals?|Date|Patient\s+ID)\b\s*:', cleaned, flags=re.IGNORECASE)[0].strip()
            obs_clean = cleaned.rstrip('.') + '.' if cleaned and not cleaned.endswith('.') else cleaned
            if obs_clean and obs_clean not in observations:
                observations.append(obs_clean)

    return observations


def extract_medical_info(text: str) -> Dict[str, Any]:
    """
    Extract structured medical information from text.
    Combines pretrained biomedical NER with deterministic parsing for
    numbers, units, dates, and observations.

    Distinguishes extracted entities from inferred information:
    - 'entities': model-extracted entity occurrences with labels, offsets, confidence.
    - 'inferred_info': empty list (no clinical inferences or assumptions made).
    - 'symptoms', 'medications', 'test_names': populated from model and deterministic matches.
    - 'test_values', 'units', 'dates': deterministically parsed to prevent hallucination.

    Safety:
    Do NOT diagnose, prescribe, or recommend treatment.
    Handle missing information safely.
    """
    result: Dict[str, Any] = {
        'patient_info': {},
        'symptoms': [],
        'medications': [],
        'test_names': [],
        'test_values': [],
        'units': [],
        'dates': [],
        'observations': [],
        'entities': [],
        'inferred_info': []
    }

    if not text or not isinstance(text, str) or not text.strip():
        return result

    text_lower = text.lower()

    # 1. Run Pretrained Biomedical Named Entity Recognition
    ner_entities = extract_biomedical_entities(text)
    result['entities'] = ner_entities

    # Check for negative medication statement (e.g., "Medications mentioned: None listed.")
    has_none_medications = bool(re.search(
        r'\b(?:medications?|meds?|drugs?|prescriptions?)(?:\s+(?:mentioned|noted|taken|ordered|prescribed))?\s*:\s*(?:none\s+listed|none|no(?:ne)?\s+reported|nil|n/a|denies|negative|not\s+listed)\b',
        text_lower
    ))

    # Map supported NER entity categories to structured fields
    for ent in ner_entities:
        label = ent.get("label", "")
        ent_text = ent.get("text", "").strip()
        if not ent_text:
            continue
        ent_lower = ent_text.lower()

        if label in ("Sign_symptom", "Disease_disorder"):
            if ent_lower not in result['symptoms']:
                result['symptoms'].append(ent_lower)
        elif label == "Medication":
            # Exclude section headings and negated medications
            if not has_none_medications and ent_lower not in MEDICATION_EXCLUSION_TERMS:
                if ent_lower not in result['medications']:
                    result['medications'].append(ent_lower)
        elif label == "Diagnostic_procedure":
            # Model-recognized diagnostic procedures remain in result['entities'].
            # Deterministically parsed test names are kept separate in result['test_names']
            # to prevent model subword noise (e.g. 'med') from corrupting test name records.
            pass

    # 2. Deterministic Parsing: Test Names (kept separate from model entities)
    tests_list = ['blood pressure', 'heart rate', 'glucose', 'cholesterol', 'hba1c', 'hemoglobin']
    for test in tests_list:
        if test in text_lower and test not in result['test_names']:
            result['test_names'].append(test)

    # Deterministic pattern matching for test names preceding measurements (e.g. "Blood Pressure: 130/85 mmHg")
    test_line_matches = re.findall(
        r'\b([A-Za-z][A-Za-z\s]{1,30})\s*:\s*\d+(?:\.\d+)?(?:/\d+)?\s*(?:mg/dl|mmhg|bpm|%|g/dl)',
        text,
        flags=re.IGNORECASE
    )
    for t_match in test_line_matches:
        t_clean = t_match.strip().lower()
        if t_clean and t_clean not in TEST_NAME_STOPWORDS and t_clean not in result['test_names']:
            result['test_names'].append(t_clean)

    # 3. Deterministic Keyword Matching for Symptoms and Medications (fallback preservation)
    symptoms_list = ['fever', 'headache', 'chest pain', 'difficulty breathing', 'severe bleeding', 'nausea', 'fatigue']
    medications_list = ['aspirin', 'ibuprofen', 'amoxicillin', 'lisinopril']

    for sym in symptoms_list:
        if sym in text_lower and sym not in result['symptoms']:
            result['symptoms'].append(sym)

    if not has_none_medications:
        for med in medications_list:
            if med in text_lower and med not in result['medications']:
                result['medications'].append(med)

    # 4. Deterministic Parsing: Dates
    # Preserves exact date strings reliably without model hallucination
    date_patterns = [
        r'\b\d{4}-\d{2}-\d{2}\b',
        r'\b\d{1,2}[/-]\d{1,2}[/-]\d{2,4}\b',
        r'\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]* \d{1,2}(?:,? \d{4})?\b',
        r'\b\d{1,2} (?:jan|feb|mar|apr|may|jun|jul|aug|sep|oct|nov|dec)[a-z]*(?: \d{4})?\b'
    ]
    combined_date_regex = '|'.join(date_patterns)
    found_dates = re.findall(combined_date_regex, text_lower)
    for d in found_dates:
        d_clean = d.strip()
        if d_clean and d_clean not in result['dates']:
            result['dates'].append(d_clean)

    # 5. Deterministic Parsing: Numeric Measurements & Units
    # Extracts verified test values and associated scientific units
    measurements = re.findall(r'(\d+(?:\.\d+)?(?:/\d+)?)\s*(mg/dl|mmhg|bpm|%|g/dl)', text_lower)
    for val, unit in measurements:
        if val not in result['test_values']:
            result['test_values'].append(val)
        if unit not in result['units']:
            result['units'].append(unit)

    # 6. Deterministic Parsing: Observations
    result['observations'] = _extract_observations(text)

    return result
