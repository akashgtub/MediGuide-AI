import os
import tempfile
from PIL import Image, ImageDraw

from mediguide import welcome_message
from ai.document_processor import process_document, extract_text_from_document
from ai.medical_extractor import (
    extract_medical_info,
    extract_biomedical_entities,
    get_ner_pipeline,
    NER_MODEL_NAME,
    SUPPORTED_NER_CATEGORIES,
)
from ai.summarizer import summarize_medical_info
from ai.translator import translate_text
from risk.risk_engine import evaluate_risk
from human_review.review_manager import create_review_request
from ai.patient_agent import process_patient_request

def test_welcome_message():
    result = welcome_message()
    assert result == "Welcome to MediGuide AI"

def test_document_processor():
    assert process_document("  Hello \n  World  ") == "Hello World"
    assert process_document("") == ""

def test_medical_extractor():
    text = "Patient has a fever and headache, taking aspirin. Blood pressure was 120/80 mmHg on Oct 12. It was noted that patient was tired."
    res = extract_medical_info(text)
    assert "fever" in res["symptoms"]
    assert "headache" in res["symptoms"]
    assert "aspirin" in res["medications"]
    assert "blood pressure" in res["test_names"]
    assert "120/80" in res["test_values"]
    assert "mmhg" in res["units"]
    assert "oct 12" in res["dates"]
    assert any("noted" in obs.lower() for obs in res["observations"])
    
    empty_res = extract_medical_info("")
    assert empty_res["symptoms"] == []

def test_summarizer():
    res = extract_medical_info("fever and blood pressure on Oct 12")
    summary = summarize_medical_info(res)
    assert "fever" in summary
    assert "blood pressure" in summary
    assert "oct 12" in summary
    assert "not a diagnosis" in summary

def test_translator():
    assert translate_text("Hello", "es") == "[Translated to es]: Hello"
    assert translate_text("Hello", "en") == "Hello"

def test_risk_engine():
    res = evaluate_risk({"symptoms": ["chest pain"]})
    assert res["is_high_risk"] == True
    
    res_low = evaluate_risk({"symptoms": ["fever"], "medications": ["aspirin"]})
    assert res_low["is_high_risk"] == False
    assert res_low["uncertainty_flag"] == False
    
    res_empty = evaluate_risk({})
    assert res_empty["uncertainty_flag"] == True

def test_review_manager():
    req = create_review_request({}, "Summ", {"is_high_risk": True, "reasons": ["chest pain"]})
    assert req["risk_level"] == "HIGH"
    assert req["status"] == "PENDING_REVIEW"
    assert "chest pain" in req["escalation_reasons"]
    assert "FINAL CLINICAL DECISIONS" in req["disclaimer"]

def test_patient_agent():
    # Test low risk
    res = process_patient_request("I have a fever and am taking aspirin.", target_language="en")
    assert res["review_request"] is None
    assert "Prepare questions" in res["guidance"][0]
    
    # Test high risk
    res_high = process_patient_request("I have chest pain.", target_language="en")
    assert res_high["review_request"] is not None
    assert res_high["review_request"]["risk_level"] == "HIGH"
    assert "Please seek professional" in res_high["guidance"][0]

def _ensure_synthetic_report(path: str = "synthetic_report.png") -> str:
    if not os.path.exists(path):
        img = Image.new("RGB", (700, 350), color=(255, 255, 255))
        draw = ImageDraw.Draw(img)
        lines = [
            "MediGuide AI Demo Medical Report",
            "Patient ID: DEMO001",
            "Date: 07 October 2026",
            "Blood Pressure: 130/85 mmHg",
            "Hemoglobin: 12.5 g/dL",
            "Reported observation:",
            "Patient reports fatigue for three days.",
            "Medications mentioned:",
            "None listed.",
        ]
        y = 20
        for line in lines:
            draw.text((20, y), line, fill=(0, 0, 0))
            y += 30
        img.save(path)
    return path

