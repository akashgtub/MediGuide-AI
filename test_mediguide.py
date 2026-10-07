from mediguide import welcome_message
from ai.document_processor import process_document
from ai.medical_extractor import extract_medical_info
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
    res = extract_medical_info("Patient has a fever and headache, taking aspirin.")
    assert "fever" in res["symptoms"]
    assert "headache" in res["symptoms"]
    assert "aspirin" in res["medications"]
    
    empty_res = extract_medical_info("")
    assert empty_res["symptoms"] == []

def test_summarizer():
    res = extract_medical_info("fever")
    summary = summarize_medical_info(res)
    assert "fever" in summary
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