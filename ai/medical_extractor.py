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

    return merged


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
            "start": 105,
            "end": 112,
            "confidence": 0.9987,
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

    # 1. Run Pretrained Biomedical Named Entity Recognition
    ner_entities = extract_biomedical_entities(text)
    result['entities'] = ner_entities

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
            if ent_lower not in result['medications']:
                result['medications'].append(ent_lower)
        elif label == "Diagnostic_procedure":
            if ent_lower not in result['test_names']:
                result['test_names'].append(ent_lower)

    text_lower = text.lower()

    # 2. Deterministic Keyword Matching (supplementary & fallback preservation)
    symptoms_list = ['fever', 'headache', 'chest pain', 'difficulty breathing', 'severe bleeding', 'nausea', 'fatigue']
    medications_list = ['aspirin', 'ibuprofen', 'amoxicillin', 'lisinopril']
    tests_list = ['blood pressure', 'heart rate', 'glucose', 'cholesterol', 'hba1c', 'hemoglobin']

    for sym in symptoms_list:
        if sym in text_lower and sym not in result['symptoms']:
            result['symptoms'].append(sym)

    for med in medications_list:
        if med in text_lower and med not in result['medications']:
            result['medications'].append(med)

    for test in tests_list:
        if test in text_lower and test not in result['test_names']:
            result['test_names'].append(test)

    # 3. Deterministic Parsing: Dates
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

    # 4. Deterministic Parsing: Numeric Measurements & Units
    # Extracts verified test values and associated scientific units
    measurements = re.findall(r'(\d+(?:\.\d+)?(?:/\d+)?)\s*(mg/dl|mmhg|bpm|%|g/dl)', text_lower)
    for val, unit in measurements:
        if val not in result['test_values']:
            result['test_values'].append(val)
        if unit not in result['units']:
            result['units'].append(unit)

    # 5. Deterministic Parsing: Observations
    sentences = re.split(r'[.!?]+', text)
    for s in sentences:
        s_clean = s.strip()
        s_lower = s_clean.lower()
        if any(keyword in s_lower for keyword in ('observed', 'noted', 'reports', 'reported', 'appears')):
            if s_clean and s_clean not in result['observations']:
                result['observations'].append(s_clean)

    return result