def test_document_processor_ocr():
    # Use synthetic demo medical report
    img_path = _ensure_synthetic_report("synthetic_report.png")
    assert os.path.exists(img_path)

    text = extract_text_from_document(img_path)
    text_normalized = " ".join(text.lower().split())

    # Verify extracted medical report contents
    assert "patient id" in text_normalized
    assert "blood pressure" in text_normalized
    assert "hemoglobin" in text_normalized
    assert "fatigue" in text_normalized

    # Verify missing file safely
    assert extract_text_from_document("non_existent_file.png") == ""
    assert extract_text_from_document("") == ""

    # Verify empty document safely
    with tempfile.NamedTemporaryFile(suffix=".png", delete=False) as empty_file:
        empty_path = empty_file.name
    try:
        assert extract_text_from_document(empty_path) == ""
    finally:
        if os.path.exists(empty_path):
            os.remove(empty_path)

    # Verify unsupported file format safely
    with tempfile.NamedTemporaryFile(suffix=".unsupported", delete=False) as unsup_file:
        unsup_file.write(b"unsupported content")
        unsup_path = unsup_file.name
    try:
        assert extract_text_from_document(unsup_path) == ""
    finally:
        if os.path.exists(unsup_path):
            os.remove(unsup_path)

def test_biomedical_ner_entities():
    # Test biomedical entity recognition on synthetic clinical text
    synthetic_text = "Patient reports fatigue and fever for three days, taking aspirin. Blood pressure was measured."
    entities = extract_biomedical_entities(synthetic_text)
    
    assert isinstance(entities, list)
    assert len(entities) > 0

    # Verify entity structure, source attribution, and exact span slicing
    labels_found = set()
    for ent in entities:
        assert "text" in ent
        assert "label" in ent
        assert "start" in ent
        assert "end" in ent
        assert "confidence" in ent
        assert ent["source"] == "ner_model"
        # Verify exact slice from original source text
        assert synthetic_text[ent["start"]:ent["end"]] == ent["text"]
        assert ent["label"] in SUPPORTED_NER_CATEGORIES
        labels_found.add(ent["label"])

    # Model should recognize symptoms such as fatigue or fever
    entity_texts = [e["text"].lower() for e in entities]
    assert any("fatigue" in t or "fever" in t for t in entity_texts)
    assert "Sign_symptom" in labels_found or "Disease_disorder" in labels_found

def test_biomedical_ner_edge_cases():
    # 1. Empty input
    assert extract_biomedical_entities("") == []
    assert extract_biomedical_entities("   ") == []
    assert extract_biomedical_entities(None) == []

    # 2. Long document safety (chunking at boundaries)
    long_synthetic_doc = "Patient reports mild fatigue and headaches. " * 50
    long_entities = extract_biomedical_entities(long_synthetic_doc)
    assert isinstance(long_entities, list)
    assert len(long_entities) > 0
    # Check that character offsets are valid within long text
    for ent in long_entities:
        assert long_synthetic_doc[ent["start"]:ent["end"]] == ent["text"]

    # 3. Model failure simulation (graceful fallback)
    import ai.medical_extractor as me
    original_pipeline = me._ner_pipeline
    try:
        # Simulate uninitialized/failing pipeline
        me._ner_pipeline = None
        def mock_get_none():
            return None
        me.get_ner_pipeline = mock_get_none
        assert me.extract_biomedical_entities("Patient has a fever") == []
        # extract_medical_info should still work safely via deterministic fallback
        fallback_res = me.extract_medical_info("Patient has a fever and headache, taking aspirin.")
        assert "fever" in fallback_res["symptoms"]
        assert "headache" in fallback_res["symptoms"]
        assert "aspirin" in fallback_res["medications"]
        assert fallback_res["entities"] == []
    finally:
        me._ner_pipeline = original_pipeline
        me.get_ner_pipeline = get_ner_pipeline

def test_medical_extractor_distinguishes_inferred_from_extracted():
    text = "Date: 07 October 2026. Blood Pressure: 130/85 mmHg. Hemoglobin: 12.5 g/dL. Patient reports fatigue. Medications: None listed."
    res = extract_medical_info(text)

    # Distinguishes extracted entities from inferred info
    assert "entities" in res
    assert "inferred_info" in res
    assert res["inferred_info"] == []  # No inferred diagnoses or prescriptions

    # Verify deterministic parsing of values and units
    assert "130/85" in res["test_values"]
    assert "12.5" in res["test_values"]
    assert "mmhg" in res["units"]
    assert "g/dl" in res["units"]
    assert any("october" in d for d in res["dates"])
    assert "fatigue" in res["symptoms"]
