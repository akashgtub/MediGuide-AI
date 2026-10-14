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
from ai.summarizer import (
    summarize_medical_info,
    get_summarization_pipeline,
    SUMMARIZATION_MODEL_NAME,
    SUMMARIZATION_MODEL_LICENSE,
    _chunk_text,
    _verify_neural_summary,
    _generate_deterministic_summary,
)
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

def test_medication_extraction_regression():
    """
    Regression test for Problem 1:
    - Input: 'Medications mentioned: None listed.' -> expected empty medication list.
    - Section headings like 'Medications mentioned:' must not be treated as medication entities.
    - Negative medication expressions (e.g., 'None listed', 'None', 'Prescriptions: None')
      must result in an empty medications list.
    """
    # 1. Negative statement with heading
    res_none = extract_medical_info("Medications mentioned: None listed.")
    assert res_none["medications"] == []
    # Section headings must not be treated as medication entities
    assert not any(ent["label"] == "Medication" for ent in res_none["entities"])

    # 2. Additional negative phrasing variations
    res_none_simple = extract_medical_info("Medications: None.")
    assert res_none_simple["medications"] == []

    res_denies = extract_medical_info("Patient denies medications.")
    assert res_denies["medications"] == []

    # 3. Positive contrast to ensure legitimate medications are still recognized
    res_positive = extract_medical_info("Medications: Aspirin 81 mg daily.")
    assert "aspirin" in res_positive["medications"]
    assert "medications" not in res_positive["medications"]

def test_test_name_extraction_regression():
    """
    Regression test for Problem 2:
    - Must NOT return 'med' as a test name.
    - Preserve complete, meaningful names such as 'Blood Pressure' and 'Hemoglobin'.
    - Keep model-recognized entities separate from deterministically parsed test names.
    """
    text = (
        "MediGuide AI Demo Medical Report. "
        "Blood Pressure: 130/85 mmHg. "
        "Hemoglobin: 12.5 g/dL."
    )
    res = extract_medical_info(text)

    # Must NOT return 'med' as a test name
    assert "med" not in res["test_names"]

    # Preserve complete, meaningful names
    assert "blood pressure" in res["test_names"]
    assert "hemoglobin" in res["test_names"]

    # Model-recognized entities are kept separate in 'entities'
    # and not conflated into 'test_names'
    assert isinstance(res["entities"], list)
    for ent in res["entities"]:
        assert ent["source"] == "ner_model"
        # Spurious 'med' subword token is not an entity
        assert ent["text"].lower() != "med"

def test_observation_extraction_regression():
    """
    Regression test for Problem 3:
    - For text 'Hemoglobin: 12.5 g/dL. Reported observation: Patient reports fatigue for three days.',
      do not include '12.5 g/dL' inside the observation.
    - Extract observation text separately while preserving exact source wording.
    """
    text = "Hemoglobin: 12.5 g/dL. Reported observation: Patient reports fatigue for three days."
    res = extract_medical_info(text)

    assert len(res["observations"]) == 1
    obs = res["observations"][0]

    # Must not contain measurement values or units
    assert "12.5" not in obs
    assert "g/dl" not in obs.lower()
    assert "hemoglobin" not in obs.lower()

    # Preserves exact source wording
    assert obs == "Patient reports fatigue for three days."

def test_synthetic_report_structured_output_quality():
    """
    Regression test for full synthetic medical report structured output.
    Verifies actual structured dictionary content and source fidelity:
    - Medication list is empty (negative statement handled properly)
    - Test names contain complete names ('blood pressure', 'hemoglobin') and no 'med'
    - Observations isolate narrative wording without measurement numbers or units
    - Original numeric values and units are faithfully preserved
    - Dates are preserved
    - Inferred info remains empty (no diagnosis or invented data)
    """
    synthetic_report_text = (
        "MediGuide AI Demo Medical Report\n"
        "Patient ID: DEMO001\n"
        "Date: 07 October 2026\n"
        "Blood Pressure: 130/85 mmHg\n"
        "Hemoglobin: 12.5 g/dL\n"
        "Reported observation:\n"
        "Patient reports fatigue for three days.\n"
        "Medications mentioned:\n"
        "None listed."
    )
    res = extract_medical_info(synthetic_report_text)

    # 1. Medications: empty, no headings as medications
    assert res["medications"] == []
    assert not any(ent["label"] == "Medication" for ent in res["entities"])

    # 2. Test names: no 'med', meaningful complete names preserved
    assert "med" not in res["test_names"]
    assert "blood pressure" in res["test_names"]
    assert "hemoglobin" in res["test_names"]

    # 3. Observation: clean narrative without measurement values
    assert res["observations"] == ["Patient reports fatigue for three days."]
    assert not any("12.5" in o for o in res["observations"])
    assert not any("g/dl" in o.lower() for o in res["observations"])

    # 4. Source fidelity: preserved numeric values, units, and dates
    assert res["test_values"] == ["130/85", "12.5"]
    assert res["units"] == ["mmhg", "g/dl"]
    assert any("07 october 2026" in d or "october" in d for d in res["dates"])
    assert res["symptoms"] == ["fatigue"]

    # 5. Inferred info: strictly empty (no diagnostic assumption)
    assert res["inferred_info"] == []

