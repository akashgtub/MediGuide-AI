from ai.document_processor import process_document
from ai.medical_extractor import extract_medical_info
from ai.summarizer import summarize_medical_info
from ai.translator import translate_text
from risk.risk_engine import evaluate_risk
from human_review.review_manager import create_review_request

def process_patient_request(document_text: str, target_language: str = "en") -> dict:
    """
    Combine summary, translation, and risk information.
    Give safe next-step guidance.
    Escalate high-risk/uncertain cases.
    """
    # 1. Process Document
    cleaned_text = process_document(document_text)
    
    # 2. Extract Info
    extracted_info = extract_medical_info(cleaned_text)
    
    # 3. Summarize
    summary = summarize_medical_info(extracted_info)
    
    # 4. Evaluate Risk
    risk_result = evaluate_risk(extracted_info)
    
    # 5. Determine Guidance and Escalation
    guidance = []
    review_request = None
    
    if risk_result.get("is_high_risk") or risk_result.get("uncertainty_flag"):
        guidance.append("Please seek professional medical review based on the flagged information.")
        review_request = create_review_request(extracted_info, summary, risk_result)
    else:
        guidance.append("Prepare questions for a doctor and bring relevant documents to your next consultation.")
        
    # 6. Translate
    translated_summary = translate_text(summary, target_language)
    translated_guidance = [translate_text(g, target_language) for g in guidance]
    
    return {
        "translated_summary": translated_summary,
        "guidance": translated_guidance,
        "review_request": review_request,
        "disclaimer": translate_text("This system does not diagnose or prescribe.", target_language)
    }
